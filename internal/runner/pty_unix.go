//go:build !windows && !darwin

package runner

import (
	"os/exec"

	"github.com/charmbracelet/x/xpty"
)

// unixTerminalPty releases the parent's slave after the child inherits it.
// Keeping that duplicate open prevents the master reader from reaching EOF
// when the target and its descendants finish, forcing a full drain timeout.
type unixTerminalPty struct {
	*pollingUnixPTY
}

func newTerminalPty(width, height int) (xpty.Pty, error) {
	p, err := newPollingUnixPTY(width, height)
	if err != nil {
		return nil, err
	}
	return &unixTerminalPty{pollingUnixPTY: p}, nil
}

func (p *unixTerminalPty) Start(cmd *exec.Cmd) error {
	if err := p.UnixPty.Start(cmd); err != nil {
		return err
	}
	p.releaseParentSlave()
	return nil
}
