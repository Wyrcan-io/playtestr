//go:build !windows

package runner

import (
	"context"
	"os"
	"path/filepath"
	"testing"
)

func TestWorkspaceCleanupDoesNotFollowTargetCreatedSymlink(t *testing.T) {
	external := filepath.Join(t.TempDir(), "external.txt")
	if err := os.WriteFile(external, []byte("sentinel"), 0600); err != nil {
		t.Fatal(err)
	}
	root, err := os.MkdirTemp("", "playtestr-workspace-")
	if err != nil {
		t.Fatal(err)
	}
	workspace := &preparedWorkspace{root: root, token: "owned"}
	if err := os.WriteFile(filepath.Join(root, workspaceMarker), []byte(workspace.token), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(external, filepath.Join(root, "target-link")); err != nil {
		t.Fatal(err)
	}
	if err := workspace.cleanup(context.Background()); err != nil {
		t.Fatal(err)
	}
	if data, err := os.ReadFile(external); err != nil || string(data) != "sentinel" {
		t.Fatalf("external target changed: %q, %v", data, err)
	}
}
