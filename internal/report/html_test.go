package report

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"

	"github.com/Wyrcan-io/playtestr/internal/runner"
)

func TestRenderHTMLMixedSuiteIsOfflineEscapedAndComplete(t *testing.T) {
	working := t.TempDir()
	root := filepath.Join(working, "artifacts")
	if err := os.MkdirAll(filepath.Join(root, "run"), 0755); err != nil {
		t.Fatal(err)
	}
	screenReference := filepath.ToSlash(filepath.Join("artifacts", "run", "snapshot.actual.txt"))
	diffReference := filepath.ToSlash(filepath.Join("artifacts", "run", "snapshot.diff.txt"))
	hostile := "terminal <script>alert(1)</script>\n\x1b]8;;https://evil.invalid\aoutside\x1b]8;;\a\n雪🙂"
	diff := "--- expected: screen.txt\n+++ actual: screen.txt\n@@ -1,1 +1,1 @@\n-<expected>\n+<script>wrong()</script>\n"
	writeTestFile(t, filepath.Join(working, filepath.FromSlash(screenReference)), []byte(hostile))
	writeTestFile(t, filepath.Join(working, filepath.FromSlash(diffReference)), []byte(diff))
	exitCode := 7
	document := Document{
		ReportVersion: 1, RunnerVersion: "v0.2.0-rc.1", OS: "test-os", Arch: "test-arch",
		Summary: Summary{Total: 5, Passed: 1, Failed: 2, Cancelled: 1, NotRun: 1},
		Results: []runner.RunResult{
			{
				SpecVersion: 1, Name: "duplicate <name>", SpecPath: "tests/one.json", Status: "failed", DurationMS: 21,
				Viewport: runner.TerminalSize{Width: 80, Height: 24},
				Steps:    []runner.StepResult{{Number: 1, Action: "expect", Status: "passed"}, {Number: 2, Action: "snapshot", Status: "failed", Failure: &runner.Failure{Category: runner.FailureSnapshotMismatch, Message: "captured mismatch"}}},
				Target:   runner.TargetReport{Exited: true, ExitCode: &exitCode},
				Failure:  &runner.Failure{Category: runner.FailureSnapshotMismatch, Message: "screen <b>did not match</b>"},
				Cleanup:  runner.CleanupReport{Attempted: true, Forced: true, ConfirmedExited: true, Mechanism: "test tree", Failure: &runner.Failure{Category: runner.FailureCleanup, Message: "recorded cleanup warning"}},
				Evidence: runner.EvidenceReport{ScreenPath: screenReference, DiffPath: diffReference},
			},
			{
				SpecVersion: 1, Name: "duplicate <name>", SpecPath: "tests/two.json", Status: "failed", Viewport: runner.TerminalSize{Width: 100, Height: 30},
				Steps:    []runner.StepResult{{Number: 1, Action: "expect", Status: "failed", Failure: &runner.Failure{Category: runner.FailureAssertionTimeout, Message: "timed out"}}},
				Failure:  &runner.Failure{Category: runner.FailureAssertionTimeout, Message: "timed out"},
				Cleanup:  runner.CleanupReport{Attempted: true, Graceful: true, ConfirmedExited: true},
				Evidence: runner.EvidenceReport{ScreenPath: filepath.ToSlash(filepath.Join("artifacts", "run", "missing.actual.txt"))},
			},
			{SpecVersion: 1, Name: "pass", SpecPath: "tests/pass.json", Status: "passed", Viewport: runner.TerminalSize{Width: 80, Height: 24}, Cleanup: runner.CleanupReport{}, Evidence: runner.EvidenceReport{}},
			{SpecVersion: 1, Name: "cancelled", SpecPath: "tests/cancelled.json", Status: "cancelled", Viewport: runner.TerminalSize{Width: 80, Height: 24}, Failure: &runner.Failure{Category: runner.FailureCancellation, Message: "cancelled"}, Cleanup: runner.CleanupReport{Attempted: true}, Evidence: runner.EvidenceReport{Failures: []runner.Failure{{Category: runner.FailureArtifact, Message: "screen write failed"}}}},
			{Name: "later", SpecPath: "tests/later.json", Status: "not_run", Cleanup: runner.CleanupReport{}, Evidence: runner.EvidenceReport{}},
		},
	}
	input := filepath.Join(root, "results.json")
	writeDocument(t, input, document)
	output := filepath.Join(working, "portable report.html")
	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: output, WorkingDirectory: working}); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(output)
	if err != nil {
		t.Fatal(err)
	}
	html := string(data)
	for _, wanted := range []string{
		"Run diagnosis", "tests/one.json", "tests/two.json", "First failing step", "snapshot_mismatch",
		"Expected expression:</b> unavailable in report v1", "Screen evidence is referenced but the file is missing",
		"Exit confirmed: true", "recorded cleanup warning", "screen write failed", "cancelled", "tests/later.json", "雪🙂", "Readable evidence is embedded, not cryptographically verified",
	} {
		if !strings.Contains(html, wanted) {
			t.Errorf("HTML does not contain %q", wanted)
		}
	}
	for _, forbidden := range []string{"<script>", "href=\"https://evil.invalid", "src=", "http-equiv=\"refresh\""} {
		if strings.Contains(html, forbidden) {
			t.Errorf("HTML contains unsafe external/active content %q", forbidden)
		}
	}
	if !strings.Contains(html, "&lt;script&gt;alert(1)&lt;/script&gt;") || !strings.Contains(html, "&lt;script&gt;wrong()&lt;/script&gt;") {
		t.Error("hostile screen or diff text was not HTML escaped")
	}
	if strings.Index(html, "tests/one.json") > strings.Index(html, "tests/two.json") || strings.Count(html, "duplicate &lt;name&gt;") < 2 {
		t.Error("failures are not stable and distinguishable by spec identity")
	}
	if !strings.Contains(html, "default-src &#39;none&#39;") && !strings.Contains(html, "default-src 'none'") {
		t.Error("offline content security policy is absent")
	}
	moved := filepath.Join(t.TempDir(), "moved.html")
	if err := os.Rename(output, moved); err != nil {
		t.Fatal(err)
	}
	movedData, err := os.ReadFile(moved)
	if err != nil || !bytes.Equal(data, movedData) {
		t.Fatalf("portable output changed after move: %v", err)
	}
}

