package runner

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"testing"
	"time"

	"github.com/charmbracelet/x/xpty"
	"golang.org/x/term"
)

func TestAdversarialStressHelper(t *testing.T) {
	mode := os.Getenv("PLAYTESTR_STRESS_KIND")
	if mode == "" {
		return
	}
	if mode == "output" {
		n, err := strconv.Atoi(os.Getenv("PLAYTESTR_STRESS_BYTES"))
		if err != nil || n < 1 || n > 5000 {
			os.Exit(8)
		}
		fmt.Print(strings.Repeat("x", n) + "\r\noutput complete\r\n")
		os.Exit(0)
	}
	old, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		os.Exit(9)
	}
	defer term.Restore(int(os.Stdin.Fd()), old)
	switch mode {
	case "reappear":
		fmt.Print("phase one processing\r\n")
		for _, output := range []string{"phase two ready", "phase three processing complete"} {
			var value [1]byte
			if _, err := io.ReadFull(os.Stdin, value[:]); err != nil || value[0] != 'x' {
				os.Exit(12)
			}
			fmt.Printf("\x1b[2J\x1b[H%s\r\n", output)
		}
		os.Exit(0)
	case "rapid", "paste":
		n := 64 * 5
		if mode == "paste" {
			n, err = strconv.Atoi(os.Getenv("PLAYTESTR_STRESS_BYTES"))
			if err != nil || n < 1 || n > 8192 {
				os.Exit(8)
			}
		}
		fmt.Print("bounded input ready\r\n")
		value := make([]byte, n)
		if _, err := io.ReadFull(os.Stdin, value); err != nil {
			os.Exit(10)
		}
		fmt.Printf("exact input %x\r\n", sha256.Sum256(value))
		os.Exit(0)
	case "resize":
		stop, done := make(chan struct{}), make(chan struct{})
		go func() {
			defer close(done)
			ticker := time.NewTicker(10 * time.Millisecond)
			defer ticker.Stop()
			for {
				width, height, err := term.GetSize(int(os.Stdout.Fd()))
				if err != nil {
					return
				}
				fmt.Printf("\x1b[H\x1b[2Kresize activity ready size=%dx%d\r\n", width, height)
				select {
				case <-stop:
					return
				case <-ticker.C:
				}
			}
		}()
		var value [1]byte
		_, readErr := io.ReadFull(os.Stdin, value[:])
		close(stop)
		<-done
		if readErr != nil || value[0] != 'q' {
			os.Exit(11)
		}
		fmt.Print("\x1b[2;1Hresize stream complete\r\n")
		os.Exit(0)
	case "query":
		fmt.Print("unsupported cursor query waiting\r\n\x1b[6n")
		var value [1]byte
		_, _ = io.ReadFull(os.Stdin, value[:])
		fmt.Printf("query first byte=%02x\r\n", value[0])
		os.Exit(4)
	default:
		os.Exit(8)
	}
}

func runAdversarialStressSpec(t *testing.T, mode string, steps []Step, timeout int, outputCap int64, extra map[string]string) RunResult {
	t.Helper()
	env := map[string]string{"PLAYTESTR_STRESS_KIND": mode}
	for name, value := range extra {
		env[name] = value
	}
	spec := Spec{Version: SpecVersion, Command: []string{os.Args[0], "-test.run=^TestAdversarialStressHelper$"},
		Env: env, Width: 200, Height: 40, TimeoutMS: timeout, RunTimeoutMS: 15000,
		MaxOutputBytes: outputCap, Steps: steps}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "stress.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	options := RunOptions{}
	if evidence := os.Getenv("PLAYTESTR_ADVERSARIAL_EVIDENCE_DIR"); evidence != "" {
		if err := os.MkdirAll(evidence, 0700); err != nil {
			t.Fatal(err)
		}
		folder, err := os.MkdirTemp(evidence, strings.ReplaceAll(t.Name(), "/", "-")+"-")
		if err != nil {
			t.Fatal(err)
		}
		options.ArtifactPrefix = filepath.Join(folder, "stress")
	}
	result := RunDetailedContext(context.Background(), path, options, &bytes.Buffer{})
	if !result.Cleanup.ConfirmedExited {
		t.Fatalf("real stress target cleanup unconfirmed: %+v", result.Cleanup)
	}
	return result
}

func TestAdversarialRapidKeysPreserveEveryEvent(t *testing.T) {
	steps := []Step{{Expect: "bounded input ready"}}
	for i := 0; i < 64; i++ {
		steps = append(steps, Step{Key: "CtrlA"}, Step{Key: "CtrlK"}, Step{Key: "Enter"}, Step{Key: "CtrlJ"}, Step{Text: "x"})
	}
	// Literal expected bytes are independent of the product's key lookup.
	want := sha256.Sum256(bytes.Repeat([]byte{1, 11, 13, 10, 'x'}, 64))
	steps = append(steps, Step{Expect: fmt.Sprintf("exact input %x", want)}, Step{Exit: intPointer(0)})
	if result := runAdversarialStressSpec(t, "rapid", steps, 5000, 100000, nil); result.Err() != nil {
		t.Fatal(result.Err())
	}
}

func TestAdversarialDisappearanceAndReappearance(t *testing.T) {
	steps := []Step{{Expect: "phase one processing"}, {Expect: "processing"},
		{Text: "x"}, {Expect: "phase two ready"}, {ExpectNot: "processing"},
		{Text: "x"}, {Expect: "phase three processing complete"}, {Expect: "processing"}, {Exit: intPointer(0)}}
	if result := runAdversarialStressSpec(t, "reappear", steps, 5000, 100000, nil); result.Err() != nil {
		t.Fatal(result.Err())
	}
}

