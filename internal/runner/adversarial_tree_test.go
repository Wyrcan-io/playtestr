package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"testing"
	"time"
)

// This target deliberately inherits the real PTY in both descendant generations.
// It proves cleanup beyond the direct child, including a naturally exited parent.
func TestAdversarialTreeHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_ADVERSARIAL_HELPER") != "1" {
		return
	}
	mode := os.Getenv("PLAYTESTR_TREE_ROLE")
	root := os.Getenv("PLAYTESTR_TREE_STATE")
	if mode == "grandchild" {
		_ = os.WriteFile(filepath.Join(root, "grandchild.pid"), []byte(strconv.Itoa(os.Getpid())), 0600)
		fmt.Print("grandchild retains real PTY\r\n")
		time.Sleep(30 * time.Second)
		os.Exit(0)
	}
	// This control exercises descendants after process-tree attachment. The
	// separate immediate-startup control must also prove the launch boundary.
	time.Sleep(200 * time.Millisecond)
	role := "child"
	if mode == "child" {
		_ = os.WriteFile(filepath.Join(root, "child.pid"), []byte(strconv.Itoa(os.Getpid())), 0600)
		role = "grandchild"
	}
	child := exec.Command(os.Args[0], "-test.run=^TestAdversarialTreeHelper$")
	child.Env = append(os.Environ(), "PLAYTESTR_TREE_ROLE="+role)
	child.Stdin, child.Stdout, child.Stderr = os.Stdin, os.Stdout, os.Stderr
	if err := child.Start(); err != nil {
		fmt.Printf("descendant launch failed: %v\r\n", err)
		os.Exit(8)
	}
	if mode == "child" {
		time.Sleep(30 * time.Second)
		os.Exit(0)
	}
	deadline := time.Now().Add(5 * time.Second)
	for time.Now().Before(deadline) {
		if _, err := os.Stat(filepath.Join(root, "grandchild.pid")); err == nil {
			fmt.Print("two-generation process tree ready\r\n")
			if mode == "parent-exits" {
				os.Exit(0)
			}
			time.Sleep(30 * time.Second)
			os.Exit(0)
		}
		time.Sleep(10 * time.Millisecond)
	}
	os.Exit(9)
}

func TestAdversarialGrandchildAndRetainedPTYCleanup(t *testing.T) {
	for _, mode := range []string{"parent-exits", "parent-times-out"} {
		t.Run(mode, func(t *testing.T) {
			root := t.TempDir()
			steps := []Step{{Expect: "two-generation process tree ready"}, {Exit: intPointer(0)}}
			if mode == "parent-times-out" {
				steps[1] = Step{Expect: "deliberately absent"}
			}
			spec := Spec{Version: SpecVersion, Command: []string{os.Args[0], "-test.run=^TestAdversarialTreeHelper$"},
				Env:   map[string]string{"PLAYTESTR_ADVERSARIAL_HELPER": "1", "PLAYTESTR_TREE_STATE": root, "PLAYTESTR_TREE_ROLE": mode},
				Width: 80, Height: 10, TimeoutMS: 3000, RunTimeoutMS: 15000, MaxOutputBytes: 100000, Steps: steps}
			data, err := json.Marshal(spec)
			if err != nil {
				t.Fatal(err)
			}
			path := filepath.Join(root, "tree.json")
			if err := os.WriteFile(path, data, 0600); err != nil {
				t.Fatal(err)
			}
			result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
			if mode == "parent-exits" && result.Err() != nil {
				t.Fatalf("natural parent exit with inherited descendant PTYs: %v", result.Err())
			}
			if mode == "parent-times-out" && (result.Failure == nil || result.Failure.Category != FailureAssertionTimeout) {
				t.Fatalf("expected bounded assertion timeout: %+v", result)
			}
			if !result.Cleanup.ConfirmedExited {
				t.Fatalf("process tree exit unconfirmed: %+v", result.Cleanup)
			}
			for _, name := range []string{"child.pid", "grandchild.pid"} {
				value, err := os.ReadFile(filepath.Join(root, name))
				if err != nil {
					t.Fatal(err)
				}
				pid, err := strconv.Atoi(string(value))
				if err != nil {
					t.Fatal(err)
				}
				deadline := time.Now().Add(2 * time.Second)
				for processExists(pid) && time.Now().Before(deadline) {
					time.Sleep(10 * time.Millisecond)
				}
				if processExists(pid) {
					t.Fatalf("%s process %d survived confirmed cleanup", name, pid)
				}
			}
		})
	}
}