func TestRenderHTMLRejectsUnsafeEvidenceReferences(t *testing.T) {
	working := t.TempDir()
	root := filepath.Join(working, "root")
	if err := os.MkdirAll(root, 0755); err != nil {
		t.Fatal(err)
	}
	abs := filepath.Join(root, "absolute.actual.txt")
	cases := []struct{ name, reference string }{
		{"traversal", "../outside.actual.txt"},
		{"absolute", abs},
		{"remote", "https://example.invalid/screen.actual.txt"},
		{"network", `\\server\share\screen.actual.txt`},
	}
	for _, test := range cases {
		t.Run(test.name, func(t *testing.T) {
			document := oneFailure(test.reference, "")
			input := filepath.Join(working, test.name+".json")
			writeDocument(t, input, document)
			err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(working, test.name+".html"), WorkingDirectory: working})
			if err == nil {
				t.Fatal("unsafe reference was accepted")
			}
		})
	}
}

func TestRenderHTMLRejectsEscapingSymlinkOrJunction(t *testing.T) {
	working := t.TempDir()
	root := filepath.Join(working, "root")
	outside := filepath.Join(working, "outside")
	if err := os.MkdirAll(root, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(outside, 0755); err != nil {
		t.Fatal(err)
	}
	link := filepath.Join(root, "escape")
	if err := os.Symlink(outside, link); err != nil {
		if runtime.GOOS != "windows" {
			t.Skipf("filesystem does not permit a test symlink: %v", err)
		}
		if output, junctionErr := exec.Command("cmd", "/c", "mklink", "/J", link, outside).CombinedOutput(); junctionErr != nil {
			t.Skipf("filesystem does not permit a test junction: %v (%s)", junctionErr, output)
		}
	}
	reference := filepath.ToSlash(filepath.Join("root", "escape", "screen.actual.txt"))
	input := filepath.Join(working, "results.json")
	writeDocument(t, input, oneFailure(reference, ""))
	err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(working, "report.html"), WorkingDirectory: working})
	if err == nil || !(strings.Contains(err.Error(), "outside evidence root") || strings.Contains(err.Error(), "symbolic link or junction")) {
		t.Fatalf("error = %v", err)
	}
}

