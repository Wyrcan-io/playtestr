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
	"syscall"
	"testing"
	"time"

	"github.com/Wyrcan-io/playtestr/internal/console"
)

func TestNavigationInputHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_NAVIGATION_INPUT_HELPER") != "1" {
		return
	}
	input, err := console.Open(os.Stdin)
	if err != nil {
		os.Exit(2)
	}
	defer input.Close()
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	fmt.Print("standard navigation ready\r\n")
	var pending []byte
	for _, want := range []string{"Home", "End", "PageUp", "PageDown"} {
		for {
			data, err := input.Read(ctx)
			if err != nil {
				os.Exit(3)
			}
			pending = append(pending, data...)
			events, rest, err := console.Decode(pending, false)
			if err != nil {
				os.Exit(4)
			}
			pending = rest
			if len(events) == 0 {
				continue
			}
			if len(events) != 1 || events[0].Key != want || events[0].Text != "" {
				fmt.Printf("unexpected navigation event: %+v\r\n", events)
				os.Exit(5)
			}
			fmt.Printf("navigation %s confirmed\r\n", want)
			break
		}
	}
	// Shift+Home is deliberately outside the supported named-key contract.
	// A native operator reader must reject it rather than silently record Home.
	for {
		data, readErr := input.Read(ctx)
		if readErr != nil {
			// ERROR_NOT_SUPPORTED is 50 on Windows. EOF, cancellation,
			// deadline expiry and other reader failures are not rejection proof.
			if runtime.GOOS != "windows" || !errors.Is(readErr, syscall.Errno(50)) {
				os.Exit(7)
			}
			fmt.Print("modified navigation rejected\r\n")
			break
		}
		pending = append(pending, data...)
		events, rest, decodeErr := console.Decode(pending, false)
		pending = rest
		if decodeErr != nil {
			fmt.Print("modified navigation rejected\r\n")
			break
		}
		if len(events) != 0 {
			fmt.Printf("modified navigation silently changed: %+v\r\n", events)
			os.Exit(6)
		}
	}
	os.Exit(0)
}

func TestAdversarialStandardNavigationKeys(t *testing.T) {
	spec := Spec{Version: SpecVersion, Command: []string{os.Args[0], "-test.run=^TestNavigationInputHelper$"},
		Env: map[string]string{"PLAYTESTR_NAVIGATION_INPUT_HELPER": "1"}, Width: 80, Height: 24,
		TimeoutMS: 5000, RunTimeoutMS: 30000, MaxOutputBytes: 100000,
		Steps: []Step{{Expect: "standard navigation ready"}}}
	for _, key := range []string{"Home", "End", "PageUp", "PageDown"} {
		spec.Steps = append(spec.Steps, Step{Key: key}, Step{Expect: "navigation " + key + " confirmed"})
	}
	spec.Steps = append(spec.Steps, Step{Text: "\x1b[1;2H"}, Step{Expect: "modified navigation rejected"}, Step{Exit: intPointer(0)})
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "navigation.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	result := RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
	if result.Err() != nil || !result.Cleanup.ConfirmedExited {
		t.Fatalf("standard navigation input failed: %v; cleanup=%+v", result.Err(), result.Cleanup)
	}
}
