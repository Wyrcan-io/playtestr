//go:build windows

package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"golang.org/x/sys/windows"
)

func TestAdversarialWorkspaceLongPathHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_WORKSPACE_LONG_PATH_HELPER") != "1" {
		return
	}
	working, err := os.Getwd()
	if err != nil {
		os.Exit(7)
	}
	long, err := canonicalWorkspaceRoot(working)
	if err != nil || !strings.EqualFold(working, long) {
		os.Exit(8)
	}
	fmt.Print("long workspace path ready\r\n")
	os.Exit(0)
}

func TestAdversarialWindowsWorkspaceExpandsShortTemporaryPath(t *testing.T) {
	parent, err := canonicalWorkspaceRoot(t.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	pointer, err := windows.UTF16PtrFromString(parent)
	if err != nil {
		t.Fatal(err)
	}
	buffer := make([]uint16, 32768)
	n, err := windows.GetShortPathName(pointer, &buffer[0], uint32(len(buffer)))
	if err != nil || n == 0 || n >= uint32(len(buffer)) {
		t.Skipf("Native short-name prerequisite unavailable: %v", err)
	}
	short := windows.UTF16ToString(buffer[:n])
	if strings.EqualFold(parent, short) {
		t.Skip("Native temporary filesystem has no different short alias")
	}
	t.Setenv("TEMP", short)
	t.Setenv("TMP", short)
	fixture := filepath.Join(parent, "fixture")
	if err := os.Mkdir(fixture, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(fixture, "sentinel"), []byte("synthetic\n"), 0600); err != nil {
		t.Fatal(err)
	}
	spec := Spec{Version: WorkspaceSpecVersion, Command: []string{os.Args[0], "-test.run=^TestAdversarialWorkspaceLongPathHelper$"},
		Workspace: &WorkspaceSpec{Fixture: "fixture", CWD: ".", Home: "temporary", Temp: "temporary"},
		Env:       map[string]string{"PLAYTESTR_WORKSPACE_LONG_PATH_HELPER": "1"}, Width: 80, Height: 24,
		TimeoutMS: 5000, RunTimeoutMS: 15000, MaxOutputBytes: 100000,
		Steps: []Step{{Expect: "long workspace path ready"}, {Exit: intPointer(0)}}}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(parent, "long-path.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
	if result.Err() != nil {
		t.Fatal(result.Err())
	}
	if !result.Cleanup.ConfirmedExited || !result.Workspace.Cleaned {
		t.Fatalf("native path cleanup unconfirmed: %+v %+v", result.Cleanup, result.Workspace)
	}
}
