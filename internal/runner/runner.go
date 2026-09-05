package runner

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/charmbracelet/x/xpty"
	"github.com/hinshun/vt10x"
)

type Step struct {
	Key      string `json:"key,omitempty"`
	Text     string `json:"text,omitempty"`
	Expect   string `json:"expect,omitempty"`
	Snapshot string `json:"snapshot,omitempty"`
	Exit     *int   `json:"exit,omitempty"`
}
type Spec struct {
	Name      string   `json:"name"`
	Command   []string `json:"command"`
	Width     int      `json:"width"`
	Height    int      `json:"height"`
	TimeoutMS int      `json:"timeout_ms"`
	Steps     []Step   `json:"steps"`
}

var keys = map[string]string{"Enter": "\r", "ArrowDown": "\x1b[B", "ArrowUp": "\x1b[A", "ArrowRight": "\x1b[C", "ArrowLeft": "\x1b[D", "Escape": "\x1b", "Tab": "\t", "Backspace": "\x7f", "CtrlC": "\x03"}

func Load(path string) (Spec, error) {
	var s Spec
	f, e := os.Open(path)
	if e != nil {
		return s, e
	}
	defer f.Close()
	d := json.NewDecoder(f)
	d.DisallowUnknownFields()
	if e = d.Decode(&s); e != nil {
		return s, e
	}
	var extra any
	if d.Decode(&extra) != io.EOF {
		return s, fmt.Errorf("expected one JSON object")
	}
	if len(s.Command) == 0 || s.Command[0] == "" {
		return s, fmt.Errorf("command is required")
	}
	if s.Width == 0 {
		s.Width = 80
	}
	if s.Height == 0 {
		s.Height = 24
	}
	if s.TimeoutMS == 0 {
		s.TimeoutMS = 3000
	}
	if s.Width < 1 || s.Width > 500 || s.Height < 1 || s.Height > 200 || s.TimeoutMS < 1 || s.TimeoutMS > 120000 {
		return s, fmt.Errorf("invalid dimensions or timeout")
	}
	if len(s.Steps) == 0 {
		return s, fmt.Errorf("steps are required")
	}
	for i, step := range s.Steps {
		n := 0
		for _, v := range []string{step.Key, step.Text, step.Expect, step.Snapshot} {
			if v != "" {
				n++
			}
		}
		if step.Exit != nil {
			n++
		}
		if n != 1 {
			return s, fmt.Errorf("step %d must have exactly one action", i+1)
		}
		if step.Exit != nil && (*step.Exit < 0 || *step.Exit > 255) {
			return s, fmt.Errorf("step %d exit code must be between 0 and 255", i+1)
		}
		if step.Key != "" {
			if _, ok := keys[step.Key]; !ok {
				return s, fmt.Errorf("unknown key %q", step.Key)
			}
		}
		if step.Snapshot != "" && (filepath.Base(step.Snapshot) != step.Snapshot || strings.ContainsAny(step.Snapshot, "/\\:") || step.Snapshot == "..") {
			return s, fmt.Errorf("snapshot must be a filename")
		}
	}
	return s, nil
}

