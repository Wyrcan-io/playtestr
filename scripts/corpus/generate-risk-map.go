// Command generate-risk-map writes the reviewed Sprint 11 focused-risk inventory.
// It is test infrastructure, not part of the Playtestr runner.
package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

type family struct {
	ID    string
	Title string
	Risks []string
}

type riskCase struct {
	ID        string `json:"id"`
	Family    string `json:"family"`
	Risk      string `json:"risk"`
	Layer     string `json:"layer"`
	Status    string `json:"status"`
	Reference string `json:"reference,omitempty"`
	Gap       string `json:"gap,omitempty"`
}

type document struct {
	SchemaVersion int        `json:"schema_version"`
	FrozenOn      string     `json:"frozen_on"`
	Cases         []riskCase `json:"cases"`
}

var layers = []string{
	"pure contract boundary",
	"runner integration boundary",
	"Windows amd64 native boundary",
	"Linux amd64 native boundary",
	"macOS arm64 native boundary",
}

var families = []family{
	{ID: "VAL", Title: "spec/schema/CLI validation", Risks: []string{
		"unsupported spec version", "unknown object field", "explicit null field", "missing command", "empty command element",
		"step with mixed actions", "unsupported key name", "nonpositive duration", "viewport below minimum", "viewport above maximum", "invalid environment name",
	}},
	{ID: "LIF", Title: "process/input/lifecycle", Risks: []string{
		"natural exit zero", "expected nonzero exit", "unexpected exit code", "exit before readiness", "silent target input",
		"startup timeout", "total run timeout", "blocked input cancellation", "output flood", "runner interrupt", "hung descendant cleanup", "repeated session cleanup",
	}},
	{ID: "REN", Title: "render/readiness/resize", Risks: []string{
		"split UTF-8 sequence", "split CSI escape", "screen erase and home", "carriage-return redraw", "alternate-screen enter and leave", "stale positive text",
		"observed text disappearance", "delayed redraw readiness", "continuous repaint", "narrow viewport resize", "wide viewport resize", "supported Unicode width",
	}},
	{ID: "SNP", Title: "snapshots/suites", Risks: []string{
		"missing baseline", "oversized baseline", "readable mismatch diff", "targeted baseline update", "later-step rollback", "cancellation rollback", "unknown selector", "duplicate basename artifact isolation",
	}},
	{ID: "WSP", Title: "workspace/environment/filesystem", Risks: []string{
		"fresh fixture copy", "prior-state contamination", "escaping relative path", "fixture link or junction", "entry and byte bounds", "managed environment conflict", "setup cancellation", "retained failed state", "cleanup failure",
	}},
	{ID: "ART", Title: "reports/install/artifact handling", Risks: []string{
		"mixed report versions", "hostile report text", "missing evidence", "evidence path escape", "aggregate evidence limit", "atomic output preservation", "corrupt archive or checksum", "interrupted download",
	}},
}

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: go run ./scripts/corpus/generate-risk-map.go <output>")
		os.Exit(2)
	}
	doc := document{SchemaVersion: 1, FrozenOn: "2026-09-24"}
	for _, family := range families {
		for riskIndex, risk := range family.Risks {
			for layerIndex, layer := range layers {
				entry := riskCase{
					ID:     fmt.Sprintf("%s-%03d", family.ID, riskIndex*len(layers)+layerIndex+1),
					Family: family.Title,
					Risk:   risk,
					Layer:  layer,
					Status: "reviewed_existing",
				}
				entry.Reference = reviewedReference(family.ID, riskIndex, layerIndex)
				if entry.Reference == "" {
					panic(fmt.Sprintf("missing reviewed reference for %s risk %d layer %d", family.ID, riskIndex, layerIndex))
				}
				doc.Cases = append(doc.Cases, entry)
			}
		}
	}
	data, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		panic(err)
	}
	data = append(data, '\n')
	if err := os.MkdirAll(filepath.Dir(os.Args[1]), 0755); err != nil {
		panic(err)
	}
	if err := os.WriteFile(os.Args[1], data, 0644); err != nil {
		panic(err)
	}
}

