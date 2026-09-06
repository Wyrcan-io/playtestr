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
)

func TestCLIHelperProcess(t *testing.T) {
	if os.Getenv("PLAYTESTR_CLI_HELPER") != "1" {
		return
	}
	if os.Getenv("PLAYTESTR_CLI_EXIT") == "1" {
		fmt.Print("finished\r\n")
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
	for _, args := range [][]string{{"--version"}, {"--help"}, {"test", "--help"}} {
		var stdout, stderr bytes.Buffer
		if code := run(context.Background(), args, &stdout, &stderr); code != 0 {
			t.Fatalf("args=%v code=%d stderr=%q", args, code, stderr.String())
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

func writeCLISpec(t *testing.T, name string, second bool) string {
	t.Helper()
	environment := map[string]string{"PLAYTESTR_CLI_HELPER": "1"}
	if second {
		environment["PLAYTESTR_SECOND_SPEC"] = "1"
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
	first := writeCLISpec(t, "first", false)
	second := writeCLISpec(t, "second", true)
	ctx, cancel := context.WithCancel(context.Background())
	time.AfterFunc(100*time.Millisecond, cancel)
	var stdout, stderr bytes.Buffer
	reportPath := filepath.Join(t.TempDir(), "cancelled.json")
	code := run(ctx, []string{"test", "--report", reportPath, first, second}, &stdout, &stderr)
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
}

func TestSnapshotSelectorCLIValidation(t *testing.T) {
	for _, test := range []struct {
		name string
		args []string
		want string
	}{
		{name: "requires update", args: []string{"test", "--snapshot", "one.txt", "spec.json"}, want: "--snapshot requires --update"},
		{name: "requires one spec", args: []string{"test", "--update", "--snapshot", "one.txt", "one.json", "two.json"}, want: "--snapshot requires exactly one spec.json"},
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
