package main

import (
	"os"
	"path/filepath"
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
