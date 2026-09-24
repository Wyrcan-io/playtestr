// Command qualification-campaign executes the frozen R6 repeat plan and writes
// one append-only JSON record for every first attempt. It is release tooling,
// not part of the Playtestr product contract.
package main

import (
	"bufio"
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

type plan struct {
	SchemaVersion int `json:"schema_version"`
	Attempts      int `json:"attempts_per_workflow_host"`
	Workflows     []struct {
		ID      string `json:"id"`
		Project string `json:"project"`
		Spec    string `json:"spec"`
		Class   string `json:"class"`
	} `json:"workflows"`
}

type report struct {
	Summary struct {
		Total, Passed, Failed, Cancelled, NotRun int
	} `json:"summary"`
	Results []struct {
		Status     string `json:"status"`
		DurationMS int64  `json:"duration_ms"`
		Steps      []struct {
			Action     string `json:"action"`
			DurationMS int64  `json:"duration_ms"`
		} `json:"steps"`
		Failure *struct {
			Category string `json:"category"`
		} `json:"failure"`
		Cleanup struct {
			ConfirmedExited bool `json:"confirmed_exited"`
		} `json:"cleanup"`
		Workspace *struct {
			CleanupAttempted bool `json:"cleanup_attempted"`
			Cleaned          bool `json:"cleaned"`
			Retained         bool `json:"retained"`
		} `json:"workspace"`
		Evidence struct {
			ScreenPath string `json:"screen_path"`
		} `json:"evidence"`
	} `json:"results"`
}

type attemptRecord struct {
	SchemaVersion     int      `json:"schema_version"`
	AttemptID         string   `json:"attempt_id"`
	Host              string   `json:"host"`
	WorkflowID        string   `json:"workflow_id"`
	Project           string   `json:"project"`
	Class             string   `json:"class"`
	Ordinal           int      `json:"ordinal"`
	StartedUTC        string   `json:"started_utc"`
	Phase             string   `json:"phase"`
	TotalWallMS       int64    `json:"total_wall_ms"`
	ReportMS          int64    `json:"report_ms,omitempty"`
	TargetStartupMS   int64    `json:"target_startup_ms,omitempty"`
	IntentionalWaitMS int64    `json:"intentional_wait_ms,omitempty"`
	RunnerOverheadMS  int64    `json:"runner_overhead_ms,omitempty"`
	RunnerCPUUserMS   int64    `json:"runner_cpu_user_ms,omitempty"`
	RunnerCPUSystemMS int64    `json:"runner_cpu_system_ms,omitempty"`
	ArtifactBytes     int64    `json:"artifact_bytes,omitempty"`
	RunnerSHA256      string   `json:"runner_sha256"`
	SpecSHA256        string   `json:"spec_sha256"`
	TargetSHA256      []string `json:"target_sha256"`
	ExitCode          int      `json:"exit_code"`
	RunnerStatus      string   `json:"runner_status"`
	FailureCategory   string   `json:"failure_category,omitempty"`
	Cleanup           string   `json:"cleanup"`
	SurvivorCheck     string   `json:"survivor_check"`
	AssertionOutcome  string   `json:"assertion_oracle_outcome"`
	Disposition       string   `json:"disposition"`
	Report            string   `json:"report,omitempty"`
}

type stringsFlag []string

func (s *stringsFlag) String() string { return strings.Join(*s, ",") }
func (s *stringsFlag) Set(value string) error {
	*s = append(*s, value)
	return nil
}

func main() {
	var targets stringsFlag
	runner := flag.String("runner", "", "path to extracted frozen Playtestr executable")
	planPath := flag.String("plan", "release/qualification-plan.json", "qualification plan")
	out := flag.String("out", "artifacts/qualification", "evidence directory")
	attemptsOverride := flag.Int("attempts", 0, "attempt count override for preflight only")
	flag.Var(&targets, "target", "target or oracle file whose SHA-256 is recorded (repeatable)")
	flag.Parse()
	if *runner == "" || len(targets) == 0 {
		fatal(errors.New("-runner and at least one -target are required"))
	}

	p := readPlan(*planPath)
	attempts := p.Attempts
	if *attemptsOverride > 0 {
		attempts = *attemptsOverride
	}
	if attempts < 1 || len(p.Workflows) != 10 {
		fatal(fmt.Errorf("invalid campaign dimensions: workflows=%d attempts=%d", len(p.Workflows), attempts))
	}
	if err := os.MkdirAll(*out, 0o755); err != nil {
		fatal(err)
	}
	runnerHash := mustHash(*runner)
	targetHashes := make([]string, 0, len(targets))
	for _, target := range targets {
		targetHashes = append(targetHashes, filepath.ToSlash(target)+":"+mustHash(target))
	}

	ledgerPath := filepath.Join(*out, "attempts.jsonl")
	ledger, err := os.OpenFile(ledgerPath, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0o600)
	if err != nil {
		fatal(err)
	}
	defer ledger.Close()
	writer := bufio.NewWriter(ledger)
	defer writer.Flush()

	host := runtime.GOOS + "_" + runtime.GOARCH
	completed := 0
	for _, workflow := range p.Workflows {
		for ordinal := 1; ordinal <= attempts; ordinal++ {
			started := time.Now().UTC()
			reportPath := filepath.Join(*out, fmt.Sprintf("%s-%03d.json", strings.ToLower(workflow.ID), ordinal))
			ctx, cancel := context.WithTimeout(context.Background(), 45*time.Second)
			command := exec.CommandContext(ctx, *runner, "test", "--report", reportPath, workflow.Spec)
			output, runErr := command.CombinedOutput()
			cancel()
			exitCode := 0
			if runErr != nil {
				exitCode = -1
				var exitErr *exec.ExitError
				if errors.As(runErr, &exitErr) {
					exitCode = exitErr.ExitCode()
				}
			}
			record := attemptRecord{
				SchemaVersion: 2, AttemptID: fmt.Sprintf("%s-%03d", workflow.ID, ordinal), Host: host,
				WorkflowID: workflow.ID, Project: workflow.Project, Class: workflow.Class, Ordinal: ordinal,
				StartedUTC: started.Format(time.RFC3339Nano), Phase: attemptPhase(ordinal), TotalWallMS: time.Since(started).Milliseconds(),
				RunnerSHA256: runnerHash, SpecSHA256: mustHash(workflow.Spec), TargetSHA256: targetHashes,
				ExitCode: exitCode, Disposition: "unexpected_failure", Report: filepath.ToSlash(reportPath),
				SurvivorCheck: "not_confirmed", AssertionOutcome: "failed",
			}
			if command.ProcessState != nil {
				record.RunnerCPUUserMS = command.ProcessState.UserTime().Milliseconds()
				record.RunnerCPUSystemMS = command.ProcessState.SystemTime().Milliseconds()
			}
			if info, statErr := os.Stat(reportPath); statErr == nil {
				record.ArtifactBytes = info.Size()
			}
			var parsed report
			if data, readErr := os.ReadFile(reportPath); readErr == nil && json.Unmarshal(data, &parsed) == nil && len(parsed.Results) == 1 {
				result := parsed.Results[0]
				record.ReportMS, record.TargetStartupMS, record.IntentionalWaitMS, record.RunnerOverheadMS = reportMetrics(result.DurationMS, result.Steps, record.TotalWallMS)
				record.RunnerStatus = result.Status
				if result.Failure != nil {
					record.FailureCategory = result.Failure.Category
				}
				record.Cleanup = "confirmed_exited"
				if !result.Cleanup.ConfirmedExited {
					record.Cleanup = "not_confirmed"
				} else {
					record.SurvivorCheck = "confirmed_exited"
				}
				if result.Workspace != nil {
					record.Cleanup += fmt.Sprintf(";workspace_cleaned=%t;workspace_retained=%t", result.Workspace.Cleaned, result.Workspace.Retained)
				}
				if exitCode == 0 && parsed.Summary.Total == 1 && parsed.Summary.Passed == 1 && result.Status == "passed" && result.Cleanup.ConfirmedExited && (result.Workspace == nil || result.Workspace.Cleaned) {
					record.Disposition = "pass"
					record.AssertionOutcome = "passed"
				}
				if record.Disposition != "pass" && result.Evidence.ScreenPath != "" {
					if copied, copyErr := copyEvidence(result.Evidence.ScreenPath, filepath.Join(*out, record.AttemptID+".actual.txt")); copyErr == nil {
						record.ArtifactBytes += copied
					}
				}
			}
			if record.Disposition == "pass" && ordinal != 1 {
				if err := os.Remove(reportPath); err != nil {
					record.Disposition = "evidence_cleanup_failure"
				}
			}
			if err := json.NewEncoder(writer).Encode(record); err != nil {
				fatal(err)
			}
			if err := writer.Flush(); err != nil {
				fatal(err)
			}
			completed++
			if record.Disposition != "pass" {
				_ = os.WriteFile(filepath.Join(*out, record.AttemptID+".log"), output, 0o600)
				fatal(fmt.Errorf("%s: %s (exit %d)", record.AttemptID, record.Disposition, exitCode))
			}
		}
	}
	if finalHash := mustHash(*runner); finalHash != runnerHash {
		fatal(fmt.Errorf("runner changed during campaign: %s -> %s", runnerHash, finalHash))
	}
	summary := map[string]any{
		"schema_version": 2, "status": "passed", "host": host, "runner_sha256": runnerHash,
		"workflow_count": len(p.Workflows), "attempts_per_workflow": attempts, "attempt_count": completed,
		"first_attempt_failures": 0, "managed_cleanup_failures": 0, "completed_utc": time.Now().UTC().Format(time.RFC3339Nano),
	}
	writeJSON(filepath.Join(*out, "summary.json"), summary)
}

func attemptPhase(ordinal int) string {
	if ordinal == 1 {
		return "cold_first_attempt"
	}
	return "warm_fresh_process"
}

func reportMetrics(reportMS int64, steps []struct {
	Action     string `json:"action"`
	DurationMS int64  `json:"duration_ms"`
}, wallMS int64) (int64, int64, int64, int64) {
	var startupMS, waitMS int64
	if len(steps) > 0 {
		startupMS = steps[0].DurationMS
	}
	for _, step := range steps {
		if step.Action == "wait" || step.Action == "wait_for_redraw" {
			waitMS += step.DurationMS
		}
	}
	overheadMS := wallMS - reportMS
	if overheadMS < 0 {
		overheadMS = 0
	}
	return reportMS, startupMS, waitMS, overheadMS
}

func copyEvidence(source, destination string) (int64, error) {
	data, err := os.ReadFile(source)
	if err != nil {
		return 0, err
	}
	if err := os.WriteFile(destination, data, 0o600); err != nil {
		return 0, err
	}
	return int64(len(data)), nil
}

func readPlan(path string) plan {
	data, err := os.ReadFile(path)
	if err != nil {
		fatal(err)
	}
	var result plan
	if err := json.Unmarshal(data, &result); err != nil {
		fatal(err)
	}
	return result
}

func mustHash(path string) string {
	file, err := os.Open(path)
	if err != nil {
		fatal(err)
	}
	defer file.Close()
	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		fatal(err)
	}
	return hex.EncodeToString(hash.Sum(nil))
}

func writeJSON(path string, value any) {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		fatal(err)
	}
	data = append(data, '\n')
	if err := os.WriteFile(path, data, 0o600); err != nil {
		fatal(err)
	}
}

func fatal(err error) {
	fmt.Fprintln(os.Stderr, "qualification-campaign:", err)
	os.Exit(1)
}