func TestAdversarialBoundedUnicodeLiteralPaste(t *testing.T) {
	payload := strings.Repeat("caf\u00e9 \u96ea spaced \"value\"\n", 100)
	want := sha256.Sum256([]byte(payload))
	steps := []Step{{Expect: "bounded input ready"}, {Text: payload},
		{Expect: fmt.Sprintf("exact input %x", want)}, {Exit: intPointer(0)}}
	result := runAdversarialStressSpec(t, "paste", steps, 5000, 100000,
		map[string]string{"PLAYTESTR_STRESS_BYTES": strconv.Itoa(len(payload))})
	if result.Err() != nil {
		t.Fatal(result.Err())
	}
}

func TestAdversarialRepeatedResizeDuringOutput(t *testing.T) {
	steps := []Step{{Expect: "resize activity ready"}}
	for i := 0; i < 12; i++ {
		width, height := 80+5*i, 24+i%3
		steps = append(steps, Step{Resize: &TerminalSize{Width: width, Height: height}},
			Step{WaitForRedraw: true}, Step{Expect: fmt.Sprintf("size=%dx%d", width, height)})
	}
	steps = append(steps, Step{Text: "q"}, Step{Expect: "resize stream complete"}, Step{Exit: intPointer(0)})
	if result := runAdversarialStressSpec(t, "resize", steps, 5000, 200000, nil); result.Err() != nil {
		t.Fatal(result.Err())
	}
}

func TestAdversarialOutputCapBoundary(t *testing.T) {
	for _, test := range []struct {
		name  string
		count int
		pass  bool
	}{{"near-cap", 3840, true}, {"over-cap", 4300, false}} {
		t.Run(test.name, func(t *testing.T) {
			result := runAdversarialStressSpec(t, "output", []Step{{Expect: "output complete"}, {Exit: intPointer(0)}},
				5000, 4096, map[string]string{"PLAYTESTR_STRESS_BYTES": strconv.Itoa(test.count)})
			if test.pass {
				if result.Err() != nil {
					t.Fatal(result.Err())
				}
			} else if result.Failure == nil || result.Failure.Category != FailureOutputLimit {
				t.Fatalf("expected accurate over-cap failure: %+v", result)
			}
		})
	}
}

func TestAdversarialUnsupportedCursorQueryIsBounded(t *testing.T) {
	start := time.Now()
	result := runAdversarialStressSpec(t, "query", []Step{{Expect: "unsupported cursor query waiting"},
		{Expect: "a cursor reply was received"}}, 500, 100000, nil)
	// ConPTY may itself answer VT queries; the runner makes no cross-platform
	// reply promise. The helper deliberately rejects any first byte with exit 4.
	boundedExit := result.Failure != nil && result.Failure.Category == FailureUnexpectedExit &&
		result.Target.ExitCode != nil && *result.Target.ExitCode == 4
	if result.Failure == nil || (result.Failure.Category != FailureAssertionTimeout && !boundedExit) {
		t.Fatalf("unsupported query must produce a bounded accurate timeout or declared helper exit: %+v", result)
	}
	if time.Since(start) > 10*time.Second {
		t.Fatal("unsupported query exceeded independent test deadline")
	}
}

type stressTracePTY struct {
	xpty.Pty
	mu  sync.Mutex
	raw strings.Builder
}

func (p *stressTracePTY) Read(value []byte) (int, error) {
	n, err := p.Pty.Read(value)
	p.mu.Lock()
	if p.raw.Len()+n <= 32768 {
		p.raw.Write(value[:n])
	}
	p.mu.Unlock()
	return n, err
}

func (p *stressTracePTY) AwaitResize(ctx context.Context) error {
	if backend, ok := p.Pty.(interface{ AwaitResize(context.Context) error }); ok {
		return backend.AwaitResize(ctx)
	}
	return nil
}

func TestAdversarialContinuousResizeRawProbe(t *testing.T) {
	if os.Getenv("PLAYTESTR_TRACE_RESIZE") != "1" {
		t.Skip("Opt-in bounded raw-transport investigation")
	}
	backend, err := newTerminalPty(200, 40)
	if err != nil {
		t.Fatal(err)
	}
	trace := &stressTracePTY{Pty: backend}
	s, err := startTerminalSessionWithPTY(sessionConfig{
		command: []string{os.Args[0], "-test.run=^TestAdversarialStressHelper$"},
		env:     append(os.Environ(), "PLAYTESTR_STRESS_KIND=resize"), width: 200, height: 40, maxOutputBytes: 100000,
	}, trace)
	if err != nil {
		t.Fatal(err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		result := s.stop(ctx)
		trace.mu.Lock()
		t.Logf("raw=%q", trace.raw.String())
		trace.mu.Unlock()
		if !result.confirmedExited || result.err != nil {
			t.Errorf("raw probe cleanup: %+v", result)
		}
	}()
	deadline := time.Now().Add(5 * time.Second)
	for !strings.Contains(s.observe().screen, "resize activity ready") && time.Now().Before(deadline) {
		time.Sleep(5 * time.Millisecond)
	}
	for _, size := range []TerminalSize{{80, 24}, {85, 25}, {90, 26}} {
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		err := s.resize(ctx, size.Width, size.Height)
		cancel()
		t.Logf("requested=%dx%d error=%v screen=%q", size.Width, size.Height, err, s.observe().screen)
		if err != nil {
			t.Fatal(err)
		}
	}
}
