package main

import (
	"bufio"
	"fmt"
	"os"
	"path/filepath"

	"golang.org/x/term"
)

func main() {
	oldState, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		fmt.Fprintf(os.Stderr, "enter raw mode: %v\n", err)
		os.Exit(2)
	}
	defer term.Restore(int(os.Stdin.Fd()), oldState) //nolint:errcheck

	items := []string{"Alpha", "Beta", "Gamma"}
	selected := 0
	draw := func() {
		fmt.Print("\x1b[2J\x1b[HSelect record\r\n\r\n")
		for index, item := range items {
			marker := "  "
			if index == selected {
				marker = "> "
			}
			fmt.Printf("%s%s\r\n", marker, item)
		}
		fmt.Print("\r\nUse arrows and Enter\r\n")
	}
	draw()

	reader := bufio.NewReader(os.Stdin)
	for {
		input, readErr := reader.ReadByte()
		if readErr != nil {
			fmt.Fprintf(os.Stderr, "read input: %v\n", readErr)
			os.Exit(2)
		}
		switch input {
		case 3, 'q':
			os.Exit(130)
		case 27:
			prefix, _ := reader.ReadByte()
			direction, _ := reader.ReadByte()
			if prefix != '[' {
				continue
			}
			switch direction {
			case 'A':
				selected = (selected + len(items) - 1) % len(items)
			case 'B':
				selected = (selected + 1) % len(items)
			default:
				continue
			}
			draw()
		case '\r', '\n':
			committed := commitSelection(selected)
			result := items[committed]
			if err := writeOracle(result); err != nil {
				fmt.Fprintf(os.Stderr, "write oracle: %v\n", err)
				os.Exit(3)
			}
			fmt.Printf("\x1b[2J\x1b[HSelected: %s\r\n", result)
			return
		}
	}
}

func writeOracle(result string) error {
	path := os.Getenv("C1_RESULT_PATH")
	if path == "" {
		return fmt.Errorf("C1_RESULT_PATH is required")
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, []byte(result+"\n"), 0o600)
}
