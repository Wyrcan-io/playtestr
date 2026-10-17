//go:build !windows

package runner

import (
	"errors"
	"fmt"
	"os"
	"sync"

	"github.com/charmbracelet/x/xpty"
	"golang.org/x/sys/unix"
)

// pollingUnixPTY keeps native reads and writes nonblocking. In particular,
// closing a Linux master descriptor alone need not release a syscall already
// blocked writing replies to a target that never reads terminal input.
type pollingUnixPTY struct {
	*xpty.UnixPty
	mu            sync.Mutex
	closed        bool
	fd            int
	slaveReleased bool
	releaseErr    error
}

func newPollingUnixPTY(width, height int) (*pollingUnixPTY, error) {
	p, err := xpty.NewUnixPty(width, height)
	if err != nil {
		return nil, err
	}
	fd := int(p.Master().Fd())
	if err := unix.SetNonblock(fd, true); err != nil {
		return nil, errors.Join(fmt.Errorf("set terminal master nonblocking: %w", err), p.Close())
	}
	return &pollingUnixPTY{UnixPty: p, fd: fd}, nil
}

func (p *pollingUnixPTY) releaseParentSlave() {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.releaseParentSlaveLocked()
}

func (p *pollingUnixPTY) releaseParentSlaveLocked() {
	if !p.slaveReleased {
		p.slaveReleased = true
		if err := p.Slave().Close(); err != nil {
			p.releaseErr = fmt.Errorf("release parent terminal slave: %w", err)
		}
	}
}

func (p *pollingUnixPTY) Read(buffer []byte) (int, error) {
	for {
		p.mu.Lock()
		if p.closed {
			p.mu.Unlock()
			return 0, os.ErrClosed
		}
		events := []unix.PollFd{{Fd: int32(p.fd), Events: unix.POLLIN}}
		ready, err := unix.Poll(events, 25)
		if err == nil && ready > 0 {
			n, readErr := unix.Read(p.fd, buffer)
			p.mu.Unlock()
			if readErr == unix.EAGAIN || readErr == unix.EINTR {
				continue
			}
			return n, readErr
		}
		p.mu.Unlock()
		if err != nil && err != unix.EINTR {
			return 0, err
		}
	}
}

func (p *pollingUnixPTY) Write(buffer []byte) (int, error) {
	written := 0
	for written < len(buffer) {
		p.mu.Lock()
		if p.closed {
			p.mu.Unlock()
			return written, os.ErrClosed
		}
		events := []unix.PollFd{{Fd: int32(p.fd), Events: unix.POLLOUT}}
		ready, err := unix.Poll(events, 25)
		if err == nil && ready > 0 {
			var n int
			n, err = unix.Write(p.fd, buffer[written:min(len(buffer), written+32768)])
			if n > 0 {
				written += n
			}
		}
		p.mu.Unlock()
		if err != nil && err != unix.EAGAIN && err != unix.EINTR {
			return written, err
		}
	}
	return written, nil
}

func (p *pollingUnixPTY) Close() error {
	p.mu.Lock()
	defer p.mu.Unlock()
	if p.closed {
		return nil
	}
	p.closed = true
	p.releaseParentSlaveLocked()
	return errors.Join(p.releaseErr, p.Master().Close())
}
