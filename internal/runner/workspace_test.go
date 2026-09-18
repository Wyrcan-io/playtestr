package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

func TestWorkspaceSpecValidation(t *testing.T) {
	tests := []struct {
		name string
		spec Spec
		want string
	}{
		{name: "v1 workspace", spec: workspaceTestSpec(), want: "requires spec version 2"},
		{name: "v2 without workspace", spec: Spec{Version: WorkspaceSpecVersion, Command: []string{os.Args[0]}, Steps: []Step{{Exit: intPointer(0)}}}, want: "requires workspace"},
		{name: "top level cwd", spec: withWorkspaceChange(func(spec *Spec) { spec.CWD = "." }), want: "cannot be combined"},
		{name: "escaping fixture", spec: withWorkspaceChange(func(spec *Spec) { spec.Workspace.Fixture = "../fixture" }), want: "stay below"},
		{name: "absolute cwd", spec: withWorkspaceChange(func(spec *Spec) {
			spec.Workspace.CWD = filepath.VolumeName(os.TempDir()) + string(os.PathSeparator) + "outside"
		}), want: "relative path"},
		{name: "home value", spec: withWorkspaceChange(func(spec *Spec) { spec.Workspace.Home = "shared" }), want: "must be \"temporary\""},
		{name: "managed env conflict", spec: withWorkspaceChange(func(spec *Spec) { spec.Env[managedHomeName()] = "outside" }), want: "conflicts with managed"},
		{name: "managed inherit conflict", spec: withWorkspaceChange(func(spec *Spec) { spec.InheritEnv = []string{managedTempName()} }), want: "conflicts with managed"},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			path := writeWorkspaceSpec(t, test.spec)
			if _, err := Load(path); err == nil || !strings.Contains(err.Error(), test.want) {
				t.Fatalf("Load() error = %v, want %q", err, test.want)
			}
		})
	}
}

func TestWorkspaceRunsTwiceFromFreshFixtureAndCleans(t *testing.T) {
	root := t.TempDir()
	fixture := filepath.Join(root, "fixture")
	if err := os.Mkdir(fixture, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(fixture, "seed.txt"), []byte("reviewed"), 0644); err != nil {
		t.Fatal(err)
	}
	spec := validWorkspaceSpec("workspace-state")
	path := writeWorkspaceSpecAt(t, root, spec)
	for attempt := 1; attempt <= 2; attempt++ {
		var output bytes.Buffer
		result := RunDetailedContext(context.Background(), path, RunOptions{}, &output)
		if err := result.Err(); err != nil {
			t.Fatalf("attempt %d: %v\n%s", attempt, err, output.String())
		}
		if !strings.Contains(output.String(), "PASS") || result.Workspace == nil || !result.Workspace.Prepared || !result.Workspace.Cleaned || result.Workspace.Retained {
			t.Fatalf("attempt %d result = %+v, output=%q", attempt, result.Workspace, output.String())
		}
	}
	if data, err := os.ReadFile(filepath.Join(fixture, "seed.txt")); err != nil || string(data) != "reviewed" {
		t.Fatalf("source seed changed: %q, %v", data, err)
	}
	if _, err := os.Stat(filepath.Join(fixture, "state.txt")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("source fixture was mutated: %v", err)
	}
}

