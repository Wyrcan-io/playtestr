package runner

import (
	"context"
	"fmt"
	"io"
	"os/exec"
	"strings"
	"sync"
	"time"

	"github.com/charmbracelet/x/xpty"
)

type sessionConfig struct {
	command        []string
	dir            string
	env            []string
	width          int
	height         int
	maxOutputBytes int64
}

type processOutcome struct {
	done chan struct{}
	mu   sync.RWMutex
	code int
	err  error
}

type sessionObservation struct {
	screen              string
	lastOutput          time.Time
	outputBytes         int64
	outputLimitExceeded bool
}

type cleanupResult struct {
	attempted       bool
	graceful        bool
	forced          bool
	confirmedExited bool
	mechanism       string
	err             error
}

type terminalSession struct {
	pty      xpty.Pty
	cmd      *exec.Cmd
	tree     *processTree
	terminal *screenEmulator
	outcome  *processOutcome

	mu                  sync.Mutex
	lastOutput          time.Time
	outputBytes         int64
	maxOutputBytes      int64
	outputLimitExceeded bool
	resizeOutputBytes   int64
	resizeStartedAt     time.Time
	hasResizeBaseline   bool

	firstOutput chan struct{}
	outputLimit chan struct{}
	readerDone  chan struct{}
	firstOnce   sync.Once
	limitOnce   sync.Once
	stopOnce    sync.Once
	writeMu     sync.Mutex
	stopResult  cleanupResult
}

func startTerminalSession(config sessionConfig) (*terminalSession, error) {
	p, err := xpty.NewPty(config.width, config.height)
	if err != nil {
		return nil, fmt.Errorf("create pseudoterminal: %w", err)
	}
	cmd := exec.Command(config.command[0], config.command[1:]...)
	cmd.Dir = config.dir
	cmd.Env = config.env
	configureProcess(cmd)
	if err := p.Start(cmd); err != nil {
		_ = p.Close()
		return nil, fmt.Errorf("start target: %w", err)
	}
	tree, err := attachProcessTree(cmd.Process.Pid)
	if err != nil {
		_ = cmd.Process.Kill()
		_ = p.Close()
		return nil, fmt.Errorf("attach target process tree: %w", err)
	}
	s := &terminalSession{
		pty:            p,
		cmd:            cmd,
		tree:           tree,
		terminal:       newScreenEmulator(config.width, config.height),
		outcome:        newProcessOutcome(cmd),
		lastOutput:     time.Now(),
		maxOutputBytes: config.maxOutputBytes,
		firstOutput:    make(chan struct{}),
		outputLimit:    make(chan struct{}),
		readerDone:     make(chan struct{}),
	}
	go s.readOutput()
	return s, nil
}

func newProcessOutcome(cmd *exec.Cmd) *processOutcome {
	o := &processOutcome{done: make(chan struct{})}
	go func() {
		err := xpty.WaitProcess(context.Background(), cmd)
		code := -1
		if cmd.ProcessState != nil {
			code = cmd.ProcessState.ExitCode()
		}
		o.mu.Lock()
		o.code = code
		o.err = err
		o.mu.Unlock()
		close(o.done)
	}()
	return o
}

func (o *processOutcome) result() (code int, err error, exited bool) {
	select {
	case <-o.done:
		o.mu.RLock()
		defer o.mu.RUnlock()
		return o.code, o.err, true
	default:
		return 0, nil, false
	}
}

func (o *processOutcome) wait(ctx context.Context) (code int, err error, exited bool) {
	select {
	case <-o.done:
		return o.result()
	case <-ctx.Done():
		return 0, ctx.Err(), false
	}
}

func (s *terminalSession) readOutput() {
	defer close(s.readerDone)
	buffer := make([]byte, 8192)
	for {
		n, err := s.pty.Read(buffer)
		if n > 0 {
			s.mu.Lock()
			s.outputBytes += int64(n)
			accepted := n
			if remaining := s.maxOutputBytes - (s.outputBytes - int64(n)); int64(accepted) > remaining {
				accepted = max(0, int(remaining))
			}
			if accepted > 0 {
				s.terminal.Write(buffer[:accepted])
				s.lastOutput = time.Now()
				if strings.TrimSpace(normalize(s.terminal.String())) != "" {
					s.firstOnce.Do(func() { close(s.firstOutput) })
				}
			}
			if s.outputBytes > s.maxOutputBytes {
				s.outputLimitExceeded = true
				s.limitOnce.Do(func() { close(s.outputLimit) })
			}
			s.mu.Unlock()
		}
		if err != nil {
			return
		}
	}
}

