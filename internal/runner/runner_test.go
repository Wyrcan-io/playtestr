package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"testing"
	"time"

	"golang.org/x/term"
)

func TestScreenRedraw(t *testing.T) {
	terminal := newScreenEmulator(30, 5)
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
		`{"command":["demo"],"run_timeout_ms":-1,"steps":[{"expect":"ok"}]}`,
		`{"command":["demo"],"max_output_bytes":-1,"steps":[{"expect":"ok"}]}`,
		`{"command":["demo"],"env":{"BAD-NAME":"value"},"steps":[{"expect":"ok"}]}`,
		`{"command":["demo"],"steps":[{"snapshot":"screen.txt"}]}`,
		`{"command":["demo"],"steps":[{"expect":"ready"},{"key":"Enter"},{"snapshot":"screen.txt"}]}`,
		`{"command":["demo"],"steps":[{"resize":{"width":0,"height":20}}]}`,
		`{"command":["demo"],"steps":[{"resize":{"width":80,"height":201}}]}`,
		`{"command":["demo"],"steps":[{"expect":"ready"},{"snapshot":"same.txt"},{"snapshot":"same.txt"}]}`,
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
	case "silent-input":
		buffer := make([]byte, 1)
		_, _ = os.Stdin.Read(buffer)
		fmt.Print("input received\r\n")
		os.Exit(0)
	case "no-output":
		time.Sleep(10 * time.Second)
		os.Exit(0)
	case "delayed-redraw":
		fmt.Print("\x1b[2J\x1b[Hloading")
		time.Sleep(100 * time.Millisecond)
		fmt.Print("\x1b[2J\x1b[Hready")
		time.Sleep(75 * time.Millisecond)
		fmt.Print(" complete")
		time.Sleep(10 * time.Second)
		os.Exit(0)
	case "self-hang":
		_ = os.WriteFile(os.Getenv("PLAYTESTR_PID_FILE"), []byte(strconv.Itoa(os.Getpid())), 0600)
		fmt.Print("self running\r\n")
		time.Sleep(10 * time.Second)
		os.Exit(0)
	case "flood":
		chunk := strings.Repeat("x", 1024)
		for {
			fmt.Print(chunk)
		}
	case "cwd-env":
		cwd, _ := os.Getwd()
		fmt.Printf("cwd-base=%s\r\nmarker=%s\r\nsecret=%s\r\ninherited=%s\r\n", filepath.Base(cwd), os.Getenv("PLAYTESTR_MARKER"), os.Getenv("PLAYTESTR_SECRET"), os.Getenv("PLAYTESTR_INHERITED"))
		os.Exit(0)
	case "resize":
		old, err := term.MakeRaw(int(os.Stdin.Fd()))
		if err != nil {
			os.Exit(9)
		}
		defer term.Restore(int(os.Stdin.Fd()), old)
		fmt.Print("\x1b[2J\x1b[Hresize ready")
		buffer := make([]byte, 1)
		_, _ = os.Stdin.Read(buffer)
		width, height, err := term.GetSize(int(os.Stdout.Fd()))
		if err != nil {
			os.Exit(10)
		}
		fmt.Printf("\x1b[2J\x1b[Hresized %dx%d\r\n", width, height)
		os.Exit(0)
	case "parent-child", "parent-exits-child":
		// The delay ensures the runner attaches the parent to its process group
		// before this deterministic fixture creates a descendant.
		time.Sleep(200 * time.Millisecond)
		child := exec.Command(os.Args[0], "-test.run=TestHelperProcess", "--", "child-sleep")
		child.Env = os.Environ()
		if err := child.Start(); err != nil {
			fmt.Printf("child start failed: %v\r\n", err)
			os.Exit(8)
		}
		_ = os.WriteFile(os.Getenv("PLAYTESTR_PID_FILE"), []byte(strconv.Itoa(child.Process.Pid)), 0600)
		fmt.Printf("child started: %d\r\n", child.Process.Pid)
		if mode == "parent-exits-child" {
			os.Exit(0)
		}
		time.Sleep(10 * time.Second)
		os.Exit(0)
	case "child-sleep":
		time.Sleep(10 * time.Second)
		os.Exit(0)
	default:
		os.Exit(99)
	}
}

