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
		if n != 1 {
			return s, fmt.Errorf("step %d must have exactly one action", i+1)
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
	done := make(chan error, 1)
	go func() { done <- xpty.WaitProcess(context.Background(), cmd) }()
	defer func() {
		_ = cmd.Process.Kill()
		select {
		case <-done:
		case <-time.After(2 * time.Second):
		}
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
		fmt.Fprintf(out, "  PASS step %d\n", i+1)
	}
	fmt.Fprintf(out, "PASS %s\n", s.Name)
	return nil
}
