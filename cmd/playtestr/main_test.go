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
	if os.Getenv("PLAYTESTR_SECOND_SPEC") == "1" {
		fmt.Print("SECOND SPEC STARTED\r\n")
	}
	for {
		time.Sleep(time.Second)
	}
}

func writeCLISpec(t *testing.T, name string, second bool) string {
	t.Helper()
	environment := map[string]string{"PLAYTESTR_CLI_HELPER": "1"}
	if second {
		environment["PLAYTESTR_SECOND_SPEC"] = "1"
	}
	spec := map[string]any{
		"name": name, "command": []string{os.Args[0], "-test.run=TestCLIHelperProcess"},
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
	code := run(ctx, []string{"test", first, second}, &stdout, &stderr)
	if code != 130 {
		t.Fatalf("exit code = %d, stderr = %s", code, stderr.String())
	}
	if strings.Contains(stdout.String(), "SECOND SPEC STARTED") || strings.Contains(stderr.String(), "second") {
		t.Fatalf("second spec ran after cancellation: stdout=%q stderr=%q", stdout.String(), stderr.String())
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