func TestWorkspaceFailureCleanupAndExplicitRetention(t *testing.T) {
	for _, keep := range []bool{false, true} {
		t.Run(map[bool]string{false: "clean", true: "retain"}[keep], func(t *testing.T) {
			root := t.TempDir()
			fixture := filepath.Join(root, "fixture")
			if err := os.Mkdir(fixture, 0755); err != nil {
				t.Fatal(err)
			}
			if err := os.WriteFile(filepath.Join(fixture, "seed.txt"), []byte("reviewed"), 0644); err != nil {
				t.Fatal(err)
			}
			spec := validWorkspaceSpec("workspace-hang")
			spec.TimeoutMS = 100
			spec.Steps = []Step{{Expect: "fresh workspace"}, {Expect: "never"}}
			path := writeWorkspaceSpecAt(t, root, spec)
			result := RunDetailedContext(context.Background(), path, RunOptions{KeepWorkspaceOnFailure: keep}, &bytes.Buffer{})
			if result.Failure == nil || result.Failure.Category != FailureAssertionTimeout || result.Workspace == nil {
				t.Fatalf("result = %+v", result)
			}
			if result.Evidence.ScreenPath == "" {
				t.Fatal("failure screen was not written")
			}
			if keep {
				if !result.Workspace.Retained || result.Workspace.RetainedPath == "" {
					t.Fatalf("workspace not retained: %+v", result.Workspace)
				}
				if _, err := os.Stat(filepath.Join(result.Workspace.RetainedPath, "fixture", "state.txt")); err != nil {
					t.Fatalf("retained target state missing: %v", err)
				}
				if err := os.RemoveAll(result.Workspace.RetainedPath); err != nil {
					t.Fatal(err)
				}
			} else if !result.Workspace.Cleaned || result.Workspace.Retained {
				t.Fatalf("workspace cleanup = %+v", result.Workspace)
			}
		})
	}
}

func TestWorkspaceCleanupFailurePreventsSnapshotCommit(t *testing.T) {
	root := t.TempDir()
	fixture := filepath.Join(root, "fixture")
	if err := os.Mkdir(fixture, 0755); err != nil {
		t.Fatal(err)
	}
	spec := validWorkspaceSpec("workspace-marker-tamper")
	spec.Steps = []Step{{Expect: "workspace ready"}, {Snapshot: "workspace.txt"}}
	path := writeWorkspaceSpecAt(t, root, spec)
	result := RunDetailedContext(context.Background(), path, RunOptions{Update: true}, &bytes.Buffer{})
	if result.Failure == nil || result.Failure.Category != FailureWorkspaceCleanup || result.Workspace == nil || result.Workspace.CleanupFailure == nil || !result.Workspace.Retained {
		t.Fatalf("result = %+v", result)
	}
	baseline := filepath.Join(root, "snapshots", "workspace.txt")
	if _, err := os.Stat(baseline); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("snapshot committed after workspace cleanup failure: %v", err)
	}
	if err := os.RemoveAll(result.Workspace.RetainedPath); err != nil {
		t.Fatal(err)
	}
}

func TestWorkspaceFixtureCopyRejectsUnsafeAndBoundedInputs(t *testing.T) {
	t.Run("cancelled", func(t *testing.T) {
		source := t.TempDir()
		if err := os.WriteFile(filepath.Join(source, "file"), []byte("value"), 0644); err != nil {
			t.Fatal(err)
		}
		ctx, cancel := context.WithCancel(context.Background())
		cancel()
		err := copyWorkspaceFixture(ctx, source, filepath.Join(t.TempDir(), "copy"))
		if err == nil || !strings.Contains(err.Error(), "cancelled") {
			t.Fatalf("error = %v", err)
		}
	})

	t.Run("oversized file", func(t *testing.T) {
		source := t.TempDir()
		file, err := os.Create(filepath.Join(source, "large"))
		if err != nil {
			t.Fatal(err)
		}
		if err := file.Truncate(workspaceMaxFileBytes + 1); err != nil {
			t.Fatal(err)
		}
		_ = file.Close()
		err = copyWorkspaceFixture(context.Background(), source, filepath.Join(t.TempDir(), "copy"))
		if err == nil || !strings.Contains(err.Error(), "exceeds limit") {
			t.Fatalf("error = %v", err)
		}
	})

	t.Run("too many entries", func(t *testing.T) {
		source := t.TempDir()
		for index := 0; index <= workspaceMaxEntries; index++ {
			if err := os.Mkdir(filepath.Join(source, fmt.Sprintf("entry-%04d", index)), 0755); err != nil {
				t.Fatal(err)
			}
		}
		err := copyWorkspaceFixture(context.Background(), source, filepath.Join(t.TempDir(), "copy"))
		if err == nil || !strings.Contains(err.Error(), "filesystem entries") {
			t.Fatalf("error = %v", err)
		}
	})

	t.Run("symbolic link", func(t *testing.T) {
		source := t.TempDir()
		external := filepath.Join(t.TempDir(), "external")
		if err := os.WriteFile(external, []byte("sentinel"), 0644); err != nil {
			t.Fatal(err)
		}
		if err := os.Symlink(external, filepath.Join(source, "link")); err != nil {
			if runtime.GOOS == "windows" {
				t.Skipf("creating a Windows symlink is unavailable: %v", err)
			}
			t.Fatal(err)
		}
		err := copyWorkspaceFixture(context.Background(), source, filepath.Join(t.TempDir(), "copy"))
		if err == nil || !strings.Contains(err.Error(), "symbolic link or junction") {
			t.Fatalf("error = %v", err)
		}
		if data, err := os.ReadFile(external); err != nil || string(data) != "sentinel" {
			t.Fatalf("external sentinel changed: %q, %v", data, err)
		}
	})
}