func TestRenderHTMLCanonicalizesWorkingDirectoryAlias(t *testing.T) {
	parent := t.TempDir()
	working := filepath.Join(parent, "real")
	root := filepath.Join(working, "artifacts")
	if err := os.MkdirAll(root, 0755); err != nil {
		t.Fatal(err)
	}
	alias := filepath.Join(parent, "working-alias")
	if err := os.Symlink(working, alias); err != nil {
		if runtime.GOOS != "windows" {
			t.Skipf("filesystem does not permit a working-directory symlink: %v", err)
		}
		if output, junctionErr := exec.Command("cmd", "/c", "mklink", "/J", alias, working).CombinedOutput(); junctionErr != nil {
			t.Skipf("filesystem does not permit a working-directory junction: %v (%s)", junctionErr, output)
		}
	}
	reference := filepath.ToSlash(filepath.Join("artifacts", "screen.actual.txt"))
	writeTestFile(t, filepath.Join(root, "screen.actual.txt"), []byte("captured through an aliased working directory"))
	input := filepath.Join(root, "results.json")
	writeDocument(t, input, oneFailure(reference, ""))
	output := filepath.Join(parent, "report.html")
	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: output, WorkingDirectory: alias}); err != nil {
		t.Fatal(err)
	}
}

func TestRenderHTMLRejectsMalformedVersionOversizeAndInconsistentInput(t *testing.T) {
	working := t.TempDir()
	root := filepath.Join(working, "root")
	if err := os.MkdirAll(root, 0755); err != nil {
		t.Fatal(err)
	}
	tests := []struct {
		name string
		data []byte
		want string
	}{
		{"malformed", []byte(`{"report_version":`), "decode report"},
		{"unknown", []byte(`{"report_version":1,"runner_version":"x","os":"x","arch":"x","summary":{"total":0,"passed":0,"failed":0,"cancelled":0,"not_run":0},"results":[],"extra":true}`), "unknown field"},
		{"wrong-version", mustJSON(t, Document{ReportVersion: 2, Summary: Summary{}}), "unsupported report version"},
		{"wrong-summary", mustJSON(t, Document{ReportVersion: 1, Summary: Summary{Total: 1}}), "inconsistent"},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			input := filepath.Join(working, test.name+".json")
			writeTestFile(t, input, test.data)
			err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(working, test.name+".html"), WorkingDirectory: working})
			if err == nil || !strings.Contains(err.Error(), test.want) {
				t.Fatalf("error = %v, want %q", err, test.want)
			}
		})
	}
	oversized := filepath.Join(working, "oversized.json")
	writeTestFile(t, oversized, bytes.Repeat([]byte(" "), maxReportBytes+1))
	if err := RenderHTML(HTMLOptions{InputPath: oversized, EvidenceRoot: root, OutputPath: filepath.Join(working, "oversized.html"), WorkingDirectory: working}); err == nil || !strings.Contains(err.Error(), "exceeds") {
		t.Fatalf("oversized report error = %v", err)
	}
}

