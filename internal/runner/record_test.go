package runner

import (
	"context"
	"errors"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

func newHelperRecording(t *testing.T, mode string, configure func(*Spec)) *Recording {
	t.Helper()
	spec := Spec{Version: 1, Command: []string{os.Args[0], "-test.run=TestHelperProcess", "--", mode}, Env: map[string]string{"PLAYTESTR_HELPER_PROCESS": "1"}, TimeoutMS: 5000, RunTimeoutMS: 30000}
	if configure != nil {
		configure(&spec)
	}
	dir := t.TempDir()
	if spec.Workspace != nil {
		if err := os.Mkdir(filepath.Join(dir, "fixture"), 0755); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(filepath.Join(dir, "fixture", "seed.txt"), []byte("synthetic"), 0600); err != nil {
			t.Fatal(err)
		}
	}
	r, err := StartRecording(context.Background(), filepath.Join(dir, "recorded.json"), spec)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		if err := r.Close(); err != nil {
			t.Error(err)
		}
	})
	return r
}

func capture(t *testing.T, r *Recording, steps ...Step) {
	t.Helper()
	for _, s := range steps {
		if err := r.Capture(s); err != nil {
			t.Fatal(err)
		}
	}
}

func TestRecordingReplayExportAndMaintenance(t *testing.T) {
	r := newHelperRecording(t, "modal-transition", nil)
	capture(t, r, Step{Expect: "Keybindings"}, Step{Snapshot: "modal.txt"}, Step{Key: "Escape"}, Step{ExpectNot: "Keybindings"}, Step{Expect: "Main ready"}, Step{Exit: intPointer(0)}, Step{Snapshot: "main.txt"})
	if err := r.Export(context.Background()); err == nil {
		t.Fatal("unreplayed export accepted")
	}
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
	if err := r.Export(context.Background()); err != nil {
		t.Fatal(err)
	}
	if err := RunContext(context.Background(), r.path, false, io.Discard); err != nil {
		t.Fatal(err)
	}
	if err := r.Export(context.Background()); err == nil {
		t.Fatal("overwrite accepted")
	}
	steps := r.Steps()
	steps[4].Expect = "target defect"
	if err := r.Edit(steps); err != nil {
		t.Fatal(err)
	}
	if result := r.Replay(context.Background(), io.Discard); result.Err() == nil {
		t.Fatal("bad edit passed")
	}
	first, screen := r.FirstFailure()
	if first == nil || !strings.Contains(screen, "Main ready") {
		t.Fatal("first failure evidence lost")
	}
	steps[4].Expect = "Main ready"
	if err := r.Edit(steps); err != nil {
		t.Fatal(err)
	}
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
	if again, _ := r.FirstFailure(); again != first {
		t.Fatal("recovery erased first failure")
	}
	if _, err := os.Stat(r.path + ".actual.txt"); !errors.Is(err, os.ErrNotExist) {
		t.Fatal("secret-bearing replay draft persisted")
	}
}

func TestRecordingInvalidActionsAreNotAccepted(t *testing.T) {
	r := newHelperRecording(t, "private-input", nil)
	capture(t, r, Step{Expect: "private input ready"})
	for _, step := range []Step{{Key: "F12"}, {Text: string([]byte{255})}, {Text: strings.Repeat("x", 65537)}, {Resize: &TerminalSize{Width: 501, Height: 10}}, {Snapshot: "../bad.txt"}, {Expect: " "}, {Key: "Enter", Text: "two"}} {
		before := len(r.Steps())
		if err := r.Capture(step); err == nil {
			t.Fatalf("accepted %+v", step)
		}
		if len(r.Steps()) != before {
			t.Fatal("invalid event entered draft")
		}
	}
	capture(t, r, Step{Snapshot: "ready.txt"})
	if err := r.Capture(Step{Snapshot: "ready.txt"}); err == nil {
		t.Fatal("duplicate accepted")
	}
	capture(t, r, Step{Text: "hello"})
	if err := r.Capture(Step{Snapshot: "unready.txt"}); err == nil {
		t.Fatal("unready snapshot accepted")
	}
	if err := r.Capture(Step{Expect: "private input ready"}); err == nil {
		t.Fatal("stale anchor accepted")
	}
}

func TestRecordingRerecordFreshPrefix(t *testing.T) {
	r := newHelperRecording(t, "modal-transition", nil)
	capture(t, r, Step{Expect: "Keybindings"}, Step{Snapshot: "modal.txt"}, Step{Key: "Escape"}, Step{Expect: "Main ready"}, Step{Exit: intPointer(0)})
	if err := r.Rerecord(context.Background(), 2); err != nil {
		t.Fatal(err)
	}
	capture(t, r, Step{Key: "Escape"}, Step{ExpectNot: "Keybindings"}, Step{Expect: "Main ready"}, Step{Exit: intPointer(0)})
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
}

