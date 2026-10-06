package runner

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"time"
	"unicode/utf8"
)

const maxRecordText = 64 * 1024

// Recording is an in-memory candidate. Calls are serialized by its controller.
// Target output remains synchronized by the existing terminal session.
type Recording struct {
	spec         Spec
	path         string
	ctx          context.Context
	parent       context.Context
	cancel       context.CancelFunc
	session      *terminalSession
	workspace    *preparedWorkspace
	snapshots    map[string]string
	beforeInput  string
	transition   bool
	replayed     bool
	fixtureHash  [32]byte
	firstFailure *RunResult
	firstScreen  string
	watchDone    chan struct{}
	closeErr     error
}

// StartRecording validates setup and starts only the explicitly declared target.
func StartRecording(ctx context.Context, path string, setup Spec) (*Recording, error) {
	setup.Steps = []Step{{Expect: "recording setup validation"}}
	data, err := json.Marshal(setup)
	if err != nil {
		return nil, err
	}
	spec, err := decodeSpec(data, path)
	if err != nil {
		return nil, err
	}
	spec.Steps = nil
	absolute, err := filepath.Abs(path)
	if err != nil {
		return nil, err
	}
	// macOS /var and /tmp are system symlinks. Resolve the explicitly chosen
	// directory once, then validate canonical paths without following output links.
	if info, statErr := os.Lstat(absolute); statErr == nil && (info.Mode()&os.ModeSymlink != 0 || workspaceReparsePoint(absolute)) {
		return nil, fmt.Errorf("output cannot be a link/junction")
	}
	absolute, err = canonicalRecordPath(absolute)
	if err != nil {
		return nil, err
	}
	if err := safeRecordPath(absolute); err != nil {
		return nil, err
	}
	r := &Recording{spec: spec, path: absolute, snapshots: make(map[string]string), parent: ctx}
	r.ctx, r.cancel = context.WithTimeout(ctx, time.Duration(spec.RunTimeoutMS)*time.Millisecond)
	if spec.Workspace != nil {
		r.fixtureHash, err = r.hashFixture()
		if err != nil {
			r.cancel()
			return nil, err
		}
	}
	if err := r.start(); err != nil {
		return nil, errors.Join(err, r.Close())
	}
	return r, nil
}

func (r *Recording) start() error {
	dir, err := targetDirectory(r.path, r.spec.CWD)
	if err != nil {
		return err
	}
	command, environment := r.spec.Command, targetEnvironment(r.spec)
	if r.spec.Workspace != nil {
		r.workspace, err = prepareWorkspace(r.ctx, r.path, r.spec)
		if err != nil {
			return err
		}
		dir, command = r.workspace.workingDir, r.workspace.command
		environment = targetEnvironmentWithManaged(r.spec, r.workspace.managedEnv)
	}
	r.session, err = startTerminalSession(sessionConfig{command: command, dir: dir, env: environment, width: r.spec.Width, height: r.spec.Height, maxOutputBytes: r.spec.MaxOutputBytes})
	if err == nil {
		session, captureContext, cancel := r.session, r.ctx, r.cancel
		r.watchDone = make(chan struct{})
		done := r.watchDone
		go func() {
			defer close(done)
			select {
			case <-captureContext.Done():
			case <-session.outputLimit:
				cancel()
			}
			stopContext, stopCancel := context.WithTimeout(context.Background(), 3*time.Second)
			defer stopCancel()
			session.stop(stopContext)
		}()
	}
	return err
}

// Context bounds the entire capture, including idle operator time.
func (r *Recording) Context() context.Context {
	if r.session == nil {
		return r.parent
	}
	return r.ctx
}

// InputError preserves target overflow as the cause of an idle input wakeup.
func (r *Recording) InputError(err error) error {
	if r.session != nil && r.session.observe().outputLimitExceeded {
		return errOutputLimit
	}
	return err
}

// Screen returns the normalized rendered viewport, never raw ANSI output.
func (r *Recording) Screen() string {
	if r.session == nil {
		return ""
	}
	return r.session.observe().screen
}

// ResolvedSetup returns the actual launched executable and working directory.
func (r *Recording) ResolvedSetup() (string, string) {
	if r.session == nil {
		return "", ""
	}
	return r.session.cmd.Path, r.session.cmd.Dir
}

