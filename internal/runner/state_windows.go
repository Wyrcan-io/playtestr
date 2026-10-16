//go:build windows

package runner

import "os"

func openStateFile(root *os.Root, path string) (*os.File, error) {
	return root.Open(path)
}
