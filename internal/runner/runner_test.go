package runner

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/hinshun/vt10x"
)

func TestScreenRedraw(t *testing.T) {
	terminal := vt10x.New(vt10x.WithSize(30, 5))
	terminal.Write([]byte("old content\x1b[2J\x1b[H\x1b[32mready\x1b[0m"))
	if got := normalize(terminal.String()); got != "ready\n" {
		t.Fatalf("got %q", got)
	}
}

func TestRejectInvalidSpecs(t *testing.T) {
	for _, data := range []string{
		`{"command":["demo"],"steps":[{"key":"Wrong"}]}`,
		`{"command":["demo"],"steps":[{"snapshot":"../escape"}]}`,
		`{"command":["demo"],"steps":[{"key":"Enter","expect":"ok"}]}`,
		`{"command":["demo"],"width":-1,"steps":[{"expect":"ok"}]}`,
		`{"command":["demo"],"steps":[{"expect":"ok"}],"typo":true}`,
		`{"command":["demo"],"steps":[{"exit":256}]}`,
		`{"command":["demo"],"steps":[{"exit":-1}]}`,
	} {
		path := filepath.Join(t.TempDir(), "test.json")
		if e := os.WriteFile(path, []byte(data), 0600); e != nil {
			t.Fatal(e)
		}
		if _, e := Load(path); e == nil {
			t.Fatalf("accepted %s", data)
		}
	}
}

func intPointer(value int) *int { return &value }

func TestHelperProcess(t *testing.T) {
	if os.Getenv("PLAYTESTR_HELPER_PROCESS") != "1" {
		return
	}
	mode := os.Args[len(os.Args)-1]
	switch mode {
	case "exit-zero":
		fmt.Print("finished cleanly\r\n")
		os.Exit(0)
	case "exit-seven":
		fmt.Print("about to crash\r\n")
		os.Exit(7)
	case "hang":
		fmt.Print("still running\r\n")
		time.Sleep(10 * time.Second)
		os.Exit(0)
	default:
		os.Exit(99)
	}
}

func runHelperSpec(t *testing.T, mode string, steps []Step, timeoutMS int) error {
	t.Helper()
	t.Setenv("PLAYTESTR_HELPER_PROCESS", "1")
	spec := Spec{
		Name:      mode,
		Command:   []string{os.Args[0], "-test.run=TestHelperProcess", "--", mode},
		Width:     40,
		Height:    8,
		TimeoutMS: timeoutMS,
		Steps:     steps,
	}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "spec.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	return Run(path, false, &bytes.Buffer{})
}

func TestExpectedExitZero(t *testing.T) {
	if err := runHelperSpec(t, "exit-zero", []Step{{Exit: intPointer(0)}, {Expect: "finished cleanly"}}, 5000); err != nil {
		t.Fatal(err)
	}
}

func TestExpectedNonzeroExit(t *testing.T) {
	if err := runHelperSpec(t, "exit-seven", []Step{{Exit: intPointer(7)}}, 5000); err != nil {
		t.Fatal(err)
	}
}

func TestWrongExitCode(t *testing.T) {
	err := runHelperSpec(t, "exit-seven", []Step{{Expect: "about to crash"}, {Exit: intPointer(0)}}, 5000)
	if err == nil || !strings.Contains(err.Error(), "expected exit code 0, got 7") {
		t.Fatalf("got %v", err)
	}
}

func TestExitWhileWaitingForText(t *testing.T) {
	err := runHelperSpec(t, "exit-seven", []Step{{Expect: "never printed"}}, 5000)
	if err == nil || !strings.Contains(err.Error(), "process exited with code 7") {
		t.Fatalf("got %v", err)
	}
}

func TestExitTimeout(t *testing.T) {
	err := runHelperSpec(t, "hang", []Step{{Exit: intPointer(0)}}, 100)
	if err == nil || !strings.Contains(err.Error(), "timed out waiting for process to exit") {
		t.Fatalf("got %v", err)
	}
}
