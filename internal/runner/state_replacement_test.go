package runner

import (
	"context"
	"errors"
	"os"
	"path/filepath"
	"runtime"
	"testing"
	"time"
)

func TestStateConcurrentLinkReplacementNeverApprovesOwnedCanary(t *testing.T) {
	root := t.TempDir()
	canary := filepath.Join(root, "owned-canary")
	if err := os.WriteFile(canary, []byte("unselected canary"), 0600); err != nil {
		t.Fatal(err)
	}
	selected := filepath.Join(root, "selected")
	if err := os.Symlink(canary, selected); err != nil {
		t.Skipf("native symlink creation unavailable: %v", err)
	}
	if err := os.Remove(selected); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	ready, done := make(chan struct{}), make(chan error, 1)
	go func() {
		for i := 0; i < 128; i++ {
			if err := ctx.Err(); err != nil {
				done <- err
				return
			}
			if err := os.Remove(selected); err != nil && !errors.Is(err, os.ErrNotExist) {
				done <- err
				return
			}
			if err := os.Symlink(canary, selected); err != nil {
				done <- err
				return
			}
			if i == 0 {
				close(ready)
			}
			runtime.Gosched()
			if err := os.Remove(selected); err != nil {
				done <- err
				return
			}
			if err := os.WriteFile(selected, []byte("reviewed bytes"), 0600); err != nil {
				done <- err
				return
			}
		}
		done <- nil
	}()
	defer func() {
		cancel()
		select {
		case err := <-done:
			if err != nil && !errors.Is(err, context.Canceled) {
				t.Errorf("owned writer failed: %v", err)
			}
		case <-time.After(5 * time.Second):
			t.Error("owned writer shutdown unconfirmed")
		}
	}()
	select {
	case <-ready:
	case <-ctx.Done():
		t.Fatal("writer never reached link replacement")
	}
	for i := 0; i < 128; i++ {
		if err := ctx.Err(); err != nil {
			t.Fatal("independent replacement test deadline exceeded")
		}
		if err := assertState(ctx, root, fileState("selected", []byte("unselected canary"))); err == nil {
			t.Fatal("a linked owned canary was incorrectly approved as the selected regular file")
		}
	}
}
