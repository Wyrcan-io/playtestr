package main

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/Wyrcan-io/playtestr/internal/discovery"
	"github.com/Wyrcan-io/playtestr/internal/report"
	"github.com/Wyrcan-io/playtestr/internal/runner"
)

func TestCLIHelperProcess(t *testing.T) {
	if os.Getenv("PLAYTESTR_CLI_HELPER") != "1" {
		return
	}
	if sentinel := os.Getenv("PLAYTESTR_CLI_SENTINEL"); sentinel != "" {
		_ = os.WriteFile(sentinel, []byte("started"), 0600)
	}
	if os.Getenv("PLAYTESTR_CLI_EXIT") == "1" {
		fmt.Print("finished\r\n")
		if os.Getenv("PLAYTESTR_CLI_EXIT_CODE") == "7" {
			os.Exit(7)
		}
		os.Exit(0)
	}
	if os.Getenv("PLAYTESTR_SECOND_SPEC") == "1" {
		fmt.Print("SECOND SPEC STARTED\r\n")
	}
	for {
		time.Sleep(time.Second)
	}
}

func TestVersionAndHelp(t *testing.T) {
	for _, args := range [][]string{{"--version"}, {"--help"}, {"test", "--help"}, {"report", "--help"}} {
		var stdout, stderr bytes.Buffer
		if code := run(context.Background(), args, &stdout, &stderr); code != 0 {
			t.Fatalf("args=%v code=%d stderr=%q", args, code, stderr.String())
		}
	}
}

func TestOfflineReportCLI(t *testing.T) {
	directory, err := os.MkdirTemp(".", ".cli-report-")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.RemoveAll(directory) })
	screen := filepath.Join(directory, "failure.actual.txt")
	if err := os.WriteFile(filepath.Join(directory, "failure.actual.txt"), []byte("captured screen\n"), 0600); err != nil {
		t.Fatal(err)
	}
	document := report.New("test", []runner.RunResult{{
		SpecVersion: 1, Name: "failure", SpecPath: "tests/failure.json", Status: "failed",
		Viewport: runner.TerminalSize{Width: 80, Height: 24},
		Steps:    []runner.StepResult{{Number: 1, Action: "expect", Status: "failed", Failure: &runner.Failure{Category: runner.FailureAssertionTimeout, Message: "timeout"}}},
		Failure:  &runner.Failure{Category: runner.FailureAssertionTimeout, Message: "timeout"},
		Cleanup:  runner.CleanupReport{Attempted: true, ConfirmedExited: true}, Evidence: runner.EvidenceReport{ScreenPath: screen},
	}})
	input := filepath.Join(directory, "results.json")
	if err := report.Write(input, document); err != nil {
		t.Fatal(err)
	}
	output := filepath.Join(directory, "report.html")
	var stdout, stderr bytes.Buffer
	code := run(context.Background(), []string{"report", "--input", input, "--evidence-root", directory, "--output", output}, &stdout, &stderr)
	if code != 0 || !strings.Contains(stdout.String(), "Offline report saved:") || stderr.Len() != 0 {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
	data, err := os.ReadFile(output)
	if err != nil || !strings.Contains(string(data), "captured screen") {
		t.Fatalf("offline report: err=%v data=%q", err, data)
	}
}

func TestOfflineReportCLIUsageAndRenderingErrors(t *testing.T) {
	for _, test := range []struct {
		args []string
		want string
		code int
	}{
		{args: []string{"report"}, want: "are required", code: 2},
		{args: []string{"report", "extra"}, want: "does not accept positional", code: 2},
		{args: []string{"report", "--input", "missing.json", "--evidence-root", ".", "--output", "out.html"}, want: "FAIL render report", code: 1},
	} {
		var stdout, stderr bytes.Buffer
		if code := run(context.Background(), test.args, &stdout, &stderr); code != test.code || !strings.Contains(stderr.String(), test.want) {
			t.Fatalf("args=%v code=%d stdout=%q stderr=%q", test.args, code, stdout.String(), stderr.String())
		}
	}
}

