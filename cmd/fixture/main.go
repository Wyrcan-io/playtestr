package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: fixture <hang|flood|input|child|sleep>")
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
	default:
		fmt.Fprintf(os.Stderr, "unknown fixture mode %q\n", os.Args[1])
		os.Exit(2)
	}
}
