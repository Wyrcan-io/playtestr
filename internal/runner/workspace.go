package runner

import (
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"io/fs"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

const (
	workspaceMaxFiles     = 1_000
	workspaceMaxEntries   = 2_000
	workspaceMaxBytes     = 32 * 1024 * 1024
	workspaceMaxFileBytes = 8 * 1024 * 1024
	workspaceMaxDepth     = 32
	workspaceCopyTimeout  = 30 * time.Second
	workspaceCleanupTime  = 5 * time.Second
	workspaceMarker       = ".playtestr-owner"
)

type preparedWorkspace struct {
	root       string
	workingDir string
	command    []string
	managedEnv map[string]string
	token      string
}

func validateWorkspaceSpec(spec Spec) error {
	if spec.Workspace == nil {
		return nil
	}
	workspace := spec.Workspace
	if spec.CWD != "" {
		return fmt.Errorf("cwd cannot be combined with workspace")
	}
	if workspace.Fixture == "" {
		return fmt.Errorf("workspace.fixture is required")
	}
	if err := validateWorkspaceRelativePath("workspace.fixture", workspace.Fixture, false); err != nil {
		return err
	}
	if workspace.CWD == "" {
		workspace.CWD = "."
	}
	if err := validateWorkspaceRelativePath("workspace.cwd", workspace.CWD, true); err != nil {
		return err
	}
	for name, value := range map[string]string{"workspace.home": workspace.Home, "workspace.temp": workspace.Temp} {
		if value != "" && value != "temporary" {
			return fmt.Errorf("%s must be %q when set", name, "temporary")
		}
	}
	managed := managedEnvironmentNames(workspace)
	for name := range spec.Env {
		if managed[environmentKey(name)] {
			return fmt.Errorf("environment %q conflicts with managed workspace home or temp", name)
		}
	}
	for _, name := range spec.InheritEnv {
		if managed[environmentKey(name)] {
			return fmt.Errorf("inherit_env %q conflicts with managed workspace home or temp", name)
		}
	}
	return nil
}

func validateWorkspaceRelativePath(name, value string, allowDot bool) error {
	if strings.ContainsRune(value, 0) || filepath.IsAbs(value) || filepath.VolumeName(value) != "" {
		return fmt.Errorf("%s must be a relative path", name)
	}
	cleaned := filepath.Clean(value)
	if (!allowDot && cleaned == ".") || cleaned == ".." || strings.HasPrefix(cleaned, ".."+string(os.PathSeparator)) {
		return fmt.Errorf("%s must stay below its declared root", name)
	}
	return nil
}

func managedEnvironmentNames(workspace *WorkspaceSpec) map[string]bool {
	result := make(map[string]bool)
	if workspace == nil {
		return result
	}
	if workspace.Home == "temporary" {
		names := []string{"HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME"}
		if runtime.GOOS == "windows" {
			names = []string{"USERPROFILE", "HOME", "APPDATA", "LOCALAPPDATA", "HOMEDRIVE", "HOMEPATH"}
		}
		for _, name := range names {
			result[environmentKey(name)] = true
		}
	}
	if workspace.Temp == "temporary" {
		names := []string{"TMPDIR"}
		if runtime.GOOS == "windows" {
			names = []string{"TEMP", "TMP"}
		}
		for _, name := range names {
			result[environmentKey(name)] = true
		}
	}
	return result
}

func prepareWorkspace(ctx context.Context, specPath string, spec Spec) (*preparedWorkspace, error) {
	if spec.Workspace == nil {
		return nil, nil
	}
	command, err := resolveWorkspaceCommand(specPath, spec.Command)
	if err != nil {
		return nil, err
	}
	specDirectory, err := filepath.Abs(filepath.Dir(specPath))
	if err != nil {
		return nil, fmt.Errorf("resolve spec directory: %w", err)
	}
	source := filepath.Join(specDirectory, filepath.Clean(spec.Workspace.Fixture))
	if !pathWithin(specDirectory, source) {
		return nil, fmt.Errorf("workspace fixture escapes the spec directory")
	}
	if err := rejectWorkspacePathLinks(specDirectory, source); err != nil {
		return nil, err
	}

	root, err := os.MkdirTemp("", "playtestr-workspace-")
	if err != nil {
		return nil, fmt.Errorf("create workspace root: %w", err)
	}
	tokenBytes := make([]byte, 16)
	if _, err := rand.Read(tokenBytes); err != nil {
		_ = os.Remove(root)
		return nil, fmt.Errorf("create workspace ownership token: %w", err)
	}
	workspace := &preparedWorkspace{root: root, token: hex.EncodeToString(tokenBytes), command: command, managedEnv: make(map[string]string)}
	if err := os.WriteFile(filepath.Join(root, workspaceMarker), []byte(workspace.token), 0600); err != nil {
		_ = os.Remove(filepath.Join(root, workspaceMarker))
		_ = os.Remove(root)
		return nil, fmt.Errorf("write workspace ownership marker: %w", err)
	}
	destination := filepath.Join(root, "fixture")
	if err := copyWorkspaceFixture(ctx, source, destination); err != nil {
		return workspace, err
	}
	workspace.workingDir = filepath.Join(destination, filepath.Clean(spec.Workspace.CWD))
	info, err := os.Stat(workspace.workingDir)
	if err != nil {
		return workspace, fmt.Errorf("open workspace cwd %q: %w", spec.Workspace.CWD, err)
	}
	if !info.IsDir() {
		return workspace, fmt.Errorf("workspace cwd is not a directory: %s", spec.Workspace.CWD)
	}
	if spec.Workspace.Home == "temporary" {
		home := filepath.Join(root, "home")
		if err := createManagedHome(home, workspace.managedEnv); err != nil {
			return workspace, err
		}
	}
	if spec.Workspace.Temp == "temporary" {
		temporary := filepath.Join(root, "temp")
		if err := os.Mkdir(temporary, 0700); err != nil {
			return workspace, fmt.Errorf("create managed temporary directory: %w", err)
		}
		if runtime.GOOS == "windows" {
			workspace.managedEnv["TEMP"] = temporary
			workspace.managedEnv["TMP"] = temporary
		} else {
			workspace.managedEnv["TMPDIR"] = temporary
		}
	}
	return workspace, nil
}

func resolveWorkspaceCommand(specPath string, command []string) ([]string, error) {
	resolved := append([]string(nil), command...)
	program := command[0]
	if filepath.IsAbs(program) {
		resolved[0] = filepath.Clean(program)
	} else if strings.ContainsAny(program, `/\`) {
		absolute, err := filepath.Abs(filepath.Join(filepath.Dir(specPath), program))
		if err != nil {
			return nil, fmt.Errorf("resolve workspace command: %w", err)
		}
		resolved[0] = absolute
	} else {
		absolute, err := exec.LookPath(program)
		if err != nil {
			return nil, fmt.Errorf("resolve workspace command %q before changing cwd: %w", program, err)
		}
		resolved[0] = absolute
	}
	info, err := os.Stat(resolved[0])
	if err != nil && runtime.GOOS == "windows" && filepath.Ext(resolved[0]) == "" {
		if withExtension, lookupErr := exec.LookPath(resolved[0]); lookupErr == nil {
			resolved[0] = withExtension
			info, err = os.Stat(resolved[0])
		}
	}
	if err != nil {
		return nil, fmt.Errorf("inspect workspace command: %w", err)
	}
	if !info.Mode().IsRegular() {
		return nil, fmt.Errorf("workspace command is not a regular file: %s", resolved[0])
	}
	return resolved, nil
}

func rejectWorkspaceRootLink(source string) error {
	info, err := os.Lstat(source)
	if err != nil {
		return fmt.Errorf("open workspace fixture: %w", err)
	}
	if !info.IsDir() {
		return fmt.Errorf("workspace fixture is not a directory: %s", source)
	}
	if info.Mode()&os.ModeSymlink != 0 || workspaceReparsePoint(source) {
		return fmt.Errorf("workspace fixture root cannot be a symbolic link or junction")
	}
	return nil
}

func rejectWorkspacePathLinks(root, source string) error {
	relative, err := filepath.Rel(root, source)
	if err != nil || relative == "." || relative == ".." || strings.HasPrefix(relative, ".."+string(os.PathSeparator)) {
		return fmt.Errorf("workspace fixture must stay below the spec directory")
	}
	current := root
	for _, component := range strings.Split(relative, string(os.PathSeparator)) {
		current = filepath.Join(current, component)
		info, err := os.Lstat(current)
		if err != nil {
			return fmt.Errorf("open workspace fixture: %w", err)
		}
		if info.Mode()&os.ModeSymlink != 0 || workspaceReparsePoint(current) {
			return fmt.Errorf("workspace fixture path component %q cannot be a symbolic link or junction", component)
		}
	}
	return rejectWorkspaceRootLink(source)
}

func copyWorkspaceFixture(ctx context.Context, source, destination string) error {
	if err := os.Mkdir(destination, 0755); err != nil {
		return fmt.Errorf("create fixture destination: %w", err)
	}
	files := 0
	entries := 0
	var total int64
	seen := make(map[string]string)
	return filepath.WalkDir(source, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return fmt.Errorf("walk fixture: %w", walkErr)
		}
		if err := ctx.Err(); err != nil {
			return fmt.Errorf("copy fixture cancelled: %w", err)
		}
		relative, err := filepath.Rel(source, path)
		if err != nil {
			return fmt.Errorf("resolve fixture entry: %w", err)
		}
		if relative == "." {
			return nil
		}
		entries++
		if entries > workspaceMaxEntries {
			return fmt.Errorf("fixture exceeds limit of %d filesystem entries", workspaceMaxEntries)
		}
		depth := len(strings.Split(relative, string(os.PathSeparator)))
		if depth > workspaceMaxDepth {
			return fmt.Errorf("fixture entry %q exceeds depth limit of %d", filepath.ToSlash(relative), workspaceMaxDepth)
		}
		collisionKey := filepath.ToSlash(relative)
		if runtime.GOOS == "windows" || runtime.GOOS == "darwin" {
			collisionKey = strings.ToLower(collisionKey)
		}
		if previous, exists := seen[collisionKey]; exists && previous != filepath.ToSlash(relative) {
			return fmt.Errorf("fixture entries %q and %q collide on this host", previous, filepath.ToSlash(relative))
		}
		seen[collisionKey] = filepath.ToSlash(relative)
		info, err := os.Lstat(path)
		if err != nil {
			return fmt.Errorf("inspect fixture entry %q: %w", filepath.ToSlash(relative), err)
		}
		if info.Mode()&os.ModeSymlink != 0 || workspaceReparsePoint(path) {
			return fmt.Errorf("fixture entry %q is a symbolic link or junction", filepath.ToSlash(relative))
		}
		target := filepath.Join(destination, relative)
		if info.IsDir() {
			if err := os.Mkdir(target, 0755); err != nil {
				return fmt.Errorf("create fixture directory %q: %w", filepath.ToSlash(relative), err)
			}
			return nil
		}
		if !info.Mode().IsRegular() {
			return fmt.Errorf("fixture entry %q is not a regular file or directory", filepath.ToSlash(relative))
		}
		files++
		if files > workspaceMaxFiles {
			return fmt.Errorf("fixture exceeds limit of %d regular files", workspaceMaxFiles)
		}
		if info.Size() > workspaceMaxFileBytes {
			return fmt.Errorf("fixture file %q exceeds limit of %d bytes", filepath.ToSlash(relative), workspaceMaxFileBytes)
		}
		total += info.Size()
		if total > workspaceMaxBytes {
			return fmt.Errorf("fixture exceeds total limit of %d bytes", workspaceMaxBytes)
		}
		if err := copyWorkspaceFile(ctx, path, target, info); err != nil {
			return fmt.Errorf("copy fixture file %q: %w", filepath.ToSlash(relative), err)
		}
		return nil
	})
}

func copyWorkspaceFile(ctx context.Context, source, destination string, before os.FileInfo) (returnErr error) {
	input, err := os.Open(source)
	if err != nil {
		return err
	}
	defer input.Close()
	mode := os.FileMode(0644)
	if runtime.GOOS != "windows" && before.Mode().Perm()&0111 != 0 {
		mode = 0755
	}
	output, err := os.OpenFile(destination, os.O_CREATE|os.O_EXCL|os.O_WRONLY, mode)
	if err != nil {
		return err
	}
	defer func() {
		if err := output.Close(); returnErr == nil && err != nil {
			returnErr = err
		}
	}()
	buffer := make([]byte, 64*1024)
	var copied int64
	for {
		if err := ctx.Err(); err != nil {
			return fmt.Errorf("copy cancelled: %w", err)
		}
		read, readErr := input.Read(buffer)
		if read > 0 {
			copied += int64(read)
			if copied > before.Size() || copied > workspaceMaxFileBytes {
				return fmt.Errorf("source changed size during copy")
			}
			if _, err := output.Write(buffer[:read]); err != nil {
				return err
			}
		}
		if readErr == io.EOF {
			break
		}
		if readErr != nil {
			return readErr
		}
	}
	after, err := input.Stat()
	if err != nil {
		return err
	}
	if copied != before.Size() || after.Size() != before.Size() || !os.SameFile(before, after) {
		return fmt.Errorf("source changed during copy")
	}
	return nil
}

func createManagedHome(home string, environment map[string]string) error {
	if err := os.Mkdir(home, 0700); err != nil {
		return fmt.Errorf("create managed home: %w", err)
	}
	if runtime.GOOS == "windows" {
		roaming := filepath.Join(home, "AppData", "Roaming")
		local := filepath.Join(home, "AppData", "Local")
		if err := os.MkdirAll(roaming, 0700); err != nil {
			return fmt.Errorf("create managed roaming directory: %w", err)
		}
		if err := os.MkdirAll(local, 0700); err != nil {
			return fmt.Errorf("create managed local directory: %w", err)
		}
		environment["USERPROFILE"] = home
		environment["HOME"] = home
		environment["APPDATA"] = roaming
		environment["LOCALAPPDATA"] = local
		environment["HOMEDRIVE"] = filepath.VolumeName(home)
		environment["HOMEPATH"] = strings.TrimPrefix(home, filepath.VolumeName(home))
	} else {
		environment["HOME"] = home
		for name, relative := range map[string]string{
			"XDG_CONFIG_HOME": ".config", "XDG_CACHE_HOME": ".cache",
			"XDG_DATA_HOME": filepath.Join(".local", "share"), "XDG_STATE_HOME": filepath.Join(".local", "state"),
		} {
			path := filepath.Join(home, relative)
			if err := os.MkdirAll(path, 0700); err != nil {
				return fmt.Errorf("create managed home directory: %w", err)
			}
			environment[name] = path
		}
	}
	return nil
}

func (workspace *preparedWorkspace) cleanup(ctx context.Context) error {
	if workspace == nil || workspace.root == "" {
		return nil
	}
	root, err := filepath.Abs(workspace.root)
	if err != nil {
		return fmt.Errorf("resolve workspace root: %w", err)
	}
	temporary, err := filepath.Abs(os.TempDir())
	if err != nil || !pathWithin(temporary, root) || filepath.Dir(root) != filepath.Clean(temporary) || !strings.HasPrefix(filepath.Base(root), "playtestr-workspace-") {
		return fmt.Errorf("refusing to remove unowned workspace path %q", root)
	}
	info, err := os.Lstat(root)
	if err != nil {
		return err
	}
	if !info.IsDir() || info.Mode()&os.ModeSymlink != 0 || workspaceReparsePoint(root) {
		return fmt.Errorf("workspace root is no longer an owned ordinary directory")
	}
	markerPath := filepath.Join(root, workspaceMarker)
	markerInfo, err := os.Lstat(markerPath)
	if err != nil || !markerInfo.Mode().IsRegular() || workspaceReparsePoint(markerPath) {
		return fmt.Errorf("workspace ownership marker is missing or unsafe")
	}
	marker, err := os.ReadFile(markerPath)
	if err != nil || string(marker) != workspace.token {
		return fmt.Errorf("workspace ownership marker does not match")
	}
	return removeWorkspaceTree(ctx, root)
}

func removeWorkspaceTree(ctx context.Context, path string) error {
	return removeWorkspaceTreeEntry(ctx, path, true)
}

func removeWorkspaceTreeEntry(ctx context.Context, path string, ownedRoot bool) error {
	if err := ctx.Err(); err != nil {
		return fmt.Errorf("workspace cleanup cancelled: %w", err)
	}
	directory, err := os.Open(path)
	if err != nil {
		return err
	}
	for {
		entries, readErr := directory.ReadDir(128)
		for _, entry := range entries {
			if ownedRoot && entry.Name() == workspaceMarker {
				continue
			}
			if err := ctx.Err(); err != nil {
				_ = directory.Close()
				return fmt.Errorf("workspace cleanup cancelled: %w", err)
			}
			child := filepath.Join(path, entry.Name())
			info, err := os.Lstat(child)
			if err != nil {
				_ = directory.Close()
				return err
			}
			if info.IsDir() && info.Mode()&os.ModeSymlink == 0 && !workspaceReparsePoint(child) {
				if err := removeWorkspaceTreeEntry(ctx, child, false); err != nil {
					_ = directory.Close()
					return err
				}
				continue
			}
			if err := os.Remove(child); err != nil {
				_ = directory.Close()
				return err
			}
		}
		if readErr == io.EOF {
			break
		}
		if readErr != nil {
			_ = directory.Close()
			return readErr
		}
	}
	if err := directory.Close(); err != nil {
		return err
	}
	if ownedRoot {
		if err := os.Remove(filepath.Join(path, workspaceMarker)); err != nil {
			return err
		}
	}
	return os.Remove(path)
}

func pathWithin(root, candidate string) bool {
	relative, err := filepath.Rel(filepath.Clean(root), filepath.Clean(candidate))
	return err == nil && relative != ".." && !strings.HasPrefix(relative, ".."+string(os.PathSeparator))
}

func workspaceFailure(category FailureCategory, err error) *Failure {
	if err == nil {
		return nil
	}
	return &Failure{Category: category, Message: err.Error()}
}

func cleanupPreparedWorkspace(workspace *preparedWorkspace) error {
	if workspace == nil {
		return nil
	}
	ctx, cancel := context.WithTimeout(context.Background(), workspaceCleanupTime)
	defer cancel()
	if err := workspace.cleanup(ctx); err != nil && !errors.Is(err, fs.ErrNotExist) {
		return err
	}
	return nil
}

func finishWorkspace(workspace *preparedWorkspace, report *WorkspaceReport, processConfirmed, failed, keepOnFailure bool, out io.Writer) error {
	if workspace == nil || report == nil {
		return nil
	}
	if !processConfirmed || failed && keepOnFailure {
		report.Retained = true
		report.RetainedPath = workspace.root
		fmt.Fprintf(out, "Workspace retained: %s\n", workspace.root)
		return nil
	}
	report.CleanupAttempted = true
	if err := cleanupPreparedWorkspace(workspace); err != nil {
		report.Retained = true
		report.RetainedPath = workspace.root
		report.CleanupFailure = workspaceFailure(FailureWorkspaceCleanup, err)
		fmt.Fprintf(out, "Workspace retained after cleanup failure: %s\n", workspace.root)
		return err
	}
	report.Cleaned = true
	return nil
}
