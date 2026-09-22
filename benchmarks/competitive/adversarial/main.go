//go:build !windows

package main

import (
	"fmt"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"syscall"
	"time"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: adversarial <hang|flood>")
		os.Exit(2)
	}
	pidPath := os.Getenv("ADVERSARIAL_PID_PATH")
	if pidPath == "" {
		fmt.Fprintln(os.Stderr, "ADVERSARIAL_PID_PATH is required")
		os.Exit(2)
	}
	if err := os.WriteFile(pidPath, []byte(strconv.Itoa(os.Getpid())+"\n"), 0o600); err != nil {
		fmt.Fprintf(os.Stderr, "write pid: %v\n", err)
		os.Exit(2)
	}
	fmt.Printf("adversarial ready pid=%d\r\n", os.Getpid())
	switch os.Args[1] {
	case "hang":
		signals := make(chan os.Signal, 1)
		signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
		received := <-signals
		fmt.Printf("cancelled by signal %s\r\n", received)
		os.Exit(130)
	case "flood":
		chunk := strings.Repeat("0123456789abcdef", 256)
		for written := 0; written < 4*1024*1024; written += len(chunk) {
			fmt.Print(chunk)
		}
		fmt.Print("\r\nflood complete\r\n")
	case "sleep":
		time.Sleep(10 * time.Minute)
	default:
		fmt.Fprintf(os.Stderr, "unknown mode %q\n", os.Args[1])
		os.Exit(2)
	}
}
