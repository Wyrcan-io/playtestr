package report

import (
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"testing"

	"github.com/Wyrcan-io/playtestr/internal/runner"
)

func TestHTMLPreservesNativeWindowsExitStatus(t *testing.T) {
	if strconv.IntSize < 64 {
		t.Skip("published native Windows qualification uses amd64")
	}
	root := t.TempDir()
	code := uint64(0xc000013a)
	exit := int(code)
	failure := &runner.Failure{Category: runner.FailureUnexpectedExit, Message: "native target exited with an undeclared status"}
	document := Document{ReportVersion: 1, RunnerVersion: "native-exit-regression", OS: "windows", Arch: "amd64",
		Summary: Summary{Total: 1, Failed: 1}, Results: []runner.RunResult{{SpecVersion: 1,
			Name: "native interruption", SpecPath: "native.json", Status: "failed",
			Viewport: runner.TerminalSize{Width: 80, Height: 24},
			Steps:    []runner.StepResult{{Number: 1, Action: "exit", Status: "failed", Failure: failure}},
			Target:   runner.TargetReport{Exited: true, ExitCode: &exit}, Failure: failure,
			Cleanup: runner.CleanupReport{Attempted: true, ConfirmedExited: true}}}}
	input := filepath.Join(root, "native.json")
	writeDocument(t, input, document)
	output := filepath.Join(root, "native.html")
	if err := RenderHTML(HTMLOptions{InputPath: input, EvidenceRoot: root, OutputPath: output, WorkingDirectory: root}); err != nil {
		t.Fatal(err)
	}
	data, err := os.ReadFile(output)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(data), "3221225786") || !strings.Contains(string(data), "unexpected_exit") {
		t.Fatal("native status or actual failure category missing from rendered evidence")
	}
}
