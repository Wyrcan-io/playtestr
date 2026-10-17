package runner

import (
	"errors"
	"io"
	"strings"
	"testing"
)

func TestPrimaryReplyCollectorKeepsOtherQueriesUnsupported(t *testing.T) {
	e := newScreenEmulator(80, 24)
	e.Write([]byte("雪X\x1b[6n\x1b[5n\x1b]10;?\x07\x1b]4;1;?\x07\x1b[>c\x1b[c"))
	replies, err := e.takePrimaryReplies()
	if err != nil || string(replies) != "\x1b[?6c" || normalize(e.String()) != "雪X\n" {
		t.Fatalf("replies=%q error=%v screen=%q", replies, err, e.String())
	}
	if again, err := e.takePrimaryReplies(); len(again) != 0 || err != nil {
		t.Fatalf("reply was duplicated: %q %v", again, err)
	}
}

func TestPrimaryReplyCollectorRetainsBoundError(t *testing.T) {
	e := newScreenEmulator(80, 24)
	e.Write([]byte(strings.Repeat("\x1b[c", 4000)))
	replies, err := e.takePrimaryReplies()
	if len(replies) > 16*1024 || !errors.Is(err, io.ErrShortBuffer) {
		t.Fatalf("unbounded or silent reply overflow: bytes=%d error=%v", len(replies), err)
	}
}
