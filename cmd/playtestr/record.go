package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"

	"github.com/Wyrcan-io/playtestr/internal/console"
	"github.com/Wyrcan-io/playtestr/internal/runner"
	"golang.org/x/term"
)

type stringFlags []string

func (f *stringFlags) String() string         { return strings.Join(*f, ",") }
func (f *stringFlags) Set(value string) error { *f = append(*f, value); return nil }

const recordHelp = `Recorder controls (target input is separate):
  /live                       type into the target; Ctrl+G returns to controls
  /key ArrowDown              send a supported named key
  /text "hello"               send JSON-quoted text/paste (literal Ctrl+G: "\u0007")
  /expect unique new content  positive readiness checkpoint
  /absent previous content    disappearance of previously asserted content
  /exit 0                     exact expected exit code
  /snapshot name.txt          capture a ready, settled screen
  /resize 100 30; /redraw     resize and optional observed redraw wait
  /snapshot-rows name.rows.json 2 24  capture reviewed inclusive viewport rows
  /screen; /review            inspect screen or full candidate/baselines
  /delete N; /move N M         edit 1-based step positions
  /replace N {"expect":"..."} replace a step with one strict JSON action
  /rerecord N                 fresh target, retain/reconstruct first N steps
  /replay; /save               reviewed fresh replay, then export new files
  /quit                       cancel without export
No target input or raw draft is saved automatically. Review may display sensitive
text the target printed or you typed. Targets run with your permissions.
`

