// Package discovery resolves explicit files and directories into a bounded,
// deterministic suite without launching test targets.
package discovery

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
)

const (
	MaxVisitedEntries = 10_000
	MaxSelectedSpecs  = 1_000
)

var excludedDirectoryNames = map[string]struct{}{
	".cache":       {},
	".git":         {},
	".playtestr":   {},
	"artifacts":    {},
	"node_modules": {},
}

// Spec is one selected test specification. Path is suitable for execution and
// DisplayPath is the stable path printed by the CLI.
type Spec struct {
	Path        string
	DisplayPath string
	info        fs.FileInfo
}

type limits struct {
	visited  int
	selected int
}

type excludedPath struct {
	path string
	tree bool
}

// Resolve expands every argument in place. Explicit files retain argument
// order; each directory is recursively expanded and sorted by normalized
// relative path. Files referring to the same filesystem object are selected
// only once.
func Resolve(arguments []string) ([]Spec, error) {
	return ResolveExcluding(arguments, nil)
}

// ResolveExcluding additionally omits output files or trees while expanding a
// directory. Explicitly named files are never omitted, so callers can diagnose
// an input/output alias instead of silently selecting nothing.
func ResolveExcluding(arguments, excludedPaths []string) ([]Spec, error) {
	return resolve(arguments, excludedPaths, MaxVisitedEntries, MaxSelectedSpecs)
}

func resolve(arguments, excludedPaths []string, maxVisited, maxSelected int) ([]Spec, error) {
	var selected []Spec
	state := limits{}
	exclusions := make([]excludedPath, 0, len(excludedPaths))
	for _, path := range excludedPaths {
		if path == "" {
			continue
		}
		item := excludedPath{path: canonical(path), tree: true}
		if info, err := os.Stat(path); err == nil && !info.IsDir() {
			item.tree = false
		}
		exclusions = append(exclusions, item)
	}
	for _, argument := range arguments {
		cleaned := filepath.Clean(argument)
		info, err := os.Lstat(cleaned)
		if err != nil {
			return nil, fmt.Errorf("inspect selection %q: %w", argument, err)
		}
		if info.Mode()&os.ModeSymlink != 0 {
			return nil, fmt.Errorf("selection root %q is a symbolic link; pass the resolved file or directory instead", argument)
		}
		if !info.IsDir() {
			if !info.Mode().IsRegular() {
				return nil, fmt.Errorf("selection %q is not a regular file or directory", argument)
			}
			if err := appendUnique(&selected, Spec{Path: cleaned, DisplayPath: cleaned, info: info}, &state, maxSelected); err != nil {
				return nil, err
			}
			continue
		}

		var matches []Spec
		err = filepath.WalkDir(cleaned, func(path string, entry fs.DirEntry, walkErr error) error {
			if walkErr != nil {
				return fmt.Errorf("read selection directory %q: %w", path, walkErr)
			}
			if path == cleaned {
				return nil
			}
			if excluded(path, exclusions) {
				if entry.IsDir() {
					return filepath.SkipDir
				}
				return nil
			}
			state.visited++
			if state.visited > maxVisited {
				return fmt.Errorf("suite discovery exceeded limit of %d visited entries", maxVisited)
			}
			if entry.IsDir() {
				if _, excluded := excludedDirectoryNames[strings.ToLower(entry.Name())]; excluded {
					return filepath.SkipDir
				}
				return nil
			}
			if entry.Type()&os.ModeSymlink != 0 || !entry.Type().IsRegular() || filepath.Ext(entry.Name()) != ".json" {
				return nil
			}
			entryInfo, err := entry.Info()
			if err != nil {
				return fmt.Errorf("inspect selected spec %q: %w", path, err)
			}
			matches = append(matches, Spec{Path: filepath.Clean(path), DisplayPath: filepath.Clean(path), info: entryInfo})
			return nil
		})
		if err != nil {
			return nil, err
		}
		sort.Slice(matches, func(i, j int) bool {
			left, _ := filepath.Rel(cleaned, matches[i].Path)
			right, _ := filepath.Rel(cleaned, matches[j].Path)
			return normalized(left) < normalized(right)
		})
		for _, match := range matches {
			if err := appendUnique(&selected, match, &state, maxSelected); err != nil {
				return nil, err
			}
		}
	}
	if len(selected) == 0 {
		return nil, fmt.Errorf("selection matched no test specifications; pass a .json file or a directory containing .json specs")
	}
	return selected, nil
}

func excluded(path string, excludedPaths []excludedPath) bool {
	path = canonical(path)
	for _, exclusion := range excludedPaths {
		if path == exclusion.path {
			return exclusion.tree
		}
		if exclusion.tree {
			if relative, err := filepath.Rel(exclusion.path, path); err == nil && relative != ".." && !strings.HasPrefix(relative, ".."+string(os.PathSeparator)) {
				return true
			}
		}
	}
	return false
}

func canonical(path string) string {
	absolute, err := filepath.Abs(path)
	if err == nil {
		path = absolute
	}
	path = filepath.Clean(path)
	missing := make([]string, 0, 4)
	for cursor := path; ; cursor = filepath.Dir(cursor) {
		if resolved, err := filepath.EvalSymlinks(cursor); err == nil {
			for i := len(missing) - 1; i >= 0; i-- {
				resolved = filepath.Join(resolved, missing[i])
			}
			path = resolved
			break
		}
		parent := filepath.Dir(cursor)
		if parent == cursor {
			break
		}
		missing = append(missing, filepath.Base(cursor))
	}
	if runtime.GOOS == "windows" {
		path = strings.ToLower(path)
	}
	return path
}

func appendUnique(selected *[]Spec, candidate Spec, state *limits, maxSelected int) error {
	for _, existing := range *selected {
		if os.SameFile(existing.info, candidate.info) {
			return nil
		}
	}
	state.selected++
	if state.selected > maxSelected {
		return fmt.Errorf("suite selection exceeded limit of %d specs", maxSelected)
	}
	*selected = append(*selected, candidate)
	return nil
}

func normalized(path string) string {
	path = filepath.ToSlash(filepath.Clean(path))
	if runtime.GOOS == "windows" {
		path = strings.ToLower(path)
	}
	return path
}
