package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func TestAdversarialTerminalProfileEnvironmentHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_ENVIRONMENT_PROBE") != "1" {
		return
	}
	fmt.Printf("TERMINAL-PROFILE=%s\r\n", os.Getenv("TERM"))
	os.Exit(0)
}

func TestAdversarialTerminalProfileEnvironmentThroughRealPTY(t *testing.T) {
	t.Setenv("TERM", "reviewed-host-profile")
	for _, version := range []int{SpecVersion, WorkspaceSpecVersion} {
		for _, test := range []struct {
			name    string
			literal string
			inherit bool
			want    string
		}{
			{"default-does-not-inherit", "", false, "xterm-256color"},
			{"explicit-literal", "screen-256color", false, "screen-256color"},
			{"explicit-inheritance", "", true, "reviewed-host-profile"},
			{"literal-over-inheritance", "screen-256color", true, "screen-256color"},
		} {
			t.Run(fmt.Sprintf("v%d/%s", version, test.name), func(t *testing.T) {
				spec := Spec{Version: version,
					Command: []string{os.Args[0], "-test.run=^TestAdversarialTerminalProfileEnvironmentHelper$"},
					Env:     map[string]string{"PLAYTESTR_ENVIRONMENT_PROBE": "1"},
					Width:   80, Height: 3, TimeoutMS: 5000, RunTimeoutMS: 10000,
					Steps: []Step{{Expect: "TERMINAL-PROFILE=" + test.want}, {Exit: intPointer(0)}}}
				if test.literal != "" {
					spec.Env["TERM"] = test.literal
				}
				if test.inherit {
					spec.InheritEnv = []string{"TERM"}
				}
				directory := t.TempDir()
				if version == WorkspaceSpecVersion {
					if err := os.Mkdir(filepath.Join(directory, "fixture"), 0700); err != nil {
						t.Fatal(err)
					}
					spec.Workspace = &WorkspaceSpec{Fixture: "fixture", Home: "temporary", Temp: "temporary"}
				}
				data, err := json.Marshal(spec)
				if err != nil {
					t.Fatal(err)
				}
				path := filepath.Join(directory, "profile.json")
				if err := os.WriteFile(path, data, 0600); err != nil {
					t.Fatal(err)
				}
				result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
				if result.Err() != nil {
					t.Fatalf("declared terminal profile was not observed through real PTY: %v", result.Err())
				}
				if !result.Cleanup.ConfirmedExited {
					t.Fatalf("unconfirmed cleanup: %+v", result.Cleanup)
				}
			})
		}
	}
}
