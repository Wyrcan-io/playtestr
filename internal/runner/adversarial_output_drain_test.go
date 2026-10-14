package runner

import (
	"context"
	"errors"
	"os"
	"sync"
	"testing"
	"time"

	"github.com/charmbracelet/x/xpty"
)

// Hold real backend bytes until the assertion has observed actual process exit
// and constructs its final drain context. No terminal output is fabricated.
type gatedFinalOutputPTY struct {
	xpty.Pty
	gate chan struct{}
	once sync.Once
}

func (p *gatedFinalOutputPTY) release() { p.once.Do(func() { close(p.gate) }) }
func (p *gatedFinalOutputPTY) Read(value []byte) (int, error) {
	<-p.gate
	return p.Pty.Read(value)
}
func (p *gatedFinalOutputPTY) Close() error {
	p.release()
	return p.Pty.Close()
}

type releaseFinalOutputContext struct {
	context.Context
	pty *gatedFinalOutputPTY
}

func (c *releaseFinalOutputContext) Deadline() (time.Time, bool) {
	c.pty.release()
	return c.Context.Deadline()
}

func TestAdversarialFinalDrainPreservesOutputLimit(t *testing.T) {
	backend, err := newTerminalPty(80, 24)
	if err != nil {
		t.Fatal(err)
	}
	gate := &gatedFinalOutputPTY{Pty: backend, gate: make(chan struct{})}
	session, err := startTerminalSessionWithPTY(sessionConfig{
		command: []string{os.Args[0], "-test.run=^TestHelperProcess$", "--", "exit-zero"},
		env:     append(os.Environ(), "PLAYTESTR_HELPER_PROCESS=1"),
		width:   80, height: 24, maxOutputBytes: 8,
	}, gate)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() {
		gate.release()
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		if cleanup := session.stop(ctx); cleanup.err != nil || !cleanup.confirmedExited {
			t.Errorf("real target cleanup unconfirmed: %+v", cleanup)
		}
	})
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	code, waitErr, exited := session.outcome.wait(ctx)
	if !exited || code != 0 || waitErr != nil {
		t.Fatalf("real helper must exit before output delivery: code=%d exited=%v err=%v", code, exited, waitErr)
	}
	if session.observe().outputBytes != 0 {
		t.Fatal("backend gate did not hold the real final output")
	}
	err = executeStep(&releaseFinalOutputContext{Context: ctx, pty: gate}, "unused.json",
		Step{Expect: "finished cleanly"}, RunOptions{}, nil, session, false)
	if !errors.Is(err, errOutputLimit) {
		t.Fatalf("drained over-cap bytes must take precedence over target exit: %v; observation=%+v", err, session.observe())
	}
}