// Preview returns the ordinary spec and selected baselines for explicit review.
func (r *Recording) Preview() ([]byte, map[string]string, error) {
	data, err := json.MarshalIndent(r.spec, "", "  ")
	copy := make(map[string]string)
	for _, s := range r.spec.Steps {
		if s.Snapshot != "" {
			copy[s.Snapshot] = r.snapshots[s.Snapshot]
		}
	}
	return append(data, '\n'), copy, err
}

// Capture validates and executes one action before accepting it into the draft.
func (r *Recording) Capture(step Step) error {
	if r.session == nil {
		return fmt.Errorf("capture is closed; use rerecord to start fresh")
	}
	if o := r.session.observe(); o.outputLimitExceeded {
		return errOutputLimit
	}
	if err := r.ctx.Err(); err != nil {
		return err
	}
	if len(step.Text) > maxRecordText || !utf8.ValidString(step.Text) {
		return fmt.Errorf("text must be valid UTF-8 and at most %d bytes", maxRecordText)
	}
	if strings.ContainsAny(step.Text, "\x00\x1b") {
		return fmt.Errorf("text cannot contain NUL or escape sequences; use a named key")
	}
	next := r.spec
	next.Steps = append(append([]Step(nil), r.spec.Steps...), step)
	data, err := json.Marshal(next)
	if err != nil {
		return err
	}
	if _, err := decodeSpec(data, r.path); err != nil {
		return err
	}
	input := step.Key != "" || step.Text != "" || step.Resize != nil
	if input {
		if code, _, exited := r.session.outcome.result(); exited {
			return unexpectedExit("target exited with code %d before recorded input", code)
		}
	}
	if step.Expect != "" {
		if strings.TrimSpace(step.Expect) == "" {
			return fmt.Errorf("checkpoint must identify meaningful content")
		}
		if r.transition && strings.Contains(r.beforeInput, step.Expect) {
			return fmt.Errorf("stale anchor %q was already present before input; choose content identifying the new state", step.Expect)
		}
	}
	if input {
		r.beforeInput = r.Screen()
		r.transition = true
	}
	ctx, cancel := context.WithTimeout(r.ctx, time.Duration(r.spec.TimeoutMS)*time.Millisecond)
	defer cancel()
	updates := newSnapshotUpdates()
	exitAsserted := false
	for _, s := range r.spec.Steps {
		if s.Exit != nil {
			exitAsserted = true
		}
	}
	if err := executeStep(ctx, r.path, step, RunOptions{Update: true}, updates, r.session, exitAsserted); err != nil {
		return fmt.Errorf("capture step %d: %w", len(next.Steps), err)
	}
	if step.Expect != "" && strings.Count(r.Screen(), step.Expect) != 1 {
		return fmt.Errorf("ambiguous anchor: choose text appearing exactly once")
	}
	for path, content := range updates.values {
		r.snapshots[filepath.Base(path)] = content
	}
	r.spec.Steps = next.Steps
	r.replayed = false
	if step.Expect != "" || step.ExpectNot != "" || step.Exit != nil {
		r.transition = false
	}
	return nil
}

// Edit replaces the reviewed step list. Fresh replay is required after any edit.
func (r *Recording) Edit(steps []Step) error {
	next := r.spec
	next.Steps = append([]Step(nil), steps...)
	data, err := json.Marshal(next)
	if err != nil {
		return err
	}
	if _, err := decodeSpec(data, r.path); err != nil {
		return err
	}
	for _, s := range steps {
		if s.Snapshot != "" {
			if _, ok := r.snapshots[s.Snapshot]; !ok {
				return fmt.Errorf("snapshot %q has no captured candidate; rerecord it", s.Snapshot)
			}
		}
	}
	r.spec = next
	r.replayed = false
	return nil
}

// Steps returns a detached step list for control-console maintenance.
func (r *Recording) Steps() []Step {
	data, _ := json.Marshal(r.spec.Steps)
	var steps []Step
	_ = json.Unmarshal(data, &steps)
	return steps
}

