//go:build windows

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"testing"
	"time"

	"golang.org/x/sys/windows"
)

func TestCLIWindowsInheritedInterruptHelper(t *testing.T) {
	switch os.Getenv("PLAYTESTR_WINDOWS_INTERRUPT_ROLE") {
	case "parent":
		proc := windows.NewLazySystemDLL("kernel32.dll").NewProc("SetConsoleCtrlHandler")
		if ok, _, err := proc.Call(0, 1); ok == 0 {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(21)
		}
		ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
		defer cancel()
		command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestCLIWindowsInheritedInterruptHelper$")
		command.Env = append(os.Environ(), "PLAYTESTR_WINDOWS_INTERRUPT_ROLE=cli")
		command.Stdout, command.Stderr = os.Stdout, os.Stderr
		command.WaitDelay = time.Second
		if err := command.Run(); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(22)
		}
		os.Exit(0)
	case "cli":
		os.Args = []string{os.Args[0], "test", os.Getenv("PLAYTESTR_WINDOWS_INTERRUPT_SPEC")}
		main()
	case "target":
		interrupt := make(chan os.Signal, 1)
		signal.Notify(interrupt, os.Interrupt)
		fmt.Print("NATIVE-INTERRUPT-READY\r\n")
		select {
		case <-interrupt:
			fmt.Print("NATIVE-INTERRUPT-OBSERVED\r\n")
			os.Exit(7)
		case <-time.After(20 * time.Second):
			os.Exit(23)
		}
	}
}

func TestCLIWindowsTargetReceivesCtrlCFromIgnoringAncestor(t *testing.T) {
	folder := t.TempDir()
	spec := filepath.Join(folder, "interrupt.json")
	value := map[string]any{
		"version": 1, "name": "native inherited interrupt",
		"command":    []string{os.Args[0], "-test.run=^TestCLIWindowsInheritedInterruptHelper$"},
		"env":        map[string]string{"PLAYTESTR_WINDOWS_INTERRUPT_ROLE": "target"},
		"timeout_ms": 2000, "run_timeout_ms": 8000,
		"steps": []any{map[string]any{"expect": "NATIVE-INTERRUPT-READY"}, map[string]any{"key": "CtrlC"}, map[string]any{"exit": 7}},
	}
	data, err := json.Marshal(value)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(spec, data, 0600); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	command := exec.CommandContext(ctx, os.Args[0], "-test.run=^TestCLIWindowsInheritedInterruptHelper$")
	command.Env = append(os.Environ(), "PLAYTESTR_WINDOWS_INTERRUPT_ROLE=parent", "PLAYTESTR_WINDOWS_INTERRUPT_SPEC="+spec)
	command.Dir = folder
	command.WaitDelay = time.Second
	output, err := command.CombinedOutput()
	if err != nil {
		t.Fatalf("real CLI inherited-interrupt path failed: %v\n%s", err, output)
	}
}
