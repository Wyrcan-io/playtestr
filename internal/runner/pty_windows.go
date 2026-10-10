package runner

import "github.com/charmbracelet/x/xpty"

func newTerminalPty(width, height int) (xpty.Pty, error) {
	p, err := xpty.NewPty(width, height)
	if err != nil {
		return nil, err
	}
	return &windowsResizePty{Pty: p}, nil
}
