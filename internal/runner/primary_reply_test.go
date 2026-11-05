package runner

import (
	"errors"
	"io"
	"strings"
	"testing"
)

func TestTerminalReplyCollectorReturnsBoundedSupportedQueriesOnly(t *testing.T) {
	e := newScreenEmulator(80, 24)
	e.Write([]byte("termX\x1b[6n\x1b[5n\x1b]10;?\x07\x1b]11;?\x07\x1b]4;1;?\x07\x1b[>c\x1b[c"))
	replies, err := e.takeTerminalReplies()
	want := "\x1b[1;6R\x1b[0n\x1b]10;rgb:0000/0000/0000\x07\x1b]11;rgb:0000/0000/0101\x07\x1b[?6c"
	if err != nil || string(replies) != want || !strings.Contains(normalize(e.String()), "X") {
		t.Fatalf("replies=%q error=%v screen=%q", replies, err, e.String())
	}
	if again, err := e.takeTerminalReplies(); len(again) != 0 || err != nil {
		t.Fatalf("reply was duplicated: %q %v", again, err)
	}
}

func TestSupportedTerminalReplyRejectsMalformedOrUnsupportedResponses(t *testing.T) {
	for _, value := range []string{
		"\x1b[999999;1R", "\x1b[0;1R", "\x1b[1;1Rextra", "\x1b[1;;1R", "\x1b]4;1;rgb:0000/0000/0000\x07",
		"\x1b]10;rgb:gggg/0000/0000\x07", "\x1b]11;rgb:0000/0000/0101\x1b\\", "\x1b[?6n",
	} {
		if supportedTerminalReply([]byte(value)) {
			t.Fatalf("unexpectedly accepted terminal reply %q", value)
		}
	}
}

func TestTerminalReplyCollectorRetainsBoundError(t *testing.T) {
	e := newScreenEmulator(80, 24)
	e.Write([]byte(strings.Repeat("\x1b[c", 4000)))
	replies, err := e.takeTerminalReplies()
	if len(replies) > 16*1024 || !errors.Is(err, io.ErrShortBuffer) {
		t.Fatalf("unbounded or silent reply overflow: bytes=%d error=%v", len(replies), err)
	}
}