type processOutcome struct {
	done chan struct{}
	mu   sync.RWMutex
	code int
	err  error
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

func (o *processOutcome) wait(timeout time.Duration) (code int, err error, exited bool) {
	select {
	case <-o.done:
		return o.result()
	case <-time.After(timeout):
		return 0, nil, false
	}
}

func normalize(s string) string {
	lines := strings.Split(s, "\n")
	for i := range lines {
		lines[i] = strings.TrimRight(lines[i], " \r")
	}
	return strings.TrimRight(strings.Join(lines, "\n"), "\n") + "\n"
}

// Run executes a spec. Relative commands run from the caller's working directory.
func Run(path string, update bool, out io.Writer) (err error) {
	s, err := Load(path)
	if err != nil {
		return err
	}
	p, err := xpty.NewPty(s.Width, s.Height)
	if err != nil {
		return err
	}
	defer p.Close()
	cmd := exec.Command(s.Command[0], s.Command[1:]...)
	cmd.Env = append(os.Environ(), "TERM=xterm-256color")
	if err = p.Start(cmd); err != nil {
		return err
	}
	outcome := newProcessOutcome(cmd)
	defer func() {
		_ = cmd.Process.Kill()
		_, _, _ = outcome.wait(2 * time.Second)
	}()
	terminal := vt10x.New(vt10x.WithSize(s.Width, s.Height))
	var mu sync.Mutex
	last := time.Now()
	go func() {
		b := make([]byte, 8192)
		for {
			n, e := p.Read(b)
			if n > 0 {
				mu.Lock()
				_, _ = terminal.Write(b[:n])
				last = time.Now()
				mu.Unlock()
			}
			if e != nil {
				return
			}
		}
	}()
	screen := func() (string, time.Time) { mu.Lock(); defer mu.Unlock(); return normalize(terminal.String()), last }
	base := filepath.Join(filepath.Dir(path), "snapshots")
	exitAsserted := false
	defer func() {
		if err != nil {
			view, _ := screen()
			artifact := path + ".actual.txt"
			if e := os.WriteFile(artifact, []byte(view), 0644); e == nil {
				fmt.Fprintf(out, "Screen saved: %s\n", artifact)
			}
		}
	}()
	for i, step := range s.Steps {
		action := func() error {
			if step.Key != "" {
				_, e := io.WriteString(p, keys[step.Key])
				return e
			}
			if step.Text != "" {
				_, e := io.WriteString(p, step.Text)
				return e
			}
			if step.Exit != nil {
				code, waitErr, exited := outcome.wait(time.Duration(s.TimeoutMS) * time.Millisecond)
				if !exited {
					return fmt.Errorf("timed out waiting for process to exit with code %d", *step.Exit)
				}
				if code != *step.Exit {
					return fmt.Errorf("expected exit code %d, got %d", *step.Exit, code)
				}
				if code < 0 && waitErr != nil {
					return fmt.Errorf("process wait failed: %w", waitErr)
				}
				return nil
			}
			deadline := time.Now().Add(time.Duration(s.TimeoutMS) * time.Millisecond)
			var expected []byte
			if step.Snapshot != "" && !update {
				var e error
				expected, e = os.ReadFile(filepath.Join(base, step.Snapshot))
				if e != nil {
					return fmt.Errorf("read snapshot (use --update to create): %w", e)
				}
			}
			for {
				view, changed := screen()
				if code, waitErr, exited := outcome.result(); exited {
					// Give the terminal reader one scheduling turn to consume bytes that
					// were written immediately before process exit.
					time.Sleep(10 * time.Millisecond)
					view, changed = screen()
					if step.Expect != "" && strings.Contains(view, step.Expect) {
						return nil
					}
					if !exitAsserted {
						if code < 0 && waitErr != nil {
							return fmt.Errorf("process wait failed while waiting for assertion: %w", waitErr)
						}
						return fmt.Errorf("process exited with code %d before assertion matched", code)
					}
				}
				if step.Expect != "" && strings.Contains(view, step.Expect) {
					return nil
				}
				if step.Snapshot != "" && time.Since(changed) >= 150*time.Millisecond {
					if update {
						if e := os.MkdirAll(base, 0755); e != nil {
							return e
						}
						return os.WriteFile(filepath.Join(base, step.Snapshot), []byte(view), 0644)
					}
					if view == string(expected) {
						return nil
					}
				}
				if time.Now().After(deadline) {
					if step.Expect != "" {
						return fmt.Errorf("timed out waiting for %q", step.Expect)
					}
					return fmt.Errorf("snapshot mismatch: %s", step.Snapshot)
				}
				time.Sleep(10 * time.Millisecond)
			}
		}()
		if action != nil {
			return fmt.Errorf("%s: step %d: %w", s.Name, i+1, action)
		}
		if step.Exit != nil {
			exitAsserted = true
		}
		fmt.Fprintf(out, "  PASS step %d\n", i+1)
	}
	if !exitAsserted {
		if code, waitErr, exited := outcome.result(); exited {
			if code < 0 && waitErr != nil {
				return fmt.Errorf("%s: process wait failed: %w", s.Name, waitErr)
			}
			return fmt.Errorf("%s: process exited with code %d without an exit assertion", s.Name, code)
		}
	}
	fmt.Fprintf(out, "PASS %s\n", s.Name)
	return nil
}
