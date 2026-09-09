//go:build !windows

package runner

import (
	"errors"
	"os/exec"
	"syscall"
)

type processTree struct {
	pid int
}

func configureProcess(cmd *exec.Cmd) {
	// Start the target in its own session and make the PTY slave attached to
	// stdin its controlling terminal. Some full-screen applications open
	// /dev/tty directly instead of relying only on stdin/stdout.
	cmd.SysProcAttr = &syscall.SysProcAttr{Setsid: true, Setctty: true, Ctty: 0}
}

func attachProcessTree(pid int) (*processTree, error) {
	return &processTree{pid: pid}, nil
}

func (t *processTree) active() (bool, error) {
	err := syscall.Kill(-t.pid, 0)
	if err == nil || errors.Is(err, syscall.EPERM) {
		return true, nil
	}
	if errors.Is(err, syscall.ESRCH) {
		return false, nil
	}
	return false, err
}

func (t *processTree) terminate() error {
	err := syscall.Kill(-t.pid, syscall.SIGKILL)
	if errors.Is(err, syscall.ESRCH) {
		return nil
	}
	return err
}

func (t *processTree) close() error { return nil }

func (t *processTree) mechanism() string { return "unix-process-group" }

func processExists(pid int) bool {
	err := syscall.Kill(pid, 0)
	return err == nil || errors.Is(err, syscall.EPERM)
}
