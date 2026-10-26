//go:build windows

package runner

import (
	"context"
	"encoding/base64"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"testing"
)

func TestNativeWideExitHelper(t *testing.T) {
	value := os.Getenv("PLAYTESTR_WIDE_EXIT_HELPER")
	if value == "" {
		return
	}
	code, err := strconv.ParseUint(value, 10, 32)
	if err != nil {
		os.Exit(11)
	}
	fmt.Print("native wide status target ready\r\n")
	var input [1]byte
	if _, err := io.ReadFull(os.Stdin, input[:]); err != nil || input[0] != 'x' {
		os.Exit(12)
	}
	if err := os.WriteFile("saved.txt", []byte("native status evidence\n"), 0600); err != nil {
		os.Exit(13)
	}
	os.Exit(int(code))
}

func TestNativeWindowsWideExitStatusAndSameRunState(t *testing.T) {
	if strconv.IntSize < 64 {
		t.Skip("published native Windows qualification uses amd64")
	}
	for _, test := range []struct {
		name     string
		actual   uint64
		expected uint64
		pass     bool
	}{
		{"above POSIX range", 256, 256, true},
		{"native control C status", 0xc000013a, 0xc000013a, true},
		{"maximum DWORD", 0xffffffff, 0xffffffff, true},
		{"unexpected native status", 0xc000013a, 0, false},
	} {
		t.Run(test.name, func(t *testing.T) {
			root := t.TempDir()
			if err := os.Mkdir(filepath.Join(root, "fixture"), 0700); err != nil {
				t.Fatal(err)
			}
			encoded := base64.StdEncoding.EncodeToString([]byte("native status evidence\n"))
			state := StateAssertion{Path: "saved.txt", Kind: "file", BytesBase64: &encoded}
			spec := Spec{Version: 3, Command: []string{os.Args[0], "-test.run=^TestNativeWideExitHelper$"},
				Env:       map[string]string{"PLAYTESTR_WIDE_EXIT_HELPER": strconv.FormatUint(test.actual, 10)},
				Workspace: &WorkspaceSpec{Fixture: "fixture"}, Width: 80, Height: 24,
				TimeoutMS: 5000, RunTimeoutMS: 15000, MaxOutputBytes: 100000,
				Steps: []Step{{Expect: "native wide status target ready"}, {Text: "x"}, {Key: "Enter"},
					{Exit: intPointer(int(test.expected))}, {State: &state}}}
			result := RunDetailedContext(context.Background(), writeWorkspaceSpecAt(t, root, spec), RunOptions{}, io.Discard)
			if result.Target.ExitCode == nil || *result.Target.ExitCode != int(test.actual) {
				t.Fatalf("lost native Windows status: %+v; failure: %+v", result.Target, result.Failure)
			}
			if !result.Cleanup.ConfirmedExited || result.Workspace == nil || !result.Workspace.Cleaned {
				t.Fatal("native status target/workspace cleanup unconfirmed")
			}
			if test.pass {
				if result.Err() != nil || result.Steps[4].State == nil || result.Steps[4].State.Outcome != "matched" {
					t.Fatalf("exact native status and same-run state failed: %v", result.Err())
				}
			} else if result.Failure == nil || result.Failure.Category != FailureUnexpectedExit {
				t.Fatalf("wrong native status accepted: %v", result.Err())
			}
		})
	}
}
