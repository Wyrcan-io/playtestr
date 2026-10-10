//go:build windows

package runner

import (
	"context"
	"fmt"
	"strconv"
	"strings"
	"sync"

	"github.com/charmbracelet/x/xpty"
)

type consoleResizeRequest struct {
	width, height int
	done          chan struct{}
	acknowledged  bool
}

type windowsResizePty struct {
	xpty.Pty
	mu            sync.Mutex
	request       *consoleResizeRequest
	state         byte // output protocol state belongs exclusively to the PTY reader
	csi           []byte
	overflow, osc bool
}

func (p *windowsResizePty) Read(value []byte) (int, error) {
	n, err := p.Pty.Read(value)
	p.observeResize(value[:n])
	return n, err
}

func (p *windowsResizePty) Resize(width, height int) error {
	oldWidth, oldHeight, err := p.Pty.Size()
	if err != nil {
		return err
	}
	request := &consoleResizeRequest{width: width, height: height, done: make(chan struct{})}
	unchanged := oldWidth == width && oldHeight == height
	p.mu.Lock()
	p.request = request
	if unchanged {
		request.acknowledged = true
		close(request.done)
	}
	p.mu.Unlock()
	if unchanged {
		return nil
	}
	return p.Pty.Resize(width, height)
}

func (p *windowsResizePty) AwaitResize(ctx context.Context) error {
	p.mu.Lock()
	request := p.request
	p.mu.Unlock()
	if request == nil {
		return fmt.Errorf("native console resize has no request")
	}
	select {
	case <-request.done:
		return nil
	case <-ctx.Done():
		return fmt.Errorf("wait for native console resize acknowledgment at %dx%d: %w", request.width, request.height, ctx.Err())
	}
}

func (p *windowsResizePty) completeResize() {
	parts := strings.Split(string(p.csi), ";")
	if p.overflow || len(parts) != 3 || parts[0] != "8" {
		return
	}
	height, errHeight := strconv.Atoi(parts[1])
	width, errWidth := strconv.Atoi(parts[2])
	if errHeight != nil || errWidth != nil {
		return
	}
	p.mu.Lock()
	defer p.mu.Unlock()
	if request := p.request; request != nil && !request.acknowledged && request.width == width && request.height == height {
		request.acknowledged = true
		close(request.done)
	}
}

// ConPTY emits CSI 8;height;width t when it applies a console resize. Do not
// interpret lookalike data inside titles/DCS as an acknowledgment. Protocol
// capture is bounded and retains state across partial reads.
func (p *windowsResizePty) observeResize(value []byte) {
	for _, b := range value {
		switch p.state {
		case 0:
			if b == 0x1b {
				p.state = 1
			}
		case 1:
			switch b {
			case '[':
				p.state = 2
				p.csi = p.csi[:0]
				p.overflow = false
			case ']', 'P', 'X', '^', '_':
				p.state = 3
				p.osc = b == ']'
			case 0x1b:
			default:
				p.state = 0
			}
		case 2:
			if b == 0x1b {
				p.state = 1
				continue
			}
			if b == 0x18 || b == 0x1a {
				p.state = 0
				continue
			}
			if b >= 0x40 && b <= 0x7e {
				if b == 't' {
					p.completeResize()
				}
				p.state = 0
			} else if len(p.csi) < 32 {
				p.csi = append(p.csi, b)
			} else {
				p.overflow = true
			}
		case 3:
			if b == 0x1b {
				p.state = 4
			} else if (b == 7 && p.osc) || b == 0x18 || b == 0x1a {
				p.state = 0
			}
		case 4:
			if b == '\\' || (b == 7 && p.osc) || b == 0x18 || b == 0x1a {
				p.state = 0
			} else if b != 0x1b {
				p.state = 3
			}
		}
	}
}