func (s *terminalSession) observe() sessionObservation {
	s.mu.Lock()
	defer s.mu.Unlock()
	return sessionObservation{
		screen:              normalize(s.terminal.String()),
		lastOutput:          s.lastOutput,
		outputBytes:         s.outputBytes,
		outputLimitExceeded: s.outputLimitExceeded,
	}
}

func (s *terminalSession) send(ctx context.Context, value string) error {
	done := make(chan error, 1)
	go func() {
		s.writeMu.Lock()
		defer s.writeMu.Unlock()
		_, err := io.WriteString(s.pty, value)
		done <- err
	}()
	select {
	case err := <-done:
		return err
	case <-ctx.Done():
		return ctx.Err()
	case <-s.outputLimit:
		return errOutputLimit
	}
}

func (s *terminalSession) resize(ctx context.Context, width, height int) error {
	if err := ctx.Err(); err != nil {
		return err
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	if err := s.pty.Resize(width, height); err != nil {
		return fmt.Errorf("resize pseudoterminal to %dx%d: %w", width, height, err)
	}
	s.terminal.Resize(width, height)
	s.resizeOutputBytes = s.outputBytes
	s.resizeStartedAt = time.Now()
	s.hasResizeBaseline = true
	return nil
}

func (s *terminalSession) redrawBaseline() (int64, time.Time, bool) {
	s.mu.Lock()
	defer s.mu.Unlock()
	return s.resizeOutputBytes, s.resizeStartedAt, s.hasResizeBaseline
}

func (s *terminalSession) drainFinal(ctx context.Context, quiet time.Duration) error {
	initial := s.observe()
	changed := false
	ticker := time.NewTicker(5 * time.Millisecond)
	defer ticker.Stop()
	for {
		observation := s.observe()
		if observation.outputBytes != initial.outputBytes {
			changed = true
		}
		if changed && time.Since(observation.lastOutput) >= quiet {
			return nil
		}
		select {
		case <-s.readerDone:
			return nil
		case <-ctx.Done():
			return ctx.Err()
		case <-ticker.C:
		}
	}
}

func (s *terminalSession) stop(ctx context.Context) cleanupResult {
	s.stopOnce.Do(func() {
		result := cleanupResult{attempted: true, mechanism: s.tree.mechanism()}
		_, _, exited := s.outcome.result()
		if !exited {
			graceCtx, cancel := context.WithTimeout(ctx, 150*time.Millisecond)
			_ = s.send(graceCtx, keys["CtrlC"])
			_, _, exited = s.outcome.wait(graceCtx)
			cancel()
		}
		result.graceful = exited
		active, activeErr := s.tree.active()
		if activeErr != nil {
			active = true
		}
		if active {
			result.forced = true
			if err := s.tree.terminate(); err != nil {
				if activeErr != nil {
					result.err = fmt.Errorf("terminate process tree after status query failed (%v): %w", activeErr, err)
				} else {
					result.err = fmt.Errorf("terminate process tree: %w", err)
				}
			}
		}
		if err := s.pty.Close(); err != nil && result.err == nil {
			result.err = fmt.Errorf("close pseudoterminal: %w", err)
		}
		select {
		case <-s.readerDone:
		case <-ctx.Done():
			if result.err == nil {
				result.err = fmt.Errorf("wait for terminal reader: %w", ctx.Err())
			}
		}
		select {
		case <-s.outcome.done:
		case <-ctx.Done():
			if result.err == nil {
				result.err = fmt.Errorf("wait for target process: %w", ctx.Err())
			}
		}
		confirmed, confirmErr := s.waitForTreeExit(ctx)
		if confirmErr != nil && result.err == nil {
			result.err = fmt.Errorf("confirm process-tree exit: %w", confirmErr)
		}
		result.confirmedExited = confirmed
		if !result.confirmedExited && result.err == nil {
			result.err = fmt.Errorf("target process-tree termination was not confirmed")
		}
		if err := s.tree.close(); err != nil && result.err == nil {
			result.err = fmt.Errorf("close process-tree handle: %w", err)
		}
		s.stopResult = result
	})
	return s.stopResult
}

func (s *terminalSession) waitForTreeExit(ctx context.Context) (bool, error) {
	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()
	for {
		active, err := s.tree.active()
		if err != nil {
			return false, err
		}
		if !active {
			return true, nil
		}
		select {
		case <-ctx.Done():
			return false, ctx.Err()
		case <-ticker.C:
		}
	}
}