func TestWorkspaceSetupFailureDoesNotLaunchTarget(t *testing.T) {
	root := t.TempDir()
	spec := validWorkspaceSpec("workspace-state")
	spec.Workspace.Fixture = "missing"
	path := writeWorkspaceSpecAt(t, root, spec)
	result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
	if result.Failure == nil || result.Failure.Category != FailureWorkspaceSetup || result.Target.Exited || result.Cleanup.Attempted {
		t.Fatalf("result = %+v", result)
	}
	if result.Workspace == nil || result.Workspace.Prepared || result.Workspace.SetupFailure == nil {
		t.Fatalf("workspace report = %+v", result.Workspace)
	}
}

func TestWorkspaceLifecycleOutcomesCleanOwnedState(t *testing.T) {
	tests := []struct {
		name       string
		mode       string
		steps      []Step
		configure  func(*Spec)
		wantStatus string
	}{
		{name: "expected nonzero", mode: "exit-seven", steps: []Step{{Expect: "about to crash"}, {Exit: intPointer(7)}}, wantStatus: "passed"},
		{name: "output flood", mode: "flood", steps: []Step{{Expect: "never"}}, configure: func(spec *Spec) { spec.MaxOutputBytes = 4096 }, wantStatus: "failed"},
		{name: "parent child", mode: "parent-child", steps: []Step{{Expect: "child started"}, {Expect: "never"}}, configure: func(spec *Spec) {
			spec.TimeoutMS = 100
			spec.Env["PLAYTESTR_PID_FILE"] = filepath.Join(t.TempDir(), "child.pid")
		}, wantStatus: "failed"},
	}
	for _, test := range tests {
		t.Run(test.name, func(t *testing.T) {
			root := t.TempDir()
			if err := os.Mkdir(filepath.Join(root, "fixture"), 0755); err != nil {
				t.Fatal(err)
			}
			spec := validWorkspaceSpec(test.mode)
			spec.Steps = test.steps
			if test.configure != nil {
				test.configure(&spec)
			}
			result := RunDetailedContext(context.Background(), writeWorkspaceSpecAt(t, root, spec), RunOptions{}, &bytes.Buffer{})
			if result.Status != test.wantStatus || result.Workspace == nil || !result.Workspace.Cleaned || result.Workspace.Retained {
				t.Fatalf("result = %+v", result)
			}
		})
	}
}

