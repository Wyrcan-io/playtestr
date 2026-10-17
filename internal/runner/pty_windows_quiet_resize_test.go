//go:build windows

package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"testing"

	"golang.org/x/term"
)

func TestWindowsQuietSizeHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_QUIET_SIZE_HELPER") != "1" {
		return
	}
	old, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		os.Exit(2)
	}
	defer term.Restore(int(os.Stdin.Fd()), old)
	fmt.Print("quiet native size ready\r\n")
	for round := 0; round < 4; round++ {
		var value [1]byte
		if _, err := io.ReadFull(os.Stdin, value[:]); err != nil || value[0] != 13 {
			os.Exit(3)
		}
		width, height, err := term.GetSize(int(os.Stdout.Fd()))
		if err != nil {
			os.Exit(4)
		}
		fmt.Printf("\r\nround %d actual native size %dx%d\r\n", round, width, height)
	}
	os.Exit(0)
}

func TestWindowsQuietRepeatedResizeHasNativeDimensionEvidence(t *testing.T) {
	spec := Spec{Version: SpecVersion, Command: []string{os.Args[0], "-test.run=^TestWindowsQuietSizeHelper$"},
		Env: map[string]string{"PLAYTESTR_QUIET_SIZE_HELPER": "1"}, Width: 80, Height: 24,
		TimeoutMS: 5000, RunTimeoutMS: 60000, MaxOutputBytes: 32768,
		Steps: []Step{{Expect: "quiet native size ready"}}}
	for round := 0; round < 4; round++ {
		spec.Steps = append(spec.Steps, Step{Resize: &TerminalSize{Width: 40, Height: 12}},
			Step{Resize: &TerminalSize{Width: 100, Height: 28}}, Step{Key: "Enter"},
			Step{Expect: fmt.Sprintf("round %d actual native size 100x28", round)})
	}
	spec.Steps = append(spec.Steps, Step{Exit: intPointer(0)})
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "quiet-native-resize.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
	if result.Err() != nil {
		t.Fatal(result.Err())
	}
	if !result.Cleanup.ConfirmedExited {
		t.Fatal("native target cleanup unconfirmed")
	}
}
