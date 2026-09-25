package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestReportMetrics(t *testing.T) {
	steps := []struct {
		Action     string `json:"action"`
		DurationMS int64  `json:"duration_ms"`
	}{
		{Action: "expect", DurationMS: 40},
		{Action: "wait_for_redraw", DurationMS: 1000},
		{Action: "wait", DurationMS: 250},
		{Action: "exit", DurationMS: 10},
	}
	reportMS, startupMS, waitMS, overheadMS := reportMetrics(1400, steps, 1450)
	if reportMS != 1400 || startupMS != 40 || waitMS != 1250 || overheadMS != 50 {
		t.Fatalf("metrics = (%d, %d, %d, %d)", reportMS, startupMS, waitMS, overheadMS)
	}
}

func TestReportMetricsClampsNegativeOverhead(t *testing.T) {
	_, _, _, overheadMS := reportMetrics(20, nil, 10)
	if overheadMS != 0 {
		t.Fatalf("overhead = %d, want 0", overheadMS)
	}
}

func TestAttemptPhase(t *testing.T) {
	if got := attemptPhase(1); got != "cold_first_attempt" {
		t.Fatalf("attemptPhase(1) = %q", got)
	}
	if got := attemptPhase(2); got != "warm_fresh_process" {
		t.Fatalf("attemptPhase(2) = %q", got)
	}
}

func TestCopyEvidence(t *testing.T) {
	directory := t.TempDir()
	source := filepath.Join(directory, "source.txt")
	destination := filepath.Join(directory, "destination.txt")
	const content = "rendered failure evidence\n"
	if err := os.WriteFile(source, []byte(content), 0o600); err != nil {
		t.Fatal(err)
	}

	size, err := copyEvidence(source, destination)
	if err != nil {
		t.Fatal(err)
	}
	if size != int64(len(content)) {
		t.Fatalf("size = %d, want %d", size, len(content))
	}
	data, err := os.ReadFile(destination)
	if err != nil {
		t.Fatal(err)
	}
	if string(data) != content {
		t.Fatalf("content = %q", data)
	}
}

func TestQualificationInputsRemainPortable(t *testing.T) {
	repositoryRoot := filepath.Join("..", "..")
	read := func(path string) string {
		t.Helper()
		data, err := os.ReadFile(filepath.Join(repositoryRoot, filepath.FromSlash(path)))
		if err != nil {
			t.Fatal(err)
		}
		return string(data)
	}

	setup := read("scripts/qualification/setup-targets.sh")
	if strings.Contains(setup, "sha256sum --check") || strings.Contains(setup, "sha256sum -c") ||
		!strings.Contains(setup, `test "$(sha256sum "$runtime/$tarball" | awk '{print $1}')"`) {
		t.Fatal("target setup must compare the extracted sha256sum value without GNU check-mode input")
	}

	workflow := read(".github/workflows/qualification.yml")
	if strings.Contains(workflow, "cp candidate/candidate-evidence-*.json") ||
		!strings.Contains(workflow, "find candidate -name 'candidate-evidence-*.json'") {
		t.Fatal("qualification evidence copy must handle the downloaded artifact subdirectory")
	}

	var spec struct {
		Steps []map[string]any `json:"steps"`
	}
	if err := json.Unmarshal([]byte(read("corpus/workflows/micro/micro-05.json")), &spec); err != nil {
		t.Fatal(err)
	}
	for _, step := range spec.Steps {
		if step["expect"] == "draft xalpha marker" {
			t.Fatal("cancellation proof must not depend on the post-dismiss cursor position")
		}
	}

	var resizeSpec struct {
		Steps []map[string]any `json:"steps"`
	}
	if err := json.Unmarshal([]byte(read("corpus/workflows/mitmproxy/mitm-07.json")), &resizeSpec); err != nil {
		t.Fatal(err)
	}
	seenResize := false
	for _, step := range resizeSpec.Steps {
		if _, ok := step["resize"]; ok {
			seenResize = true
		}
		if seenResize && step["expect"] == "Key Bindings" {
			t.Fatal("narrow mitmproxy help assertion must use text retained by the responsive layout")
		}
	}
}
