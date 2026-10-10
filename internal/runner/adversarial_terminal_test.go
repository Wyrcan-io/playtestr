package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"
)

// The target writes real terminal control streams, never a mocked screen.
// Native PTYs may coalesce writes; the target's write boundaries are deliberate.
func TestAdversarialTerminalHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_TERMINAL_FAULT") == "" {
		return
	}
	var chunks []string
	switch os.Getenv("PLAYTESTR_TERMINAL_FAULT") {
	case "split":
		chunks = []string{"obsolete", "\x1b[", "2J\x1b[", "Hcaf\xc3", "\xa9 \xe9", "\x9b", "\xaa X", "\x1b[2;1Hsplit complete"}
	case "alternate":
		chunks = []string{"main preserved", "\x1b[?1049h\x1b[2J\x1b[Htemporary overlay", "\x1b[?1049l", "\x1b[2;1Hrestored complete"}
	case "scroll":
		chunks = []string{"obsolete row\r\n", "second row\r\n", "third row\r\n", "fourth row\r\n", "fifth row", "\x1b[1;1H\x1b[2Kfinal row", "\x1b[3;1Hscroll complete\x1b[K"}
	case "malformed":
		chunks = []string{"\x1b[999999999999999999999999999999999999A", "\x1b[2J\x1b[Hmalformed bounded", "\x1b["}
	case "wrap":
		chunks = []string{"12345678901234567890ABCDEFGHIJ", "\x1b[3;1Hwrap complete"}
	default:
		os.Exit(8)
	}
	for _, chunk := range chunks {
		_, _ = fmt.Print(chunk)
		time.Sleep(15 * time.Millisecond)
	}
	os.Exit(0)
}

func TestAdversarialTerminalStreamsThroughRealPTY(t *testing.T) {
	for _, test := range []struct{ mode, baseline string }{
		{"split", "café 雪 X\nsplit complete\n"},
		{"alternate", "main preserved\nrestored complete\n"},
		{"scroll", "final row\nfourth row\nscroll complete\n"},
		{"malformed", "malformed bounded\n"},
		{"wrap", "12345678901234567890\nABCDEFGHIJ\nwrap complete\n"},
	} {
		t.Run(test.mode, func(t *testing.T) {
			spec := Spec{Version: SpecVersion, Command: []string{os.Args[0], "-test.run=^TestAdversarialTerminalHelper$"},
				Env: map[string]string{"PLAYTESTR_TERMINAL_FAULT": test.mode}, Width: 20, Height: 3,
				TimeoutMS: 5000, RunTimeoutMS: 10000, MaxOutputBytes: 100000,
				Steps: []Step{{Exit: intPointer(0)}, {Snapshot: "expected.txt"}}}
			data, err := json.Marshal(spec)
			if err != nil {
				t.Fatal(err)
			}
			path := filepath.Join(t.TempDir(), "stream.json")
			if err := os.WriteFile(path, data, 0600); err != nil {
				t.Fatal(err)
			}
			writeBaseline(t, path, "expected.txt", test.baseline)
			result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
			if result.Err() != nil {
				t.Fatalf("real PTY %s: %v", test.mode, result.Err())
			}
			if !result.Cleanup.ConfirmedExited {
				t.Fatalf("unconfirmed cleanup: %+v", result.Cleanup)
			}
		})
	}
}
