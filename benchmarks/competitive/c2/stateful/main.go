package main

import (
	"bufio"
	"fmt"
	"os"
	"strconv"
	"strings"

	"golang.org/x/term"
)

func main() {
	configPath := os.Getenv("C2_CONFIG_PATH")
	if configPath == "" {
		fmt.Fprintln(os.Stderr, "C2_CONFIG_PATH is required")
		os.Exit(2)
	}
	oldState, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		fmt.Fprintf(os.Stderr, "enter raw mode: %v\n", err)
		os.Exit(2)
	}
	defer term.Restore(int(os.Stdin.Fd()), oldState) //nolint:errcheck

	message := ""
	input := ""
	draw := func() {
		fmt.Print("\x1b[2J\x1b[HConfigure service\r\n\r\n")
		if message != "" {
			fmt.Printf("%s\r\n\r\n", message)
		}
		fmt.Printf("Port (1024-65535): %s", input)
	}
	draw()
	reader := bufio.NewReader(os.Stdin)
	for {
		char, readErr := reader.ReadByte()
		if readErr != nil {
			fmt.Fprintf(os.Stderr, "read input: %v\n", readErr)
			os.Exit(2)
		}
		switch char {
		case 3:
			os.Exit(130)
		case '\r', '\n':
			port, parseErr := strconv.Atoi(input)
			if parseErr != nil || port < 1024 || port > 65535 {
				message = "Invalid port"
				input = ""
				draw()
				continue
			}
			writtenPort := committedPort(port)
			if err := os.WriteFile(configPath, []byte(fmt.Sprintf("port=%d\n", writtenPort)), 0o600); err != nil {
				fmt.Fprintf(os.Stderr, "write config: %v\n", err)
				os.Exit(3)
			}
			fmt.Printf("\x1b[2J\x1b[HSaved port %d\r\n", port)
			return
		case 8, 127:
			if input != "" {
				input = input[:len(input)-1]
			}
			draw()
		default:
			if char >= 32 && char < 127 {
				input += strings.ToLower(string(char))
				draw()
			}
		}
	}
}
