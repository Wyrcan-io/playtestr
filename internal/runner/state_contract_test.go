package runner

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestStateContractLargeManagedCheckpoint(t *testing.T) {
	spec := Spec{Version: 3, Command: []string{"must-not-launch"}, Workspace: &WorkspaceSpec{Fixture: "fixture"}, Steps: []Step{{Expect: "ready"}}}
	for i := 0; i < 527; i++ {
		a := fileState(fmt.Sprintf("tree/file-%03d.txt", i), []byte(fmt.Sprintf("reviewed file %d\n", i)))
		spec.Steps = append(spec.Steps, Step{State: &a})
	}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	parsed, err := decodeSpec(data, "large-checkpoint.json")
	if err != nil {
		t.Fatalf("bounded original large-tree checkpoint rejected: %v", err)
	}
	if len(parsed.Steps) != 528 {
		t.Fatalf("state assertions were dropped: %d steps", len(parsed.Steps))
	}
}

func TestStateLargeSameExecutionCheckpoint(t *testing.T) {
	root := t.TempDir()
	if err := os.Mkdir(filepath.Join(root, "fixture"), 0700); err != nil {
		t.Fatal(err)
	}
	spec := validWorkspaceSpec("state-save-many")
	spec.Version = StateSpecVersion
	spec.TimeoutMS, spec.RunTimeoutMS = 20000, 60000
	spec.Steps = []Step{{Expect: "Saved 527 files successfully"}, {Exit: intPointer(0)}}
	for i := 0; i < 527; i++ {
		a := fileState(fmt.Sprintf("file-%03d.bin", i), []byte(fmt.Sprintf("reviewed file %d\n", i)))
		spec.Steps = append(spec.Steps, Step{State: &a})
	}
	seen := make(map[string]bool)
	for _, corrupt := range []bool{false, true, false} {
		if corrupt {
			spec.Env["PLAYTESTR_CORRUPT_STATE"] = "1"
		} else {
			delete(spec.Env, "PLAYTESTR_CORRUPT_STATE")
		}
		result := RunDetailedContext(context.Background(), writeWorkspaceSpecAt(t, root, spec), RunOptions{}, io.Discard)
		if corrupt {
			if result.Failure == nil || result.Failure.Category != FailureState || result.Steps[len(result.Steps)-1].Status != "failed" {
				t.Fatalf("last-file corruption not detected: %+v %v", result, result.Err())
			}
			for _, step := range result.Steps[:len(result.Steps)-1] {
				if step.Status != "passed" {
					t.Fatalf("earlier checkpoint failed: %+v", step)
				}
			}
		} else if result.Err() != nil {
			t.Fatal(result.Err())
		}
		if result.Workspace == nil || !result.Workspace.Cleaned || !result.Cleanup.ConfirmedExited || result.InvocationID == "" || seen[result.InvocationID] {
			t.Fatalf("large checkpoint identity/cleanup incomplete: %+v", result)
		}
		seen[result.InvocationID] = true
		for _, step := range result.Steps[2:] {
			if step.State == nil || step.State.InvocationID != result.InvocationID || step.State.WorkspaceID != result.Workspace.ID {
				t.Fatal("large checkpoint came from another execution")
			}
		}
	}
}

func TestStateContractRejectsBeforeLaunch(t *testing.T) {
	for _, test := range []struct {
		name   string
		change func(*Spec)
	}{
		{"old-format", func(s *Spec) { s.Version = 2 }},
		{"no-readiness", func(s *Spec) { s.Steps = s.Steps[1:] }},
		{"invalid-base64", func(s *Spec) { v := "?"; s.Steps[1].State.BytesBase64 = &v }},
		{"missing-file-bytes", func(s *Spec) { s.Steps[1].State.BytesBase64 = nil }},
		{"mixed-expectations", func(s *Spec) { entries := []string{}; s.Steps[1].State.Entries = &entries }},
		{"missing-entry-set", func(s *Spec) { s.Steps[1].State = &StateAssertion{Path: ".", Kind: "entries"} }},
		{"unknown-kind", func(s *Spec) { s.Steps[1].State.Kind = "database" }},
		{"too-many-total-steps-with-state", func(s *Spec) {
			for i := 0; i < maxSpecSteps; i++ {
				s.Steps = append(s.Steps, s.Steps[1])
			}
		}},
		{"aggregate-expected-bytes", func(s *Spec) {
			a := fileState("file", make([]byte, maxStateFileBytes))
			s.Steps = []Step{{Expect: "ready"}}
			for i := 0; i < 9; i++ {
				s.Steps = append(s.Steps, Step{State: &a})
			}
		}},
		{"duplicate-entry-name", func(s *Spec) {
			names := []string{"same", "same"}
			s.Steps[1].State = &StateAssertion{Path: ".", Kind: "entries", Entries: &names}
		}},
	} {
		t.Run(test.name, func(t *testing.T) {
			a := fileState("file", nil)
			spec := Spec{Version: 3, Command: []string{"must-not-launch"}, Workspace: &WorkspaceSpec{Fixture: "fixture"}, Steps: []Step{{Expect: "ready"}, {State: &a}}}
			test.change(&spec)
			data, err := json.Marshal(spec)
			if err != nil {
				t.Fatal(err)
			}
			if _, err := decodeSpec(data, "contract.json"); err == nil {
				t.Fatal("invalid contract admitted before launch")
			}
		})
	}
}

