package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"golang.org/x/term"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: fixture <hang|flood|input|child|sleep|screen|resize|workspace>")
		os.Exit(2)
	}
	switch os.Args[1] {
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
