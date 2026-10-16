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

func TestStateWindowsJunctionAndLockedFile(t *testing.T) {
	root := t.TempDir()
	canary := filepath.Join(root, "owned-canary")
	if err := os.Mkdir(canary, 0700); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(canary, "value")
	if err := os.WriteFile(path, []byte("canary"), 0600); err != nil {
		t.Fatal(err)
	}
	junction := filepath.Join(root, "junction")
	output, err := exec.Command("cmd", "/c", "mklink", "/J", junction, canary).CombinedOutput()
	if err != nil {
		t.Fatalf("create owned junction: %v (%s)", err, output)
	}
	defer os.Remove(junction)
	if err := assertState(context.Background(), root, fileState("junction/value", []byte("canary"))); err == nil || !strings.Contains(err.Error(), "unsafe") {
		t.Fatalf("junction followed: %v", err)
	}
	name, err := windows.UTF16PtrFromString(path)
	if err != nil {
		t.Fatal(err)
	}
	handle, err := windows.CreateFile(name, windows.GENERIC_READ|windows.GENERIC_WRITE,
		windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE|windows.FILE_SHARE_DELETE,
		nil, windows.OPEN_EXISTING, windows.FILE_ATTRIBUTE_NORMAL, 0)
	if err != nil {
		t.Fatal(err)
	}
	defer windows.CloseHandle(handle)
	// A real exclusive byte-range lock makes ReadFile fail. A share-mode-only
	// lock is not sufficient on every privileged native rooted-open path.
	if err := windows.LockFileEx(handle, windows.LOCKFILE_EXCLUSIVE_LOCK|windows.LOCKFILE_FAIL_IMMEDIATELY, 0, 6, 0, &windows.Overlapped{}); err != nil {
		t.Fatal(err)
	}
	if _, err := os.ReadFile(path); err == nil {
		t.Fatal("native sharing lock did not prevent an independent ordinary read")
	} else {
		t.Logf("independent locked read: %v", err)
	}
	if err := assertState(context.Background(), root, fileState("owned-canary/value", []byte("canary"))); err == nil || !strings.Contains(err.Error(), "file read failed") {
		t.Fatalf("native locked read: %v", err)
	}
}