func TestStateFileAndDirectoryResourceBoundaries(t *testing.T) {
	root := t.TempDir()
	payload := make([]byte, maxStateFileBytes)
	if err := os.WriteFile(filepath.Join(root, "boundary"), payload, 0600); err != nil {
		t.Fatal(err)
	}
	if err := assertState(context.Background(), root, fileState("boundary", payload)); err != nil {
		t.Fatal(err)
	}
	encoded := base64.StdEncoding.EncodeToString(append(payload, 0))
	if _, err := validateStateAssertion(StateAssertion{Path: "boundary", Kind: "file", BytesBase64: &encoded}); err == nil {
		t.Fatal("oversized expected file accepted")
	}
	directory := filepath.Join(root, "entries")
	if err := os.Mkdir(directory, 0700); err != nil {
		t.Fatal(err)
	}
	names := make([]string, 0, 256)
	for i := 0; i < 256; i++ {
		name := fmt.Sprintf("entry-%03d", i)
		names = append(names, name)
		if err := os.WriteFile(filepath.Join(directory, name), nil, 0600); err != nil {
			t.Fatal(err)
		}
	}
	if err := assertState(context.Background(), root, StateAssertion{Path: "entries", Kind: "entries", Entries: &names}); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(directory, "extra-hidden"), nil, 0600); err != nil {
		t.Fatal(err)
	}
	if err := assertState(context.Background(), root, StateAssertion{Path: "entries", Kind: "entries", Entries: &names}); err == nil || !strings.Contains(err.Error(), "exceeds") {
		t.Fatalf("observed directory entry cap: %v", err)
	}
	if err := validateStatePath(strings.Repeat("a/", 31)+"b", false); err != nil {
		t.Fatal(err)
	}
	if err := validateStatePath(strings.Repeat("a/", 32)+"b", false); err == nil {
		t.Fatal("deep path accepted")
	}
}

func TestStateFailurePreservesSeparateCleanupError(t *testing.T) {
	root := t.TempDir()
	if err := os.Mkdir(filepath.Join(root, "fixture"), 0700); err != nil {
		t.Fatal(err)
	}
	spec := validWorkspaceSpec("workspace-marker-tamper")
	spec.Version = 3
	a := fileState("missing", nil)
	spec.Steps = []Step{{Expect: "workspace ready"}, {State: &a}}
	result := RunDetailedContext(context.Background(), writeWorkspaceSpecAt(t, root, spec), RunOptions{}, io.Discard)
	if result.Failure == nil || result.Failure.Category != FailureState || result.Workspace == nil || result.Workspace.CleanupFailure == nil || !result.Workspace.Retained || !result.Cleanup.ConfirmedExited {
		t.Fatalf("lost primary/separate cleanup outcome: %+v %v", result, result.Err())
	}
	// The known helper only changed its marker; verify the returned owned temp
	// identity and terminated tree before removing this intentional test leak.
	retained := filepath.Clean(result.Workspace.RetainedPath)
	temporaryRoot, err := canonicalWorkspaceRoot(os.TempDir())
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Dir(retained) != filepath.Clean(temporaryRoot) || !strings.HasPrefix(filepath.Base(retained), "playtestr-workspace-") {
		t.Fatal("unexpected retained path")
	}
	if err := os.RemoveAll(retained); err != nil {
		t.Fatal(err)
	}
}
