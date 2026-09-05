package main

import (
	"bufio"
	"fmt"
	"golang.org/x/term"
	"os"
)

func main() {
	old, err := term.MakeRaw(int(os.Stdin.Fd()))
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	defer term.Restore(int(os.Stdin.Fd()), old)
	selected := 0
	items := []string{"Deploy preview", "Run diagnostics", "Exit"}
	draw := func() {
		fmt.Print("\x1b[2J\x1b[H\x1b[36mPLAYTESTR / mission control\x1b[0m\r\n\r\n")
		for i, item := range items {
			if i == selected {
				fmt.Printf("\x1b[32m> %s\x1b[0m\r\n", item)
			} else {
				fmt.Printf("  %s\r\n", item)
			}
		}
		fmt.Print("\r\nUse arrow keys and Enter. Press q to quit.\r\n")
	}
	draw()
	r := bufio.NewReader(os.Stdin)
	for {
		b, e := r.ReadByte()
		if e != nil {
			return
		}
		switch b {
		case 'q', 3:
			return
		case 27:
			next, _ := r.ReadByte()
			if next == '[' {
				direction, _ := r.ReadByte()
				if direction == 'B' {
					selected = (selected + 1) % 3
				}
				if direction == 'A' {
					selected = (selected + 2) % 3
				}
				draw()
			}
		case '\r', '\n':
			if selected == 2 {
				return
			}
			draw()
			if selected == 0 {
				fmt.Print("\r\nPreview deployed successfully.\r\n")
			} else {
				fmt.Print("\r\nDiagnostics: all systems healthy.\r\n")
			}
		}
	}
}
