//go:build windows

package runner

import (
	"bytes"
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"strconv"
	"strings"
	"syscall"
	"time"

	"golang.org/x/sys/windows"
)

const consoleProbeMode = "--playtestr-internal-console-size-v1"
const consoleProbeMarker = "PLAYTESTR_INTERNAL_CONSOLE_SIZE_PROBE"

type nativeConsoleDimensions struct{ buffer, viewport TerminalSize }

// The same standalone executable supplies a private, short-lived console client.
// It starts detached, opens only CONOUT$ for reading, and never reads target text
// or input. Dispatch before CLI/test flag parsing also permits real PTY tests.
func init() {
	if len(os.Args) < 2 || os.Args[1] != consoleProbeMode || os.Getenv(consoleProbeMarker) != "1" {
		return
	}
	if len(os.Args) != 4 {
		os.Exit(2)
	}
	pid, errPID := strconv.ParseUint(os.Args[2], 10, 32)
	birth, errBirth := strconv.ParseUint(os.Args[3], 10, 64)
	if errPID != nil || errBirth != nil || pid == 0 || birth == 0 {
		os.Exit(2)
	}
	dimensions, err := attachedConsoleDimensions(uint32(pid), birth)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	_, err = fmt.Fprintf(os.Stdout, "console-size-v1 %d %d %d %d %d %d\n", pid, birth,
		dimensions.buffer.Width, dimensions.buffer.Height, dimensions.viewport.Width, dimensions.viewport.Height)
	if err != nil {
		os.Exit(1)
	}
	os.Exit(0)
}

func windowsProcessBirth(pid uint32) (birth uint64, err error) {
	handle, err := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, pid)
	if err != nil {
		return 0, fmt.Errorf("open owned console process identity: %w", err)
	}
	defer func() { err = errors.Join(err, windows.CloseHandle(handle)) }()
	return processHandleBirth(handle)
}

func processHandleBirth(handle windows.Handle) (uint64, error) {
	var birth, exit, kernel, user windows.Filetime
	if err := windows.GetProcessTimes(handle, &birth, &exit, &kernel, &user); err != nil {
		return 0, fmt.Errorf("read console process creation time: %w", err)
	}
	return uint64(birth.HighDateTime)<<32 | uint64(birth.LowDateTime), nil
}

func attachedConsoleDimensions(pid uint32, birth uint64) (result nativeConsoleDimensions, err error) {
	process, err := windows.OpenProcess(windows.PROCESS_QUERY_LIMITED_INFORMATION, false, pid)
	if err != nil {
		return result, fmt.Errorf("open owned console process: %w", err)
	}
	defer func() { err = errors.Join(err, windows.CloseHandle(process)) }()
	actual, err := processHandleBirth(process)
	if err != nil {
		return result, err
	}
	if actual != birth {
		return result, fmt.Errorf("console process identity changed")
	}
	var status uint32
	if err = windows.GetExitCodeProcess(process, &status); err != nil {
		return result, err
	}
	if status != 259 {
		return result, fmt.Errorf("console process already exited")
	}
	kernel := windows.NewLazySystemDLL("kernel32.dll")
	attached, _, cause := kernel.NewProc("AttachConsole").Call(uintptr(pid))
	if attached == 0 {
		return result, fmt.Errorf("attach owned console read-only: %w", cause)
	}
	defer func() {
		if ok, _, cause := kernel.NewProc("FreeConsole").Call(); ok == 0 {
			err = errors.Join(err, fmt.Errorf("detach console query: %w", cause))
		}
	}()
	name, err := windows.UTF16PtrFromString("CONOUT$")
	if err != nil {
		return result, err
	}
	handle, err := windows.CreateFile(name, windows.GENERIC_READ, windows.FILE_SHARE_READ|windows.FILE_SHARE_WRITE, nil, windows.OPEN_EXISTING, 0, 0)
	if err != nil {
		return result, fmt.Errorf("open console dimensions read-only: %w", err)
	}
	defer func() { err = errors.Join(err, windows.CloseHandle(handle)) }()
	var info windows.ConsoleScreenBufferInfo
	if err = windows.GetConsoleScreenBufferInfo(handle, &info); err != nil {
		return result, fmt.Errorf("query native console dimensions: %w", err)
	}
	result = nativeConsoleDimensions{buffer: TerminalSize{Width: int(info.Size.X), Height: int(info.Size.Y)},
		viewport: TerminalSize{Width: int(info.Window.Right - info.Window.Left + 1), Height: int(info.Window.Bottom - info.Window.Top + 1)}}
	return result, nil
}

