//go:build !windows

package runner

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/charmbracelet/x/xpty"
	"golang.org/x/term"
)

func TestTerminalReplyPTYHelper(t *testing.T) {
	mode := os.Getenv("PLAYTESTR_TERMINAL_REPLY_HELPER")
	if mode == "" {
		return
	}
	old, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		os.Exit(9)
	}
	defer term.Restore(int(os.Stdin.Fd()), old)
	if mode == "flood" {
		fmt.Print("reply flood started\r\n")
		for {
			fmt.Print(strings.Repeat("\x1b[c", 4096))
		}
	}
	for round := 0; round < 8; round++ {
		// Unsupported queries must not inject bytes ahead of supported replies.
		fmt.Print("\x1b]4;1;?\x07\x1b]10;?\x07\x1b]11;?\x07\x1b[6n\x1b[5n\x1b[>c\x1b[c")
		for _, expected := range []string{
			"\x1b]10;rgb:0000/0000/0000\x07", "\x1b]11;rgb:0000/0000/0101\x07",
			"\x1b[1;1R", "\x1b[0n", "\x1b[?6c",
		} {
			reply := make([]byte, len(expected))
			if _, err := io.ReadFull(os.Stdin, reply); err != nil || string(reply) != expected {
				os.Exit(12)
			}
		}
	}
	fmt.Print("\x1b[H\x1b[2Jquery startup ready\r\n")
	var key [1]byte
	if _, err := io.ReadFull(os.Stdin, key[:]); err != nil || key[0] != 'x' {
		os.Exit(13)
	}
	fmt.Print("\x1b[c")
	reply := make([]byte, len("\x1b[?6c"))
	if _, err := io.ReadFull(os.Stdin, reply); err != nil || string(reply) != "\x1b[?6c" {
		os.Exit(14)
	}
	fmt.Print("query and normal input verified\r\n")
	os.Exit(0)
}

func primaryReplySpec(t *testing.T, mode string, cap int64, expected int) RunResult {
	t.Helper()
	steps := []Step{{Expect: "query startup ready"}, {Text: "x"}, {Expect: "query and normal input verified"}, {Exit: intPointer(expected)}}
	if mode == "flood" {
		steps = []Step{{Expect: "never emitted completion"}}
	}
	spec := Spec{Version: SpecVersion, Command: []string{os.Args[0], "-test.run=^TestTerminalReplyPTYHelper$"},
		Env: map[string]string{"PLAYTESTR_TERMINAL_REPLY_HELPER": mode}, Width: 80, Height: 24,
		TimeoutMS: 3000, RunTimeoutMS: 15000, MaxOutputBytes: cap, Steps: steps}
	data, err := json.Marshal(spec)
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "reply.json")
	if err := os.WriteFile(path, data, 0600); err != nil {
		t.Fatal(err)
	}
	return RunDetailedContext(context.Background(), path, RunOptions{}, &bytes.Buffer{})
}

func TestTerminalReplyRealPTYStartupAndExactExit(t *testing.T) {
	for _, expected := range []int{0, 7} {
		result := primaryReplySpec(t, "exchange", 100000, expected)
		if expected == 0 && result.Err() != nil {
			t.Fatal(result.Err())
		}
		if expected != 0 && (result.Failure == nil || result.Failure.Category != FailureUnexpectedExit) {
			t.Fatalf("wrong expected exit must fail: %+v", result)
		}
		if !result.Cleanup.ConfirmedExited {
			t.Fatalf("unconfirmed cleanup: %+v", result.Cleanup)
		}
	}
}

func TestTerminalReplyFloodPreservesOutputLimit(t *testing.T) {
	result := primaryReplySpec(t, "flood", 4096, 0)
	if result.Failure == nil || result.Failure.Category != FailureOutputLimit || !result.Cleanup.ConfirmedExited {
		t.Fatalf("query flood must fail accurately and clean up: %+v", result)
	}
}

func TestTerminalReplyBlockedWriterStopsWithinCleanup(t *testing.T) {
	session, err := startTerminalSession(sessionConfig{
		command: []string{os.Args[0], "-test.run=^TestTerminalReplyPTYHelper$"},
		env:     append(os.Environ(), "PLAYTESTR_TERMINAL_REPLY_HELPER=flood"), width: 80, height: 24, maxOutputBytes: 2000000})
	if err != nil {
		t.Fatal(err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		session.stop(ctx)
	}()
	select {
	case <-session.firstOutput:
	case <-time.After(5 * time.Second):
		t.Fatal("query helper never became observable")
	}
	// Wait for actual backpressure, without assuming a host's PTY buffer size.
	deadline := time.Now().Add(5 * time.Second)
	for len(session.replyQueue) < cap(session.replyQueue) && time.Now().Before(deadline) {
		time.Sleep(time.Millisecond)
	}
	if len(session.replyQueue) != cap(session.replyQueue) {
		t.Fatal("real PTY reply queue did not reach backpressure")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	cleanup := session.stop(ctx)
	if cleanup.err != nil || !cleanup.confirmedExited {
		t.Fatalf("blocked reply cleanup: %+v; error: %v", cleanup, cleanup.err)
	}
	select {
	case <-session.replyDone:
	default:
		t.Fatal("reply writer survived cleanup")
	}
	select {
	case <-session.readerDone:
	default:
		t.Fatal("terminal reader survived cleanup")
	}
}

type primaryReplyWriteFailurePTY struct{ xpty.Pty }

func (p primaryReplyWriteFailurePTY) Write(value []byte) (int, error) {
	if bytes.Contains(value, []byte("\x1b[?6c")) {
		return 0, io.ErrClosedPipe
	}
	return p.Pty.Write(value)
}

func TestTerminalReplyTransportErrorIsPreservedWithRealTarget(t *testing.T) {
	pty, err := newTerminalPty(80, 24)
	if err != nil {
		t.Fatal(err)
	}
	session, err := startTerminalSessionWithPTY(sessionConfig{
		command: []string{os.Args[0], "-test.run=^TestTerminalReplyPTYHelper$"},
		env:     append(os.Environ(), "PLAYTESTR_TERMINAL_REPLY_HELPER=exchange"), width: 80, height: 24, maxOutputBytes: 100000},
		primaryReplyWriteFailurePTY{pty})
	if err != nil {
		t.Fatal(err)
	}
	defer func() {
		ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
		defer cancel()
		session.stop(ctx)
	}()
	select {
	case <-session.replyDone:
	case <-time.After(5 * time.Second):
		t.Fatal("injected reply transport failure was not observed")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	cleanup := session.stop(ctx)
	if cleanup.err == nil || !strings.Contains(cleanup.err.Error(), "write terminal reply") || !cleanup.confirmedExited {
		t.Fatalf("reply error lost or real target not cleaned up: %+v", cleanup)
	}
}
