package runner

import (
	"bytes"
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

const (
	SpecVersion  = 1
	maxSpecBytes = 1_000_000
	maxSpecSteps = 1_000
)

// Step contains exactly one terminal action or assertion.
type Step struct {
	Key      string        `json:"key,omitempty"`
	Text     string        `json:"text,omitempty"`
	Expect   string        `json:"expect,omitempty"`
	Snapshot string        `json:"snapshot,omitempty"`
	Exit     *int          `json:"exit,omitempty"`
	Resize   *TerminalSize `json:"resize,omitempty"`
}

// TerminalSize is a terminal viewport measured in columns and rows.
type TerminalSize struct {
	Width  int `json:"width"`
	Height int `json:"height"`
}

// RunOptions controls deliberate baseline updates for one spec.
type RunOptions struct {
	Update   bool
	Snapshot string
}

// Spec describes one target process and its ordered terminal interactions.
type Spec struct {
	Version          int               `json:"version"`
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
		return spec, fmt.Errorf("open spec: %w", err)
	}
	defer file.Close()
	data, err := io.ReadAll(io.LimitReader(file, maxSpecBytes+1))
	if err != nil {
		return spec, fmt.Errorf("read spec: %w", err)
	}
	if len(data) > maxSpecBytes {
		return spec, fmt.Errorf("spec exceeds %d bytes", maxSpecBytes)
	}
	data = bytes.TrimPrefix(data, []byte{0xef, 0xbb, 0xbf})
	decoder := json.NewDecoder(bytes.NewReader(data))
	decoder.DisallowUnknownFields()
	if err = decoder.Decode(&spec); err != nil {
		return spec, fmt.Errorf("decode spec: %w", err)
	}
	var extra any
	if decoder.Decode(&extra) != io.EOF {
		return spec, fmt.Errorf("expected one JSON object")
	}
	if spec.Version == 0 {
		return spec, fmt.Errorf("spec version is required; add \"version\": %d", SpecVersion)
	}
	if spec.Version != SpecVersion {
		return spec, fmt.Errorf("unsupported spec version %d; this runner supports version %d", spec.Version, SpecVersion)
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
	if len(spec.Steps) > maxSpecSteps {
		return spec, fmt.Errorf("steps exceeds limit of %d", maxSpecSteps)
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
	ready := false
	seenSnapshots := make(map[string]struct{})
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
		if step.Resize != nil {
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
		if step.Resize != nil {
			if err := validateTerminalSize(step.Resize.Width, step.Resize.Height); err != nil {
				return spec, fmt.Errorf("step %d resize: %w", i+1, err)
			}
		}
		switch {
		case step.Key != "" || step.Text != "" || step.Resize != nil:
			ready = false
		case step.Expect != "" || step.Exit != nil:
			ready = true
		case step.Snapshot != "":
			if !ready {
				return spec, fmt.Errorf("step %d snapshot %q requires a successful expect since the last input or resize, or a successful exit assertion", i+1, step.Snapshot)
			}
			if _, exists := seenSnapshots[step.Snapshot]; exists {
				return spec, fmt.Errorf("step %d snapshot %q is used more than once", i+1, step.Snapshot)
			}
			seenSnapshots[step.Snapshot] = struct{}{}
			if len(seenSnapshots) > maxStagedSnapshots {
				return spec, fmt.Errorf("snapshot steps exceed limit of %d", maxStagedSnapshots)
			}
		}
	}
	return spec, nil
}

func validateTerminalSize(width, height int) error {
	if width < 1 || width > 500 || height < 1 || height > 200 {
		return fmt.Errorf("terminal dimensions must be width 1-500 and height 1-200")
	}
	return nil
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
	return RunDetailedContext(context.Background(), path, RunOptions{Update: update}, out).Err()
}

// RunContext executes a spec and stops its process tree when the context ends.
func RunContext(parent context.Context, path string, update bool, out io.Writer) (runErr error) {
	return RunDetailedContext(parent, path, RunOptions{Update: update}, out).Err()
}

// RunContextWithOptions executes a spec with explicit snapshot update options.
func RunContextWithOptions(parent context.Context, path string, options RunOptions, out io.Writer) (runErr error) {
	return RunDetailedContext(parent, path, options, out).Err()
}

// RunDetailedContext executes one spec and returns a stable structured result.
func RunDetailedContext(parent context.Context, path string, options RunOptions, out io.Writer) (result RunResult) {
	started := time.Now()
	result = RunResult{Name: filepath.Base(path), SpecPath: filepath.Clean(path), Status: "failed"}
	defer func() { result.DurationMS = time.Since(started).Milliseconds() }()
	setFailure := func(category FailureCategory, err error) {
		result.err = err
		result.Failure = failure(category, err)
		if category == FailureCancellation {
			result.Status = "cancelled"
		}
	}
	if err := parent.Err(); err != nil {
		runErr := withCategory(FailureCancellation, fmt.Errorf("run cancelled: %w", err))
		setFailure(FailureCancellation, runErr)
		return result
	}
	spec, err := Load(path)
	if err != nil {
		runErr := withCategory(FailureInvalidSpec, err)
		setFailure(FailureInvalidSpec, runErr)
		return result
	}
	result.SpecVersion = spec.Version
	result.Name = spec.Name
	result.Viewport = TerminalSize{Width: spec.Width, Height: spec.Height}
	result.Steps = make([]StepResult, len(spec.Steps))
	for i, step := range spec.Steps {
		result.Steps[i] = StepResult{Number: i + 1, Action: stepAction(step), Status: "not_run", Resize: step.Resize}
	}
	if options.Snapshot != "" {
		if !options.Update {
			runErr := withCategory(FailureInvalidSpec, fmt.Errorf("snapshot selector requires update mode"))
			setFailure(FailureInvalidSpec, runErr)
			return result
		}
		found := false
		for _, step := range spec.Steps {
			if step.Snapshot == options.Snapshot {
				found = true
				break
			}
		}
		if !found {
			runErr := withCategory(FailureInvalidSpec, fmt.Errorf("snapshot %q is not referenced by %s", options.Snapshot, path))
			setFailure(FailureInvalidSpec, runErr)
			return result
		}
	}
	dir, err := targetDirectory(path, spec.CWD)
	if err != nil {
		runErr := withCategory(FailureInvalidSpec, err)
		setFailure(FailureInvalidSpec, runErr)
		return result
	}
	runContext, cancelRun := context.WithTimeout(parent, time.Duration(spec.RunTimeoutMS)*time.Millisecond)
	defer cancelRun()
	session, err := startTerminalSession(sessionConfig{
		command: spec.Command, dir: dir, env: targetEnvironment(spec), width: spec.Width,
		height: spec.Height, maxOutputBytes: spec.MaxOutputBytes,
	})
	if err != nil {
		runErr := withCategory(FailureLaunch, err)
		setFailure(FailureLaunch, runErr)
		return result
	}
	var runErr error

	if spec.StartupTimeoutMS > 0 {
		startupContext, cancelStartup := context.WithTimeout(runContext, time.Duration(spec.StartupTimeoutMS)*time.Millisecond)
		err = waitForStartup(startupContext, session)
		cancelStartup()
		if err != nil {
			runErr = fmt.Errorf("%s: startup: %w", spec.Name, classifyContextError(err, parent, runContext))
		}
	}

	exitAsserted := false
	updates := newSnapshotUpdates()
	if runErr == nil {
		for i, step := range spec.Steps {
			stepStarted := time.Now()
			result.Steps[i].Status = "running"
			stepContext, cancelStep := context.WithTimeout(runContext, time.Duration(spec.TimeoutMS)*time.Millisecond)
			err = executeStep(stepContext, path, step, options, updates, session, exitAsserted)
			cancelStep()
			result.Steps[i].DurationMS = time.Since(stepStarted).Milliseconds()
			if err != nil {
				runErr = fmt.Errorf("%s: step %d: %w", spec.Name, i+1, classifyContextError(err, parent, runContext))
				result.Steps[i].Status = "failed"
				result.Steps[i].Failure = failure(categoryOf(runErr), runErr)
				break
			}
			result.Steps[i].Status = "passed"
			if step.Exit != nil {
				exitAsserted = true
			}
			if step.Resize != nil {
				result.Resizes = append(result.Resizes, *step.Resize)
			}
			fmt.Fprintf(out, "  PASS step %d\n", i+1)
		}
	}
	if runErr == nil && parent.Err() != nil {
		runErr = withCategory(FailureCancellation, fmt.Errorf("%s: run cancelled: %w", spec.Name, parent.Err()))
	}

	if runErr == nil && !exitAsserted {
		observation := session.observe()
		if observation.outputLimitExceeded {
			runErr = withCategory(FailureOutputLimit, fmt.Errorf("%s: %w (%d bytes observed)", spec.Name, errOutputLimit, observation.outputBytes))
		} else if code, waitErr, exited := session.outcome.result(); exited {
			if code < 0 && waitErr != nil {
				runErr = withCategory(FailureUnexpectedExit, fmt.Errorf("%s: process wait failed: %w", spec.Name, waitErr))
			} else {
				runErr = withCategory(FailureUnexpectedExit, fmt.Errorf("%s: %w", spec.Name, unexpectedExit("process exited with code %d without an exit assertion", code)))
			}
		}
	}

	cleanupContext, cancelCleanup := context.WithTimeout(context.Background(), 3*time.Second)
	cleanup := session.stop(cleanupContext)
	cancelCleanup()
	result.Cleanup = CleanupReport{
		Attempted: cleanup.attempted, Graceful: cleanup.graceful, Forced: cleanup.forced,
		ConfirmedExited: cleanup.confirmedExited, Mechanism: cleanup.mechanism,
	}
	if cleanup.err != nil {
		cleanupErr := withCategory(FailureCleanup, fmt.Errorf("cleanup failed: %w", cleanup.err))
		result.Cleanup.Failure = failure(FailureCleanup, cleanupErr)
		if runErr == nil {
			runErr = cleanupErr
		} else {
			runErr = errors.Join(runErr, cleanupErr)
		}
	}
	if code, _, exited := session.outcome.result(); exited {
		result.Target.Exited = true
		if code >= 0 {
			result.Target.ExitCode = new(int)
			*result.Target.ExitCode = code
		}
	}
	if runErr == nil && parent.Err() != nil {
		runErr = withCategory(FailureCancellation, fmt.Errorf("%s: run cancelled: %w", spec.Name, parent.Err()))
	}
	if runErr == nil {
		if err := commitSnapshotUpdates(updates, out); err != nil {
			runErr = withCategory(FailureSnapshotUpdate, fmt.Errorf("commit snapshot updates: %w", err))
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
		var mismatch *snapshotMismatchError
		if errors.As(runErr, &mismatch) {
			observation.screen = mismatch.actual
			diffArtifact := path + ".diff.txt"
			if writeErr := writeFileAtomic(diffArtifact, []byte(mismatch.diff), 0644); writeErr == nil {
				result.Evidence.DiffPath = filepath.Clean(diffArtifact)
				fmt.Fprintf(out, "Diff saved: %s\n", diffArtifact)
			} else {
				artifactErr := fmt.Errorf("write snapshot diff: %w", writeErr)
				result.Evidence.Failures = append(result.Evidence.Failures, *failure(FailureArtifact, artifactErr))
				runErr = errors.Join(runErr, withCategory(FailureArtifact, artifactErr))
			}
		}
		artifact := path + ".actual.txt"
		if writeErr := writeFileAtomic(artifact, []byte(observation.screen), 0644); writeErr == nil {
			result.Evidence.ScreenPath = filepath.Clean(artifact)
			fmt.Fprintf(out, "Screen saved: %s\n", artifact)
		} else {
			artifactErr := fmt.Errorf("write failure screen: %w", writeErr)
			result.Evidence.Failures = append(result.Evidence.Failures, *failure(FailureArtifact, artifactErr))
			runErr = errors.Join(runErr, withCategory(FailureArtifact, artifactErr))
		}
		category := categoryOf(runErr)
		setFailure(category, runErr)
		return result
	}
	result.Status = "passed"
	fmt.Fprintf(out, "PASS %s\n", spec.Name)
	return result
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
			return unexpectedExit("process wait failed: %v", waitErr)
		}
		return unexpectedExit("process exited with code %d before producing output", code)
	case <-ctx.Done():
		return fmt.Errorf("timed out waiting for first output: %w", ctx.Err())
	}
}

func executeStep(ctx context.Context, specPath string, step Step, options RunOptions, updates *snapshotUpdates, session *terminalSession, exitAsserted bool) error {
	if step.Key != "" {
		return session.send(ctx, keys[step.Key])
	}
	if step.Text != "" {
		return session.send(ctx, step.Text)
	}
	if step.Resize != nil {
		return session.resize(ctx, step.Resize.Width, step.Resize.Height)
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
			return unexpectedExit("expected exit code %d, got %d", *step.Exit, code)
		}
		if code < 0 && waitErr != nil {
			return fmt.Errorf("process wait failed: %w", waitErr)
		}
		return nil
	}

	var expected []byte
	base := filepath.Join(filepath.Dir(specPath), "snapshots")
	updateSnapshot := options.Update && (options.Snapshot == "" || options.Snapshot == step.Snapshot)
	if step.Snapshot != "" && !updateSnapshot {
		var err error
		expected, err = readSnapshot(filepath.Join(base, step.Snapshot))
		if err != nil {
			if errors.Is(err, os.ErrNotExist) {
				return withCategory(FailureArtifact, fmt.Errorf("snapshot %q is missing (create it with --update): %w", step.Snapshot, err))
			}
			return withCategory(FailureArtifact, fmt.Errorf("read snapshot %q: %w", step.Snapshot, err))
		}
		expected = []byte(normalize(string(expected)))
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
			if updateSnapshot {
				return updates.stage(filepath.Join(base, step.Snapshot), observation.screen)
			}
			if observation.screen == string(expected) {
				return nil
			}
			return newSnapshotMismatch(step.Snapshot, string(expected), observation.screen)
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
				return unexpectedExit("process wait failed while waiting for assertion: %v", waitErr)
			}
			return unexpectedExit("process exited with code %d before assertion matched", code)
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
		return withCategory(FailureCancellation, fmt.Errorf("run cancelled: %w", parent.Err()))
	}
	if runContext.Err() != nil {
		return withCategory(FailureRunTimeout, fmt.Errorf("run exceeded total timeout: %w", runContext.Err()))
	}
	if errors.Is(err, context.DeadlineExceeded) {
		return withCategory(FailureAssertionTimeout, fmt.Errorf("step timed out: %w", err))
	}
	var alreadyCategorized *categorizedError
	if errors.As(err, &alreadyCategorized) {
		return err
	}
	if errors.Is(err, errOutputLimit) {
		return withCategory(FailureOutputLimit, err)
	}
	var mismatch *snapshotMismatchError
	if errors.As(err, &mismatch) {
		return withCategory(FailureSnapshotMismatch, err)
	}
	var exited *unexpectedExitError
	if errors.As(err, &exited) {
		return withCategory(FailureUnexpectedExit, err)
	}
	return withCategory(FailureInternal, err)
}