func TestJSONReport(t *testing.T) {
	spec := map[string]any{
		"version": 1,
		"name":    "reported",
		"command": []string{os.Args[0], "-test.run=TestCLIHelperProcess"},
		"env":     map[string]string{"PLAYTESTR_CLI_HELPER": "1", "PLAYTESTR_CLI_EXIT": "1", "SECRET_VALUE": "do-not-report-this"},
		"steps":   []map[string]any{{"exit": 0}},
	}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	directory := t.TempDir()
	specPath := filepath.Join(directory, "spec.json")
	reportPath := filepath.Join(directory, "results.json")
	if err := os.WriteFile(specPath, data, 0600); err != nil {
		t.Fatal(err)
	}
	var stdout, stderr bytes.Buffer
	if code := run(context.Background(), []string{"test", "--report", reportPath, specPath}, &stdout, &stderr); code != 0 {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
	reportData, err := os.ReadFile(reportPath)
	if err != nil {
		t.Fatal(err)
	}
	text := string(reportData)
	if !strings.Contains(text, `"report_version": 1`) || !strings.Contains(text, `"status": "passed"`) || strings.Contains(text, "do-not-report-this") {
		t.Fatalf("report = %s", reportData)
	}
}

func TestReportWriteFailureReturnsNonzero(t *testing.T) {
	directory := t.TempDir()
	specPath := filepath.Join(directory, "invalid.json")
	if err := os.WriteFile(specPath, []byte(`{"version":1,"command":[],"steps":[]}`), 0600); err != nil {
		t.Fatal(err)
	}
	var stdout, stderr bytes.Buffer
	code := run(context.Background(), []string{"test", "--report", directory, specPath}, &stdout, &stderr)
	if code != 1 || !strings.Contains(stderr.String(), "FAIL write report") {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
}

func writeCLISpec(t *testing.T, name string, second bool, sentinel string) string {
	t.Helper()
	environment := map[string]string{"PLAYTESTR_CLI_HELPER": "1"}
	if second {
		environment["PLAYTESTR_SECOND_SPEC"] = "1"
	}
	if sentinel != "" {
		environment["PLAYTESTR_CLI_SENTINEL"] = sentinel
	}
	spec := map[string]any{
		"version": 1, "name": name, "command": []string{os.Args[0], "-test.run=TestCLIHelperProcess"},
		"env": environment, "timeout_ms": 5000, "run_timeout_ms": 5000,
		"steps": []map[string]any{{"exit": 0}},
	}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), name+".json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestCancellationReturns130AndStopsLaterSpecs(t *testing.T) {
	sentinel := filepath.Join(t.TempDir(), "first-started.txt")
	first := writeCLISpec(t, "first", false, sentinel)
	second := writeCLISpec(t, "second", true, "")
	ctx, cancel := context.WithCancel(context.Background())
	fallback := time.AfterFunc(4*time.Second, cancel)
	defer fallback.Stop()
	stopPolling := make(chan struct{})
	defer close(stopPolling)
	go func() {
		poll := time.NewTicker(10 * time.Millisecond)
		defer poll.Stop()
		for {
			select {
			case <-stopPolling:
				return
			case <-poll.C:
				if _, err := os.Stat(sentinel); err == nil {
					cancel()
					return
				}
			}
		}
	}()
	var stdout, stderr bytes.Buffer
	outputRoot := t.TempDir()
	reportPath := filepath.Join(outputRoot, "cancelled.json")
	artifactsPath := filepath.Join(outputRoot, "artifacts")
	code := run(ctx, []string{"test", "--artifacts-dir", artifactsPath, "--report", reportPath, first, second}, &stdout, &stderr)
	if _, err := os.Stat(sentinel); err != nil {
		t.Fatalf("first spec did not start before cancellation: %v", err)
	}
	if code != 130 {
		t.Fatalf("exit code = %d, stderr = %s", code, stderr.String())
	}
	if strings.Contains(stdout.String(), "SECOND SPEC STARTED") || strings.Contains(stderr.String(), "second") {
		t.Fatalf("second spec ran after cancellation: stdout=%q stderr=%q", stdout.String(), stderr.String())
	}
	reportData, err := os.ReadFile(reportPath)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(reportData), `"cancelled": 1`) || !strings.Contains(string(reportData), `"not_run": 1`) {
		t.Fatalf("cancellation report = %s", reportData)
	}
	if !strings.Contains(stdout.String(), "Suite: total=2 passed=0 failed=0 cancelled=1 not-run=1") {
		t.Fatalf("cancellation summary = %q", stdout.String())
	}
	matches, err := filepath.Glob(filepath.Join(artifactsPath, "*", "*.actual.txt"))
	if err != nil || len(matches) != 1 {
		t.Fatalf("cancellation artifacts = %v, err=%v", matches, err)
	}
}

