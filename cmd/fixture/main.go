package main

import (
	"bufio"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"golang.org/x/term"
)

// wizardSuffix is an acceptance-only target behavior mutation, never a test change.
var wizardSuffix string

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: fixture <hang|flood|input|child|sleep|screen|resize|workspace>")
		os.Exit(2)
	}
	switch os.Args[1] {
	case "wizard":
		if err := wizard(); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "gum":
		delay, _ := strconv.Atoi(os.Getenv("PLAYTESTR_DELAY_MS"))
		time.Sleep(time.Duration(delay) * time.Millisecond)
		data, err := os.ReadFile("choices.txt")
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		args := []string{"choose", "--header", "Pick deployment"}
		args = append(args, strings.Fields(string(data))...)
		program := os.Getenv("PLAYTESTR_GUM")
		if program == "" {
			program = "gum"
		}
		cmd := exec.Command(program, args...)
		cmd.Stdin, cmd.Stdout, cmd.Stderr = os.Stdin, os.Stdout, os.Stderr
		if err := cmd.Run(); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
	case "hang":
		fmt.Println("fixture ready; waiting forever")
		time.Sleep(10 * time.Minute)
	case "flood":
		chunk := strings.Repeat("output ", 256)
		for {
			fmt.Print(chunk)
		}
	case "input":
		buffer := make([]byte, 1)
		if _, err := os.Stdin.Read(buffer); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Println("input received")
	case "child":
		child := exec.Command(os.Args[0], "sleep")
		if err := child.Start(); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Printf("parent %d started child %d\n", os.Getpid(), child.Process.Pid)
		time.Sleep(10 * time.Minute)
	case "sleep":
		time.Sleep(10 * time.Minute)
	case "screen":
		old, err := term.MakeRaw(int(os.Stdin.Fd()))
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer term.Restore(int(os.Stdin.Fd()), old)
		fmt.Print("old screen")
		for _, part := range [][]byte{
			[]byte("\x1b["),
			[]byte("2J\x1b[H\x1b[36mcompat main: caf"),
			{0xc3},
			{0xa9},
			[]byte(" λ\x1b[0m"),
			[]byte("\x1b[?1049h\x1b[2J\x1b[Halternate screen"),
		} {
			_, _ = os.Stdout.Write(part)
			time.Sleep(10 * time.Millisecond)
		}
		buffer := make([]byte, 1)
		_, _ = os.Stdin.Read(buffer)
		fmt.Print("\x1b[?1049l\r\ncompat complete\r\n")
	case "resize":
		old, err := term.MakeRaw(int(os.Stdin.Fd()))
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		defer term.Restore(int(os.Stdin.Fd()), old)
		fmt.Print("\x1b[2J\x1b[Hresize ready")
		buffer := make([]byte, 1)
		_, _ = os.Stdin.Read(buffer)
		width, height, err := term.GetSize(int(os.Stdout.Fd()))
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Printf("\x1b[2J\x1b[Hresized %dx%d\r\n", width, height)
	case "workspace":
		if _, err := os.Stat("state.txt"); err == nil {
			fmt.Println("workspace was already used")
			os.Exit(3)
		} else if !os.IsNotExist(err) {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		seed, err := os.ReadFile("seed.txt")
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		home, err := os.UserHomeDir()
		if err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err := os.WriteFile("state.txt", []byte("created"), 0600); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err := os.WriteFile(filepath.Join(home, "playtestr-fixture-state"), []byte("created"), 0600); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		if err := os.WriteFile(filepath.Join(os.TempDir(), "playtestr-fixture-temp"), []byte("created"), 0600); err != nil {
			fmt.Fprintln(os.Stderr, err)
			os.Exit(1)
		}
		fmt.Printf("fresh workspace seed=%s home=true temp=true\n", strings.TrimSpace(string(seed)))
	default:
		fmt.Fprintf(os.Stderr, "unknown fixture mode %q\n", os.Args[1])
		os.Exit(2)
	}
}

func wizard() error {
	traceEvents := make(chan string, 300)
	if path := os.Getenv("PLAYTESTR_WIZARD_TRACE"); path != "" {
		go func() {
			// Avoid filesystem writes in the input/resize race being investigated.
			time.Sleep(250 * time.Millisecond)
			var captured strings.Builder
			for {
				select {
				case event := <-traceEvents:
					captured.WriteString(event + "\n")
				default:
					_ = os.WriteFile(path, []byte(captured.String()), 0600)
					return
				}
			}
		}()
	}
	trace := func(format string, values ...any) {
		// Optional acceptance diagnostics contain only this synthetic fixture's
		// input. The harness supplies an owned bounded file, never user input.
		select {
		case traceEvents <- fmt.Sprintf(format, values...):
		default:
		}
	}
	if _, err := os.Stat("result.txt"); err == nil {
		return fmt.Errorf("dirty fixture: result.txt already exists")
	}
	seed, err := os.ReadFile("seed.txt")
	if err != nil {
		return err
	}
	old, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		return err
	}
	defer term.Restore(int(os.Stdin.Fd()), old)
	trace("raw ready pid=%d", os.Getpid())
	delay, _ := strconv.Atoi(os.Getenv("PLAYTESTR_DELAY_MS"))
	draw := func(text string) {
		time.Sleep(time.Duration(delay) * time.Millisecond)
		fmt.Printf("\x1b[2J\x1b[H%s\r\n", text)
	}
	draw("Project name? (synthetic workspace)")
	r := bufio.NewReader(os.Stdin)
	var name []byte
	for {
		b, err := r.ReadByte()
		trace("name byte=%02x err=%v", b, err)
		if err != nil {
			return err
		}
		if b == '\r' || b == '\n' {
			break
		}
		name = append(name, b)
		if len(name) > 256 {
			return fmt.Errorf("name exceeds 256 bytes")
		}
	}
	width, height, err := term.GetSize(int(os.Stdout.Fd()))
	trace("name=%x size=%dx%d err=%v", name, width, height, err)
	if err != nil {
		return err
	}
	draw(fmt.Sprintf("Confirm project %s at %dx%d; seed=%s", name, width, height, strings.TrimSpace(string(seed))))
	b, err := r.ReadByte()
	if err != nil {
		return err
	}
	if b != 'y' {
		return fmt.Errorf("confirmation declined")
	}
	content := fmt.Sprintf("%s:%s", name, strings.TrimSpace(string(seed)))
	if err := os.WriteFile("result.txt", []byte(content), 0600); err != nil {
		return err
	}
	actual, err := os.ReadFile("result.txt")
	if err != nil {
		return err
	}
	if string(actual) != content {
		return fmt.Errorf("saved state mismatch")
	}
	draw("Saved and verified " + content + wizardSuffix)
	return nil
}
