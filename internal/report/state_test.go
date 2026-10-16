package report

import (
	"encoding/json"
	"strings"
	"testing"

	"github.com/Wyrcan-io/playtestr/internal/runner"
)

func TestStateReportVersionAndIdentityValidation(t *testing.T) {
	result := runner.RunResult{SpecVersion: 3, SpecPath: "state.json", Status: "passed", InvocationID: "execution-a", Workspace: &runner.WorkspaceReport{ID: "execution-a"}, Steps: []runner.StepResult{{Number: 1, Action: "state", Status: "passed", State: &runner.StateObservation{InvocationID: "execution-a", WorkspaceID: "execution-a", Path: "saved.bin", Kind: "file", Outcome: "matched"}}}}
	document := New("development", []runner.RunResult{{SpecVersion: 2, SpecPath: "older.json", Status: "passed"}, result})
	if document.ReportVersion != 3 {
		t.Fatal("mixed suite downgraded state report")
	}
	if err := validateHTMLDocument(document); err != nil {
		t.Fatal(err)
	}
	for _, change := range []func(*Document){
		func(d *Document) { d.ReportVersion = 2 },
		func(d *Document) { d.Results[1].Steps[0].State.InvocationID = "other-execution" },
		func(d *Document) { d.Results[1].Steps[0].State.WorkspaceID = "other-workspace" },
		func(d *Document) { d.Results[1].Steps[0].State = nil },
		func(d *Document) { d.Results[1].Steps[0].State.Outcome = "rejected" },
	} {
		data, _ := json.Marshal(document)
		var copy Document
		json.Unmarshal(data, &copy)
		change(&copy)
		if err := validateHTMLDocument(copy); err == nil {
			t.Fatal("tampered state proof accepted")
		}
	}
	data, _ := json.Marshal(document)
	if strings.Contains(string(data), "bytes_base64") {
		t.Fatal("payload appeared in machine report")
	}
}
