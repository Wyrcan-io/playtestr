package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestStateMaintenanceRetainsExactUnrelatedJSONBytes(t *testing.T) {
	original := []byte("{\r\n  \"version\" : 3, \"steps\" : [ {\"expect\":\"ready\"}, {\"state\":{\"path\":\"file\",\"kind\":\"file\",\"bytes_base64\":\"YQ==\"}}, { \"exit\" : 0 } ]\r\n}")
	var spec Spec
	if err := json.Unmarshal(original, &spec); err != nil {
		t.Fatal(err)
	}
	replacement := fileState("file", []byte("b"))
	spec.Steps[1].State = &replacement
	updated, err := preserveUnchangedSpecBytes(original, spec.Steps, nil)
	if err != nil {
		t.Fatal(err)
	}
	start := strings.Index(string(original), `{"state"`)
	end := strings.Index(string(original[start:]), `}},`) + start + 2
	if !bytes.HasPrefix(updated, original[:start]) || !bytes.HasSuffix(updated, original[end:]) {
		t.Fatal("unrelated original JSON bytes changed")
	}
}

func stateMaintenanceFixture(t *testing.T) (string, Spec, []byte) {
	t.Helper()
	r := newHelperRecording(t, "state-save", func(s *Spec) { s.Version = StateSpecVersion; s.Workspace = &WorkspaceSpec{Fixture: "fixture"} })
	capture(t, r, Step{Expect: "Saved successfully"}, Step{Exit: intPointer(0)})
	if err := r.CaptureState("saved.bin", "file"); err != nil {
		t.Fatal(err)
	}
	if err := r.CaptureState("seed.txt", "file"); err != nil {
		t.Fatal(err)
	}
	capture(t, r, Step{Snapshot: "saved.txt"})
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
	if err := r.Export(context.Background()); err != nil {
		t.Fatal(err)
	}
	spec, err := Load(r.path)
	if err != nil {
		t.Fatal(err)
	}
	wrong := fileState("saved.bin", []byte("old reviewed state"))
	spec.Steps[2].State = &wrong
	data, err := json.MarshalIndent(spec, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(r.path, data, 0600); err != nil {
		t.Fatal(err)
	}
	snapshot, err := os.ReadFile(filepath.Join(filepath.Dir(r.path), "snapshots", "saved.txt"))
	if err != nil {
		t.Fatal(err)
	}
	return r.path, spec, snapshot
}

func TestStateMaintenancePreservesUnrelatedExpectations(t *testing.T) {
	path, original, snapshot := stateMaintenanceFixture(t)
	if result := RunDetailedContext(context.Background(), path, RunOptions{}, io.Discard); result.Failure == nil || result.Failure.Category != FailureState {
		t.Fatalf("seeded mismatch did not fail: %v", result.Err())
	}
	r, err := OpenRecording(context.Background(), path)
	if err != nil {
		t.Fatal(err)
	}
	defer r.Close()
	if err := r.UpdateStateStep(context.Background(), 3); err != nil {
		t.Fatal(err)
	}
	if err := r.Export(context.Background()); err == nil {
		t.Fatal("maintenance saved without replay")
	}
	if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
		t.Fatal(result.Err())
	}
	if err := r.Export(context.Background()); err != nil {
		t.Fatal(err)
	}
	updated, err := Load(path)
	if err != nil {
		t.Fatal(err)
	}
	original.Steps[2] = updated.Steps[2]
	oldBytes, _ := json.Marshal(original)
	newBytes, _ := json.Marshal(updated)
	if !bytes.Equal(oldBytes, newBytes) {
		t.Fatal("unrelated spec expectations changed")
	}
	got, err := os.ReadFile(filepath.Join(filepath.Dir(path), "snapshots", "saved.txt"))
	if err != nil || !bytes.Equal(got, snapshot) {
		t.Fatalf("unrelated snapshot changed: %v", err)
	}
	if err := RunContext(context.Background(), path, false, io.Discard); err != nil {
		t.Fatal(err)
	}
}

func TestStateMaintenanceCancellationAndConcurrentEditPreserveApproval(t *testing.T) {
	for _, concurrent := range []bool{false, true} {
		t.Run(map[bool]string{false: "cancelled", true: "concurrent edit"}[concurrent], func(t *testing.T) {
			path, _, _ := stateMaintenanceFixture(t)
			r, err := OpenRecording(context.Background(), path)
			if err != nil {
				t.Fatal(err)
			}
			defer r.Close()
			if err := r.UpdateStateStep(context.Background(), 3); err != nil {
				t.Fatal(err)
			}
			if result := r.Replay(context.Background(), io.Discard); result.Err() != nil {
				t.Fatal(result.Err())
			}
			before, err := os.ReadFile(path)
			if err != nil {
				t.Fatal(err)
			}
			ctx := context.Background()
			if concurrent {
				before = append(before, '\n')
				if err := os.WriteFile(path, before, 0600); err != nil {
					t.Fatal(err)
				}
			} else {
				var cancel context.CancelFunc
				ctx, cancel = context.WithCancel(ctx)
				cancel()
			}
			if err := r.Export(ctx); err == nil {
				t.Fatal("unsafe maintenance accepted")
			}
			after, err := os.ReadFile(path)
			if err != nil || !bytes.Equal(before, after) {
				t.Fatalf("approved original changed after failed save: %v", err)
			}
		})
	}
}