func runHelperSpec(t *testing.T, mode string, steps []Step, timeoutMS int) error {
	t.Helper()
	spec := Spec{
		Name:      mode,
		Command:   []string{os.Args[0], "-test.run=TestHelperProcess", "--", mode},
		Env:       map[string]string{"PLAYTESTR_HELPER_PROCESS": "1"},
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

func runConfiguredHelperSpec(t *testing.T, mode string, steps []Step, configure func(*Spec)) error {
	t.Helper()
	spec := Spec{
		Name:           mode,
		Command:        []string{os.Args[0], "-test.run=TestHelperProcess", "--", mode},
		Env:            map[string]string{"PLAYTESTR_HELPER_PROCESS": "1"},
		Width:          40,
		Height:         8,
		TimeoutMS:      5000,
		RunTimeoutMS:   5000,
		MaxOutputBytes: 2_000_000,
		Steps:          steps,
	}
	configure(&spec)
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

func TestLaunchFailure(t *testing.T) {
	spec := Spec{
		Name: "missing-target", Command: []string{"playtestr-command-that-does-not-exist"},
		Width: 40, Height: 8, TimeoutMS: 1000, RunTimeoutMS: 1000, MaxOutputBytes: 100000,
		Steps: []Step{{Exit: intPointer(0)}},
	}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "spec.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	err = Run(path, false, &bytes.Buffer{})
	if err == nil || !strings.Contains(err.Error(), "start target") {
		t.Fatalf("got %v", err)
	}
}

func TestSilentTargetCanReceiveInputWithoutStartupTimeout(t *testing.T) {
	err := runConfiguredHelperSpec(t, "silent-input", []Step{{Key: "Enter"}, {Expect: "input received"}, {Exit: intPointer(0)}}, func(_ *Spec) {})
	if err != nil {
		t.Fatal(err)
	}
}

func TestStartupTimeout(t *testing.T) {
	err := runConfiguredHelperSpec(t, "no-output", []Step{{Exit: intPointer(0)}}, func(spec *Spec) {
		spec.StartupTimeoutMS = 100
	})
	if err == nil || !strings.Contains(err.Error(), "timed out waiting for first output") {
		t.Fatalf("got %v", err)
	}
}

func TestRunTimeout(t *testing.T) {
	err := runConfiguredHelperSpec(t, "hang", []Step{{Expect: "still running"}, {Exit: intPointer(0)}}, func(spec *Spec) {
		spec.RunTimeoutMS = 150
	})
	if err == nil || !strings.Contains(err.Error(), "run exceeded total timeout") {
		t.Fatalf("got %v", err)
	}
}

func TestCancellation(t *testing.T) {
	ctx, cancel := context.WithCancel(context.Background())
	time.AfterFunc(100*time.Millisecond, cancel)
	err := runConfiguredHelperSpecContext(t, ctx, "hang", []Step{{Exit: intPointer(0)}}, func(_ *Spec) {})
	if err == nil || !strings.Contains(err.Error(), "run cancelled") {
		t.Fatalf("got %v", err)
	}
}

func TestOutputLimit(t *testing.T) {
	err := runConfiguredHelperSpec(t, "flood", []Step{{Expect: "never"}}, func(spec *Spec) {
		spec.MaxOutputBytes = 4096
	})
	if err == nil || !strings.Contains(err.Error(), "exceeded max_output_bytes") {
		t.Fatalf("got %v", err)
	}
}

func TestWorkingDirectoryAndExplicitEnvironment(t *testing.T) {
	t.Setenv("PLAYTESTR_SECRET", "must-not-leak")
	root := t.TempDir()
	work := filepath.Join(root, "work")
	if err := os.Mkdir(work, 0700); err != nil {
		t.Fatal(err)
	}
	spec := Spec{
		Name: "cwd-env", Command: []string{os.Args[0], "-test.run=TestHelperProcess", "--", "cwd-env"},
		CWD: "work", Env: map[string]string{"PLAYTESTR_HELPER_PROCESS": "1", "PLAYTESTR_MARKER": "declared"},
		Width: 80, Height: 8, TimeoutMS: 5000, RunTimeoutMS: 5000, MaxOutputBytes: 100000,
		Steps: []Step{{Expect: "cwd-base=work"}, {Expect: "marker=declared\nsecret=\ninherited="}, {Exit: intPointer(0)}},
	}
	data, _ := json.Marshal(spec)
	path := filepath.Join(root, "spec.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	if err := Run(path, false, &bytes.Buffer{}); err != nil {
		t.Fatal(err)
	}
}

func TestInheritedEnvironment(t *testing.T) {
	t.Setenv("PLAYTESTR_INHERITED", "selected")
	err := runConfiguredHelperSpec(t, "cwd-env", []Step{{Expect: "inherited=selected"}, {Exit: intPointer(0)}}, func(spec *Spec) {
		spec.InheritEnv = []string{"PLAYTESTR_INHERITED"}
	})
	if err != nil {
		t.Fatal(err)
	}
}

func TestChildProcessCleanup(t *testing.T) {
	for _, mode := range []string{"parent-child", "parent-exits-child"} {
		t.Run(mode, func(t *testing.T) {
			pidFile := filepath.Join(t.TempDir(), "child.pid")
			steps := []Step{{Expect: "child started"}, {Exit: intPointer(0)}}
			if mode == "parent-child" {
				steps = []Step{{Expect: "child started"}, {Expect: "never"}}
			}
			err := runConfiguredHelperSpec(t, mode, steps, func(spec *Spec) {
				spec.Env["PLAYTESTR_PID_FILE"] = pidFile
				if mode == "parent-child" {
					spec.TimeoutMS = 300
				}
			})
			if mode == "parent-child" && err == nil {
				t.Fatal("expected assertion timeout")
			}
			pidBytes, readErr := os.ReadFile(pidFile)
			if readErr != nil {
				t.Fatal(readErr)
			}
			pid, parseErr := strconv.Atoi(string(pidBytes))
			if parseErr != nil {
				t.Fatal(parseErr)
			}
			deadline := time.Now().Add(time.Second)
			for processExists(pid) && time.Now().Before(deadline) {
				time.Sleep(10 * time.Millisecond)
			}
			if processExists(pid) {
				t.Fatalf("child process %d survived cleanup", pid)
			}
		})
	}
}

func TestRepeatedSessionCleanup(t *testing.T) {
	for attempt := 0; attempt < 5; attempt++ {
		pidFile := filepath.Join(t.TempDir(), "target.pid")
		err := runConfiguredHelperSpec(t, "self-hang", []Step{{Expect: "never"}}, func(spec *Spec) {
			spec.Env["PLAYTESTR_PID_FILE"] = pidFile
			spec.TimeoutMS = 100
		})
		if err == nil {
			t.Fatal("expected assertion timeout")
		}
		pidBytes, readErr := os.ReadFile(pidFile)
		if readErr != nil {
			t.Fatal(readErr)
		}
		pid, parseErr := strconv.Atoi(string(pidBytes))
		if parseErr != nil {
			t.Fatal(parseErr)
		}
		if processExists(pid) {
			t.Fatalf("attempt %d left target process %d running", attempt+1, pid)
		}
	}
}

func TestSessionStopIsIdempotent(t *testing.T) {
	session, err := startTerminalSession(sessionConfig{
		command: []string{os.Args[0], "-test.run=TestHelperProcess", "--", "hang"},
		env:     targetEnvironment(Spec{Env: map[string]string{"PLAYTESTR_HELPER_PROCESS": "1"}}),
		width:   40, height: 8, maxOutputBytes: 100000,
	})
	if err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	first := session.stop(ctx)
	second := session.stop(ctx)
	if first.err != nil || second.err != nil {
		t.Fatalf("cleanup errors: first=%v second=%v", first.err, second.err)
	}
	if first != second {
		t.Fatalf("stop result changed: first=%+v second=%+v", first, second)
	}
}

func TestBlockedInputHonorsContext(t *testing.T) {
	session, err := startTerminalSession(sessionConfig{
		command: []string{os.Args[0], "-test.run=TestHelperProcess", "--", "no-output"},
		env:     targetEnvironment(Spec{Env: map[string]string{"PLAYTESTR_HELPER_PROCESS": "1"}}),
		width:   40, height: 8, maxOutputBytes: 100000,
	})
	if err != nil {
		t.Fatal(err)
	}
	writeContext, cancelWrite := context.WithTimeout(context.Background(), 50*time.Millisecond)
	err = session.send(writeContext, strings.Repeat("x", 64*1024*1024))
	cancelWrite()
	cleanupContext, cancelCleanup := context.WithTimeout(context.Background(), 3*time.Second)
	cleanup := session.stop(cleanupContext)
	cancelCleanup()
	if !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("send returned %v", err)
	}
	if cleanup.err != nil {
		t.Fatal(cleanup.err)
	}
}

func TestTargetObservesResize(t *testing.T) {
	for _, size := range []TerminalSize{{Width: 60, Height: 10}, {Width: 20, Height: 5}} {
		t.Run(fmt.Sprintf("%dx%d", size.Width, size.Height), func(t *testing.T) {
			err := runConfiguredHelperSpec(t, "resize", []Step{
				{Expect: "resize ready"},
				{Resize: &size},
				{Key: "Enter"},
				{Expect: fmt.Sprintf("resized %dx%d", size.Width, size.Height)},
				{Exit: intPointer(0)},
			}, func(_ *Spec) {})
			if err != nil {
				t.Fatal(err)
			}
		})
	}
}

func runConfiguredHelperSpecContext(t *testing.T, ctx context.Context, mode string, steps []Step, configure func(*Spec)) error {
	t.Helper()
	spec := Spec{
		Name: mode, Command: []string{os.Args[0], "-test.run=TestHelperProcess", "--", mode},
		Env: map[string]string{"PLAYTESTR_HELPER_PROCESS": "1"}, Width: 40, Height: 8,
		TimeoutMS: 5000, RunTimeoutMS: 5000, MaxOutputBytes: 2_000_000, Steps: steps,
	}
	configure(&spec)
	data, _ := json.Marshal(spec)
	path := filepath.Join(t.TempDir(), "spec.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	return RunContext(ctx, path, false, &bytes.Buffer{})
}
