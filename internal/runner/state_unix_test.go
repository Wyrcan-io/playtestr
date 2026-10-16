//go:build !windows

package runner

import (
	"context"
	"os"
	"path/filepath"
	"strings"
	"syscall"
	"testing"
)

func TestStateUnixSpecialFileAndNativePermission(t *testing.T) {
	root := t.TempDir()
	fifo := filepath.Join(root, "pipe")
	if err := syscall.Mkfifo(fifo, 0600); err != nil {
		t.Fatal(err)
	}
	if err := assertState(context.Background(), root, fileState("pipe", nil)); err == nil || !strings.Contains(err.Error(), "wrong path type") {
		t.Fatalf("FIFO accepted: %v", err)
	}
	path := filepath.Join(root, "unreadable")
	if err := os.WriteFile(path, []byte("canary"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Chmod(path, 0); err != nil {
		t.Fatal(err)
	}
	defer os.Chmod(path, 0600)
	if f, err := os.Open(path); err == nil {
		f.Close()
		t.Skip("executing user retains read access; native permission-denial path unqualified")
	}
	if err := assertState(context.Background(), root, fileState("unreadable", []byte("canary"))); err == nil || !strings.Contains(err.Error(), "unreadable") {
		t.Fatalf("native permission denial: %v", err)
	}
}
