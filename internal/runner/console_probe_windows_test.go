//go:build windows

package runner

import (
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"syscall"
	"testing"
	"time"

	"golang.org/x/sys/windows"
)

func TestWindowsConsoleProbeRejectsInvalidIdentityAndProtocol(t *testing.T) {
	valid := "console-size-v1 12 345 100 28 100 28\n"
	got, err := parseConsoleDimensions([]byte(valid), 12, 345)
	if err != nil || got.buffer.Width != 100 || got.viewport.Height != 28 {
		t.Fatalf("valid dimensions rejected: %+v %v", got, err)
	}
	for _, value := range []string{"", strings.Replace(valid, "12 345", "13 345", 1), strings.Replace(valid, "12 345", "12 346", 1),
		strings.Replace(valid, "100 28 100 28", "0 28 100 28", 1), strings.Replace(valid, "100 28 100 28", "100 28 100 40000", 1), valid + "extra", strings.Replace(valid, "100 28", "-1 28", 1)} {
		if _, err := parseConsoleDimensions([]byte(value), 12, 345); err == nil {
			t.Fatal("invalid native protocol accepted")
		}
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	birth, err := windowsProcessBirth(uint32(os.Getpid()))
	if err != nil {
		t.Fatal(err)
	}
	// The child must reject this identity before attaching to the parent's console.
	if _, err := probeWindowsConsole(ctx, uint32(os.Getpid()), birth+1); err == nil {
		t.Fatal("stale process identity accepted")
	}
}

func TestWindowsConsoleProbeFailureHelper(t *testing.T) {
	mode := os.Getenv("PLAYTESTR_CONSOLE_FAILURE_HELPER")
	if mode == "" {
		return
	}
	switch mode {
	case "exit":
		os.Exit(7)
	case "flood":
		fmt.Print(strings.Repeat("x", 8192))
		os.Exit(0)
	case "hang":
		fmt.Print("probe-child-ready")
		time.Sleep(time.Minute)
		os.Exit(0)
	default:
		os.Exit(9)
	}
}

func TestWindowsConsoleProbeChildFailureFloodAndCancellationAreBounded(t *testing.T) {
	for _, mode := range []string{"exit", "flood", "hang"} {
		t.Run(mode, func(t *testing.T) {
			ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer cancel()
			cmd := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestWindowsConsoleProbeFailureHelper$")
			cmd.Env = []string{"PLAYTESTR_CONSOLE_FAILURE_HELPER=" + mode, "SYSTEMROOT=" + os.Getenv("SYSTEMROOT")}
			cmd.SysProcAttr = &syscall.SysProcAttr{CreationFlags: windows.DETACHED_PROCESS, HideWindow: true}
			started := time.Now()
			_, err := runConsoleProbeCommand(ctx, cmd, 12, 345)
			if err == nil {
				t.Fatal("failed/flooding/canceled helper supplied passing evidence")
			}
			if mode == "hang" && !errors.Is(err, context.DeadlineExceeded) {
				t.Fatalf("lost cancellation cause: %v", err)
			}
			if cmd.Process == nil || cmd.ProcessState == nil || !cmd.ProcessState.Exited() {
				t.Fatal("query child not confirmed reaped")
			}
			if time.Since(started) > 5*time.Second {
				t.Fatal("helper exceeded context cleanup bound")
			}
		})
	}
}
