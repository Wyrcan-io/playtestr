package runner

import (
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"golang.org/x/term"
)

func TestAlternateEvidenceHelper(t *testing.T) {
	mode := os.Getenv("PLAYTESTR_ALTERNATE_EVIDENCE")
	if mode == "" {
		return
	}
	state, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		os.Exit(9)
	}
	fmt.Print("\x1b[?1049h\x1b[2J\x1b[Hreviewed TUI final frame")
	var input [1]byte
	if _, err := io.ReadFull(os.Stdin, input[:]); err != nil || input[0] != 'x' {
		os.Exit(10)
	}
	fmt.Print("\x1b[?1049l")
	if mode == "primary" {
		fmt.Print("fresh primary diagnosis")
	}
	_ = term.Restore(int(os.Stdin.Fd()), state)
	os.Exit(0)
}

func TestPostExitFailureKeepsAlternateEvidenceWithoutChangingAssertions(t *testing.T) {
	for _, name := range []string{"missing-state", "primary", "live-assertion", "snapshot"} {
		t.Run(name, func(t *testing.T) {
			root := t.TempDir()
			if err := os.Mkdir(filepath.Join(root, "fixture"), 0700); err != nil {
				t.Fatal(err)
			}
			spec := Spec{Version: 3, Name: name,
				Command:   []string{os.Args[0], "-test.run=^TestAlternateEvidenceHelper$"},
				Env:       map[string]string{"PLAYTESTR_ALTERNATE_EVIDENCE": name},
				Workspace: &WorkspaceSpec{Fixture: "fixture", CWD: ".", Home: "temporary", Temp: "temporary"},
				Width:     40, Height: 8, TimeoutMS: 3000, RunTimeoutMS: 15000, MaxOutputBytes: 100000,
				Steps: []Step{{Expect: "reviewed TUI final frame"}, {Text: "x"}, {Exit: intPointer(0)}},
			}
			category := FailureState
			switch name {
			case "live-assertion":
				spec.Steps = append(spec.Steps, Step{Expect: "reviewed TUI final frame"})
				category = FailureAssertionTimeout
			case "snapshot":
				spec.Steps = append(spec.Steps, Step{Snapshot: "wanted.txt"})
				category = FailureSnapshotMismatch
			default:
				a := fileState("saved.txt", []byte("reviewed"))
				spec.Steps = append(spec.Steps, Step{State: &a})
			}
			path := writeWorkspaceSpecAt(t, root, spec)
			if name == "snapshot" {
				writeBaseline(t, path, "wanted.txt", "reviewed TUI final frame\n")
			}
			result := RunDetailedContext(context.Background(), path, RunOptions{}, io.Discard)
			if result.Failure == nil || result.Failure.Category != category || !result.Target.Exited || result.Target.ExitCode == nil || *result.Target.ExitCode != 0 || !result.Cleanup.ConfirmedExited || result.Workspace == nil || !result.Workspace.Cleaned {
				t.Fatalf("lost actual failure/exit/cleanup: %+v %v", result, result.Err())
			}
			data, err := os.ReadFile(result.Evidence.ScreenPath)
			if err != nil {
				t.Fatal(err)
			}
			screen := string(data)
			switch name {
			case "snapshot":
				if strings.TrimSpace(screen) != "" {
					t.Fatalf("snapshot mismatch must retain its actual blank frame: %q", screen)
				}
			case "primary":
				if !strings.Contains(screen, "fresh primary diagnosis") || strings.Contains(screen, "reviewed TUI final frame") {
					t.Fatalf("replaced newer primary evidence: %q", screen)
				}
			default:
				if !strings.Contains(screen, "reviewed TUI final frame") {
					t.Fatalf("lost the final useful alternate frame: %q", screen)
				}
			}
		})
	}
}
