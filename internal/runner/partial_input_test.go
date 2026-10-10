package runner

import (
	"context"
	"errors"
	"io"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/charmbracelet/x/xpty"
)

// This deliberately faulty writer forwards a real partial input to a real
// target, then violates io.Writer's short-write error requirement. A backend
// must not turn that incomplete action into a passing input step.
type partialInputPTY struct{ xpty.Pty }

func (p partialInputPTY) Write(value []byte) (int, error) {
	if len(value) > 1 {
		value = value[:1]
	}
	return p.Pty.Write(value)
}

func TestPartialBackendInputCannotPass(t *testing.T) {
	backend, err := newTerminalPty(80, 24)
	if err != nil {
		t.Fatal(err)
	}
	s, err := startTerminalSessionWithPTY(sessionConfig{command: []string{os.Args[0], "-test.run=^TestHelperProcess$", "--", "edit-controls"},
		env: append(os.Environ(), "PLAYTESTR_HELPER_PROCESS=1"), width: 80, height: 24, maxOutputBytes: 100000}, partialInputPTY{backend})
	if err != nil {
		t.Fatal(err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		result := s.stop(ctx)
		if !result.confirmedExited || result.err != nil {
			t.Errorf("partial-input target cleanup: %+v", result)
		}
	}()
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	for !strings.Contains(s.observe().screen, "edit controls ready") && ctx.Err() == nil {
		time.Sleep(5 * time.Millisecond)
	}
	if ctx.Err() != nil {
		t.Fatal("target did not reach positive input readiness")
	}
	if err := s.send(ctx, "\x01\x0b\x0a"); !errors.Is(err, io.ErrShortWrite) {
		t.Fatalf("incomplete real input reported %v", err)
	}
}