func runRecord(ctx context.Context, args []string, stdin *os.File, stdout, stderr io.Writer) (code int) {
	flags := flag.NewFlagSet("record", flag.ContinueOnError)
	flags.SetOutput(stderr)
	output := flags.String("output", "", "new spec path (existing files refused)")
	name := flags.String("name", "recorded interaction", "test name")
	cwd := flags.String("cwd", "", "cwd relative to exported spec; incompatible with fixture")
	fixture := flags.String("fixture", "", "synthetic fixture below exported spec directory; enables v2")
	fixtureCWD := flags.String("fixture-cwd", ".", "cwd within copied fixture")
	home := flags.Bool("temporary-home", false, "fresh managed home with fixture")
	temp := flags.Bool("temporary-temp", false, "fresh managed temp with fixture")
	width := flags.Int("width", 80, "initial columns, 1-500")
	height := flags.Int("height", 24, "initial rows, 1-200")
	timeout := flags.Int("timeout-ms", 3000, "checkpoint/action deadline")
	budget := flags.Int("run-timeout-ms", 300000, "whole capture/replay budget")
	limit := flags.Int64("max-output-bytes", 2000000, "target output cap")
	var inherited, environment stringFlags
	flags.Var(&inherited, "inherit-env", "explicit environment name (repeatable)")
	flags.Var(&environment, "env", "explicit NAME=value (repeatable; reviewed in preview)")
	if err := flags.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}
	if *output == "" || flags.NArg() == 0 {
		fmt.Fprintln(stderr, "record requires --output and an explicit executable after --")
		return 2
	}
	if (*home || *temp) && *fixture == "" {
		fmt.Fprintln(stderr, "managed home/temp require --fixture")
		return 2
	}
	spec := runner.Spec{Version: 1, Name: *name, Command: flags.Args(), CWD: *cwd, Width: *width, Height: *height, TimeoutMS: *timeout, RunTimeoutMS: *budget, MaxOutputBytes: *limit, InheritEnv: inherited, Env: map[string]string{}}
	for _, item := range environment {
		key, value, ok := strings.Cut(item, "=")
		if !ok {
			fmt.Fprintln(stderr, "--env requires NAME=value")
			return 2
		}
		if _, exists := spec.Env[key]; exists {
			fmt.Fprintln(stderr, "duplicate --env name")
			return 2
		}
		spec.Env[key] = value
	}
	if *fixture != "" {
		spec.Version = 2
		spec.Workspace = &runner.WorkspaceSpec{Fixture: *fixture, CWD: *fixtureCWD}
		if *home {
			spec.Workspace.Home = "temporary"
		}
		if *temp {
			spec.Workspace.Temp = "temporary"
		}
	}
	fmt.Fprintf(stdout, "Setup: output=%q argv=%q cwd=%q fixture=%q viewport=%dx%d timeout=%dms budget=%dms output-cap=%d\n", *output, spec.Command, *cwd, *fixture, *width, *height, *timeout, *budget, *limit)
	fmt.Fprint(stdout, recordHelp)
	r, err := runner.StartRecording(ctx, *output, spec)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	resolvedTarget, resolvedDirectory := r.ResolvedSetup()
	fmt.Fprintf(stdout, "Resolved target=%q working-directory=%q\n", resolvedTarget, resolvedDirectory)
	defer func() {
		if err := r.Close(); err != nil {
			fmt.Fprintf(stderr, "Recording cleanup: %v\n", err)
			if code == 0 {
				code = 1
			}
		}
	}()
	input, err := console.Open(stdin)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	defer func() {
		fmt.Fprint(stdout, "\x1b[0m\x1b[?25h")
		if err := input.Close(); err != nil {
			fmt.Fprintf(stderr, "Restore operator terminal: %v\n", err)
			code = 1
		}
	}()
	interactive := term.IsTerminal(int(stdin.Fd()))
	controller := recordController{input: input, out: stdout, interactive: interactive}
	reviewed := false
	for {
		fmt.Fprint(stdout, "record> ")
		line, err := controller.line(r.Context())
		if err != nil {
			err = r.InputError(err)
			if !errors.Is(err, io.EOF) {
				fmt.Fprintln(stderr, err)
			}
			if errors.Is(err, context.Canceled) {
				return 130
			}
			return 1
		}
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		command, value, _ := strings.Cut(line, " ")
		var step runner.Step
		capture := true
		switch command {
		case "/key":
			step.Key = value
		case "/text":
			err = json.Unmarshal([]byte(value), &step.Text)
		case "/expect":
			step.Expect = value
		case "/absent":
			step.ExpectNot = value
		case "/exit":
			var n int
			n, err = strconv.Atoi(value)
			step.Exit = &n
		case "/snapshot":
			step.Snapshot = value
		case "/snapshot-rows":
			capture = false
			var name, extra string
			var first, last int
			n, _ := fmt.Sscan(value, &name, &first, &last, &extra)
			if n != 3 {
				err = fmt.Errorf("snapshot-rows requires file.rows.json first-row last-row")
			} else {
				err = r.CaptureRowsSnapshot(name, first, last)
				if err == nil {
					reviewed = false
				}
			}
		case "/redraw":
			step.WaitForRedraw = true
		case "/resize":
			var w, h int
			var extra string
			n, _ := fmt.Sscan(value, &w, &h, &extra)
			if n != 2 {
				err = fmt.Errorf("resize requires width height")
			}
			step.Resize = &runner.TerminalSize{Width: w, Height: h}
		case "/screen":
			capture = false
			fmt.Fprintln(stdout, r.Screen())
		case "/review":
			capture = false
			var data []byte
			var snaps map[string]string
			data, snaps, err = r.Preview()
			if err == nil {
				fmt.Fprintln(stdout, string(data))
				names := []string{}
				for n := range snaps {
					names = append(names, n)
				}
				sort.Strings(names)
				for _, n := range names {
					fmt.Fprintf(stdout, "Baseline %s:\n%s\n", n, snaps[n])
				}
				reviewed = true
			}
		case "/replay":
			capture = false
			if !reviewed {
				err = fmt.Errorf("use /review before replay")
				break
			}
			result := r.Replay(ctx, stdout)
			err = result.Err()
			if err != nil {
				if first, screen := r.FirstFailure(); first != nil {
					fmt.Fprintf(stdout, "First failed replay: %s\n%s\n", first.Failure.Category, screen)
				}
			}
		case "/save":
			capture = false
			if !reviewed {
				err = fmt.Errorf("review candidate first")
				break
			}
			err = r.Export(ctx)
			if err == nil {
				fmt.Fprintf(stdout, "Exported %s; rerun: playtestr test %s\n", *output, *output)
				return 0
			}
		case "/quit":
			return 130
		case "/help":
			capture = false
			fmt.Fprint(stdout, recordHelp)
		case "/live":
			capture = false
			reviewed = false
			err = controller.live(r)
		case "/rerecord":
			capture = false
			reviewed = false
			var n int
			n, err = strconv.Atoi(value)
			if err == nil {
				err = r.Rerecord(ctx, n)
				if err == nil {
					program, directory := r.ResolvedSetup()
					fmt.Fprintf(stdout, "Resolved target=%q working-directory=%q\n", program, directory)
				}
			}
		case "/delete", "/move", "/replace":
			capture = false
			reviewed = false
			err = editRecording(r, command, value)
		default:
			capture = false
			err = fmt.Errorf("unknown control; use /help; target typing uses /live or /text")
		}
		if capture && err == nil {
			err = r.Capture(step)
			if err == nil {
				reviewed = false
			}
		}
		if err != nil {
			fmt.Fprintf(stderr, "Recorder: %v\n", err)
		}
	}
}

