package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func writeSnapshotSpec(t *testing.T, mode string, names ...string) string {
	t.Helper()
	steps := []Step{{Expect: map[string]string{
		"exit-zero":      "finished cleanly",
		"hang":           "still running",
		"delayed-redraw": "ready",
	}[mode]}}
	if mode == "exit-zero" {
		steps = append(steps, Step{Exit: intPointer(0)})
	}
	for _, name := range names {
		steps = append(steps, Step{Snapshot: name})
	}
	if mode == "hang" {
		steps = append(steps, Step{Exit: intPointer(0)})
	}
	spec := Spec{
		Name: mode, Command: []string{os.Args[0], "-test.run=TestHelperProcess", "--", mode},
		Env: map[string]string{"PLAYTESTR_HELPER_PROCESS": "1"}, Width: 40, Height: 8,
		TimeoutMS: 5000, RunTimeoutMS: 5000, MaxOutputBytes: 100000, Steps: steps,
	}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "spec.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	return path
}

func writeBaseline(t *testing.T, specPath, name, value string) string {
	t.Helper()
	path := filepath.Join(filepath.Dir(specPath), "snapshots", name)
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, []byte(value), 0644); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestSnapshotBaselineAndReadableMismatch(t *testing.T) {
	path := writeSnapshotSpec(t, "exit-zero", "result.txt")
	writeBaseline(t, path, "result.txt", "finished cleanly   \r\n\r\n")
	if err := Run(path, false, &bytes.Buffer{}); err != nil {
		t.Fatalf("clean baseline failed: %v", err)
	}

	writeBaseline(t, path, "result.txt", "finished badly\nextra line\n")
	var output bytes.Buffer
	err := Run(path, false, &output)
	if err == nil {
		t.Fatal("changed baseline passed")
	}
	for _, expected := range []string{
		`snapshot "result.txt" did not match`,
		"--- expected: result.txt",
		"+++ actual: result.txt",
		"-finished badly",
		"-extra line",
		"+finished cleanly",
	} {
		if !strings.Contains(err.Error(), expected) {
			t.Fatalf("error did not contain %q: %v", expected, err)
		}
	}
	actual, readErr := os.ReadFile(path + ".actual.txt")
	if readErr != nil {
		t.Fatal(readErr)
	}
	if string(actual) != "finished cleanly\n" {
		t.Fatalf("actual artifact = %q", actual)
	}
	diff, readErr := os.ReadFile(path + ".diff.txt")
	if readErr != nil {
		t.Fatal(readErr)
	}
	if !bytes.Contains(diff, []byte("+finished cleanly")) {
		t.Fatalf("diff artifact = %q", diff)
	}
	if !strings.Contains(output.String(), "Diff saved:") || !strings.Contains(output.String(), "Screen saved:") {
		t.Fatalf("artifact output = %q", output.String())
	}
}

func TestSnapshotSettlesAfterExplicitReadiness(t *testing.T) {
	path := writeSnapshotSpec(t, "delayed-redraw", "settled.txt")
	writeBaseline(t, path, "settled.txt", "ready complete\n")
	if err := Run(path, false, &bytes.Buffer{}); err != nil {
		t.Fatal(err)
	}
}

func TestSnapshotMissingAndSizeFailuresAreDistinct(t *testing.T) {
	t.Run("missing", func(t *testing.T) {
		path := writeSnapshotSpec(t, "exit-zero", "missing.txt")
		err := Run(path, false, &bytes.Buffer{})
		if err == nil || !strings.Contains(err.Error(), `snapshot "missing.txt" is missing`) || !strings.Contains(err.Error(), "--update") {
			t.Fatalf("got %v", err)
		}
	})

	t.Run("oversized", func(t *testing.T) {
		path := writeSnapshotSpec(t, "exit-zero", "large.txt")
		writeBaseline(t, path, "large.txt", strings.Repeat("x", maxSnapshotBytes+1))
		err := Run(path, false, &bytes.Buffer{})
		if err == nil || !strings.Contains(err.Error(), "snapshot exceeds") {
			t.Fatalf("got %v", err)
		}
	})
}

func TestTargetedSnapshotUpdate(t *testing.T) {
	path := writeSnapshotSpec(t, "exit-zero", "selected.txt", "other.txt")
	selectedPath := writeBaseline(t, path, "selected.txt", "old selected\n")
	otherPath := writeBaseline(t, path, "other.txt", "finished cleanly\n")
	originalOther, _ := os.ReadFile(otherPath)
	var output bytes.Buffer
	err := RunContextWithOptions(context.Background(), path, RunOptions{Update: true, Snapshot: "selected.txt"}, &output)
	if err != nil {
		t.Fatal(err)
	}
	selected, _ := os.ReadFile(selectedPath)
	other, _ := os.ReadFile(otherPath)
	if string(selected) != "finished cleanly\n" {
		t.Fatalf("selected baseline = %q", selected)
	}
	if !bytes.Equal(other, originalOther) {
		t.Fatalf("unselected baseline changed: before=%q after=%q", originalOther, other)
	}
	if !strings.Contains(output.String(), "Snapshot updated:") {
		t.Fatalf("output = %q", output.String())
	}

	output.Reset()
	if err := RunContextWithOptions(context.Background(), path, RunOptions{Update: true, Snapshot: "selected.txt"}, &output); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(output.String(), "Snapshot unchanged:") {
		t.Fatalf("output = %q", output.String())
	}
}

