//go:build !windows

package runner

import (
	"context"
	"fmt"
	"io"
	"os"
	"os/signal"
	"path/filepath"
	"syscall"
	"testing"
	"time"

	"golang.org/x/term"
)

func TestNativeSignalExitHelper(t *testing.T) {
	name := os.Getenv("PLAYTESTR_SIGNAL_EXIT_HELPER")
	if name == "" {
		return
	}
	sig := syscall.SIGINT
	if name == "TERM" {
		sig = syscall.SIGTERM
	} else if name != "INT" {
		os.Exit(8)
	}
	old, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		os.Exit(9)
	}
	defer term.Restore(int(os.Stdin.Fd()), old)
	fmt.Print("native signal target ready\r\n")
	var input [1]byte
	if _, err := io.ReadFull(os.Stdin, input[:]); err != nil || input[0] != 'x' {
		os.Exit(10)
	}
	signal.Reset(sig)
	if err := syscall.Kill(os.Getpid(), sig); err != nil {
		os.Exit(11)
	}
	time.Sleep(30 * time.Second)
	os.Exit(12)
}

func TestNativeSignalExitStatusAndSameRunState(t *testing.T) {
	for _, test := range []struct {
		name, signal     string
		expected, actual int
		pass             bool
	}{
		{"interrupt", "INT", 130, 130, true},
		{"terminate", "TERM", 143, 143, true},
		{"unexpected termination", "TERM", 0, 143, false},
	} {
		t.Run(test.name, func(t *testing.T) {
			root := t.TempDir()
			if err := os.Mkdir(filepath.Join(root, "fixture"), 0700); err != nil {
				t.Fatal(err)
			}
			a := StateAssertion{Path: "unwritten", Kind: "absent"}
			spec := Spec{Version: 3, Command: []string{os.Args[0], "-test.run=^TestNativeSignalExitHelper$"},
				Env: map[string]string{"PLAYTESTR_SIGNAL_EXIT_HELPER": test.signal}, Workspace: &WorkspaceSpec{Fixture: "fixture"},
				Width: 80, Height: 24, TimeoutMS: 5000, RunTimeoutMS: 15000, MaxOutputBytes: 100000,
				Steps: []Step{{Expect: "native signal target ready"}, {Text: "x"}, {Exit: intPointer(test.expected)}, {State: &a}}}
			result := RunDetailedContext(context.Background(), writeWorkspaceSpecAt(t, root, spec), RunOptions{}, io.Discard)
			if result.Target.ExitCode == nil || *result.Target.ExitCode != test.actual {
				t.Fatalf("lost native signal status: %+v", result.Target)
			}
			if !result.Cleanup.ConfirmedExited || result.Workspace == nil || !result.Workspace.Cleaned {
				t.Fatal("signal target cleanup unconfirmed")
			}
			if test.pass {
				if result.Err() != nil || result.Steps[3].State == nil || result.Steps[3].State.Outcome != "matched" {
					t.Fatalf("declared signal status/state failed: %v", result.Err())
				}
			} else if result.Failure == nil || result.Failure.Category != FailureUnexpectedExit {
				t.Fatalf("wrong signal accepted: %v", result.Err())
			}
		})
	}
}