func editRecording(r *runner.Recording, command, value string) error {
	steps := r.Steps()
	head, tail, _ := strings.Cut(value, " ")
	n, err := strconv.Atoi(head)
	if err != nil || n < 1 || n > len(steps) {
		return fmt.Errorf("step index out of range")
	}
	n--
	switch command {
	case "/delete":
		steps = append(steps[:n], steps[n+1:]...)
	case "/replace":
		decoder := json.NewDecoder(strings.NewReader(tail))
		decoder.DisallowUnknownFields()
		var step runner.Step
		if err := decoder.Decode(&step); err != nil {
			return err
		}
		if decoder.Decode(new(any)) != io.EOF {
			return fmt.Errorf("expected one step JSON object")
		}
		steps[n] = step
	case "/move":
		m, err := strconv.Atoi(tail)
		if err != nil || m < 1 || m > len(steps) {
			return fmt.Errorf("destination out of range")
		}
		step := steps[n]
		steps = append(steps[:n], steps[n+1:]...)
		m--
		steps = append(steps, runner.Step{})
		copy(steps[m+1:], steps[m:])
		steps[m] = step
	}
	return r.Edit(steps)
}

type recordController struct {
	input       *console.Input
	out         io.Writer
	interactive bool
	pending     []byte
}

func (c *recordController) line(ctx context.Context) (string, error) {
	var line []byte
	for {
		if len(c.pending) == 0 {
			data, err := c.input.Read(ctx)
			if err != nil {
				return "", err
			}
			c.pending = data
			if len(data) == 0 {
				continue
			}
		}
		b := c.pending[0]
		c.pending = c.pending[1:]
		if b == 3 {
			return "", context.Canceled
		}
		if b == '\r' || b == '\n' {
			if c.interactive {
				fmt.Fprint(c.out, "\r\n")
			}
			return string(line), nil
		}
		if b == 127 || b == 8 {
			if len(line) > 0 {
				_, size := utf8.DecodeLastRune(line)
				line = line[:len(line)-size]
				if c.interactive {
					fmt.Fprint(c.out, "\b \b")
				}
			}
			continue
		}
		if len(line) >= 65536 {
			return "", fmt.Errorf("control line exceeds 64 KiB")
		}
		line = append(line, b)
		if c.interactive {
			fmt.Fprintf(c.out, "%c", b)
		}
	}
}
func (c *recordController) live(r *runner.Recording) error {
	fmt.Fprintln(c.out, "Live capture; Ctrl+G returns to controls. Literal control: /text \"\\u0007\"")
	var buffered []byte
	last := time.Now()
	previous := ""
	for {
		screen := r.Screen()
		if screen != previous {
			if c.interactive {
				fmt.Fprint(c.out, "\x1b[2J\x1b[H")
			}
			fmt.Fprint(c.out, strings.ReplaceAll(screen, "\n", "\r\n"))
			previous = screen
		}
		data := c.pending
		c.pending = nil
		if len(data) == 0 {
			var err error
			data, err = c.input.Read(r.Context())
			if err != nil {
				return err
			}
		}
		for n, b := range data {
			if b == 7 {
				c.pending = data[n+1:]
				data = data[:n]
				defer fmt.Fprint(c.out, "\r\n")
				if len(data) == 0 {
					return nil
				}
				events, _, err := console.Decode(append(buffered, data...), true)
				if err != nil {
					return err
				}
				return captureEvents(r, events)
			}
		}
		if len(data) > 0 {
			last = time.Now()
			buffered = append(buffered, data...)
		}
		if len(buffered) > 65536 {
			return fmt.Errorf("paste exceeds 64 KiB")
		}
		events, rest, err := console.Decode(buffered, time.Since(last) > 80*time.Millisecond)
		buffered = rest
		if err != nil {
			return err
		}
		if err := captureEvents(r, events); err != nil {
			return err
		}
	}
}
func captureEvents(r *runner.Recording, events []console.Event) error {
	for n := 0; n < len(events); n++ {
		e := events[n]
		if e.Text != "" {
			for n+1 < len(events) && events[n+1].Text != "" {
				n++
				e.Text += events[n].Text
			}
		}
		if err := r.Capture(runner.Step{Key: e.Key, Text: e.Text}); err != nil {
			return err
		}
	}
	return nil
}
