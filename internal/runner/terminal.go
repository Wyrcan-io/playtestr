package runner

import (
	"bytes"
	"io"
	"strconv"
	"unicode/utf8"

	"github.com/Wyrcan-io/playtestr/internal/terminal/vt10x"
)

// screenEmulator keeps partial UTF-8 runes between PTY reads. vt10x keeps VT
// parser state across writes, but its Write method does not retain an incomplete
// rune at the end of a write.
type screenEmulator struct {
	terminal        vt10x.Terminal
	pending         []byte
	terminalReplies []byte
	replyError      error
}

func newScreenEmulator(width, height int) *screenEmulator {
	e := &screenEmulator{}
	e.terminal = vt10x.New(vt10x.WithSize(width, height), vt10x.WithWriter(terminalReplyCollector{e}))
	return e
}

// PTY reads are capped at 8192 bytes. Color queries have larger replies, so
// keep collection independently bounded and retain overflow as an error.
type terminalReplyCollector struct{ emulator *screenEmulator }

func (w terminalReplyCollector) Write(value []byte) (int, error) {
	if !supportedTerminalReply(value) {
		return len(value), nil
	}
	if len(w.emulator.terminalReplies)+len(value) > 16*1024 {
		w.emulator.replyError = io.ErrShortBuffer
		return 0, io.ErrShortBuffer
	}
	w.emulator.terminalReplies = append(w.emulator.terminalReplies, value...)
	return len(value), nil
}

// vt10x emits replies for a deliberately small set of terminal queries. Only
// those emulator-generated response shapes are allowed back to the child.
func supportedTerminalReply(value []byte) bool {
	if bytes.Equal(value, []byte("\x1b[?6c")) || bytes.Equal(value, []byte("\x1b[0n")) {
		return true
	}
	if len(value) >= 6 && bytes.HasPrefix(value, []byte("\x1b[")) && value[len(value)-1] == 'R' {
		parts := bytes.Split(value[2:len(value)-1], []byte(";"))
		if len(parts) != 2 {
			return false
		}
		for _, part := range parts {
			if len(part) == 0 || len(part) > 5 {
				return false
			}
			for _, digit := range part {
				if digit < '0' || digit > '9' {
					return false
				}
			}
			position, err := strconv.Atoi(string(part))
			if err != nil || position == 0 {
				return false
			}
		}
		return true
	}
	// OSC 10/11 replies carry the emulator's default foreground/background.
	if len(value) != 24 || value[0] != 0x1b || value[1] != ']' ||
		(value[2] != '1' || (value[3] != '0' && value[3] != '1') || value[4] != ';') ||
		!bytes.HasPrefix(value[5:], []byte("rgb:")) || value[len(value)-1] != 0x07 {
		return false
	}
	for i, b := range value[9 : len(value)-1] {
		if i == 4 || i == 9 || i == 14 {
			if b != '/' {
				return false
			}
		} else if !((b >= '0' && b <= '9') || (b >= 'a' && b <= 'f')) {
			return false
		}
	}
	return true
}

func (e *screenEmulator) takeTerminalReplies() ([]byte, error) {
	value, err := e.terminalReplies, e.replyError
	e.terminalReplies, e.replyError = nil, nil
	return value, err
}

func (e *screenEmulator) Write(chunk []byte) {
	data := make([]byte, 0, len(e.pending)+len(chunk))
	data = append(data, e.pending...)
	data = append(data, chunk...)
	e.pending = e.pending[:0]
	complete := 0
	for complete < len(data) {
		if !utf8.FullRune(data[complete:]) {
			break
		}
		_, size := utf8.DecodeRune(data[complete:])
		complete += size
	}
	if complete > 0 {
		_, _ = e.terminal.Write(data[:complete])
	}
	if complete < len(data) {
		e.pending = append(e.pending, data[complete:]...)
	}
}

func (e *screenEmulator) String() string {
	return e.terminal.String()
}

func (e *screenEmulator) LastAlternateScreen() string {
	return e.terminal.LastAlternateScreen()
}

func (e *screenEmulator) Rows() int {
	_, rows := e.terminal.Size()
	return rows
}

func (e *screenEmulator) Resize(width, height int) {
	e.terminal.Resize(width, height)
}

func (e *screenEmulator) Mode() vt10x.ModeFlag {
	return e.terminal.Mode()
}
