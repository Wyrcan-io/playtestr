//go:build !windows

package main

import (
	"bufio"
	"fmt"
	"os"
	"os/signal"
	"syscall"

	"golang.org/x/term"
)

func main() {
	oldState, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		fmt.Fprintf(os.Stderr, "enter raw mode: %v\n", err)
		os.Exit(2)
	}
	defer term.Restore(int(os.Stdin.Fd()), oldState) //nolint:errcheck

	modal := false
	draw := func() {
		width, height, sizeErr := term.GetSize(int(os.Stdout.Fd()))
		if sizeErr != nil {
			fmt.Fprintf(os.Stderr, "get terminal size: %v\n", sizeErr)
			os.Exit(2)
		}
		fmt.Print("\x1b[2J\x1b[H")
		if modal {
			fmt.Printf("Help modal\r\n\r\nSize: %dx%d\r\n\r\nEscape closes help\r\n", width, height)
			return
		}
		fmt.Printf("Main screen\r\n\r\nSize: %dx%d\r\n\r\nPress ? for help\r\n", width, height)
	}

	input := make(chan byte)
	readErrors := make(chan error, 1)
	go func() {
		reader := bufio.NewReader(os.Stdin)
		for {
			char, readErr := reader.ReadByte()
			if readErr != nil {
				readErrors <- readErr
				return
			}
			input <- char
		}
	}()
	resizes := make(chan os.Signal, 1)
	signal.Notify(resizes, syscall.SIGWINCH)
	defer signal.Stop(resizes)
	draw()
	for {
		select {
		case <-resizes:
			draw()
		case readErr := <-readErrors:
			fmt.Fprintf(os.Stderr, "read input: %v\n", readErr)
			os.Exit(2)
		case char := <-input:
			switch char {
			case 3:
				os.Exit(130)
			case 'q':
				return
			case '?':
				modal = true
				draw()
			case 27:
				modal = modalAfterDismiss(modal)
				draw()
			}
		}
	}
}