func TestWorkspaceCancellationCleansAfterTarget(t *testing.T) {
	root := t.TempDir()
	fixture := filepath.Join(root, "fixture")
	if err := os.Mkdir(fixture, 0755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(fixture, "seed.txt"), []byte("reviewed"), 0644); err != nil {
		t.Fatal(err)
	}
	spec := validWorkspaceSpec("workspace-hang")
	spec.Steps = []Step{{Expect: "fresh workspace"}, {Expect: "never"}}
	ctx, cancel := context.WithCancel(context.Background())
	time.AfterFunc(time.Second, cancel)
	result := RunDetailedContext(ctx, writeWorkspaceSpecAt(t, root, spec), RunOptions{}, &bytes.Buffer{})
	if result.Status != "cancelled" || result.Workspace == nil || !result.Workspace.Cleaned || !result.Cleanup.ConfirmedExited {
		t.Fatalf("result = %+v", result)
	}
}

func TestWorkspaceCommandResolutionPrecedesFixtureCWD(t *testing.T) {
	root := t.TempDir()
	programName := "chosen"
	if runtime.GOOS == "windows" {
		programName += ".exe"
	}
	program := filepath.Join(root, programName)
	if err := os.WriteFile(program, []byte("program"), 0755); err != nil {
		t.Fatal(err)
	}
	t.Setenv("PATH", root+string(os.PathListSeparator)+os.Getenv("PATH"))
	resolved, err := resolveWorkspaceCommand(filepath.Join(root, "spec.json"), []string{programName})
	if err != nil {
		t.Fatal(err)
	}
	if filepath.Clean(resolved[0]) != filepath.Clean(program) {
		t.Fatalf("resolved command = %q, want %q", resolved[0], program)
	}
}

func TestWorkspaceCleanupHonorsCancellation(t *testing.T) {
	root, err := os.MkdirTemp("", "playtestr-workspace-")
	if err != nil {
		t.Fatal(err)
	}
	workspace := &preparedWorkspace{root: root, token: "owned"}
	if err := os.WriteFile(filepath.Join(root, workspaceMarker), []byte(workspace.token), 0600); err != nil {
		t.Fatal(err)
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	if err := workspace.cleanup(ctx); err == nil || !strings.Contains(err.Error(), "cancelled") {
		t.Fatalf("cleanup error = %v", err)
	}
	if _, err := os.Stat(root); err != nil {
		t.Fatalf("cancelled cleanup removed root: %v", err)
	}
	if err := os.RemoveAll(root); err != nil {
		t.Fatal(err)
	}
}

func validWorkspaceSpec(mode string) Spec {
	return Spec{
		Version: WorkspaceSpecVersion, Name: mode,
		Command:   []string{os.Args[0], "-test.run=TestHelperProcess", "--", mode},
		Env:       map[string]string{"PLAYTESTR_HELPER_PROCESS": "1"},
		Workspace: &WorkspaceSpec{Fixture: "fixture", CWD: ".", Home: "temporary", Temp: "temporary"},
		Width:     60, Height: 10, TimeoutMS: 3000, RunTimeoutMS: 10000, MaxOutputBytes: 100000,
		Steps: []Step{{Expect: "fresh workspace seed=reviewed home=true temp=true"}, {Exit: intPointer(0)}},
	}
}

func workspaceTestSpec() Spec {
	spec := validWorkspaceSpec("workspace-state")
	spec.Version = SpecVersion
	return spec
}

func withWorkspaceChange(change func(*Spec)) Spec {
	spec := validWorkspaceSpec("workspace-state")
	change(&spec)
	return spec
}

func writeWorkspaceSpec(t *testing.T, spec Spec) string {
	t.Helper()
	root := t.TempDir()
	if err := os.Mkdir(filepath.Join(root, "fixture"), 0755); err != nil {
		t.Fatal(err)
	}
	return writeWorkspaceSpecAt(t, root, spec)
}

func writeWorkspaceSpecAt(t *testing.T, root string, spec Spec) string {
	t.Helper()
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(root, "workspace.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	return path
}

func managedHomeName() string {
	if runtime.GOOS == "windows" {
		return "USERPROFILE"
	}
	return "HOME"
}

func managedTempName() string {
	if runtime.GOOS == "windows" {
		return "TEMP"
	}
	return "TMPDIR"
}
