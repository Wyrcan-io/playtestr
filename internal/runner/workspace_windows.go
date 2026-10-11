//go:build windows

package runner

import (
	"fmt"
	"syscall"

	"golang.org/x/sys/windows"
)

func canonicalWorkspaceRoot(path string) (string, error) {
	pointer, err := windows.UTF16PtrFromString(path)
	if err != nil {
		return "", err
	}
	buffer := make([]uint16, 32768)
	n, err := windows.GetLongPathName(pointer, &buffer[0], uint32(len(buffer)))
	if err != nil {
		return "", fmt.Errorf("expand native workspace path: %w", err)
	}
	if n == 0 || n >= uint32(len(buffer)) {
		return "", fmt.Errorf("expanded workspace path exceeds native bound")
	}
	return windows.UTF16ToString(buffer[:n]), nil
}

func workspaceReparsePoint(path string) bool {
	pointer, err := syscall.UTF16PtrFromString(path)
	if err != nil {
		return true
	}
	attributes, err := windows.GetFileAttributes(pointer)
	return err != nil || attributes&windows.FILE_ATTRIBUTE_REPARSE_POINT != 0
}
