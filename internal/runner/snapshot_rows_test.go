package runner

import (
	"context"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestRowSnapshotFreshCaptureReplayAndRealDefect(t *testing.T) {
	r := newHelperRecording(t, "row-view", nil)
	capture(t, r, Step{Expect: "row "})
	if err := r.CaptureRowsSnapshot("body.rows.json", 2, 2); err != nil {
		t.Fatal(err)
	}
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
	if err := r.Export(context.Background()); err != nil {
		t.Fatal(err)
	}
	data, err := readSnapshot(filepath.Join(filepath.Dir(r.path), "snapshots", "body.rows.json"))
	if err != nil {
		t.Fatal(err)
	}
	rows, err := decodeSnapshotRows(data)
	if err != nil || rows.Text != "row stable caf\u00e9\n" {
		t.Fatalf("rows=%+v err=%v", rows, err)
	}
	// Different target PIDs are ignored only because the author selected row 2.
	for i := 0; i < 2; i++ {
		if err := RunContext(context.Background(), r.path, false, io.Discard); err != nil {
			t.Fatal(err)
		}
	}
	spec := r.spec
	spec.Env["PLAYTESTR_ROWS_DEFECT"] = "1"
	changed, _ := json.Marshal(spec)
	if err := os.WriteFile(r.path, changed, 0600); err != nil {
		t.Fatal(err)
	}
	result := RunDetailedContext(context.Background(), r.path, RunOptions{}, io.Discard)
	if result.Failure == nil || result.Failure.Category != FailureSnapshotMismatch {
		t.Fatalf("result=%+v", result)
	}
	screen, err := os.ReadFile(result.Evidence.ScreenPath)
	if err != nil || !strings.Contains(string(screen), "instance=") || !strings.Contains(string(screen), "row broken") {
		t.Fatalf("complete failure viewport lost: %s, %v", screen, err)
	}
	if !result.Cleanup.ConfirmedExited {
		t.Fatal("defect target cleanup unconfirmed")
	}
	// Selected intentional updates preserve the explicit range and format.
	if err := RunContextWithOptions(context.Background(), r.path, RunOptions{Update: true, Snapshot: "body.rows.json"}, io.Discard); err != nil {
		t.Fatal(err)
	}
	updated, err := readSnapshot(filepath.Join(filepath.Dir(r.path), "snapshots", "body.rows.json"))
	if err != nil {
		t.Fatal(err)
	}
	next, err := decodeSnapshotRows(updated)
	if err != nil || next.First != 2 || next.Last != 2 || next.Text != "row broken caf\u00e9\n" {
		t.Fatalf("updated=%+v err=%v", next, err)
	}
}

func TestRowSnapshotRejectsUnreadyEmptyInvalidAndResizedBounds(t *testing.T) {
	r := newHelperRecording(t, "row-view", nil)
	if err := r.CaptureRowsSnapshot("body.rows.json", 2, 2); err == nil {
		t.Fatal("unready capture accepted")
	}
	capture(t, r, Step{Expect: "row "})
	for _, bounds := range [][2]int{{0, 2}, {3, 2}, {1, 501}, {4, 4}} {
		if err := r.CaptureRowsSnapshot("body.rows.json", bounds[0], bounds[1]); err == nil {
			t.Fatalf("bounds %v accepted", bounds)
		}
	}
	if err := r.CaptureRowsSnapshot("body.txt", 2, 2); err == nil {
		t.Fatal("implicit format accepted")
	}
	capture(t, r, Step{Resize: &TerminalSize{Width: 80, Height: 10}})
	if err := r.CaptureRowsSnapshot("body.rows.json", 2, 24); err == nil {
		t.Fatal("range outside resized viewport accepted")
	}
}

func TestRowSnapshotMetadataIsStrict(t *testing.T) {
	for _, text := range []string{"", "null", `""`, `"   "`, `"a\nb\nc\n"`} {
		data := `{"snapshot_version":1,"first_row":1,"last_row":2`
		if text != "" {
			data += `,"text":` + text
		}
		data += `}`
		if _, err := decodeSnapshotRows([]byte(data)); err == nil {
			t.Fatalf("invalid text accepted: %s", data)
		}
	}
	for _, data := range []string{`{}`, `{"snapshot_version":2,"first_row":1,"last_row":2}`, `{"snapshot_version":1,"first_row":1,"last_row":2,"mask":"auto"}`, `{"snapshot_version":1,"first_row":1,"last_row":2} {}`, `{"snapshot_version":1,"first_row":0,"last_row":2}`} {
		if _, err := decodeSnapshotRows([]byte(data)); err == nil {
			t.Fatalf("invalid metadata accepted: %s", data)
		}
	}
}

func TestRowSnapshotUpdateRemainsUnchangedAfterLaterFailure(t *testing.T) {
	r := newHelperRecording(t, "row-view", nil)
	capture(t, r, Step{Expect: "row "})
	if err := r.CaptureRowsSnapshot("body.rows.json", 2, 2); err != nil {
		t.Fatal(err)
	}
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
	if err := r.Export(context.Background()); err != nil {
		t.Fatal(err)
	}
	baseline := filepath.Join(filepath.Dir(r.path), "snapshots", "body.rows.json")
	before, err := os.ReadFile(baseline)
	if err != nil {
		t.Fatal(err)
	}
	spec := r.spec
	spec.Env["PLAYTESTR_ROWS_DEFECT"] = "1"
	spec.Steps = append(spec.Steps, Step{Expect: "missing final confirmation"})
	spec.TimeoutMS = 300
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(r.path, data, 0600); err != nil {
		t.Fatal(err)
	}
	result := RunDetailedContext(context.Background(), r.path, RunOptions{Update: true, Snapshot: "body.rows.json"}, io.Discard)
	if result.Err() == nil || !result.Cleanup.ConfirmedExited {
		t.Fatalf("result=%+v", result)
	}
	after, err := os.ReadFile(baseline)
	if err != nil {
		t.Fatal(err)
	}
	if string(before) != string(after) {
		t.Fatal("row snapshot staged update committed after later failure")
	}
}
