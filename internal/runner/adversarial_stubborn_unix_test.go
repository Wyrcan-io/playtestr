//go:build !windows

package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"os/signal"
	"path/filepath"
	"strconv"
	"syscall"
	"testing"
	"time"
)

func publishStubbornHeartbeat(path string, value []byte, beforeWrite func()) error {
	// A reader must retain the last complete heartbeat while the next value is
	// being written. Truncating the published file exposes an empty checkpoint.
	staging := path + ".next"
	file, err := os.OpenFile(staging, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	defer func() {
		_ = file.Close()
		_ = os.Remove(staging)
	}()
	if beforeWrite != nil {
		beforeWrite()
	}
	if _, err := file.Write(value); err != nil {
		return err
	}
	if err := file.Close(); err != nil {
		return err
	}
	return os.Rename(staging, path)
}

func TestAdversarialStubbornHeartbeatPublication(t *testing.T) {
	path := filepath.Join(t.TempDir(), "child.heartbeat")
	if err := os.WriteFile(path, []byte("7"), 0600); err != nil {
		t.Fatal(err)
	}
	err := publishStubbornHeartbeat(path, []byte("8"), func() {
		value, err := os.ReadFile(path)
		if err != nil || string(value) != "7" {
			t.Errorf("previous heartbeat disappeared before replacement: value=%q error=%v", value, err)
		}
	})
	if err != nil {
		t.Fatal(err)
	}
	value, err := os.ReadFile(path)
	if err != nil || string(value) != "8" {
		t.Fatalf("replacement heartbeat missing: value=%q error=%v", value, err)
	}
}

func TestAdversarialStubbornUnixHelper(t *testing.T) {
	role := os.Getenv("PLAYTESTR_STUBBORN_ROLE")
	if role == "" {
		return
	}
	root := os.Getenv("PLAYTESTR_STUBBORN_STATE")
	if role != "parent" {
		// A controlling-terminal leader's exit must not end the children before
		// Playtestr's process-group cleanup is exercised.
		signal.Ignore(syscall.SIGTERM, syscall.SIGHUP)
		if err := os.WriteFile(filepath.Join(root, role+".pid"), []byte(strconv.Itoa(os.Getpid())), 0600); err != nil {
			fmt.Fprintf(os.Stderr, "stubborn helper: write %s PID: %v\n", role, err)
			os.Exit(8)
		}
	}
	if role != "grandchild" {
		next := "child"
		if role == "child" {
			next = "grandchild"
		}
		child := exec.Command(os.Args[0], "-test.run=^TestAdversarialStubbornUnixHelper$")
		child.Env = append(os.Environ(), "PLAYTESTR_STUBBORN_ROLE="+next)
		child.Stdin, child.Stdout, child.Stderr = os.Stdin, os.Stdout, os.Stderr
		if err := child.Start(); err != nil {
			fmt.Fprintf(os.Stderr, "stubborn helper: start %s: %v\n", next, err)
			os.Exit(8)
		}
	}
	if role != "parent" {
		deadline := time.Now().Add(30 * time.Second)
		for counter := 1; time.Now().Before(deadline); counter++ {
			if err := publishStubbornHeartbeat(filepath.Join(root, role+".heartbeat"), []byte(strconv.Itoa(counter)), nil); err != nil {
				fmt.Fprintf(os.Stderr, "stubborn helper: publish %s heartbeat: %v\n", role, err)
				os.Exit(8)
			}
			time.Sleep(25 * time.Millisecond)
		}
		os.Exit(0)
	}
	read := func(name string) int {
		value, err := os.ReadFile(filepath.Join(root, name))
		if err != nil || len(value) > 32 {
			return 0
		}
		n, _ := strconv.Atoi(string(value))
		return n
	}
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if read("child.pid") > 0 && read("grandchild.pid") > 0 && read("child.heartbeat") > 0 && read("grandchild.heartbeat") > 0 {
			break
		}
		time.Sleep(10 * time.Millisecond)
	}
	previous := map[string]int{}
	for _, name := range []string{"child", "grandchild"} {
		pid := read(name + ".pid")
		previous[name] = read(name + ".heartbeat")
		if pid <= 0 || previous[name] <= 0 {
			fmt.Fprintf(os.Stderr, "stubborn helper: invalid %s checkpoint: pid=%d heartbeat=%d\n", name, pid, previous[name])
			os.Exit(8)
		}
		if err := syscall.Kill(pid, syscall.SIGTERM); err != nil {
			fmt.Fprintf(os.Stderr, "stubborn helper: signal %s PID %d: %v\n", name, pid, err)
			os.Exit(8)
		}
	}
	deadline = time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		// Advancing post-signal heartbeats prove both are executing, not zombies
		// whose PID merely remains visible after a failed cleanup.
		if read("child.heartbeat") >= previous["child"]+4 && read("grandchild.heartbeat") >= previous["grandchild"]+4 {
			fmt.Print("two live generations ignored actual SIGTERM\r\n")
			os.Exit(0)
		}
		time.Sleep(10 * time.Millisecond)
	}
	os.Exit(9)
}

func TestAdversarialStubbornUnixDescendantCleanup(t *testing.T) {
	root := t.TempDir()
	spec := Spec{Version: SpecVersion, Command: []string{os.Args[0], "-test.run=^TestAdversarialStubbornUnixHelper$"},
		Env:   map[string]string{"PLAYTESTR_STUBBORN_ROLE": "parent", "PLAYTESTR_STUBBORN_STATE": root},
		Width: 80, Height: 10, TimeoutMS: 10000, RunTimeoutMS: 15000, MaxOutputBytes: 100000,
		Steps: []Step{{Expect: "two live generations ignored actual SIGTERM"}, {Exit: intPointer(0)}}}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(root, "stubborn.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
	if result.Err() != nil || !result.Cleanup.ConfirmedExited {
		detail, _ := json.Marshal(result)
		screen, screenErr := os.ReadFile(result.Evidence.ScreenPath)
		t.Fatalf("stubborn descendant test failed: error=%v result=%s screen=%q screen_error=%v", result.Err(), detail, screen, screenErr)
	}
	for _, name := range []string{"child", "grandchild"} {
		data, err := os.ReadFile(filepath.Join(root, name+".pid"))
		if err != nil {
			t.Fatal(err)
		}
		pid, err := strconv.Atoi(string(data))
		if err != nil || pid <= 0 {
			t.Fatalf("invalid captured %s PID: %q", name, data)
		}
		deadline := time.Now().Add(2 * time.Second)
		for processExists(pid) && time.Now().Before(deadline) {
			time.Sleep(10 * time.Millisecond)
		}
		if processExists(pid) {
			t.Fatalf("stubborn %s PID %d survived confirmed cleanup", name, pid)
		}
	}
}
