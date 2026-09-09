package runner

import (
	"errors"
	"fmt"
)

// FailureCategory is a stable machine-readable reason for a failed run.
type FailureCategory string

const (
	FailureInvalidSpec      FailureCategory = "invalid_spec"
	FailureLaunch           FailureCategory = "launch_failure"
	FailureAssertionTimeout FailureCategory = "assertion_timeout"
	FailureRunTimeout       FailureCategory = "run_timeout"
	FailureUnexpectedExit   FailureCategory = "unexpected_exit"
	FailureSnapshotMismatch FailureCategory = "snapshot_mismatch"
	FailureOutputLimit      FailureCategory = "output_limit"
	FailureCancellation     FailureCategory = "cancelled"
	FailureCleanup          FailureCategory = "cleanup_failure"
	FailureArtifact         FailureCategory = "artifact_failure"
	FailureSnapshotUpdate   FailureCategory = "snapshot_update_failure"
	FailureInternal         FailureCategory = "internal_error"
)

// Failure describes one failure without requiring consumers to parse prose.
type Failure struct {
	Category FailureCategory `json:"category"`
	Message  string          `json:"message"`
}

// StepResult records the outcome of one declared step. Input and expected text
// are deliberately omitted so reports cannot become a new secret sink.
type StepResult struct {
	Number     int           `json:"number"`
	Action     string        `json:"action"`
	Status     string        `json:"status"`
	DurationMS int64         `json:"duration_ms"`
	Failure    *Failure      `json:"failure,omitempty"`
	Resize     *TerminalSize `json:"resize,omitempty"`
}

// CleanupReport keeps cleanup evidence separate from the failure that caused it.
type CleanupReport struct {
	Attempted       bool     `json:"attempted"`
	Graceful        bool     `json:"graceful"`
	Forced          bool     `json:"forced"`
	ConfirmedExited bool     `json:"confirmed_exited"`
	Mechanism       string   `json:"mechanism,omitempty"`
	Failure         *Failure `json:"failure,omitempty"`
}

// TargetReport records the final target outcome when it is known.
type TargetReport struct {
	Exited   bool `json:"exited"`
	ExitCode *int `json:"exit_code,omitempty"`
}

// EvidenceReport points to bounded local evidence files.
type EvidenceReport struct {
	ScreenPath string    `json:"screen_path,omitempty"`
	DiffPath   string    `json:"diff_path,omitempty"`
	Failures   []Failure `json:"failures,omitempty"`
}

// RunResult is the structured outcome for one test specification.
type RunResult struct {
	SpecVersion int            `json:"spec_version,omitempty"`
	Name        string         `json:"name"`
	SpecPath    string         `json:"spec_path"`
	Status      string         `json:"status"`
	DurationMS  int64          `json:"duration_ms"`
	Viewport    TerminalSize   `json:"viewport"`
	Resizes     []TerminalSize `json:"resizes,omitempty"`
	Steps       []StepResult   `json:"steps,omitempty"`
	Target      TargetReport   `json:"target"`
	Failure     *Failure       `json:"failure,omitempty"`
	Cleanup     CleanupReport  `json:"cleanup"`
	Evidence    EvidenceReport `json:"evidence"`
	err         error
}

// Err returns the full Go error chain for programmatic callers.
func (r RunResult) Err() error { return r.err }

func failure(category FailureCategory, err error) *Failure {
	if err == nil {
		return nil
	}
	message := err.Error()
	switch category {
	case FailureInvalidSpec:
		message = "test specification is invalid"
	case FailureLaunch:
		message = "target could not be started"
	case FailureSnapshotMismatch:
		message = "rendered screen did not match the reviewed snapshot"
	}
	return &Failure{Category: category, Message: message}
}

type categorizedError struct {
	category FailureCategory
	err      error
}

func (e *categorizedError) Error() string { return e.err.Error() }
func (e *categorizedError) Unwrap() error { return e.err }

func withCategory(category FailureCategory, err error) error {
	if err == nil {
		return nil
	}
	return &categorizedError{category: category, err: err}
}

func categoryOf(err error) FailureCategory {
	var categorized *categorizedError
	if errors.As(err, &categorized) {
		return categorized.category
	}
	return FailureInternal
}

type unexpectedExitError struct {
	message string
}

func (e *unexpectedExitError) Error() string { return e.message }

func unexpectedExit(format string, args ...any) error {
	return &unexpectedExitError{message: fmt.Sprintf(format, args...)}
}

func stepAction(step Step) string {
	switch {
	case step.Key != "":
		return "key"
	case step.Text != "":
		return "text"
	case step.Expect != "":
		return "expect"
	case step.ExpectNot != "":
		return "expect_not"
	case step.WaitForRedraw:
		return "wait_for_redraw"
	case step.Snapshot != "":
		return "snapshot"
	case step.Exit != nil:
		return "exit"
	case step.Resize != nil:
		return "resize"
	default:
		return "invalid"
	}
}
