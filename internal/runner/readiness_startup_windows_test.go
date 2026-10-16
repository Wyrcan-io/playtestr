//go:build windows

package runner

import (
	"context"
	"os"
	"strings"
	"testing"
	"time"
)

// Opt-in diagnosis uses only synthetic output, never an ambient target command.
func TestReadinessNativeShellNodeStartupProbe(t *testing.T) {
	node := os.Getenv("PLAYTESTR_NODE_STARTUP_PROBE")
	if node == "" {
		t.Skip("opt-in installed Node startup investigation")
	}
	commands := [][]string{{"cmd.exe", "/d", "/c", "echo synthetic-startup-ready"}, {node, "-e", "console.log('synthetic-startup-ready')"}}
	if entry := os.Getenv("PLAYTESTR_PLOP_LIBRARY_PROBE"); entry != "" {
		commands = append(commands, []string{node, "-e", "console.log('synthetic-import-start'); import(process.argv[1]).then(()=>console.log('synthetic-startup-ready'))", entry})
	}
	for _, command := range commands {
		t.Run(command[0], func(t *testing.T) {
			backend, err := newTerminalPty(80, 24)
			if err != nil {
				t.Fatal(err)
			}
			probe := &nativeProbePTY{Pty: backend}
			s, err := startTerminalSessionWithPTY(sessionConfig{command: command, env: os.Environ(), width: 80, height: 24, maxOutputBytes: 4096}, probe)
			if err != nil {
				t.Fatal(err)
			}
			ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cancel()
			for !strings.Contains(s.observe().screen, "synthetic-startup-ready") && ctx.Err() == nil {
				time.Sleep(5 * time.Millisecond)
			}
			observation := s.observe()
			cleanupCtx, cleanupCancel := context.WithTimeout(context.Background(), 5*time.Second)
			defer cleanupCancel()
			cleanup := s.stop(cleanupCtx)
			probe.mu.Lock()
			raw := probe.raw.String()
			probe.mu.Unlock()
			t.Logf("synthetic output bytes=%d raw=%q cleanup=%+v", observation.outputBytes, raw, cleanup)
			if !cleanup.confirmedExited || cleanup.err != nil {
				t.Fatal("cleanup unconfirmed")
			}
			if !strings.Contains(observation.screen, "synthetic-startup-ready") {
				t.Fatal("startup readiness absent")
			}
		})
	}
}
