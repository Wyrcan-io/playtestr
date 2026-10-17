package runner

import (
	"bytes"
	"io"
	"unicode/utf8"

	"github.com/Wyrcan-io/playtestr/internal/terminal/vt10x"
)

// screenEmulator keeps partial UTF-8 runes between PTY reads. vt10x keeps VT
// parser state across writes, but its Write method does not retain an incomplete
// rune at the end of a write.
type screenEmulator struct {
	terminal       vt10x.Terminal
	pending        []byte
	primaryReplies []byte
	replyError     error
}

func newScreenEmulator(width, height int) *screenEmulator {
	e := &screenEmulator{}
	e.terminal = vt10x.New(vt10x.WithSize(width, height), vt10x.WithWriter(primaryReplyCollector{e}))
	return e
}

// The PTY reader supplies at most 8192 bytes per batch. Even all-DA input
// generates fewer than 16 KiB of replies. Keep the collector independently
// bounded for direct emulator users and retain an overflow as an error.
type primaryReplyCollector struct{ emulator *screenEmulator }

func (w primaryReplyCollector) Write(value []byte) (int, error) {
	if !bytes.Equal(value, []byte("\x1b[?6c")) {
		return len(value), nil
	}
	if len(w.emulator.primaryReplies)+len(value) > 16*1024 {
		w.emulator.replyError = io.ErrShortBuffer
		return 0, io.ErrShortBuffer
	}
	w.emulator.primaryReplies = append(w.emulator.primaryReplies, value...)
	return len(value), nil
}

func (e *screenEmulator) takePrimaryReplies() ([]byte, error) {
	value, err := e.primaryReplies, e.replyError
	e.primaryReplies, e.replyError = nil, nil
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