func TestRecordingCancellationAndFloodStopIdleTargets(t *testing.T) {
	for _, mode := range []string{"hang", "flood"} {
		t.Run(mode, func(t *testing.T) {
			r := newHelperRecording(t, mode, func(s *Spec) { s.RunTimeoutMS = 500; s.MaxOutputBytes = 2048 })
			select {
			case <-r.Context().Done():
			case <-time.After(5 * time.Second):
				t.Fatal("idle recording unbounded")
			}
			if mode == "flood" && !errors.Is(r.InputError(context.Canceled), errOutputLimit) {
				t.Fatal("idle overflow misclassified as operator cancellation")
			}
			if err := r.Close(); err != nil {
				t.Fatal(err)
			}
			if _, err := os.Stat(r.path); !errors.Is(err, os.ErrNotExist) {
				t.Fatal("cancel exported")
			}
		})
	}
}

func TestRecordingFixtureChangesAndCanceledExport(t *testing.T) {
	r := newHelperRecording(t, "workspace-state", func(s *Spec) {
		s.Version = 2
		s.Workspace = &WorkspaceSpec{Fixture: "fixture", Home: "temporary", Temp: "temporary"}
	})
	capture(t, r, Step{Expect: "fresh workspace seed=synthetic"}, Step{Exit: intPointer(0)}, Step{Snapshot: "state.txt"})
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := r.Export(ctx); !errors.Is(err, context.Canceled) {
		t.Fatalf("canceled export: %v", err)
	}
	if _, err := os.Stat(r.path); !errors.Is(err, os.ErrNotExist) {
		t.Fatal("canceled export persisted")
	}
	if err := os.WriteFile(filepath.Join(filepath.Dir(r.path), "fixture", "seed.txt"), []byte("changed"), 0600); err != nil {
		t.Fatal(err)
	}
	if result := r.Replay(context.Background(), io.Discard); result.Err() == nil || !strings.Contains(result.Err().Error(), "fixture changed") {
		t.Fatalf("dirty fixture: %v", result.Err())
	}
}

func TestRecordingCleanupFailureIsPreserved(t *testing.T) {
	r := newHelperRecording(t, "workspace-marker-tamper", func(s *Spec) { s.Version = 2; s.Workspace = &WorkspaceSpec{Fixture: "fixture"} })
	capture(t, r, Step{Expect: "workspace ready"})
	w := r.workspace
	err := r.Close()
	if err == nil || !strings.Contains(err.Error(), "retained") {
		t.Fatalf("cleanup evidence: %v", err)
	}
	if r.Close() != err {
		t.Fatal("idempotent close erased cleanup failure")
	}
	if _, statErr := os.Stat(w.root); statErr != nil {
		t.Fatal("unowned workspace removed")
	}
	// Test-only repair of this known synthetic marker; preserve the original error.
	if repairErr := os.WriteFile(filepath.Join(w.root, workspaceMarker), []byte(w.token), 0600); repairErr != nil {
		t.Fatal(repairErr)
	}
	if repairErr := cleanupPreparedWorkspace(w); repairErr != nil {
		t.Fatal(repairErr)
	}
	r.closeErr = nil
	r.workspace = nil
}

func TestRecordingTracksDescendantCleanupAndExpectedNonzero(t *testing.T) {
	r := newHelperRecording(t, "parent-child", nil)
	capture(t, r, Step{Expect: "child started:"})
	session := r.session
	if err := r.Close(); err != nil {
		t.Fatal(err)
	}
	if !session.stopResult.confirmedExited {
		t.Fatal("descendants unconfirmed")
	}
	nonzero := newHelperRecording(t, "exit-seven", nil)
	capture(t, nonzero, Step{Expect: "about to crash"}, Step{Exit: intPointer(7)})
	if result := nonzero.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
}

func TestRecordingRejectsAmbiguousAndDynamicReadiness(t *testing.T) {
	ambiguous := newHelperRecording(t, "ambiguous-output", nil)
	if err := ambiguous.Capture(Step{Expect: "ready"}); err == nil {
		t.Fatal("ambiguous anchor accepted")
	}
	if len(ambiguous.Steps()) != 0 {
		t.Fatal("ambiguous candidate entered draft")
	}
	dynamic := newHelperRecording(t, "dynamic-output", nil)
	capture(t, dynamic, Step{Expect: "dynamic ready"}, Step{Snapshot: "dynamic.txt"})
	result := dynamic.Replay(context.Background(), io.Discard)
	if result.Failure == nil || result.Failure.Category != FailureSnapshotMismatch {
		t.Fatalf("dynamic content silently normalized: %+v", result)
	}
}

type interruptedExportContext struct {
	context.Context
	checks int
}

func (c *interruptedExportContext) Err() error {
	c.checks++
	if c.checks >= 4 {
		return context.Canceled
	}
	return nil
}

func TestRecordingInterruptedExportRollsBackWrittenFiles(t *testing.T) {
	r := newHelperRecording(t, "exit-zero", nil)
	capture(t, r, Step{Exit: intPointer(0)}, Step{Snapshot: "first.txt"}, Step{Snapshot: "second.txt"})
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
	ctx := &interruptedExportContext{Context: context.Background()}
	if err := r.Export(ctx); !errors.Is(err, context.Canceled) {
		t.Fatalf("interrupted transaction: %v", err)
	}
	for _, path := range []string{r.path, filepath.Join(filepath.Dir(r.path), "snapshots", "first.txt"), filepath.Join(filepath.Dir(r.path), "snapshots", "second.txt")} {
		if _, err := os.Stat(path); !errors.Is(err, os.ErrNotExist) {
			t.Fatalf("partial export left %s: %v", path, err)
		}
	}
}