// Rerecord retains a prefix, then reconstructs it against a fresh target/fixture.
func (r *Recording) Rerecord(ctx context.Context, prefix int) error {
	if prefix < 0 || prefix > len(r.spec.Steps) {
		return fmt.Errorf("prefix out of range")
	}
	if err := r.Close(); err != nil {
		return err
	}
	r.ctx, r.cancel = context.WithTimeout(ctx, time.Duration(r.spec.RunTimeoutMS)*time.Millisecond)
	r.spec.Steps = r.spec.Steps[:prefix]
	r.replayed, r.transition = false, false
	if err := r.checkFixture(); err != nil {
		return err
	}
	if err := r.start(); err != nil {
		return errors.Join(err, r.Close())
	}
	exited := false
	for _, step := range r.spec.Steps {
		stepCtx, cancel := context.WithTimeout(r.ctx, time.Duration(r.spec.TimeoutMS)*time.Millisecond)
		err := executeStep(stepCtx, r.path, step, RunOptions{recordSnapshots: r.snapshots}, nil, r.session, exited)
		cancel()
		if err != nil {
			return errors.Join(fmt.Errorf("reconstruct prefix: %w", err), r.Close())
		}
		if step.Exit != nil {
			exited = true
		}
		if step.Key != "" || step.Text != "" || step.Resize != nil {
			r.transition = true
		} else if step.Expect != "" || step.ExpectNot != "" || step.Exit != nil {
			r.transition = false
		}
	}
	r.beforeInput = r.Screen()
	return nil
}

// Replay uses the ordinary runner and fresh workspace without persisting drafts.
// The first failure and its screen remain in memory even if a later replay passes.
func (r *Recording) Replay(ctx context.Context, out io.Writer) RunResult {
	r.replayed = false
	if err := r.Close(); err != nil {
		return RunResult{Status: "failed", Failure: failure(FailureCleanup, err), err: err}
	}
	if err := r.checkFixture(); err != nil {
		return RunResult{Status: "failed", Failure: failure(FailureWorkspaceSetup, err), err: err}
	}
	var screen string
	result := RunDetailedContext(ctx, r.path, RunOptions{recordSpec: &r.spec, recordSnapshots: r.snapshots, noArtifacts: true, recordEvidence: &screen}, out)
	if result.Status == "passed" {
		r.replayed = true
	} else if r.firstFailure == nil {
		r.firstFailure = &result
		r.firstScreen = screen
	}
	return result
}

// FirstFailure returns preserved evidence for diagnosis, without disk persistence.
func (r *Recording) FirstFailure() (*RunResult, string) { return r.firstFailure, r.firstScreen }

// Export commits only a freshly replayed, explicitly reviewed candidate. Existing
// specs and baselines are refused; selected maintenance uses test --update instead.
func (r *Recording) Export(ctx context.Context) error {
	if !r.replayed {
		return fmt.Errorf("review and successfully replay the current candidate before export")
	}
	if err := r.checkFixture(); err != nil {
		return err
	}
	data, snapshots, err := r.Preview()
	if err != nil {
		return err
	}
	if _, err := decodeSpec(data, r.path); err != nil {
		return err
	}
	updates := newSnapshotUpdates()
	for name, content := range snapshots {
		if err := updates.stage(filepath.Join(filepath.Dir(r.path), "snapshots", name), content); err != nil {
			return err
		}
	}
	if err := updates.stage(r.path, string(data)); err != nil {
		return err
	}
	for path := range updates.values {
		if err := safeRecordPath(path); err != nil {
			return err
		}
		if _, err := os.Lstat(path); !errors.Is(err, os.ErrNotExist) {
			return fmt.Errorf("refusing to overwrite %s", path)
		}
	}
	if err := ctx.Err(); err != nil {
		return err
	}
	// Exclusive reservation prevents accidental overwrite by concurrent recorders.
	reserved := []string{}
	for path := range updates.values {
		if err := os.MkdirAll(filepath.Dir(path), 0755); err != nil {
			rollbackRecordReservations(reserved)
			return err
		}
		f, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0600)
		if err != nil {
			rollbackRecordReservations(reserved)
			return err
		}
		reserved = append(reserved, path)
		if err := f.Close(); err != nil {
			rollbackRecordReservations(reserved)
			return err
		}
	}
	if err := ctx.Err(); err != nil {
		rollbackRecordReservations(reserved)
		return err
	}
	// Commit snapshots first, spec last. Cancellation/error removes every reserved
	// file. This is a runtime transaction, not a filesystem power-loss guarantee.
	for _, path := range appendRecordSpecLast(reserved, r.path) {
		if err := ctx.Err(); err != nil {
			rollbackRecordReservations(reserved)
			return err
		}
		if err := writeFileAtomic(path, []byte(updates.values[path]), 0644); err != nil {
			rollbackRecordReservations(reserved)
			return err
		}
	}
	if err := ctx.Err(); err != nil {
		rollbackRecordReservations(reserved)
		return err
	}
	return nil
}

