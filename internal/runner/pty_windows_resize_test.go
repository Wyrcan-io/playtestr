//go:build windows

package runner

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"
)

func TestWindowsResizeRepliesRequireCurrentDimensions(t *testing.T) {
	for _, test := range []struct {
		name, stream string
		acknowledged bool
	}{
		{"current", "\x1b[8;30;100t", true},
		{"stale", "\x1b[8;24;80t", false},
		{"dimensions reversed", "\x1b[8;100;30t", false},
		{"other window operation", "\x1b[4;30;100t", false},
		{"incomplete", "\x1b[8;30;100", false},
		{"fake title", "\x1b]0;\x1b[8;30;100t\a", false},
		{"fake DCS", "\x1bP\x1b[8;30;100t\x1b\\", false},
		{"after title", "\x1b]0;title\a\x1b[8;30;100t", true},
		{"oversized", "\x1b[8;" + strings.Repeat("0", 10000) + "30;100t", false},
		{"canceled", "\x1b[8;30;100\x18t", false},
		{"repeated acknowledgment", "\x1b[8;30;100t\x1b[8;30;100t", true},
	} {
		t.Run(test.name, func(t *testing.T) {
			p := &windowsResizePty{request: &consoleResizeRequest{width: 100, height: 30, done: make(chan struct{})}}
			for _, b := range []byte(test.stream) {
				p.observeResize([]byte{b})
			}
			select {
			case <-p.request.done:
				if !test.acknowledged {
					t.Fatal("unrelated output falsely completed a resize")
				}
			default:
				if test.acknowledged {
					t.Fatal("actual current acknowledgment not observed")
				}
			}
			if len(p.csi) > 32 {
				t.Fatal("protocol capture exceeds bound")
			}
		})
	}
}

func TestWindowsResizeWithoutAcknowledgmentIsBounded(t *testing.T) {
	p := &windowsResizePty{request: &consoleResizeRequest{width: 100, height: 30, done: make(chan struct{})}}
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Millisecond)
	defer cancel()
	if err := p.AwaitResize(ctx); !errors.Is(err, context.DeadlineExceeded) {
		t.Fatalf("unacknowledged resize returned %v", err)
	}
}