func TestSnapshotUpdatesAreNotCommittedAfterLaterFailure(t *testing.T) {
	path := writeSnapshotSpec(t, "exit-zero", "selected.txt", "later.txt")
	selectedPath := writeBaseline(t, path, "selected.txt", "keep this\n")
	writeBaseline(t, path, "later.txt", "force mismatch\n")
	err := RunContextWithOptions(context.Background(), path, RunOptions{Update: true, Snapshot: "selected.txt"}, &bytes.Buffer{})
	if err == nil || !strings.Contains(err.Error(), `snapshot "later.txt" did not match`) {
		t.Fatalf("got %v", err)
	}
	selected, _ := os.ReadFile(selectedPath)
	if string(selected) != "keep this\n" {
		t.Fatalf("staged update was committed after failure: %q", selected)
	}
}

func TestSnapshotUpdatesAreNotCommittedAfterCancellation(t *testing.T) {
	path := writeSnapshotSpec(t, "hang", "selected.txt")
	selectedPath := writeBaseline(t, path, "selected.txt", "keep this\n")
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	// Cancel only after the runner confirms that the snapshot step completed.
	// Process startup and the settling period can exceed 350 ms on busy hosts.
	output := cancelAfterStepWriter{step: "  PASS step 2\n", cancel: cancel}
	err := RunContextWithOptions(ctx, path, RunOptions{Update: true}, &output)
	if err == nil || !strings.Contains(err.Error(), "run cancelled") {
		t.Fatalf("got %v", err)
	}
	if !strings.Contains(output.String(), "PASS step 2") {
		t.Fatalf("snapshot was not staged before cancellation: %q", output.String())
	}
	selected, _ := os.ReadFile(selectedPath)
	if string(selected) != "keep this\n" {
		t.Fatalf("staged update was committed after cancellation: %q", selected)
	}
}

// The runner writes progress synchronously. This needs no timer, polling, or
// concurrent access to the captured output.
type cancelAfterStepWriter struct {
	bytes.Buffer
	step   string
	cancel context.CancelFunc
}

func (w *cancelAfterStepWriter) Write(p []byte) (int, error) {
	n, err := w.Buffer.Write(p)
	if strings.Contains(w.String(), w.step) {
		w.cancel()
	}
	return n, err
}

func TestUnknownSnapshotSelectorFailsBeforeTargetLaunch(t *testing.T) {
	pidFile := filepath.Join(t.TempDir(), "target.pid")
	spec := Spec{
		Name: "does-not-launch", Command: []string{os.Args[0], "-test.run=TestHelperProcess", "--", "self-hang"},
		Env:   map[string]string{"PLAYTESTR_HELPER_PROCESS": "1", "PLAYTESTR_PID_FILE": pidFile},
		Steps: []Step{{Expect: "self running"}, {Snapshot: "known.txt"}},
	}
	data, _ := json.Marshal(spec)
	path := filepath.Join(t.TempDir(), "spec.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	err := RunContextWithOptions(context.Background(), path, RunOptions{Update: true, Snapshot: "unknown.txt"}, &bytes.Buffer{})
	if err == nil || !strings.Contains(err.Error(), "is not referenced") {
		t.Fatalf("got %v", err)
	}
	if _, err := os.Stat(pidFile); !errorsIsNotExist(err) {
		t.Fatalf("target launched before selector validation: %v", err)
	}
}

func errorsIsNotExist(err error) bool {
	return err != nil && os.IsNotExist(err)
}

func TestUnifiedTextDiffAddedRemovedAndSeparatedChanges(t *testing.T) {
	diff := unifiedTextDiff("screen.txt",
		"alpha\nremove me\ncontext one\ncontext two\ncontext three\ncontext four\nold tail\n",
		"alpha\ncontext one\ncontext two\ncontext three\ncontext four\nnew tail\nadded\n")
	for _, expected := range []string{"--- expected: screen.txt", "-remove me", "-old tail", "+new tail", "+added", "@@"} {
		if !strings.Contains(diff, expected) {
			t.Fatalf("diff did not contain %q:\n%s", expected, diff)
		}
	}
}
