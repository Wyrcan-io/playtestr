package runner

import (
	"strings"
	"testing"

	"github.com/Wyrcan-io/playtestr/internal/terminal/vt10x"
)

func TestRenderedScreenContract(t *testing.T) {
	t.Run("normalization", func(t *testing.T) {
		got := normalize("  leading  \r\n\r\ninside   \r\n\r\n")
		if got != "  leading\n\ninside\n" {
			t.Fatalf("got %q", got)
		}
	})

	t.Run("carriage return cursor movement and erase", func(t *testing.T) {
		terminal := newScreenEmulator(30, 5)
		terminal.Write([]byte("progress 10%\rprogress 100%\x1b[K\r\nsecond\x1b[1A\rfinal\x1b[K"))
		if got := normalize(terminal.String()); got != "final\nsecond\n" {
			t.Fatalf("got %q", got)
		}
	})

	t.Run("split escape sequence", func(t *testing.T) {
		terminal := newScreenEmulator(30, 5)
		terminal.Write([]byte("obsolete"))
		terminal.Write([]byte("\x1b["))
		terminal.Write([]byte("2J\x1b["))
		terminal.Write([]byte("Hready"))
		if got := normalize(terminal.String()); got != "ready\n" {
			t.Fatalf("got %q", got)
		}
	})

	t.Run("split UTF-8", func(t *testing.T) {
		terminal := newScreenEmulator(30, 5)
		terminal.Write([]byte{'c', 'a', 'f', 0xc3})
		terminal.Write([]byte{0xa9, ' ', 0xce})
		terminal.Write([]byte{0xbb})
		if got := normalize(terminal.String()); got != "café λ\n" {
			t.Fatalf("got %q", got)
		}
	})

	t.Run("alternate screen", func(t *testing.T) {
		terminal := newScreenEmulator(30, 5)
		terminal.Write([]byte("main screen"))
		terminal.Write([]byte("\x1b[?1049h\x1b[2J\x1b[Halternate screen"))
		if terminal.Mode()&vt10x.ModeAltScreen == 0 {
			t.Fatal("alternate-screen mode was not entered")
		}
		if got := normalize(terminal.String()); got != "alternate screen\n" {
			t.Fatalf("alternate screen = %q", got)
		}
		terminal.Write([]byte("\x1b[?1049l"))
		if terminal.Mode()&vt10x.ModeAltScreen != 0 {
			t.Fatal("alternate-screen mode was not left")
		}
		if got := normalize(terminal.String()); !strings.HasPrefix(got, "main screen") {
			t.Fatalf("restored screen = %q", got)
		}
	})
}

func TestRenderedWideScreenContract(t *testing.T) {
	t.Run("split bytes and addressed redraw", func(t *testing.T) {
		e := newScreenEmulator(8, 3)
		for _, b := range []byte("  雪 X\x1b[1;6HZ") {
			e.Write([]byte{b})
		}
		if got := normalize(e.String()); got != "  雪 Z\n" {
			t.Fatalf("screen = %q", got)
		}
	})
	t.Run("crop and expand both screens", func(t *testing.T) {
		e := newScreenEmulator(6, 3)
		e.Write([]byte("abc雪\x1b[?1049h\x1b[2J\x1b[H123雪"))
		e.Resize(4, 3)
		e.Resize(8, 3)
		if got := normalize(e.String()); got != "123\n" {
			t.Fatalf("alternate = %q", got)
		}
		e.Write([]byte("\x1b[?1049l"))
		if got := normalize(e.String()); got != "abc\n" {
			t.Fatalf("main = %q", got)
		}
		e.Write([]byte("\x1b[H\x1b[2J雪X"))
		if got := normalize(e.String()); got != "雪X\n" {
			t.Fatalf("redraw = %q", got)
		}
	})
	t.Run("queries do not alter rendered text", func(t *testing.T) {
		e := newScreenEmulator(8, 3)
		e.Write([]byte("雪X\x1b[6n\x1b[c"))
		if got := normalize(e.String()); got != "雪X\n" {
			t.Fatalf("screen = %q", got)
		}
	})
	// NFD combining marks are intentionally still outside the rendering contract.
	// Passing a precomposed accent must not silently broaden that claim.
	t.Run("combining boundary remains explicit", func(t *testing.T) {
		e := newScreenEmulator(8, 3)
		e.Write([]byte("e\u0301X"))
		if c := e.terminal.Cursor(); c.X != 3 {
			t.Fatalf("unexpected combining behavior: %v", c)
		}
	})
}
