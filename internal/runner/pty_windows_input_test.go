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

func TestWindowsEnterExactByteHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_WIN32_KEYS_HELPER") != "1" {
		return
	}
	old, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		os.Exit(2)
	}
	defer term.Restore(int(os.Stdin.Fd()), old)
	fmt.Print("native exact input ready\r\n")
	for i, want := range []byte{13, 10, 13} {
		var value [1]byte
		if _, err := io.ReadFull(os.Stdin, value[:]); err != nil || value[0] != want {
			os.Exit(3)
		}
		fmt.Printf("byte-%d-confirmed %02x\r\n", i, value[0])
	}
	os.Exit(0)
}

func TestWindowsEnterAndCtrlJRemainDistinctThroughRealPTY(t *testing.T) {
	for i := 0; i < 10; i++ {
		spec := Spec{Version: SpecVersion, Command: []string{os.Args[0], "-test.run=^TestWindowsEnterExactByteHelper$"},
			Env: map[string]string{"PLAYTESTR_WIN32_KEYS_HELPER": "1"}, Width: 80, Height: 24,
			TimeoutMS: 5000, RunTimeoutMS: 15000, MaxOutputBytes: 100000,
			Steps: []Step{{Expect: "native exact input ready"}, {Resize: &TerminalSize{Width: 100, Height: 30}},
				{Key: "Enter"}, {Expect: "byte-0-confirmed 0d"}, {Key: "CtrlJ"}, {Expect: "byte-1-confirmed 0a"},
				{Key: "Enter"}, {Expect: "byte-2-confirmed 0d"}, {Exit: intPointer(0)}}}
		data, err := json.Marshal(spec)
		if err != nil {
			t.Fatal(err)
		}
		path := filepath.Join(t.TempDir(), "exact-input.json")
		if err := os.WriteFile(path, data, 0600); err != nil {
			t.Fatal(err)
		}
		result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
		if result.Err() != nil {
			t.Fatal(result.Err())
		}
		if !result.Cleanup.ConfirmedExited {
			t.Fatal("unconfirmed native cleanup")
		}
	}
}