func TestRenderHTMLBoundsEvidenceAndPreservesOutputOnEveryFailure(t *testing.T) {
	working := t.TempDir()
	root := filepath.Join(working, "artifacts")
	if err := os.MkdirAll(root, 0755); err != nil {
		t.Fatal(err)
	}
	reference := filepath.ToSlash(filepath.Join("artifacts", "large.actual.txt"))
	writeTestFile(t, filepath.Join(working, filepath.FromSlash(reference)), bytes.Repeat([]byte("x"), maxEvidenceFileBytes+1))
	input := filepath.Join(root, "results.json")
	writeDocument(t, input, oneFailure(reference, ""))
	output := filepath.Join(working, "report.html")
	original := []byte("previous report")
	writeTestFile(t, output, original)
	err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: output, WorkingDirectory: working})
	if err == nil || !strings.Contains(err.Error(), "exceeds") {
		t.Fatalf("error = %v", err)
	}
	current, readErr := os.ReadFile(output)
	if readErr != nil || !bytes.Equal(current, original) {
		t.Fatalf("previous output changed: %v, %q", readErr, current)
	}

	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: input, WorkingDirectory: working}); err == nil || !strings.Contains(err.Error(), "aliases input") {
		t.Fatalf("input alias error = %v", err)
	}

	writeTestFile(t, filepath.Join(root, "large.actual.txt"), []byte("screen"))
	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(root, "large.actual.txt"), WorkingDirectory: working}); err == nil || !strings.Contains(err.Error(), "aliases admitted evidence") {
		t.Fatalf("evidence alias error = %v", err)
	}
	missingReference := filepath.ToSlash(filepath.Join("artifacts", "missing.actual.txt"))
	writeDocument(t, input, oneFailure(missingReference, ""))
	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(root, "missing.actual.txt"), WorkingDirectory: working}); err == nil || !strings.Contains(err.Error(), "aliases admitted evidence") {
		t.Fatalf("missing evidence alias error = %v", err)
	}

	blockedParent := filepath.Join(working, "not-a-directory")
	writeTestFile(t, blockedParent, []byte("keep"))
	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(blockedParent, "report.html"), WorkingDirectory: working}); err == nil {
		t.Fatal("unwritable output was accepted")
	}
	kept, _ := os.ReadFile(blockedParent)
	if string(kept) != "keep" {
		t.Fatal("failed output write changed its blocking input")
	}
}

func TestRenderHTMLRejectsInconsistentAndSharedArtifactAssociation(t *testing.T) {
	working := t.TempDir()
	root := filepath.Join(working, "root")
	if err := os.MkdirAll(root, 0755); err != nil {
		t.Fatal(err)
	}
	for _, name := range []string{"one.actual.txt", "two.diff.txt", "shared.actual.txt"} {
		writeTestFile(t, filepath.Join(root, name), []byte("evidence"))
	}
	input := filepath.Join(working, "results.json")
	document := oneFailure(filepath.ToSlash(filepath.Join("root", "one.actual.txt")), filepath.ToSlash(filepath.Join("root", "two.diff.txt")))
	writeDocument(t, input, document)
	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(working, "one.html"), WorkingDirectory: working}); err == nil || !strings.Contains(err.Error(), "inconsistent") {
		t.Fatalf("inconsistent association error = %v", err)
	}
	shared := filepath.ToSlash(filepath.Join("root", "shared.actual.txt"))
	document = oneFailure(shared, "")
	second := document.Results[0]
	second.SpecPath = "tests/two.json"
	document.Results = append(document.Results, second)
	document.Summary = Summary{Total: 2, Failed: 2}
	writeDocument(t, input, document)
	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(working, "two.html"), WorkingDirectory: working}); err == nil || !strings.Contains(err.Error(), "associated with both") {
		t.Fatalf("shared association error = %v", err)
	}

	hardScreen := filepath.Join(root, "hard.actual.txt")
	hardDiff := filepath.Join(root, "hard.diff.txt")
	writeTestFile(t, hardScreen, []byte("same physical evidence"))
	if err := os.Link(hardScreen, hardDiff); err != nil {
		t.Skipf("filesystem does not support hard-link association check: %v", err)
	}
	document = oneFailure(filepath.ToSlash(filepath.Join("root", "hard.actual.txt")), filepath.ToSlash(filepath.Join("root", "hard.diff.txt")))
	writeDocument(t, input, document)
	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(working, "hard.html"), WorkingDirectory: working}); err == nil || !strings.Contains(err.Error(), "aliases evidence") {
		t.Fatalf("hard-link association error = %v", err)
	}
}

