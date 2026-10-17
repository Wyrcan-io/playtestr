//go:build windows

package main

import (
	"fmt"

	"golang.org/x/sys/windows"
)

func prepareInterruptHandling() error {
	// The NULL-handler ignore attribute survives CreateProcess. Restore normal
	// processing in this CLI before os/signal registration and target creation.
	proc := windows.NewLazySystemDLL("kernel32.dll").NewProc("SetConsoleCtrlHandler")
	if ok, _, err := proc.Call(0, 0); ok == 0 {
		return fmt.Errorf("restore Windows interrupt processing: %w", err)
	}
	return nil
}
