package runner

import (
	"unicode/utf8"

	"github.com/hinshun/vt10x"
)

// screenEmulator keeps partial UTF-8 runes between PTY reads. vt10x keeps VT
// parser state across writes, but its Write method does not retain an incomplete
// rune at the end of a write.
type screenEmulator struct {
	terminal vt10x.Terminal
	pending  []byte
}

func newScreenEmulator(width, height int) *screenEmulator {
	return &screenEmulator{terminal: vt10x.New(vt10x.WithSize(width, height))}
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

func (e *screenEmulator) Resize(width, height int) {
	e.terminal.Resize(width, height)
}

func (e *screenEmulator) Mode() vt10x.ModeFlag {
	return e.terminal.Mode()
}
