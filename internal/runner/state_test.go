package runner

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func fileState(path string, data []byte) StateAssertion {
	encoded := base64.StdEncoding.EncodeToString(data)
	return StateAssertion{Path: path, Kind: "file", BytesBase64: &encoded}
}

func TestStateExactBytesAndTypes(t *testing.T) {
	for _, payload := range [][]byte{nil, []byte("a\n"), []byte("a\r\n"), []byte("\x00caf\u00e9\n"), []byte("same length")} {
		t.Run(base64.StdEncoding.EncodeToString(payload), func(t *testing.T) {
			root := t.TempDir()
			path := filepath.Join(root, "saved.bin")
			if err := os.WriteFile(path, payload, 0600); err != nil {
				t.Fatal(err)
			}
			a := fileState("saved.bin", payload)
			if err := assertState(context.Background(), root, a); err != nil {
				t.Fatal(err)
			}
			corrupt := append([]byte(nil), payload...)
			if len(corrupt) > 0 {
				corrupt[len(corrupt)-1] ^= 1
			} else {
				corrupt = []byte{0}
			}
			if err := os.WriteFile(path, corrupt, 0600); err != nil {
				t.Fatal(err)
			}
			if err := assertState(context.Background(), root, a); err == nil || !strings.Contains(err.Error(), "wrong file bytes") {
				t.Fatalf("corruption passed: %v", err)
			}
			if err := os.Remove(path); err != nil {
				t.Fatal(err)
			}
			if err := assertState(context.Background(), root, a); err == nil || !strings.Contains(err.Error(), "missing") {
				t.Fatalf("missing: %v", err)
			}
			if err := os.Mkdir(path, 0700); err != nil {
				t.Fatal(err)
			}
			if err := assertState(context.Background(), root, a); err == nil || !strings.Contains(err.Error(), "wrong path type") {
				t.Fatalf("wrong type: %v", err)
			}
		})
	}
}

func TestStateDirectoriesAbsenceAndBounds(t *testing.T) {
	root := t.TempDir()
	for _, a := range []StateAssertion{{Path: "missing", Kind: "absent"}, {Path: ".", Kind: "directory"}, {Path: ".", Kind: "empty_directory"}} {
		if err := assertState(context.Background(), root, a); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.WriteFile(filepath.Join(root, ".hidden"), []byte("unselected-secret-canary"), 0600); err != nil {
		t.Fatal(err)
	}
	names := []string{".hidden"}
	if err := assertState(context.Background(), root, StateAssertion{Path: ".", Kind: "entries", Entries: &names}); err != nil {
		t.Fatal(err)
	}
	for _, a := range []StateAssertion{{Path: ".", Kind: "empty_directory"}, {Path: ".hidden", Kind: "absent"}, fileState(".hidden", []byte("wrong"))} {
		err := assertState(context.Background(), root, a)
		if err == nil || strings.Contains(err.Error(), "unselected-secret-canary") {
			t.Fatalf("bad or revealing outcome: %v", err)
		}
	}
	if err := os.WriteFile(filepath.Join(root, "large"), make([]byte, maxStateFileBytes+1), 0600); err != nil {
		t.Fatal(err)
	}
	if err := assertState(context.Background(), root, fileState("large", nil)); err == nil || !strings.Contains(err.Error(), "exceeds") {
		t.Fatalf("oversize: %v", err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := assertState(ctx, root, StateAssertion{Path: ".", Kind: "directory"}); err != context.Canceled {
		t.Fatalf("cancellation: %v", err)
	}
}

func TestStatePathValidation(t *testing.T) {
	for _, path := range []string{"", "../escape", "/root", "C:drive", "//server/share", "a\\b", "a/../b", "a/./b", "a//b", "a:", "a\x00b", "CON", "nul.txt", "COM1", "a.", "a ", "a/"} {
		if err := validateStatePath(path, false); err == nil {
			t.Errorf("accepted %q", path)
		}
	}
	for _, path := range []string{"nested/file.bin", "caf\u00e9 space.txt", ".hidden"} {
		if err := validateStatePath(path, false); err != nil {
			t.Errorf("rejected %q: %v", path, err)
		}
	}
}

func TestStateRejectsOwnedLinks(t *testing.T) {
	root := t.TempDir()
	canary := filepath.Join(root, "canary")
	if err := os.Mkdir(canary, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(canary, "secret"), []byte("canary"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.Symlink(canary, filepath.Join(root, "linked")); err != nil {
		t.Skipf("native symlink prerequisite unavailable: %v", err)
	}
	for _, a := range []StateAssertion{{Path: "linked", Kind: "directory"}, fileState("linked/secret", []byte("canary")), {Path: "linked/missing", Kind: "absent"}} {
		if err := assertState(context.Background(), root, a); err == nil {
			t.Fatalf("link accepted: %+v", a)
		}
	}
}

func TestStateSameExecutionCorruptionAndCleanup(t *testing.T) {
	root := t.TempDir()
	if err := os.Mkdir(filepath.Join(root, "fixture"), 0700); err != nil {
		t.Fatal(err)
	}
	spec := validWorkspaceSpec("state-save")
	spec.Version = StateSpecVersion
	a := fileState("saved.bin", []byte("reviewed\r\n\x00caf\u00e9\n"))
	spec.Steps = []Step{{Expect: "Saved successfully"}, {Exit: intPointer(0)}, {State: &a}}
	var ids []string
	for _, corrupt := range []bool{false, true, false} {
		if corrupt {
			spec.Env["PLAYTESTR_CORRUPT_STATE"] = "1"
		} else {
			delete(spec.Env, "PLAYTESTR_CORRUPT_STATE")
		}
		result := RunDetailedContext(context.Background(), writeWorkspaceSpecAt(t, root, spec), RunOptions{Update: true}, io.Discard)
		if corrupt {
			if result.Failure == nil || result.Failure.Category != FailureState || result.Steps[0].Status != "passed" || result.Steps[1].Status != "passed" {
				t.Fatalf("false green or earlier failure: %+v, %v", result, result.Err())
			}
		} else if result.Err() != nil {
			t.Fatal(result.Err())
		}
		if result.Workspace == nil || !result.Workspace.Cleaned || !result.Cleanup.ConfirmedExited {
			t.Fatalf("cleanup incomplete: %+v", result)
		}
		observation := result.Steps[2].State
		if observation == nil || observation.InvocationID == "" || observation.InvocationID != result.InvocationID || observation.WorkspaceID != result.Workspace.ID {
			t.Fatal("same execution identity missing")
		}
		for _, id := range ids {
			if id == result.InvocationID {
				t.Fatal("invocation reused")
			}
		}
		ids = append(ids, result.InvocationID)
		data, _ := json.Marshal(result)
		if strings.Contains(string(data), `reviewed\r\n\u0000caf`) || strings.Contains(string(data), `reviewex\r\n\u0000caf`) || strings.Contains(string(data), *a.BytesBase64) {
			t.Fatal("file contents leaked into report")
		}
	}
}

func TestStateRecorderReviewReplayExport(t *testing.T) {
	r := newHelperRecording(t, "state-save", func(s *Spec) { s.Version = StateSpecVersion; s.Workspace = &WorkspaceSpec{Fixture: "fixture"} })
	capture(t, r, Step{Expect: "Saved successfully"}, Step{Exit: intPointer(0)})
	if err := r.CaptureState("saved.bin", "file"); err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(r.StatePreview(), `\x00`) || !strings.Contains(r.StatePreview(), `\r\n`) {
		t.Fatal("binary preview not escaped")
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
}
