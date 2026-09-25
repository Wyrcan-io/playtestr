package main

import (
	"bufio"
	"fmt"
	"os"

	"golang.org/x/term"
)

func main() {
	oldState, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
	defer term.Restore(int(os.Stdin.Fd()), oldState) //nolint:errcheck
	modal := false
	lastWidth, lastHeight := 0, 0
	draw := func() {
		width, height, sizeErr := term.GetSize(int(os.Stdout.Fd()))
		if sizeErr != nil {
			fmt.Fprintln(os.Stderr, sizeErr)
			os.Exit(2)
		}
		width, height = reportedSize(width, height)
		lastWidth, lastHeight = width, height
		fmt.Print("\x1b[2J\x1b[H")
		if modal {
			fmt.Printf("Help modal\r\n\r\nSize: %dx%d\r\n\r\nEscape closes help\r\n", width, height)
			return
		}
		fmt.Printf("Main screen\r\n\r\nSize: %dx%d\r\n\r\nPress ? for help\r\n", width, height)
	}
	reader := bufio.NewReader(os.Stdin)
	draw()
	for {
		char, readErr := reader.ReadByte()
		if readErr != nil {
			fmt.Fprintln(os.Stderr, readErr)
			os.Exit(2)
		}
		switch char {
		case 'q':
			if path := os.Getenv("COMPAT_RESULT_PATH"); path != "" {
				value := fmt.Sprintf("size=%dx%d modal=%t\n", lastWidth, lastHeight, modal)
				if err := os.WriteFile(path, []byte(value), 0o600); err != nil {
					fmt.Fprintln(os.Stderr, err)
					os.Exit(3)
				}
			}
			return
		case '?':
			modal = true
			draw()
		case '\r', '\n':
			draw()
		case 27:
			modal = false
			draw()
		}
	}
}
