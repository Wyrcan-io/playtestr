//go:build windows

package runner

import (
	"fmt"
	"os"
	"syscall"
)

func readExactLetterControls(value []byte) (int, error) {
	// os.Stdin.Read deliberately treats CtrlZ as EOF in Go's Windows console
	// reader. Read the native raw console characters to verify transport bytes,
	// without confusing that library convention with a dropped PTY input.
	for received := 0; received < len(value); {
		chars := make([]uint16, len(value)-received)
		var n uint32
		if err := syscall.ReadConsole(syscall.Handle(os.Stdin.Fd()), &chars[0], uint32(len(chars)), &n, nil); err != nil {
			return received, err
		}
		if n == 0 || n > uint32(len(chars)) {
			return received, fmt.Errorf("invalid native console character count %d", n)
		}
		for _, char := range chars[:n] {
			if char > 127 {
				return received, fmt.Errorf("unexpected non-ASCII control input %04x", char)
			}
			value[received] = byte(char)
			received++
		}
		if received == len(value) {
			return received, nil
		}
	}
	return 0, nil
}
