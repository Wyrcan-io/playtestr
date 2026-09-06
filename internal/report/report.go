// Package report writes the versioned Playtestr machine report.
package report

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	"github.com/Wyrcan-io/playtestr/internal/runner"
)

const (
	// Version is the current machine-report contract.
	Version        = 1
	maxReportBytes = 8 * 1024 * 1024
)

// Summary counts every requested spec, including specs skipped after cancellation.
type Summary struct {
	Total     int `json:"total"`
	Passed    int `json:"passed"`
	Failed    int `json:"failed"`
	Cancelled int `json:"cancelled"`
	NotRun    int `json:"not_run"`
}

// Document is the top-level JSON report contract.
type Document struct {
	ReportVersion int                `json:"report_version"`
	RunnerVersion string             `json:"runner_version"`
	OS            string             `json:"os"`
	Arch          string             `json:"arch"`
	Summary       Summary            `json:"summary"`
	Results       []runner.RunResult `json:"results"`
}

// New creates a report while preserving the caller's spec order.
func New(runnerVersion string, results []runner.RunResult) Document {
	document := Document{
		ReportVersion: Version,
		RunnerVersion: runnerVersion,
		OS:            runtime.GOOS,
		Arch:          runtime.GOARCH,
		Results:       results,
	}
	document.Summary.Total = len(results)
	for _, result := range results {
		switch result.Status {
		case "passed":
			document.Summary.Passed++
		case "cancelled":
			document.Summary.Cancelled++
		case "not_run":
			document.Summary.NotRun++
		default:
			document.Summary.Failed++
		}
	}
	return document
}

// Write atomically replaces path with a bounded, indented JSON document.
func Write(path string, document Document) (returnErr error) {
	var data bytes.Buffer
	encoder := json.NewEncoder(&data)
	encoder.SetIndent("", "  ")
	encoder.SetEscapeHTML(false)
	if err := encoder.Encode(document); err != nil {
		return fmt.Errorf("encode report: %w", err)
	}
	if data.Len() > maxReportBytes {
		return fmt.Errorf("report exceeds %d bytes", maxReportBytes)
	}
	directory := filepath.Dir(path)
	if err := os.MkdirAll(directory, 0755); err != nil {
		return fmt.Errorf("create report directory: %w", err)
	}
	temporary, err := os.CreateTemp(directory, ".playtestr-report-*")
	if err != nil {
		return fmt.Errorf("create temporary report: %w", err)
	}
	temporaryPath := temporary.Name()
	defer func() {
		_ = temporary.Close()
		_ = os.Remove(temporaryPath)
	}()
	if err := temporary.Chmod(0644); err != nil {
		return fmt.Errorf("set report permissions: %w", err)
	}
	if _, err := temporary.Write(data.Bytes()); err != nil {
		return fmt.Errorf("write temporary report: %w", err)
	}
	if err := temporary.Sync(); err != nil {
		return fmt.Errorf("sync temporary report: %w", err)
	}
	if err := temporary.Close(); err != nil {
		return fmt.Errorf("close temporary report: %w", err)
	}
	if err := os.Rename(temporaryPath, path); err != nil {
		return fmt.Errorf("replace report %s: %w", path, err)
	}
	return nil
}
