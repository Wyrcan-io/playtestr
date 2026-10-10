package runner

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/charmbracelet/x/xpty"
)

type nativeProbePTY struct {
	xpty.Pty
	mu     sync.Mutex
	raw    strings.Builder
	writes []string
}

func (p *nativeProbePTY) Read(buffer []byte) (int, error) {
	n, err := p.Pty.Read(buffer)
	p.mu.Lock()
	if p.raw.Len()+n <= 4096 {
		p.raw.Write(buffer[:n])
	}
	p.mu.Unlock()
	return n, err
}
func (p *nativeProbePTY) Write(buffer []byte) (int, error) {
	originalLength := len(buffer)
	encoded := false
	if os.Getenv("PLAYTESTR_PROBE_WIN32_ENTER") == "1" && string(buffer) == "\r" {
		buffer = []byte("\x1b[13;28;13;1;0;1_\x1b[13;28;13;0;0;1_")
		encoded = true
	}
	n, err := p.Pty.Write(buffer)
	p.mu.Lock()
	if len(p.writes) < 8 {
		p.writes = append(p.writes, fmt.Sprintf("%x -> %d %v", buffer, n, err))
	}
	p.mu.Unlock()
	if encoded && n == len(buffer) {
		return originalLength, err
	}
	return n, err
}

func (p *nativeProbePTY) Resize(width, height int) error {
	if err := p.Pty.Resize(width, height); err != nil {
		return err
	}
	if os.Getenv("PLAYTESTR_PROBE_RESIZE_ACK") != "1" {
		return nil
	}
	deadline := time.Now().Add(3 * time.Second)
	want := fmt.Sprintf("\x1b[8;%d;%dt", height, width)
	for time.Now().Before(deadline) {
		p.mu.Lock()
		found := strings.Contains(p.raw.String(), want)
		p.mu.Unlock()
		if found {
			return nil
		}
		time.Sleep(time.Millisecond)
	}
	return fmt.Errorf("native resize acknowledgment absent")
}

func TestAdversarialSessionResizeInputProbe(t *testing.T) {
	target := os.Getenv("PLAYTESTR_WIZARD_PROBE_TARGET")
	if target == "" {
		t.Skip("opt-in real session traffic investigation")
	}
	for i := 0; i < 500; i++ {
		root := t.TempDir()
		if err := os.WriteFile(filepath.Join(root, "seed.txt"), []byte("synthetic\n"), 0600); err != nil {
			t.Fatal(err)
		}
		var backend xpty.Pty
		var err error
		if os.Getenv("PLAYTESTR_PROBE_LEGACY_BACKEND") == "1" {
			backend, err = xpty.NewPty(80, 24)
		} else {
			backend, err = newTerminalPty(80, 24)
		}
		if err != nil {
			t.Fatal(err)
		}
		probe := &nativeProbePTY{Pty: backend}
		s, err := startTerminalSessionWithPTY(sessionConfig{command: []string{target, "wizard"}, dir: root,
			env: append(os.Environ(), "PLAYTESTR_DELAY_MS=0"), width: 80, height: 24, maxOutputBytes: 4096}, probe)
		if err != nil {
			t.Fatal(err)
		}
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		for !strings.Contains(s.observe().screen, "Project name?") && ctx.Err() == nil {
			time.Sleep(5 * time.Millisecond)
		}
		textErr := s.send(ctx, "atlas")
		resizeErr := s.resize(ctx, 100, 30)
		enterErr := s.send(ctx, "\r")
		deadline := time.Now().Add(time.Second)
		for !strings.Contains(s.observe().screen, "Confirm project") && time.Now().Before(deadline) {
			time.Sleep(5 * time.Millisecond)
		}
		observed := s.observe().screen
		cancel()
		cleanupCtx, cleanupCancel := context.WithTimeout(context.Background(), 3*time.Second)
		cleanup := s.stop(cleanupCtx)
		cleanupCancel()
		if !cleanup.confirmedExited {
			t.Fatalf("probe cleanup unconfirmed: %+v", cleanup)
		}
		if !strings.Contains(observed, "Confirm project") {
			probe.mu.Lock()
			output, writes := probe.raw.String(), append([]string(nil), probe.writes...)
			probe.mu.Unlock()
			t.Fatalf("iteration=%d errors=%v/%v/%v writes=%v screen=%q raw=%q hex=%x", i, textErr, resizeErr, enterErr, writes, observed, output, output)
		}
		if i%50 == 0 {
			fmt.Printf("real session probe %d passed\n", i+1)
		}
	}
}