func TestSnapshotSelectorCLIValidation(t *testing.T) {
	one := writeCLISpec(t, "one", false, "")
	two := writeCLISpec(t, "two", false, "")
	for _, test := range []struct {
		name string
		args []string
		want string
	}{
		{name: "requires update", args: []string{"test", "--snapshot", "one.txt", one}, want: "--snapshot requires --update"},
		{name: "requires one spec", args: []string{"test", "--update", "--snapshot", "one.txt", one, two}, want: "--snapshot requires exactly one resolved spec"},
	} {
		t.Run(test.name, func(t *testing.T) {
			var stdout, stderr bytes.Buffer
			if code := run(context.Background(), test.args, &stdout, &stderr); code != 2 {
				t.Fatalf("exit code = %d, stdout=%q stderr=%q", code, stdout.String(), stderr.String())
			}
			if !strings.Contains(stderr.String(), test.want) {
				t.Fatalf("stderr = %q", stderr.String())
			}
		})
	}
}

func TestWorkspaceCLIEmitsReportV2AndCanRetainFailure(t *testing.T) {
	root := t.TempDir()
	fixture := filepath.Join(root, "fixture")
	if err := os.Mkdir(fixture, 0755); err != nil {
		t.Fatal(err)
	}
	writeSpec := func(name string, exit bool) string {
		t.Helper()
		environment := map[string]string{"PLAYTESTR_CLI_HELPER": "1"}
		steps := []map[string]any{{"expect": "never"}}
		timeoutMS := 100
		if exit {
			environment["PLAYTESTR_CLI_EXIT"] = "1"
			steps = []map[string]any{{"expect": "finished"}, {"exit": 0}}
			timeoutMS = 3000
		}
		spec := map[string]any{
			"version": 2, "name": name,
			"command": []string{os.Args[0], "-test.run=TestCLIHelperProcess"},
			"env":     environment, "timeout_ms": timeoutMS, "run_timeout_ms": 10000,
			"workspace": map[string]any{"fixture": "fixture", "home": "temporary", "temp": "temporary"},
			"steps":     steps,
		}
		data, err := json.Marshal(spec)
		if err != nil {
			t.Fatal(err)
		}
		path := filepath.Join(root, name+".json")
		if err := os.WriteFile(path, data, 0600); err != nil {
			t.Fatal(err)
		}
		return path
	}

	passReport := filepath.Join(root, "pass-report.json")
	var stdout, stderr bytes.Buffer
	if code := run(context.Background(), []string{"test", "--report", passReport, writeSpec("pass", true)}, &stdout, &stderr); code != 0 {
		t.Fatalf("pass code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
	passData, err := os.ReadFile(passReport)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(passData), `"report_version": 2`) || !strings.Contains(string(passData), `"cleaned": true`) {
		t.Fatalf("workspace report = %s", passData)
	}

	failureReport := filepath.Join(root, "failure-report.json")
	stdout.Reset()
	stderr.Reset()
	if code := run(context.Background(), []string{"test", "--keep-workspace-on-failure", "--report", failureReport, writeSpec("failure", false)}, &stdout, &stderr); code != 1 {
		t.Fatalf("failure code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
	if !strings.Contains(stdout.String(), "Workspace retained:") {
		t.Fatalf("retention output = %q", stdout.String())
	}
	var document report.Document
	failureData, err := os.ReadFile(failureReport)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(failureData, &document); err != nil {
		t.Fatal(err)
	}
	retained := document.Results[0].Workspace
	if retained == nil || !retained.Retained || retained.RetainedPath == "" {
		t.Fatalf("retained workspace report = %+v", retained)
	}
	if err := os.RemoveAll(retained.RetainedPath); err != nil {
		t.Fatal(err)
	}
}

func writeSuiteSpec(t *testing.T, path, name string, expectedExit int, fail bool) {
	t.Helper()
	steps := []map[string]any{{"expect": "finished"}, {"exit": expectedExit}}
	if fail {
		steps = []map[string]any{{"expect": "never rendered"}}
	}
	spec := map[string]any{
		"version": 1,
		"name":    name,
		"command": []string{os.Args[0], "-test.run=TestCLIHelperProcess"},
		"env": map[string]string{
			"PLAYTESTR_CLI_HELPER":    "1",
			"PLAYTESTR_CLI_EXIT":      "1",
			"PLAYTESTR_CLI_EXIT_CODE": fmt.Sprint(expectedExit),
		},
		"steps": steps,
	}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
}

func TestDirectorySuiteContinuesAndSummarizes(t *testing.T) {
	root := t.TempDir()
	writeSuiteSpec(t, filepath.Join(root, "a-fail.json"), "intentional failure", 0, true)
	writeSuiteSpec(t, filepath.Join(root, "b-pass.json"), "ordinary pass", 0, false)
	writeSuiteSpec(t, filepath.Join(root, "nested", "c-nonzero.json"), "expected nonzero", 7, false)

	var stdout, stderr bytes.Buffer
	code := run(context.Background(), []string{"test", root}, &stdout, &stderr)
	if code != 1 {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
	if !strings.Contains(stdout.String(), "PASS ordinary pass") || !strings.Contains(stdout.String(), "PASS expected nonzero") {
		t.Fatalf("later specs did not run: %q", stdout.String())
	}
	if !strings.Contains(stdout.String(), "Suite: total=3 passed=2 failed=1 cancelled=0 not-run=0") ||
		!strings.Contains(stdout.String(), "a-fail.json status=failed category=unexpected_exit step=1") {
		t.Fatalf("summary = %q", stdout.String())
	}
}

func TestListResolvesWithoutLaunching(t *testing.T) {
	root := t.TempDir()
	writeSuiteSpec(t, filepath.Join(root, "b.json"), "b", 0, false)
	aPath := filepath.Join(root, "a.json")
	writeSuiteSpec(t, aPath, "a", 0, false)
	sentinel := filepath.Join(root, "started.txt")
	data, err := os.ReadFile(aPath)
	if err != nil {
		t.Fatal(err)
	}
	var spec map[string]any
	if err := json.Unmarshal(data, &spec); err != nil {
		t.Fatal(err)
	}
	spec["env"].(map[string]any)["PLAYTESTR_CLI_SENTINEL"] = sentinel
	data, _ = json.Marshal(spec)
	if err := os.WriteFile(aPath, data, 0600); err != nil {
		t.Fatal(err)
	}
	var stdout, stderr bytes.Buffer
	if code := run(context.Background(), []string{"test", "--list", root}, &stdout, &stderr); code != 0 {
		t.Fatalf("code=%d stderr=%q", code, stderr.String())
	}
	text := stdout.String()
	if strings.Contains(text, "PASS step") || strings.Index(text, "a.json") > strings.Index(text, "b.json") {
		t.Fatalf("list output = %q", text)
	}
	if _, err := os.Stat(sentinel); !os.IsNotExist(err) {
		t.Fatalf("--list launched target; sentinel error = %v", err)
	}
}

func TestSelectionErrorsReturnUsageStatus(t *testing.T) {
	empty := t.TempDir()
	for _, path := range []string{empty, filepath.Join(empty, "missing")} {
		var stdout, stderr bytes.Buffer
		if code := run(context.Background(), []string{"test", path}, &stdout, &stderr); code != 2 || !strings.Contains(stderr.String(), "selection error:") {
			t.Fatalf("path=%q code=%d stdout=%q stderr=%q", path, code, stdout.String(), stderr.String())
		}
	}
}

func TestAuthoringEmptySelectionExplainsNextActionWithoutLaunch(t *testing.T) {
	empty := t.TempDir()
	var stdout, stderr bytes.Buffer
	if code := run(context.Background(), []string{"test", empty}, &stdout, &stderr); code != 2 {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
	if text := stderr.String(); !strings.Contains(text, "selection error:") || !strings.Contains(text, "selection matched no test specifications") {
		t.Fatalf("stderr does not identify the empty selection or next action: %q", text)
	}
	if strings.Contains(stdout.String(), "PASS step") {
		t.Fatalf("empty selection launched a target: %q", stdout.String())
	}
}

func TestArtifactRunDirectoriesSeparateDuplicateBasenamesAndNoStaleReferences(t *testing.T) {
	root := t.TempDir()
	first := filepath.Join(root, "one", "menu.json")
	second := filepath.Join(root, "two", "menu.json")
	writeSuiteSpec(t, first, "first menu", 0, true)
	writeSuiteSpec(t, second, "second menu", 0, true)
	artifacts := filepath.Join(t.TempDir(), "artifacts")
	reportPath := filepath.Join(artifacts, "results.json")

	var stdout, stderr bytes.Buffer
	if code := run(context.Background(), []string{"test", "--artifacts-dir", artifacts, "--report", reportPath, root}, &stdout, &stderr); code != 1 {
		t.Fatalf("failure code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
	matches, err := filepath.Glob(filepath.Join(artifacts, "*", "*.actual.txt"))
	if err != nil || len(matches) != 2 || filepath.Base(matches[0]) == filepath.Base(matches[1]) {
		t.Fatalf("artifacts = %v, err=%v", matches, err)
	}
	failureData, err := os.ReadFile(reportPath)
	if err != nil {
		t.Fatal(err)
	}
	var failureReport struct {
		Results []struct {
			Evidence struct {
				ScreenPath string `json:"screen_path"`
			} `json:"evidence"`
		} `json:"results"`
	}
	if err := json.Unmarshal(failureData, &failureReport); err != nil {
		t.Fatal(err)
	}
	if len(failureReport.Results) != 2 || failureReport.Results[0].Evidence.ScreenPath == failureReport.Results[1].Evidence.ScreenPath {
		t.Fatalf("report evidence paths are not distinct: %+v", failureReport.Results)
	}
	for _, result := range failureReport.Results {
		if _, err := os.Stat(result.Evidence.ScreenPath); err != nil {
			t.Fatalf("report references unwritten evidence %q: %v", result.Evidence.ScreenPath, err)
		}
	}

	writeSuiteSpec(t, first, "first menu", 0, false)
	writeSuiteSpec(t, second, "second menu", 0, false)
	stdout.Reset()
	stderr.Reset()
	if code := run(context.Background(), []string{"test", "--artifacts-dir", artifacts, "--report", reportPath, root}, &stdout, &stderr); code != 0 {
		t.Fatalf("pass code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
	data, err := os.ReadFile(reportPath)
	if err != nil {
		t.Fatal(err)
	}
	if strings.Contains(string(data), "screen_path") || strings.Contains(string(data), "diff_path") {
		t.Fatalf("passing report references stale evidence: %s", data)
	}
	entries, err := os.ReadDir(artifacts)
	if err != nil {
		t.Fatal(err)
	}
	runDirectories := 0
	for _, entry := range entries {
		if entry.IsDir() {
			runDirectories++
		}
	}
	if runDirectories != 2 {
		t.Fatalf("run directory count = %d", runDirectories)
	}
}

func TestOutputAliasesAreRejectedBeforeLaunch(t *testing.T) {
	root := t.TempDir()
	specPath := filepath.Join(root, "spec.json")
	writeSuiteSpec(t, specPath, "alias", 0, false)
	original, err := os.ReadFile(specPath)
	if err != nil {
		t.Fatal(err)
	}
	for _, args := range [][]string{
		{"test", "--report", specPath, specPath},
		{"test", "--report", specPath, root},
		{"test", "--artifacts-dir", specPath, specPath},
	} {
		var stdout, stderr bytes.Buffer
		if code := run(context.Background(), args, &stdout, &stderr); code != 2 || !strings.Contains(stderr.String(), "aliases selected spec") {
			t.Fatalf("args=%v code=%d stdout=%q stderr=%q", args, code, stdout.String(), stderr.String())
		}
		current, err := os.ReadFile(specPath)
		if err != nil || !bytes.Equal(current, original) {
			t.Fatalf("spec changed: err=%v", err)
		}
	}
}

func TestArtifactDirectoryCannotContainSelectedSpecs(t *testing.T) {
	root := t.TempDir()
	specPath := filepath.Join(root, "spec.json")
	writeSuiteSpec(t, specPath, "contained", 0, false)
	var stdout, stderr bytes.Buffer
	if code := run(context.Background(), []string{"test", "--artifacts-dir", root, specPath}, &stdout, &stderr); code != 2 || !strings.Contains(stderr.String(), "contains selected spec") {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
}

func TestArtifactIDsAreSafeAndDistinct(t *testing.T) {
	one := discovery.Spec{Path: filepath.Join(t.TempDir(), "one", "menu.json"), DisplayPath: `tests/one/menu.json`}
	two := discovery.Spec{Path: filepath.Join(t.TempDir(), "two", "menu.json"), DisplayPath: `tests/two/menu.json`}
	first := artifactID(one)
	second := artifactID(two)
	if first == second || unsafeArtifactCharacter.MatchString(first) || unsafeArtifactCharacter.MatchString(second) {
		t.Fatalf("artifact IDs are not safe and distinct: %q %q", first, second)
	}
}

func TestSharedSnapshotUpdateRejectedBeforeLaunch(t *testing.T) {
	root := t.TempDir()
	for _, name := range []string{"one.json", "two.json"} {
		spec := map[string]any{
			"version": 1,
			"command": []string{os.Args[0], "-test.run=TestCLIHelperProcess"},
			"env":     map[string]string{"PLAYTESTR_CLI_HELPER": "1"},
			"steps":   []map[string]any{{"expect": "ready"}, {"snapshot": "shared.txt"}},
		}
		data, _ := json.Marshal(spec)
		if err := os.WriteFile(filepath.Join(root, name), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
	var stdout, stderr bytes.Buffer
	if code := run(context.Background(), []string{"test", "--update", root}, &stdout, &stderr); code != 2 || !strings.Contains(stderr.String(), "snapshot update is ambiguous") {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
}

func TestOutputCannotAliasSnapshotBaseline(t *testing.T) {
	root := t.TempDir()
	specPath := filepath.Join(root, "spec.json")
	spec := map[string]any{
		"version": 1,
		"command": []string{os.Args[0], "-test.run=TestCLIHelperProcess"},
		"env":     map[string]string{"PLAYTESTR_CLI_HELPER": "1"},
		"steps":   []map[string]any{{"expect": "ready"}, {"snapshot": "screen.txt"}},
	}
	data, _ := json.Marshal(spec)
	if err := os.WriteFile(specPath, data, 0600); err != nil {
		t.Fatal(err)
	}
	baseline := filepath.Join(root, "snapshots", "screen.txt")
	var stdout, stderr bytes.Buffer
	if code := run(context.Background(), []string{"test", "--report", baseline, specPath}, &stdout, &stderr); code != 2 || !strings.Contains(stderr.String(), "aliases snapshot baseline") {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
	if _, err := os.Stat(baseline); !os.IsNotExist(err) {
		t.Fatalf("baseline destination was written: %v", err)
	}
}

func TestSuiteAggregateStepLimit(t *testing.T) {
	root := t.TempDir()
	steps := make([]map[string]any, 1000)
	zero := 0
	for i := range steps {
		steps[i] = map[string]any{"exit": zero}
	}
	for i := 0; i < 11; i++ {
		spec := map[string]any{"version": 1, "command": []string{"missing-target"}, "steps": steps}
		data, _ := json.Marshal(spec)
		if err := os.WriteFile(filepath.Join(root, fmt.Sprintf("%02d.json", i)), data, 0600); err != nil {
			t.Fatal(err)
		}
	}
	var stdout, stderr bytes.Buffer
	if code := run(context.Background(), []string{"test", root}, &stdout, &stderr); code != 2 || !strings.Contains(stderr.String(), "aggregate steps") {
		t.Fatalf("code=%d stdout=%q stderr=%q", code, stdout.String(), stderr.String())
	}
}
