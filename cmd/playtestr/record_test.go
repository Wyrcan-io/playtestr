package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"reflect"
	"regexp"
	"strings"
	"testing"

	"github.com/Wyrcan-io/playtestr/internal/runner"
	"golang.org/x/term"
)

func TestRecorderRerecordDisplaysCurrentWorkspace(t *testing.T) {
	dir := t.TempDir()
	fixture := filepath.Join(dir, "fixtures")
	if err := os.Mkdir(fixture, 0700); err != nil {
		t.Fatal(err)
	}
	input, writer, err := os.Pipe()
	if err != nil {
		t.Fatal(err)
	}
	defer input.Close()
	_, err = io.WriteString(writer, "/expect Name?\n/rerecord 0\n/expect Name?\n/quit\n")
	writer.Close()
	if err != nil {
		t.Fatal(err)
	}
	var output, errors bytes.Buffer
	code := runRecord(context.Background(), []string{"--output", filepath.Join(dir, "recorded.json"), "--fixture", "fixtures", "--temporary-home", "--temporary-temp", "--timeout-ms", "10000", "--env", "PLAYTESTR_TARGET_HELPER=1", "--", os.Args[0], "-test.run=TestRecorderTargetHelper"}, input, &output, &errors)
	if code != 130 || errors.Len() != 0 {
		t.Fatalf("code=%d errors=%s", code, &errors)
	}
	matches := regexp.MustCompile(`working-directory=("[^"\n]*")`).FindAllStringSubmatch(output.String(), -1)
	if len(matches) != 2 {
		t.Fatalf("expected initial and fresh workspace identities; got %d: %s", len(matches), &output)
	}
	if matches[0][1] == matches[1][1] {
		t.Fatal("rerecord displayed the removed original workspace")
	}
}

func TestRecorderOperatorHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_OPERATOR_HELPER") != "1" {
		return
	}
	before, err := term.GetState(int(os.Stdin.Fd()))
	if err != nil {
		t.Fatal(err)
	}
	code := runRecord(context.Background(), []string{"--output", os.Getenv("PLAYTESTR_RECORD_OUTPUT"), "--timeout-ms", "10000", "--env", "PLAYTESTR_TARGET_HELPER=1", "--", os.Args[0], "-test.run=TestRecorderTargetHelper"}, os.Stdin, os.Stdout, os.Stderr)
	after, err := term.GetState(int(os.Stdin.Fd()))
	if err != nil {
		t.Fatal(err)
	}
	if !reflect.DeepEqual(before, after) {
		t.Fatal("operator terminal mode not restored")
	}
	fmt.Println("operator restored=true")
	os.Exit(code)
}

func TestRecorderTargetHelper(t *testing.T) {
	if os.Getenv("PLAYTESTR_TARGET_HELPER") != "1" {
		return
	}
	state, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		t.Fatal(err)
	}
	defer term.Restore(int(os.Stdin.Fd()), state)
	fmt.Print("\x1b[2J\x1b[HName?")
	r := bufio.NewReader(os.Stdin)
	var name strings.Builder
	for {
		b, err := r.ReadByte()
		if err != nil {
			t.Fatal(err)
		}
		if b == '\r' {
			break
		}
		name.WriteByte(b)
	}
	fmt.Print("\x1b[2J\x1b[HConfirm " + name.String())
	if _, err := r.ReadByte(); err != nil {
		t.Fatal(err)
	}
	fmt.Print("\x1b[2J\x1b[HComplete " + name.String())
}

func TestNativeRecorderLiveInputAndOperatorRestoration(t *testing.T) {
	for _, cancel := range []bool{false, true} {
		t.Run(fmt.Sprint("cancel=", cancel), func(t *testing.T) {
			dir := t.TempDir()
			output := filepath.Join(dir, "recorded.json")
			commands := "/expect Name?\n/live\ncafé\r\a/expect Confirm café\n/snapshot confirm.txt\n/key Enter\n/expect Complete café\n/exit 0\n/review\n/replay\n/save\n"
			code := 0
			anchor := "Exported "
			if cancel {
				commands = "/expect Name?\n/quit\n"
				code = 130
				anchor = "operator restored=true"
			}
			spec := runner.Spec{Version: 1, Command: []string{os.Args[0], "-test.run=TestRecorderOperatorHelper"}, Env: map[string]string{"PLAYTESTR_OPERATOR_HELPER": "1", "PLAYTESTR_RECORD_OUTPUT": output}, Width: 120, Height: 80, TimeoutMS: 15000, RunTimeoutMS: 40000, Steps: []runner.Step{{Expect: "record>"}, {Text: commands}, {Expect: anchor}, {Exit: &code}}}
			data, _ := json.Marshal(spec)
			path := filepath.Join(dir, "operator.json")
			if err := os.WriteFile(path, data, 0600); err != nil {
				t.Fatal(err)
			}
			if result := runner.RunDetailedContext(context.Background(), path, runner.RunOptions{}, os.Stdout); result.Err() != nil {
				t.Fatal(result.Err())
			}
			if !cancel {
				if err := runner.RunContext(context.Background(), output, false, io.Discard); err != nil {
					t.Fatal(err)
				}
			} else {
				if _, err := os.Stat(output); !os.IsNotExist(err) {
					t.Fatal("canceled recording exported")
				}
			}
		})
	}
}