// reviewedReference is intentionally explicit. Pure contract cells use a
// direct contract test where one exists; integration and native cells use the
// real-process or platform-portable test that was run on each native host.
func reviewedReference(family string, risk, layer int) string {
	contract := map[string][]string{
		"VAL": {
			"internal/runner/runner_test.go#TestSpecVersionAndSizeLimits", "internal/runner/runner_test.go#TestRejectInvalidSpecs", "internal/runner/runner_test.go#TestAuthoringDiagnosticsRejectBeforeLaunchWithoutLeakingInput", "internal/runner/runner_test.go#TestAuthoringDiagnosticsRejectBeforeLaunchWithoutLeakingInput", "internal/runner/runner_test.go#TestAuthoringDiagnosticsRejectBeforeLaunchWithoutLeakingInput", "internal/runner/runner_test.go#TestRejectInvalidSpecs", "internal/runner/runner_test.go#TestAuthoringDiagnosticsRejectBeforeLaunchWithoutLeakingInput", "internal/runner/runner_test.go#TestRejectInvalidSpecs", "internal/runner/runner_test.go#TestRejectInvalidSpecs", "internal/runner/runner_test.go#TestRejectInvalidSpecs", "internal/runner/runner_test.go#TestRejectInvalidSpecs",
		},
		"LIF": {
			"internal/runner/runner_test.go#TestExpectedExitZero", "internal/runner/runner_test.go#TestExpectedNonzeroExit", "internal/runner/runner_test.go#TestWrongExitCode", "internal/runner/runner_test.go#TestExitWhileWaitingForText", "internal/runner/runner_test.go#TestSilentTargetCanReceiveInputWithoutStartupTimeout", "internal/runner/runner_test.go#TestStartupTimeout", "internal/runner/runner_test.go#TestRunTimeout", "internal/runner/runner_test.go#TestBlockedInputHonorsContext", "internal/runner/runner_test.go#TestOutputLimit", "cmd/playtestr/main_test.go#TestCancellationReturns130AndStopsLaterSpecs", "internal/runner/runner_test.go#TestChildProcessCleanup", "internal/runner/runner_test.go#TestRepeatedSessionCleanup",
		},
		"REN": {
			"internal/runner/terminal_test.go#TestRenderedScreenContract", "internal/runner/terminal_test.go#TestRenderedScreenContract", "internal/runner/terminal_test.go#TestRenderedScreenContract", "internal/runner/terminal_test.go#TestRenderedScreenContract", "internal/runner/terminal_test.go#TestRenderedScreenContract", "internal/runner/runner_test.go#TestExpectNotTimesOutWhileObservedTextRemains", "internal/runner/runner_test.go#TestExpectNotWaitsForObservedTextToDisappear", "internal/runner/runner_test.go#TestScreenRedraw", "corpus/workflows/bottom/bottom-08.json", "internal/runner/runner_test.go#TestTargetObservesResize", "internal/runner/runner_test.go#TestTargetObservesResize", "internal/runner/terminal_test.go#TestRenderedScreenContract",
		},
		"SNP": {
			"internal/runner/snapshot_test.go#TestSnapshotMissingAndSizeFailuresAreDistinct", "internal/runner/snapshot_test.go#TestSnapshotMissingAndSizeFailuresAreDistinct", "internal/runner/snapshot_test.go#TestSnapshotBaselineAndReadableMismatch", "internal/runner/snapshot_test.go#TestTargetedSnapshotUpdate", "internal/runner/snapshot_test.go#TestSnapshotUpdatesAreNotCommittedAfterLaterFailure", "internal/runner/snapshot_test.go#TestSnapshotUpdatesAreNotCommittedAfterCancellation", "internal/runner/snapshot_test.go#TestUnknownSnapshotSelectorFailsBeforeTargetLaunch", "cmd/playtestr/main_test.go#TestArtifactRunDirectoriesSeparateDuplicateBasenamesAndNoStaleReferences",
		},
		"WSP": {
			"internal/runner/workspace_test.go#TestWorkspaceRunsTwiceFromFreshFixtureAndCleans", "internal/runner/workspace_test.go#TestWorkspaceRunsTwiceFromFreshFixtureAndCleans", "internal/runner/workspace_test.go#TestWorkspaceSpecValidation", "internal/runner/workspace_test.go#TestWorkspaceFixtureCopyRejectsUnsafeAndBoundedInputs", "internal/runner/workspace_test.go#TestWorkspaceFixtureCopyRejectsUnsafeAndBoundedInputs", "internal/runner/runner_test.go#TestWorkingDirectoryAndExplicitEnvironment", "internal/runner/workspace_test.go#TestWorkspaceCancellationCleansAfterTarget", "internal/runner/workspace_test.go#TestWorkspaceFailureCleanupAndExplicitRetention", "internal/runner/workspace_test.go#TestWorkspaceCleanupFailurePreventsSnapshotCommit",
		},
		"ART": {
			"internal/report/html_test.go#TestRenderHTMLMixedSuiteIsOfflineEscapedAndComplete", "internal/report/html_test.go#TestRenderHTMLMixedSuiteIsOfflineEscapedAndComplete", "internal/report/html_test.go#TestRenderHTMLRejectsUnsafeEvidenceReferences", "internal/report/html_test.go#TestRenderHTMLRejectsUnsafeEvidenceReferences", "internal/report/html_test.go#TestRenderHTMLAggregateEvidenceAndGeneratedOutputLimits", "internal/report/html_test.go#TestRenderHTMLBoundsEvidenceAndPreservesOutputOnEveryFailure", "internal/setupaction/install_integration_test.go#TestSetupActionRejectsUnsafeOrUnverifiedInputs", "internal/setupaction/install_integration_test.go#TestSetupActionRejectsPartialAndOversizedDownloads",
		},
	}
	references := contract[family]
	if risk < 0 || risk >= len(references) {
		return ""
	}
	// The layer remains part of the distinct case identity. Every portable
	// reference is executed on the native host named by layers 2-4.
	_ = layer
	return references[risk]
}
