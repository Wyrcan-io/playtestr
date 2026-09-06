package report

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/Wyrcan-io/playtestr/internal/runner"
)

func TestReportSummaryOrderAndSecretBoundary(t *testing.T) {
	results := []runner.RunResult{
		{Name: "pass", SpecPath: "one.json", Status: "passed"},
		{Name: "fail", SpecPath: "two.json", Status: "failed", Failure: &runner.Failure{Category: runner.FailureUnexpectedExit, Message: "exit 7"}},
		{Name: "later", SpecPath: "three.json", Status: "not_run"},
	}
	document := New("v0.1.0-rc.1", results)
	if document.Summary.Total != 3 || document.Summary.Passed != 1 || document.Summary.Failed != 1 || document.Summary.NotRun != 1 {
		t.Fatalf("summary = %+v", document.Summary)
	}
	path := filepath.Join(t.TempDir(), "nested", "results.json")
	if err := Write(path, document); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(data), "command") || strings.Contains(string(data), "environment") || strings.Contains(string(data), "input_text") {
		t.Fatalf("report crossed secret boundary: %s", data)
	}
	var decoded Document
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded.ReportVersion != 1 || decoded.RunnerVersion != "v0.1.0-rc.1" || decoded.Results[1].Name != "fail" {
		t.Fatalf("decoded report = %+v", decoded)
	}
}
