//go:build windows

package main

import (
	"bytes"
	"context"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"testing"

	"github.com/Wyrcan-io/playtestr/internal/runner"
)

func TestRecorderNativeStatusTargetHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_RECORDER_WIDE_EXIT") != "1" {
		return
	}
	if err := os.WriteFile("saved.txt", []byte("native recorded bytes\n"), 0600); err != nil {
		os.Exit(7)
	}
	fmt.Print("native fixture saved\r\n")
	code := uint64(0xc000013a)
	os.Exit(int(code))
}

func TestRecorderExportsAndReplaysNativeWindowsExit(t *testing.T) {
	if strconv.IntSize < 64 {
		t.Skip("published native Windows qualification uses amd64")
	}
	root := t.TempDir()
	if err := os.Mkdir(filepath.Join(root, "fixture"), 0700); err != nil {
		t.Fatal(err)
	}
	input, writer, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	defer input.Close()
	if _, err := io.WriteString(writer, "/exit 3221225786\n/file saved.txt\n/review\n/replay\n/save\n"); err != nil {
		t.Fatal(err)
	}
	writer.Close()
	path := filepath.Join(root, "native.json")
	var output, diagnosis bytes.Buffer
	code := runRecord(context.Background(), []string{"--output", path, "--fixture", "fixture",
		"--temporary-home", "--temporary-temp", "--timeout-ms", "10000", "--run-timeout-ms", "30000",
		"--env", "PLAYTESTR_RECORDER_WIDE_EXIT=1", "--", os.Args[0], "-test.run=^TestRecorderNativeStatusTargetHelper$"},
		input, &output, &diagnosis)
	if code != 0 {
		t.Fatalf("public native status recording failed: code=%d; %s; %s", code, &output, &diagnosis)
	}
	spec, err := runner.Load(path)
	if err != nil || spec.Version != 3 || len(spec.Steps) != 2 || spec.Steps[0].Exit == nil || uint64(*spec.Steps[0].Exit) != 0xc000013a {
		t.Fatalf("export lost the exact native status: %+v; %v", spec, err)
	}
	result := runner.RunDetailedContext(context.Background(), path, runner.RunOptions{}, io.Discard)
	if result.Err() != nil || result.Steps[1].State == nil || result.Steps[1].State.Outcome != "matched" ||
		!result.Cleanup.ConfirmedExited || result.Workspace == nil || !result.Workspace.Cleaned {
		t.Fatalf("ordinary exported native status/state test failed: %v", result.Err())
	}
}
