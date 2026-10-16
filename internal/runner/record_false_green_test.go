package runner

import (
	"context"
	"io"
	"testing"
)

func TestRecordingRejectedStateCannotSilentlyDisappearFromExport(t *testing.T) {
	r := newHelperRecording(t, "state-save", func(s *Spec) { s.Version = 3; s.Workspace = &WorkspaceSpec{Fixture: "fixture"} })
	capture(t, r, Step{Expect: "Saved successfully"}, Step{Exit: intPointer(0)})
	if err := r.CaptureState("never-written", "file"); err == nil {
		t.Fatal("missing file capture passed")
	}
	if result := r.Replay(context.Background(), io.Discard); result.Err() == nil {
		t.Fatal("rejected saved-state control disappeared into successful replay")
	}
	if err := r.Export(context.Background()); err == nil {
		t.Fatal("partial candidate exported despite unresolved state capture failure")
	}
}

func TestRecordingInputOnlyCandidateCannotReplayAsUsefulTest(t *testing.T) {
	r := newHelperRecording(t, "hang", nil)
	capture(t, r, Step{Text: "x"}, Step{Key: "Enter"})
	if result := r.Replay(context.Background(), io.Discard); result.Err() == nil {
		t.Fatal("input-only recording falsely passed without a completion checkpoint")
	}
}

func TestRecordingExplicitDiscardStillRequiresFreshCompletion(t *testing.T) {
	r := newHelperRecording(t, "hang", nil)
	capture(t, r, Step{Expect: "still running"}, Step{Text: "x"})
	if err := r.Capture(Step{Key: "F12"}); err == nil {
		t.Fatal("unsupported control accepted")
	}
	r.DiscardCaptureErrors()
	if result := r.Replay(context.Background(), io.Discard); result.Err() == nil {
		t.Fatal("discarding an error supplied false completion evidence")
	}
	// Explicitly retain only the initial positive checkpoint in fresh state.
	if err := r.Rerecord(context.Background(), 1); err != nil {
		t.Fatal(err)
	}
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
}