func appendRecordSpecLast(paths []string, spec string) []string {
	result := []string{}
	for _, path := range paths {
		if path != spec {
			result = append(result, path)
		}
	}
	return append(result, spec)
}

func rollbackRecordReservations(paths []string) {
	for _, path := range paths {
		_ = os.Remove(path)
	}
}

func safeRecordPath(path string) error {
	if strings.ContainsRune(path, 0) || filepath.Ext(path) == "" {
		return fmt.Errorf("output requires a filename with extension")
	}
	for current := path; ; current = filepath.Dir(current) {
		info, err := os.Lstat(current)
		if err == nil && (info.Mode()&os.ModeSymlink != 0 || workspaceReparsePoint(current)) {
			return fmt.Errorf("recording path contains link/junction: %s", current)
		}
		if err != nil && !errors.Is(err, os.ErrNotExist) {
			return err
		}
		if filepath.Dir(current) == current {
			break
		}
	}
	return nil
}

func canonicalRecordPath(path string) (string, error) {
	parent := filepath.Dir(path)
	missing := []string{filepath.Base(path)}
	for {
		_, err := os.Lstat(parent)
		if err == nil {
			break
		}
		if !errors.Is(err, os.ErrNotExist) {
			return "", err
		}
		missing = append(missing, filepath.Base(parent))
		next := filepath.Dir(parent)
		if next == parent {
			return "", fmt.Errorf("output has no existing parent")
		}
		parent = next
	}
	resolved, err := filepath.EvalSymlinks(parent)
	if err != nil {
		return "", err
	}
	for i := len(missing) - 1; i >= 0; i-- {
		resolved = filepath.Join(resolved, missing[i])
	}
	return resolved, nil
}

func (r *Recording) hashFixture() ([32]byte, error) {
	var zero [32]byte
	if r.spec.Workspace == nil {
		return zero, nil
	}
	// Use the same bounded copier so links, entry/file limits and races are rejected.
	ctx, cancel := context.WithTimeout(context.Background(), workspaceCopyTimeout)
	defer cancel()
	w, err := prepareWorkspace(ctx, r.path, r.spec)
	if err != nil {
		return zero, errors.Join(err, cleanupPreparedWorkspace(w))
	}
	defer cleanupPreparedWorkspace(w)
	h := sha256.New()
	root := filepath.Join(w.root, "fixture")
	err = filepath.WalkDir(root, func(path string, entry os.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(root, path)
		fmt.Fprintf(h, "%d:%s:%t\n", len(rel), filepath.ToSlash(rel), entry.IsDir())
		if !entry.IsDir() {
			data, err := os.ReadFile(path)
			if err != nil {
				return err
			}
			fmt.Fprintf(h, "%d:", len(data))
			h.Write(data)
		}
		return nil
	})
	if err != nil {
		return zero, err
	}
	copy(zero[:], h.Sum(nil))
	return zero, nil
}

func (r *Recording) checkFixture() error {
	hash, err := r.hashFixture()
	if err != nil {
		return err
	}
	if hash != r.fixtureHash {
		return fmt.Errorf("fixture changed since setup; restart recording against the reviewed fixture")
	}
	return nil
}

// Close terminates the entire tracked target tree before removing owned state.
func (r *Recording) Close() error {
	if r.closeErr != nil {
		return r.closeErr
	}
	if r.cancel != nil {
		r.cancel()
	}
	confirmed := true
	var err error
	if r.session != nil {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		cleanup := r.session.stop(ctx)
		cancel()
		confirmed, err = cleanup.confirmedExited, cleanup.err
		r.session = nil
	}
	if r.watchDone != nil {
		<-r.watchDone
		r.watchDone = nil
	}
	if r.workspace != nil {
		if confirmed {
			if cleanupErr := cleanupPreparedWorkspace(r.workspace); cleanupErr != nil {
				err = errors.Join(err, fmt.Errorf("workspace retained at %s after cleanup failure: %w", r.workspace.root, cleanupErr))
			} else {
				r.workspace = nil
			}
		} else {
			err = errors.Join(err, fmt.Errorf("workspace retained because target exit unconfirmed: %s", r.workspace.root))
		}
	}
	r.closeErr = err
	return err
}