type consoleProbeOutput struct {
	bytes.Buffer
	overflow bool
}

func (b *consoleProbeOutput) Write(p []byte) (int, error) {
	remaining := 128 - b.Len()
	if len(p) > remaining {
		b.overflow = true
		b.Buffer.Write(p[:remaining])
		return len(p), nil
	}
	return b.Buffer.Write(p)
}

func parseConsoleDimensions(value []byte, pid uint32, birth uint64) (result nativeConsoleDimensions, err error) {
	fields := strings.Fields(string(value))
	if len(fields) != 7 || fields[0] != "console-size-v1" {
		return result, fmt.Errorf("invalid native console dimension protocol")
	}
	values := make([]uint64, 6)
	for i := range values {
		values[i], err = strconv.ParseUint(fields[i+1], 10, 64)
		if err != nil {
			return result, fmt.Errorf("invalid native console dimension value: %w", err)
		}
	}
	if values[0] != uint64(pid) || values[1] != birth {
		return result, fmt.Errorf("native console identity mismatch")
	}
	for _, n := range values[2:] {
		if n < 1 || n > 32767 {
			return result, fmt.Errorf("native console dimension outside bounds")
		}
	}
	return nativeConsoleDimensions{buffer: TerminalSize{Width: int(values[2]), Height: int(values[3])},
		viewport: TerminalSize{Width: int(values[4]), Height: int(values[5])}}, nil
}

func probeWindowsConsole(ctx context.Context, pid uint32, birth uint64) (nativeConsoleDimensions, error) {
	var empty nativeConsoleDimensions
	executable, err := os.Executable()
	if err != nil {
		return empty, fmt.Errorf("locate native console query executable: %w", err)
	}
	cmd := exec.CommandContext(ctx, executable, consoleProbeMode, strconv.FormatUint(uint64(pid), 10), strconv.FormatUint(birth, 10))
	cmd.SysProcAttr = &syscall.SysProcAttr{CreationFlags: windows.DETACHED_PROCESS, HideWindow: true}
	cmd.Env = []string{consoleProbeMarker + "=1"}
	for _, name := range []string{"SYSTEMROOT", "WINDIR"} {
		if value := os.Getenv(name); value != "" {
			cmd.Env = append(cmd.Env, name+"="+value)
		}
	}
	return runConsoleProbeCommand(ctx, cmd, pid, birth)
}

func runConsoleProbeCommand(ctx context.Context, cmd *exec.Cmd, pid uint32, birth uint64) (nativeConsoleDimensions, error) {
	var empty nativeConsoleDimensions
	var stdout, stderr consoleProbeOutput
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	cmd.WaitDelay = 100 * time.Millisecond
	if err := cmd.Run(); err != nil {
		return empty, fmt.Errorf("native console query failed (bounded diagnostic %q): %w", stderr.String(), errors.Join(ctx.Err(), err))
	}
	if cmd.ProcessState == nil || !cmd.ProcessState.Exited() {
		return empty, fmt.Errorf("native console query cleanup unconfirmed")
	}
	if stdout.overflow || stderr.overflow {
		return empty, fmt.Errorf("native console query output limit exceeded")
	}
	if stderr.Len() != 0 {
		return empty, fmt.Errorf("native console query produced unexpected diagnostic output")
	}
	return parseConsoleDimensions(stdout.Bytes(), pid, birth)
}
