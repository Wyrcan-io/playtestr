package runner

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"
)

// Opt-in diagnosis of an intermittent native backend fault. This intentionally
// bypasses runner screen parsing so retained VT queries can be inspected.
// It is not a passing compatibility control or external project scenario.
func TestAdversarialNativeResizeInputProbe(t *testing.T) {
	target := os.Getenv("PLAYTESTR_WIZARD_PROBE_TARGET")
	if target == "" {
		t.Skip("opt-in native raw-stream investigation")
	}
	for i := 0; i < 200; i++ {
		root := t.TempDir()
		if err := os.WriteFile(filepath.Join(root, "seed.txt"), []byte("synthetic\n"), 0600); err != nil {
			t.Fatal(err)
		}
		p, err := newTerminalPty(80, 24)
		if err != nil {
			t.Fatal(err)
		}
		cmd := exec.Command(target, "wizard")
		cmd.Dir = root
		cmd.Env = append(os.Environ(), "PLAYTESTR_DELAY_MS=0")
		configureProcess(cmd)
		if err := p.Start(cmd); err != nil {
			_ = p.Close()
			t.Fatal(err)
		}
		tree, err := attachProcessTree(cmd.Process.Pid)
		if err != nil {
			_ = cmd.Process.Kill()
			_ = p.Close()
			_ = cmd.Wait()
			t.Fatal(err)
		}
		if err := activateProcess(cmd); err != nil {
			t.Fatal(abortTerminalStartup(cmd, p, tree, err))
		}
		var mu sync.Mutex
		var raw strings.Builder
		readerDone := make(chan struct{})
		go func() {
			defer close(readerDone)
			buffer := make([]byte, 1024)
			for {
				n, err := p.Read(buffer)
				mu.Lock()
				if raw.Len()+n <= 4096 {
					raw.Write(buffer[:n])
				}
				mu.Unlock()
				if err != nil {
					return
				}
			}
		}()
		view := func() string { mu.Lock(); defer mu.Unlock(); return raw.String() }
		deadline := time.Now().Add(3 * time.Second)
		for !strings.Contains(view(), "Project name?") && time.Now().Before(deadline) {
			time.Sleep(time.Millisecond)
		}
		if !strings.Contains(view(), "Project name?") {
			_ = tree.terminate()
			_ = p.Close()
			_ = cmd.Wait()
			_ = tree.close()
			t.Fatal("no initial prompt")
		}
		nText, eText := p.Write([]byte("atlas"))
		eResize := p.Resize(100, 30)
		nEnter, eEnter := p.Write([]byte("\r"))
		deadline = time.Now().Add(time.Second)
		for !strings.Contains(view(), "Confirm project") && time.Now().Before(deadline) {
			time.Sleep(time.Millisecond)
		}
		observed := view()
		_ = tree.terminate()
		_ = p.Close()
		_ = cmd.Wait()
		_ = tree.close()
		select {
		case <-readerDone:
		case <-time.After(3 * time.Second):
			t.Fatal("probe reader did not stop")
		}
		if !strings.Contains(observed, "Confirm project") {
			t.Fatalf("iteration=%d text=%d/%v resize=%v enter=%d/%v raw=%q hex=%x", i, nText, eText, eResize, nEnter, eEnter, observed, observed)
		}
		if i%20 == 0 {
			fmt.Printf("native raw-stream probe %d passed\n", i+1)
		}
	}
}
