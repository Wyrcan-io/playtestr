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
	spec := Spec{Version: SpecVersion,
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

func TestStructuredSnapshotMismatchResult(t *testing.T) {
	path := writeSnapshotSpec(t, "exit-zero", "result.txt")
	writeBaseline(t, path, "result.txt", "wrong\n")
	result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
	if result.Status != "failed" || result.Failure == nil || result.Failure.Category != FailureSnapshotMismatch {
		t.Fatalf("result = %+v", result)
	}
	if strings.Contains(result.Failure.Message, "finished cleanly") || strings.Contains(result.Failure.Message, "wrong") {
		t.Fatalf("structured failure embedded terminal content: %q", result.Failure.Message)
	}
	if len(result.Steps) != 3 || result.Steps[0].Status != "passed" || result.Steps[1].Status != "passed" || result.Steps[2].Status != "failed" {
		t.Fatalf("steps = %+v", result.Steps)
	}
	if !result.Target.Exited || result.Target.ExitCode == nil || *result.Target.ExitCode != 0 {
		t.Fatalf("target = %+v", result.Target)
	}
	if !result.Cleanup.Attempted || !result.Cleanup.ConfirmedExited || result.Evidence.ScreenPath == "" || result.Evidence.DiffPath == "" {
		t.Fatalf("cleanup/evidence = %+v %+v", result.Cleanup, result.Evidence)
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

func TestCancellationImmediatelyAfterFinalStepPreventsSnapshotCommit(t *testing.T) {
	spec := Spec{
		Version: SpecVersion, Name: "cancel-after-final-step",
		Command: []string{os.Args[0], "-test.run=TestHelperProcess", "--", "hang"},
		Env:     map[string]string{"PLAYTESTR_HELPER_PROCESS": "1"},
		Width:   40, Height: 8, TimeoutMS: 5000, RunTimeoutMS: 5000, MaxOutputBytes: 100000,
		Steps: []Step{{Expect: "still running"}, {Snapshot: "final.txt"}},
	}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "spec.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	baseline := writeBaseline(t, path, "final.txt", "keep this\n")
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()
	output := cancelAfterStepWriter{step: "  PASS step 2\n", cancel: cancel}
	result := RunDetailedContext(ctx, path, RunOptions{Update: true}, &output)
	if result.Status != "cancelled" || result.Failure == nil || result.Failure.Category != FailureCancellation {
		t.Fatalf("result = %+v", result)
	}
	content, err := os.ReadFile(baseline)
	if err != nil {
		t.Fatal(err)
	}
	if string(content) != "keep this\n" {
		t.Fatalf("snapshot was committed after final-step cancellation: %q", content)
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
	spec := Spec{Version: SpecVersion,
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

func TestUnifiedTextDiffShowsEmptyAndFinalNewlineDifferences(t *testing.T) {
	newline := unifiedTextDiff("screen.txt", "same", "same\n")
	if !strings.Contains(newline, "No newline at end of file") {
		t.Fatalf("newline diff = %q", newline)
	}
	empty := unifiedTextDiff("screen.txt", "", "content\n")
	if !strings.Contains(empty, "+content") {
		t.Fatalf("empty diff = %q", empty)
	}
}

func TestStagedSnapshotMemoryIsBounded(t *testing.T) {
	updates := newSnapshotUpdates()
	err := updates.stage("large.txt", strings.Repeat("x", maxStagedSnapshotBytes+1))
	if err == nil || categoryOf(err) != FailureSnapshotUpdate {
		t.Fatalf("got %v (%s)", err, categoryOf(err))
	}
	if len(updates.values) != 0 || updates.bytes != 0 {
		t.Fatalf("oversized update was staged: %+v", updates)
	}
}

func TestSnapshotRollbackRestoresEveryChangedFile(t *testing.T) {
	directory := t.TempDir()
	existing := filepath.Join(directory, "existing.txt")
	created := filepath.Join(directory, "created.txt")
	if err := os.WriteFile(existing, []byte("new existing\n"), 0644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(created, []byte("new created\n"), 0644); err != nil {
		t.Fatal(err)
	}
	originals := map[string]originalSnapshot{
		existing: {data: []byte("old existing\n"), exists: true},
		created:  {exists: false},
	}
	if changed := rollbackSnapshotUpdates([]string{existing, created}, originals); len(changed) != 0 {
		t.Fatalf("rollback left changed files: %v", changed)
	}
	content, err := os.ReadFile(existing)
	if err != nil || string(content) != "old existing\n" {
		t.Fatalf("existing file was not restored: %q, %v", content, err)
	}
	if _, err := os.Stat(created); !os.IsNotExist(err) {
		t.Fatalf("created file survived rollback: %v", err)
	}
}
