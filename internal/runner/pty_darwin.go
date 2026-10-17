package runner

import "github.com/charmbracelet/x/xpty"

// macOS can discard unread output when the last slave descriptor closes. Keep
// the parent's slave until ordinary bounded session cleanup. Linux releases
// that duplicate at startup; both hosts share bounded native read/write polling.
func newTerminalPty(width, height int) (xpty.Pty, error) {
	return newPollingUnixPTY(width, height)
}