func TestRenderHTMLAggregateEvidenceAndGeneratedOutputLimits(t *testing.T) {
	if testing.Short() {
		t.Skip("resource-boundary coverage")
	}
	working := t.TempDir()
	root := filepath.Join(working, "root")
	if err := os.MkdirAll(root, 0755); err != nil {
		t.Fatal(err)
	}
	document := Document{ReportVersion: 1, RunnerVersion: "test", OS: runtime.GOOS, Arch: runtime.GOARCH}
	for index := 0; index < maxAggregateEvidence/maxEvidenceFileBytes+1; index++ {
		name := fmt.Sprintf("screen-%03d.actual.txt", index)
		writeTestFile(t, filepath.Join(root, name), bytes.Repeat([]byte("x"), maxEvidenceFileBytes))
		result := oneFailure(filepath.ToSlash(filepath.Join("root", name)), "").Results[0]
		result.SpecPath = fmt.Sprintf("tests/%03d.json", index)
		document.Results = append(document.Results, result)
	}
	document.Summary = Summary{Total: len(document.Results), Failed: len(document.Results)}
	input := filepath.Join(working, "aggregate.json")
	writeDocument(t, input, document)
	err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(working, "aggregate.html"), WorkingDirectory: working})
	if err == nil || !strings.Contains(err.Error(), "aggregate limit") {
		t.Fatalf("aggregate error = %v", err)
	}

	// Exactly 24 MiB is admitted, but HTML escaping can still exceed the
	// independent 32 MiB generated-document cap.
	document.Results = document.Results[:maxAggregateEvidence/maxEvidenceFileBytes]
	for index := range document.Results {
		name := fmt.Sprintf("screen-%03d.actual.txt", index)
		writeTestFile(t, filepath.Join(root, name), bytes.Repeat([]byte("<"), maxEvidenceFileBytes))
	}
	document.Summary = Summary{Total: len(document.Results), Failed: len(document.Results)}
	writeDocument(t, input, document)
	err = RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: filepath.Join(working, "html-limit.html"), WorkingDirectory: working})
	if err == nil || !strings.Contains(err.Error(), "generated report exceeds") {
		t.Fatalf("HTML limit error = %v", err)
	}
}

func oneFailure(screen, diff string) Document {
	return Document{
		ReportVersion: 1, RunnerVersion: "test", OS: "test", Arch: "test", Summary: Summary{Total: 1, Failed: 1},
		Results: []runner.RunResult{{
			SpecVersion: 1, Name: "failure", SpecPath: "tests/one.json", Status: "failed", Viewport: runner.TerminalSize{Width: 80, Height: 24},
			Steps:   []runner.StepResult{{Number: 1, Action: "expect", Status: "failed", Failure: &runner.Failure{Category: runner.FailureAssertionTimeout, Message: "timeout"}}},
			Failure: &runner.Failure{Category: runner.FailureAssertionTimeout, Message: "timeout"}, Cleanup: runner.CleanupReport{Attempted: true, ConfirmedExited: true},
			Evidence: runner.EvidenceReport{ScreenPath: screen, DiffPath: diff},
		}},
	}
}

func writeDocument(t *testing.T, path string, document Document) {
	t.Helper()
	writeTestFile(t, path, mustJSON(t, document))
}

func mustJSON(t *testing.T, value any) []byte {
	t.Helper()
	data, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	return data
}

func writeTestFile(t *testing.T, path string, data []byte) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
}
