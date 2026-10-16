package runner

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/base64"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"slices"
	"strings"
	"unicode/utf8"
)

const maxStateFileBytes = 64 * 1024

func stateWorkspaceID(workspace *preparedWorkspace) string {
	// Do not publish the cleanup ownership marker itself.
	digest := sha256.Sum256([]byte(workspace.token))
	return fmt.Sprintf("%x", digest[:16])
}

func openStateRoot(base string) (*os.Root, error) {
	info, err := os.Lstat(base)
	if err != nil || !info.IsDir() || info.Mode()&os.ModeSymlink != 0 || workspaceReparsePoint(base) {
		return nil, stateError("unsafe workspace root")
	}
	root, err := os.OpenRoot(base)
	if err != nil {
		return nil, err
	}
	opened, err := root.Lstat(".")
	if err != nil || !os.SameFile(info, opened) {
		root.Close()
		return nil, stateError("workspace root changed")
	}
	return root, nil
}

// StateAssertion compares one explicitly selected path in the managed fixture.
type StateAssertion struct {
	Path        string    `json:"path"`
	Kind        string    `json:"kind"`
	BytesBase64 *string   `json:"bytes_base64,omitempty"`
	Entries     *[]string `json:"entries,omitempty"`
}

// StateObservation binds a payload-free checkpoint to this execution/workspace.
type StateObservation struct {
	InvocationID string `json:"invocation_id"`
	WorkspaceID  string `json:"workspace_id"`
	Path         string `json:"path"`
	Kind         string `json:"kind"`
	Outcome      string `json:"outcome"`
}

