//go:build windows

package runner

import (
	"context"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"testing"
	"time"

	"github.com/charmbracelet/x/xpty"
	"golang.org/x/sys/windows"
)

// A real backend with a delayed Start return makes the scheduling window
// deterministic. The target itself forks immediately, without a startup sleep.
type delayedStartPTY struct{ xpty.Pty }

func (p delayedStartPTY) Start(cmd *exec.Cmd) error {
	if err := p.Pty.Start(cmd); err != nil {
		return err
	}
	time.Sleep(time.Second)
	return nil
}

func TestAdversarialDetachedStartupHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_DETACHED_STARTUP") != "1" {
		return
	}
	root, role := os.Getenv("PLAYTESTR_TREE_STATE"), os.Getenv("PLAYTESTR_TREE_ROLE")
	if role != "parent" {
		if err := os.WriteFile(filepath.Join(root, role+".pid"), []byte(strconv.Itoa(os.Getpid())), 0600); err != nil {
			os.Exit(8)
		}
	}
	if role != "grandchild" {
		next := "child"
		if role == "child" {
			next = "grandchild"
		}
		child := exec.Command(os.Args[0], "-test.run=^TestAdversarialDetachedStartupHelper$")
		child.Env = append(os.Environ(), "PLAYTESTR_TREE_ROLE="+next)
		child.SysProcAttr = &syscall.SysProcAttr{CreationFlags: windows.CREATE_NO_WINDOW}
		if err := child.Start(); err != nil {
			os.Exit(9)
		}
	}
	if role == "parent" {
		deadline := time.Now().Add(5 * time.Second)
		for time.Now().Before(deadline) {
			if _, err := os.Stat(filepath.Join(root, "grandchild.pid")); err == nil {
				fmt.Print("two-generation process tree ready\r\n")
				break
			}
			time.Sleep(5 * time.Millisecond)
		}
	}
	time.Sleep(30 * time.Second)
	os.Exit(0)
}

func TestAdversarialWindowsImmediateDescendantsCannotEscapeStartup(t *testing.T) {
	root := t.TempDir()
	backend, err := newTerminalPty(80, 24)
	if err != nil {
		t.Fatal(err)
	}
	s, err := startTerminalSessionWithPTY(sessionConfig{
		command: []string{os.Args[0], "-test.run=^TestAdversarialDetachedStartupHelper$"},
		env: append(os.Environ(), "PLAYTESTR_DETACHED_STARTUP=1",
			"PLAYTESTR_TREE_ROLE=parent", "PLAYTESTR_TREE_STATE="+root),
		width: 80, height: 24, maxOutputBytes: 100000,
	}, delayedStartPTY{backend})
	if err != nil {
		t.Fatal(err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		s.stop(ctx)
	}()
	deadline := time.Now().Add(5 * time.Second)
	for !strings.Contains(s.observe().screen, "two-generation process tree ready") && time.Now().Before(deadline) {
		time.Sleep(5 * time.Millisecond)
	}
	if !strings.Contains(s.observe().screen, "two-generation process tree ready") {
		t.Fatal("immediate descendant target did not reach positive readiness")
	}
	// Keep handles to the exact observed processes across cleanup, avoiding PID
	// reuse and independently terminating them if the product regression escapes.
	var handles []windows.Handle
	defer func() {
		for _, handle := range handles {
			_ = windows.TerminateProcess(handle, 1)
			state, err := windows.WaitForSingleObject(handle, 3000)
			if err != nil || state != windows.WAIT_OBJECT_0 {
				t.Errorf("independent exact-handle fallback cleanup unconfirmed: %d, %v", state, err)
			}
			_ = windows.CloseHandle(handle)
		}
	}()
	for _, name := range []string{"child.pid", "grandchild.pid"} {
		data, err := os.ReadFile(filepath.Join(root, name))
		if err != nil {
			t.Fatal(err)
		}
		pid, err := strconv.Atoi(string(data))
		if err != nil {
			t.Fatal(err)
		}
		handle, err := windows.OpenProcess(windows.SYNCHRONIZE|windows.PROCESS_TERMINATE, false, uint32(pid))
		if err != nil {
			t.Fatal(err)
		}
		handles = append(handles, handle)
		t.Logf("independent observed %s pid=%d", name, pid)
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	result := s.stop(ctx)
	if !result.confirmedExited || result.err != nil {
		t.Errorf("startup cleanup result: %+v", result)
	}
	for index, handle := range handles {
		state, err := windows.WaitForSingleObject(handle, 2000)
		if err != nil || state != windows.WAIT_OBJECT_0 {
			t.Errorf("descendant %d survived cleanup reported confirmed=%v: wait=%d error=%v", index, result.confirmedExited, state, err)
		}
	}
}
