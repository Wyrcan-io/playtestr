package runner

import (
	"strings"
	"testing"

	"github.com/hinshun/vt10x"
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