func validateStatePath(path string, allowRoot bool) error {
	if path == "." && allowRoot {
		return nil
	}
	if path == "" || len(path) > 4096 || !utf8.ValidString(path) || strings.ContainsAny(path, "\\:\x00<>\"|?*") || strings.HasPrefix(path, "/") {
		return fmt.Errorf("unsupported relative path")
	}
	parts := strings.Split(path, "/")
	if len(parts) > 32 {
		return fmt.Errorf("path exceeds 32 components")
	}
	for _, part := range parts {
		if part == "" || part == "." || part == ".." || strings.TrimRight(part, ". ") != part {
			return fmt.Errorf("unsafe path component")
		}
		for _, c := range part {
			if c < 32 || c == 127 {
				return fmt.Errorf("control character in path")
			}
		}
		stem := strings.ToUpper(strings.SplitN(part, ".", 2)[0])
		suffix := ""
		if strings.HasPrefix(stem, "COM") || strings.HasPrefix(stem, "LPT") {
			suffix = stem[3:]
		}
		if slices.Contains([]string{"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}, stem) || (strings.HasPrefix(stem, "COM") || strings.HasPrefix(stem, "LPT")) && utf8.RuneCountInString(suffix) == 1 && strings.ContainsAny(suffix, "123456789¹²³") {
			return fmt.Errorf("reserved path component")
		}
	}
	return nil
}

func validateStateAssertion(a StateAssertion) (int, error) {
	if err := validateStatePath(a.Path, a.Kind != "file" && a.Kind != "absent"); err != nil {
		return 0, err
	}
	switch a.Kind {
	case "file":
		if a.BytesBase64 == nil || a.Entries != nil {
			return 0, fmt.Errorf("file requires bytes_base64 only")
		}
		if len(*a.BytesBase64) > base64.StdEncoding.EncodedLen(maxStateFileBytes) {
			return 0, fmt.Errorf("expected file exceeds 65536 bytes")
		}
		data, err := base64.StdEncoding.Strict().DecodeString(*a.BytesBase64)
		if err != nil || len(data) > maxStateFileBytes {
			return 0, fmt.Errorf("invalid or oversized bytes_base64")
		}
		return len(data), nil
	case "entries":
		if a.Entries == nil || len(*a.Entries) > 256 {
			return 0, fmt.Errorf("entries requires at most 256 names")
		}
		seen := map[string]bool{}
		for _, name := range *a.Entries {
			if err := validateStatePath(name, false); err != nil || strings.Contains(name, "/") {
				return 0, fmt.Errorf("entries must be immediate portable names")
			}
			if seen[name] {
				return 0, fmt.Errorf("duplicate entry")
			}
			seen[name] = true
		}
	case "absent", "directory", "empty_directory":
		if a.Entries != nil {
			return 0, fmt.Errorf("unexpected entries expectation")
		}
	default:
		return 0, fmt.Errorf("unsupported state kind")
	}
	if a.BytesBase64 != nil {
		return 0, fmt.Errorf("bytes_base64 requires file kind")
	}
	return 0, nil
}

func stateError(reason string) error {
	return withCategory(FailureState, fmt.Errorf("saved-state checkpoint: %s; inspect the selected path and reviewed expectation, then rerun", reason))
}

// stateInfo checks every selected component without intentionally following links.
// os.Root additionally prevents a replacement link escaping the selected root.
func stateInfo(root *os.Root, base, path string) (os.FileInfo, error) {
	current := "."
	if path != "." {
		for _, part := range strings.Split(path, "/") {
			current = filepath.Join(current, part)
			info, err := root.Lstat(current)
			if err != nil {
				return nil, err
			}
			if info.Mode()&os.ModeSymlink != 0 || workspaceReparsePoint(filepath.Join(base, current)) {
				return nil, stateError("unsafe linked path")
			}
			if current != filepath.FromSlash(path) && !info.IsDir() {
				return nil, stateError("wrong ancestor type")
			}
		}
	}
	return root.Lstat(filepath.FromSlash(path))
}

func assertState(ctx context.Context, base string, a StateAssertion) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	if _, err := validateStateAssertion(a); err != nil {
		return stateError("invalid assertion")
	}
	if base == "" {
		return stateError("managed workspace unavailable")
	}
	root, err := openStateRoot(base)
	if err != nil {
		return stateError("cannot open managed workspace")
	}
	defer root.Close()
	info, err := stateInfo(root, base, a.Path)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			if a.Kind == "absent" {
				return ctx.Err()
			}
			return stateError("missing path")
		}
		var categorized *categorizedError
		if errors.As(err, &categorized) {
			return err
		}
		return stateError("unreadable path")
	}
	if a.Kind == "absent" {
		return stateError("unexpected existing path")
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	if a.Kind == "file" && !info.Mode().IsRegular() || a.Kind != "file" && !info.IsDir() {
		return stateError("wrong path type")
	}
	f, err := openStateFile(root, filepath.FromSlash(a.Path))
	if err != nil {
		return stateError("unreadable path")
	}
	defer f.Close()
	opened, err := f.Stat()
	if err != nil || !os.SameFile(info, opened) || opened.Mode() != info.Mode() {
		return stateError("path changed while opening")
	}
	if a.Kind == "file" {
		if info.Size() > maxStateFileBytes {
			return stateError("observed file exceeds 65536 bytes")
		}
		data := make([]byte, 0, int(info.Size()))
		buffer := make([]byte, 4096)
		for {
			if err := ctx.Err(); err != nil {
				return err
			}
			n, e := f.Read(buffer)
			data = append(data, buffer[:n]...)
			if len(data) > maxStateFileBytes {
				return stateError("observed file exceeds 65536 bytes")
			}
			if e == io.EOF {
				break
			}
			if e != nil {
				return stateError("file read failed")
			}
		}
		after, e := f.Stat()
		if e != nil || after.Size() != info.Size() || !after.ModTime().Equal(info.ModTime()) || int64(len(data)) != after.Size() {
			return stateError("file changed during observation")
		}
		expected, _ := base64.StdEncoding.Strict().DecodeString(*a.BytesBase64)
		if !bytes.Equal(data, expected) {
			return stateError("wrong file bytes")
		}
	} else if a.Kind != "directory" {
		entries, e := f.ReadDir(257)
		if e != nil && e != io.EOF {
			return stateError("directory read failed")
		}
		if len(entries) > 256 {
			return stateError("directory exceeds 256 entries")
		}
		names := make([]string, 0, len(entries))
		for _, entry := range entries {
			if err := ctx.Err(); err != nil {
				return err
			}
			child, e := stateInfo(root, base, strings.TrimPrefix(a.Path+"/"+entry.Name(), "./"))
			if e != nil || (!child.IsDir() && !child.Mode().IsRegular()) {
				return stateError("unsafe or changing directory entry")
			}
			names = append(names, entry.Name())
		}
		expected := []string{}
		if a.Entries != nil {
			expected = append(expected, (*a.Entries)...)
		}
		slices.Sort(names)
		slices.Sort(expected)
		if !slices.Equal(names, expected) {
			return stateError("wrong directory entries")
		}
	}
	final, e := stateInfo(root, base, a.Path)
	if e != nil || !os.SameFile(info, final) || final.Size() != info.Size() || !final.ModTime().Equal(info.ModTime()) {
		return stateError("path changed during observation")
	}
	return ctx.Err()
}
