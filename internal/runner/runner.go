package runner

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"runtime"
	"sort"
	"strings"
	"time"
)

var errOutputLimit = errors.New("target exceeded max_output_bytes")

// Step contains exactly one terminal action or assertion.
type Step struct {
	Key      string `json:"key,omitempty"`
	Text     string `json:"text,omitempty"`
	Expect   string `json:"expect,omitempty"`
	Snapshot string `json:"snapshot,omitempty"`
	Exit     *int   `json:"exit,omitempty"`
}

// Spec describes one target process and its ordered terminal interactions.
type Spec struct {
	Name             string            `json:"name"`
	Command          []string          `json:"command"`
	CWD              string            `json:"cwd,omitempty"`
	Env              map[string]string `json:"env,omitempty"`
	InheritEnv       []string          `json:"inherit_env,omitempty"`
	Width            int               `json:"width"`
	Height           int               `json:"height"`
	TimeoutMS        int               `json:"timeout_ms"`
	RunTimeoutMS     int               `json:"run_timeout_ms"`
	StartupTimeoutMS int               `json:"startup_timeout_ms,omitempty"`
	MaxOutputBytes   int64             `json:"max_output_bytes"`
	Steps            []Step            `json:"steps"`
}

var (
	keys = map[string]string{
		"Enter": "\r", "ArrowDown": "\x1b[B", "ArrowUp": "\x1b[A",
		"ArrowRight": "\x1b[C", "ArrowLeft": "\x1b[D", "Escape": "\x1b",
		"Tab": "\t", "Backspace": "\x7f", "CtrlC": "\x03",
	}
	environmentName = regexp.MustCompile(`^[A-Za-z_][A-Za-z0-9_]*$`)
)

func Load(path string) (Spec, error) {
	var spec Spec
	file, err := os.Open(path)
	if err != nil {
		return spec, err
	}
	defer file.Close()
	decoder := json.NewDecoder(file)
	decoder.DisallowUnknownFields()
	if err = decoder.Decode(&spec); err != nil {
		return spec, err
	}
	var extra any
	if decoder.Decode(&extra) != io.EOF {
		return spec, fmt.Errorf("expected one JSON object")
	}
	if spec.Name == "" {
		spec.Name = filepath.Base(path)
	}
	if len(spec.Command) == 0 || spec.Command[0] == "" {
		return spec, fmt.Errorf("command is required")
	}
	for i, value := range spec.Command {
		if strings.ContainsRune(value, '\x00') {
			return spec, fmt.Errorf("command value %d contains a NUL byte", i)
		}
	}
	if spec.Width == 0 {
		spec.Width = 80
	}
	if spec.Height == 0 {
		spec.Height = 24
	}
	if spec.TimeoutMS == 0 {
		spec.TimeoutMS = 3000
	}
	if spec.RunTimeoutMS == 0 {
		spec.RunTimeoutMS = 30000
	}
	if spec.MaxOutputBytes == 0 {
		spec.MaxOutputBytes = 2_000_000
	}
	if spec.Width < 1 || spec.Width > 500 || spec.Height < 1 || spec.Height > 200 {
		return spec, fmt.Errorf("terminal dimensions are invalid")
	}
	if spec.TimeoutMS < 1 || spec.TimeoutMS > 120000 || spec.RunTimeoutMS < 1 || spec.RunTimeoutMS > 3_600_000 || spec.StartupTimeoutMS < 0 || spec.StartupTimeoutMS > 120000 {
		return spec, fmt.Errorf("timeouts are invalid")
	}
	if spec.MaxOutputBytes < 1 || spec.MaxOutputBytes > 1_000_000_000 {
		return spec, fmt.Errorf("max_output_bytes must be between 1 and 1000000000")
	}
	if len(spec.Steps) == 0 {
		return spec, fmt.Errorf("steps are required")
	}
	seenEnvironment := make(map[string]string)
	for name, value := range spec.Env {
		if !environmentName.MatchString(name) {
			return spec, fmt.Errorf("invalid environment name %q", name)
		}
		if strings.ContainsRune(value, '\x00') {
			return spec, fmt.Errorf("environment value %q contains a NUL byte", name)
		}
		key := environmentKey(name)
		if previous, exists := seenEnvironment[key]; exists {
			return spec, fmt.Errorf("environment names %q and %q conflict", previous, name)
		}
		seenEnvironment[key] = name
	}
	for _, name := range spec.InheritEnv {
		if !environmentName.MatchString(name) {
			return spec, fmt.Errorf("invalid inherited environment name %q", name)
		}
	}
	for i, step := range spec.Steps {
		actions := 0
		for _, value := range []string{step.Key, step.Text, step.Expect, step.Snapshot} {
			if value != "" {
				actions++
			}
		}
		if step.Exit != nil {
			actions++
		}
		if actions != 1 {
			return spec, fmt.Errorf("step %d must have exactly one action", i+1)
		}
		if step.Exit != nil && (*step.Exit < 0 || *step.Exit > 255) {
			return spec, fmt.Errorf("step %d exit code must be between 0 and 255", i+1)
		}
		if step.Key != "" {
			if _, ok := keys[step.Key]; !ok {
				return spec, fmt.Errorf("unknown key %q", step.Key)
			}
		}
		if step.Snapshot != "" && (filepath.Base(step.Snapshot) != step.Snapshot || strings.ContainsAny(step.Snapshot, "/\\:") || step.Snapshot == "..") {
			return spec, fmt.Errorf("snapshot must be a filename")
		}
	}
	return spec, nil
}

