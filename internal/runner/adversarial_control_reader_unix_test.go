//go:build !windows

package runner

import (
	"io"
	"os"
)

func readExactLetterControls(value []byte) (int, error) {
	return io.ReadFull(os.Stdin, value)
}
