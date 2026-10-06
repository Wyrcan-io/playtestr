package main

import (
	"bytes"
	"strings"
	"testing"
)

func TestWorkflowExplicitChoicesAndPins(t *testing.T) {
	var out, err bytes.Buffer
	args := []string{"--print", "--source-revision", strings.Repeat("a", 40), "--os", "linux,macos,windows", "--suite", "tests/space name's.json", "--build", "go build -o bin/app ./cmd/app", "--setup", "go mod download"}
	if code := runWorkflow(args, &out, &err); code != 0 {
		t.Fatalf("%d %s", code, err.String())
	}
	yaml := out.String()
	for _, required := range []string{"contents: read", "persist-credentials: false", "ubuntu-24.04, macos-15, windows-2025", "source-$SOURCE_REVISION", "context_manifest.py", "report_summary.py", "cancel-in-progress: true", "'tests/space name'\"'\"'s.json'"} {
		if !strings.Contains(yaml, required) {
			t.Fatal("missing", required)
		}
	}
	for _, forbidden := range []string{"pull_request_target", "secrets.", "continue-on-error", "@SOURCE@", "@BUILD@", "uses: actions/checkout@v"} {
		if strings.Contains(yaml, forbidden) {
			t.Fatal("unsafe/unresolved", forbidden)
		}
	}
}

func TestWorkflowRejectsMissingAndHostileChoices(t *testing.T) {
	base := []string{"--print", "--source-revision", strings.Repeat("a", 40), "--suite", "tests", "--build", "true"}
	for _, extra := range [][]string{{"--os", "self-hosted"}, {"--retention-days", "31"}, {"--suite", "../outside"}, {"--runner-version", "v1.0.0"}, {"--source-revision", "main"}, {"--suite", "bad\nname"}, {"--suite", "${{ github.event.pull_request.title }}"}, {"--build", "echo '${{ github.event.pull_request.title }}'"}} {
		var out, err bytes.Buffer
		if code := runWorkflow(append(append([]string{}, base...), extra...), &out, &err); code == 0 {
			t.Fatal("accepted", extra)
		}
	}
}

func TestWorkflowDoesNotReinterpretLiteralCommandMarkers(t *testing.T) {
	var out, err bytes.Buffer
	args := []string{"--print", "--source-revision", strings.Repeat("a", 40), "--suite", "test.json", "--build", "printf '@SOURCE@ @SUITES@'"}
	if code := runWorkflow(args, &out, &err); code != 0 {
		t.Fatal(code, err.String())
	}
	if !strings.Contains(out.String(), "printf '@SOURCE@ @SUITES@'") {
		t.Fatal("literal build command was rewritten")
	}
}