func normalize(value string) string {
	lines := strings.Split(value, "\n")
	for i := range lines {
		lines[i] = strings.TrimRight(lines[i], " \r")
	}
	return strings.TrimRight(strings.Join(lines, "\n"), "\n") + "\n"
}

func environmentKey(name string) string {
	if runtime.GOOS == "windows" {
		return strings.ToUpper(name)
	}
	return name
}

func targetEnvironment(spec Spec) []string {
	allowed := []string{"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "LC_CTYPE"}
	if runtime.GOOS == "windows" {
		allowed = []string{"PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "TEMP", "TMP", "USERPROFILE"}
	}
	values := make(map[string]string)
	inherit := func(name string) {
		if value, ok := os.LookupEnv(name); ok {
			values[environmentKey(name)] = name + "=" + value
		}
	}
	for _, name := range allowed {
		inherit(name)
	}
	for _, name := range spec.InheritEnv {
		inherit(name)
	}
	for name, value := range spec.Env {
		values[environmentKey(name)] = name + "=" + value
	}
	values[environmentKey("TERM")] = "TERM=xterm-256color"
	result := make([]string, 0, len(values))
	for _, value := range values {
		result = append(result, value)
	}
	sort.Strings(result)
	return result
}

func targetDirectory(specPath, configured string) (string, error) {
	if configured == "" {
		return "", nil
	}
	if !filepath.IsAbs(configured) {
		configured = filepath.Join(filepath.Dir(specPath), configured)
	}
	absolute, err := filepath.Abs(configured)
	if err != nil {
		return "", fmt.Errorf("resolve cwd: %w", err)
	}
	info, err := os.Stat(absolute)
	if err != nil {
		return "", fmt.Errorf("open cwd: %w", err)
	}
	if !info.IsDir() {
		return "", fmt.Errorf("cwd is not a directory: %s", absolute)
	}
	return absolute, nil
}

// Run executes a spec with a background context.
func Run(path string, update bool, out io.Writer) error {
	return RunContext(context.Background(), path, update, out)
}

// RunContext executes a spec and stops its process tree when the context ends.
func RunContext(parent context.Context, path string, update bool, out io.Writer) (runErr error) {
	if err := parent.Err(); err != nil {
		return fmt.Errorf("run cancelled: %w", err)
	}
	spec, err := Load(path)
	if err != nil {
		return err
	}
	dir, err := targetDirectory(path, spec.CWD)
	if err != nil {
		return err
	}
	runContext, cancelRun := context.WithTimeout(parent, time.Duration(spec.RunTimeoutMS)*time.Millisecond)
	defer cancelRun()
	session, err := startTerminalSession(sessionConfig{
		command: spec.Command, dir: dir, env: targetEnvironment(spec), width: spec.Width,
		height: spec.Height, maxOutputBytes: spec.MaxOutputBytes,
	})
	if err != nil {
		return err
	}

	if spec.StartupTimeoutMS > 0 {
		startupContext, cancelStartup := context.WithTimeout(runContext, time.Duration(spec.StartupTimeoutMS)*time.Millisecond)
		err = waitForStartup(startupContext, session)
		cancelStartup()
		if err != nil {
			runErr = fmt.Errorf("%s: startup: %w", spec.Name, classifyContextError(err, parent, runContext))
		}
	}

	exitAsserted := false
	if runErr == nil {
		for i, step := range spec.Steps {
			stepContext, cancelStep := context.WithTimeout(runContext, time.Duration(spec.TimeoutMS)*time.Millisecond)
			err = executeStep(stepContext, path, step, update, session, exitAsserted)
			cancelStep()
			if err != nil {
				runErr = fmt.Errorf("%s: step %d: %w", spec.Name, i+1, classifyContextError(err, parent, runContext))
				break
			}
			if step.Exit != nil {
				exitAsserted = true
			}
			fmt.Fprintf(out, "  PASS step %d\n", i+1)
		}
	}

	if runErr == nil && !exitAsserted {
		observation := session.observe()
		if observation.outputLimitExceeded {
			runErr = fmt.Errorf("%s: %w (%d bytes observed)", spec.Name, errOutputLimit, observation.outputBytes)
		} else if code, waitErr, exited := session.outcome.result(); exited {
			if code < 0 && waitErr != nil {
				runErr = fmt.Errorf("%s: process wait failed: %w", spec.Name, waitErr)
			} else {
				runErr = fmt.Errorf("%s: process exited with code %d without an exit assertion", spec.Name, code)
			}
		}
	}

	cleanupContext, cancelCleanup := context.WithTimeout(context.Background(), 3*time.Second)
	cleanup := session.stop(cleanupContext)
	cancelCleanup()
	if cleanup.err != nil {
		cleanupErr := fmt.Errorf("cleanup failed: %w", cleanup.err)
		if runErr == nil {
			runErr = cleanupErr
		} else {
			runErr = errors.Join(runErr, cleanupErr)
		}
	}
	if runErr != nil {
		if cleanup.confirmedExited {
			mode := "clean"
			if cleanup.forced {
				mode = "forced"
			}
			fmt.Fprintf(out, "Cleanup: process tree stopped (%s, %s)\n", mode, cleanup.mechanism)
		}
		observation := session.observe()
		artifact := path + ".actual.txt"
		if writeErr := os.WriteFile(artifact, []byte(observation.screen), 0644); writeErr == nil {
			fmt.Fprintf(out, "Screen saved: %s\n", artifact)
		} else {
			runErr = errors.Join(runErr, fmt.Errorf("write failure screen: %w", writeErr))
		}
		return runErr
	}
	fmt.Fprintf(out, "PASS %s\n", spec.Name)
	return nil
}

func waitForStartup(ctx context.Context, session *terminalSession) error {
	select {
	case <-session.firstOutput:
		return nil
	case <-session.outputLimit:
		return errOutputLimit
	case <-session.outcome.done:
		code, waitErr, _ := session.outcome.result()
		if code < 0 && waitErr != nil {
			return fmt.Errorf("process wait failed: %w", waitErr)
		}
		return fmt.Errorf("process exited with code %d before producing output", code)
	case <-ctx.Done():
		return fmt.Errorf("timed out waiting for first output: %w", ctx.Err())
	}
}

func executeStep(ctx context.Context, specPath string, step Step, update bool, session *terminalSession, exitAsserted bool) error {
	if step.Key != "" {
		return session.send(ctx, keys[step.Key])
	}
	if step.Text != "" {
		return session.send(ctx, step.Text)
	}
	if step.Exit != nil {
		code, waitErr, exited := session.outcome.wait(ctx)
		if !exited {
			return fmt.Errorf("timed out waiting for process to exit with code %d: %w", *step.Exit, waitErr)
		}
		drainContext, cancelDrain := context.WithTimeout(ctx, 250*time.Millisecond)
		_ = session.drainFinal(drainContext, 25*time.Millisecond)
		cancelDrain()
		if observation := session.observe(); observation.outputLimitExceeded {
			return fmt.Errorf("%w (%d bytes observed)", errOutputLimit, observation.outputBytes)
		}
		if code != *step.Exit {
			return fmt.Errorf("expected exit code %d, got %d", *step.Exit, code)
		}
		if code < 0 && waitErr != nil {
			return fmt.Errorf("process wait failed: %w", waitErr)
		}
		return nil
	}

	var expected []byte
	base := filepath.Join(filepath.Dir(specPath), "snapshots")
	if step.Snapshot != "" && !update {
		var err error
		expected, err = os.ReadFile(filepath.Join(base, step.Snapshot))
		if err != nil {
			return fmt.Errorf("read snapshot (use --update to create): %w", err)
		}
	}
	ticker := time.NewTicker(10 * time.Millisecond)
	defer ticker.Stop()
	for {
		observation := session.observe()
		if observation.outputLimitExceeded {
			return fmt.Errorf("%w (%d bytes observed)", errOutputLimit, observation.outputBytes)
		}
		if step.Expect != "" && strings.Contains(observation.screen, step.Expect) {
			return nil
		}
		if step.Snapshot != "" && time.Since(observation.lastOutput) >= 150*time.Millisecond {
			if update {
				if err := os.MkdirAll(base, 0755); err != nil {
					return err
				}
				return os.WriteFile(filepath.Join(base, step.Snapshot), []byte(observation.screen), 0644)
			}
			if observation.screen == string(expected) {
				return nil
			}
		}
		if code, waitErr, exited := session.outcome.result(); exited && !exitAsserted {
			drainContext, cancelDrain := context.WithTimeout(ctx, 250*time.Millisecond)
			_ = session.drainFinal(drainContext, 25*time.Millisecond)
			cancelDrain()
			observation = session.observe()
			if step.Expect != "" && strings.Contains(observation.screen, step.Expect) {
				return nil
			}
			if code < 0 && waitErr != nil {
				return fmt.Errorf("process wait failed while waiting for assertion: %w", waitErr)
			}
			return fmt.Errorf("process exited with code %d before assertion matched", code)
		}
		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-session.outputLimit:
			continue
		case <-ticker.C:
		}
	}
}

func classifyContextError(err error, parent, runContext context.Context) error {
	if parent.Err() != nil {
		return fmt.Errorf("run cancelled: %w", parent.Err())
	}
	if runContext.Err() != nil {
		return fmt.Errorf("run exceeded total timeout: %w", runContext.Err())
	}
	if errors.Is(err, context.DeadlineExceeded) {
		return fmt.Errorf("step timed out: %w", err)
	}
	return err
}
