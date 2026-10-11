//go:build windows

package runner

import (
	"context"
	"errors"
	"strings"
	"testing"
	"time"

	"github.com/charmbracelet/x/xpty"
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

type resizeFenceReader struct {
	xpty.Pty
	entered chan struct{}
	release chan struct{}
}

func (p *resizeFenceReader) Read(value []byte) (int, error) {
	close(p.entered)
	<-p.release
	return copy(value, "ordinary output"), nil
}

func TestWindowsResizeOutputFenceRequiresReturnedCurrentRequest(t *testing.T) {
	for _, kind := range []string{"before-return", "current-after-return", "superseded"} {
		t.Run(kind, func(t *testing.T) {
			reader := &resizeFenceReader{entered: make(chan struct{}), release: make(chan struct{})}
			request := &consoleResizeRequest{done: make(chan struct{}), returned: kind != "before-return"}
			p := &windowsResizePty{Pty: reader, request: request}
			done := make(chan struct{})
			go func() { defer close(done); _, _ = p.Read(make([]byte, 100)) }()
			<-reader.entered
			p.mu.Lock()
			if kind == "superseded" {
				p.request = &consoleResizeRequest{done: make(chan struct{}), returned: true}
			} else {
				request.returned = true
			}
			p.mu.Unlock()
			close(reader.release)
			<-done
			select {
			case <-p.request.done:
				if kind != "current-after-return" {
					t.Fatal("old output completed a newer or not-yet-returned resize")
				}
			default:
				if kind == "current-after-return" {
					t.Fatal("post-return output did not complete current transport fence")
				}
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
