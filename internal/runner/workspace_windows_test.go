//go:build windows

package runner

import (
	"context"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"

	"golang.org/x/sys/windows"
)

func TestWorkspaceOwnershipMarkerUsesNativeHiddenAttribute(t *testing.T) {
	root := t.TempDir()
	fixture := filepath.Join(root, "fixture")
	if err := os.Mkdir(fixture, 0700); err != nil {
		t.Fatal(err)
	}
	input := filepath.Join(fixture, "reviewed café.txt")
	if err := os.WriteFile(input, []byte("protected bytes\n"), 0600); err != nil {
		t.Fatal(err)
	}
	spec := validWorkspaceSpec("workspace-state")
	workspace, err := prepareWorkspace(context.Background(), filepath.Join(root, "test.json"), spec)
	if err != nil {
		t.Fatal(err)
	}
	cleaned := false
	t.Cleanup(func() {
		if cleaned {
			return
		}
		if err := workspace.cleanup(context.Background()); err != nil {
			t.Error(err)
		}
	})
	marker := filepath.Join(workspace.root, workspaceMarker)
	pointer, err := windows.UTF16PtrFromString(marker)
	if err != nil {
		t.Fatal(err)
	}
	attributes, err := windows.GetFileAttributes(pointer)
	if err != nil {
		t.Fatal(err)
	}
	if attributes&windows.FILE_ATTRIBUTE_HIDDEN == 0 {
		t.Fatalf("ownership marker appears in a default Windows directory view: attributes=%#x", attributes)
	}
	if attributes&windows.FILE_ATTRIBUTE_READONLY != 0 {
		t.Fatal("ownership marker must remain writable for owned cleanup")
	}
	data, err := os.ReadFile(marker)
	if err != nil || string(data) != workspace.token {
		t.Fatalf("marker ownership changed: %q, %v", data, err)
	}
	pointer, err = windows.UTF16PtrFromString(filepath.Join(workspace.workingDir, "reviewed café.txt"))
	if err != nil {
		t.Fatal(err)
	}
	attributes, err = windows.GetFileAttributes(pointer)
	if err != nil || attributes&windows.FILE_ATTRIBUTE_HIDDEN != 0 {
		t.Fatalf("ordinary fixture visibility changed: attributes=%#x, %v", attributes, err)
	}
	if err := workspace.cleanup(context.Background()); err != nil {
		t.Fatal(err)
	}
	cleaned = true
	if _, err := os.Stat(workspace.root); !os.IsNotExist(err) {
		t.Fatalf("hidden-marker workspace was not removed: %v", err)
	}
}

func TestWorkspaceCopyRejectsWindowsJunction(t *testing.T) {
	source := t.TempDir()
	external := t.TempDir()
	junction := filepath.Join(source, "junction")
	command := exec.Command("cmd.exe", "/d", "/s", "/c", "mklink", "/J", junction, external)
	if output, err := command.CombinedOutput(); err != nil {
		t.Skipf("creating a test junction is unavailable: %v: %s", err, output)
	}
	err := copyWorkspaceFixture(context.Background(), source, filepath.Join(t.TempDir(), "copy"))
	if err == nil || !strings.Contains(err.Error(), "symbolic link or junction") {
		t.Fatalf("error = %v", err)
	}
	if err := os.WriteFile(filepath.Join(external, "sentinel"), []byte("safe"), 0600); err != nil {
		t.Fatal(err)
	}
}

func TestWorkspaceCleanupDoesNotFollowWindowsJunction(t *testing.T) {
	external := t.TempDir()
	sentinel := filepath.Join(external, "sentinel")
	if err := os.WriteFile(sentinel, []byte("safe"), 0600); err != nil {
		t.Fatal(err)
	}
	workspace := newOwnedWindowsWorkspace(t)
	junction := filepath.Join(workspace.root, "target-junction")
	command := exec.Command("cmd.exe", "/d", "/s", "/c", "mklink", "/J", junction, external)
	if output, err := command.CombinedOutput(); err != nil {
		t.Skipf("creating a test junction is unavailable: %v: %s", err, output)
	}
	if err := workspace.cleanup(context.Background()); err != nil {
		t.Fatal(err)
	}
	if data, err := os.ReadFile(sentinel); err != nil || string(data) != "safe" {
		t.Fatalf("external target changed: %q, %v", data, err)
	}
}

func TestWorkspaceCleanupReportsLockedFile(t *testing.T) {
	workspace := newOwnedWindowsWorkspace(t)
	locked := filepath.Join(workspace.root, "locked.txt")
	if err := os.WriteFile(locked, []byte("locked"), 0600); err != nil {
		t.Fatal(err)
	}
	name, err := windows.UTF16PtrFromString(locked)
	if err != nil {
		t.Fatal(err)
	}
	handle, err := windows.CreateFile(name, windows.GENERIC_READ, 0, nil, windows.OPEN_EXISTING, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		t.Fatal(err)
	}
	if err := workspace.cleanup(context.Background()); err == nil {
		windows.CloseHandle(handle)
		t.Fatal("cleanup unexpectedly removed a locked file")
	}
	if _, err := os.Stat(workspace.root); err != nil {
		windows.CloseHandle(handle)
		t.Fatalf("cleanup failure did not retain workspace: %v", err)
	}
	if err := windows.CloseHandle(handle); err != nil {
		t.Fatal(err)
	}
	if err := workspace.cleanup(context.Background()); err != nil {
		t.Fatalf("cleanup after unlock: %v", err)
	}
}

func newOwnedWindowsWorkspace(t *testing.T) *preparedWorkspace {
	t.Helper()
	root, err := os.MkdirTemp("", "playtestr-workspace-")
	if err != nil {
		t.Fatal(err)
	}
	workspace := &preparedWorkspace{root: root, token: "owned"}
	if err := os.WriteFile(filepath.Join(root, workspaceMarker), []byte(workspace.token), 0600); err != nil {
		t.Fatal(err)
	}
	return workspace
}
