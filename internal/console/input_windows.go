package console

import (
	"golang.org/x/sys/windows"
	"io"
	"os"
	"strings"
	"unicode/utf8"
	"unsafe"
)

var readConsoleInput = windows.NewLazySystemDLL("kernel32.dll").NewProc("ReadConsoleInputW")
var peekNamedPipe = windows.NewLazySystemDLL("kernel32.dll").NewProc("PeekNamedPipe")

func readNative(file *os.File, raw bool) ([]byte, error) {
	handle := windows.Handle(file.Fd())
	if raw {
		wait, err := windows.WaitForSingleObject(handle, 0)
		if err != nil {
			return nil, err
		}
		if wait != windows.WAIT_OBJECT_0 {
			return nil, nil
		}
		// INPUT_RECORD: event type/padding then 16-byte KEY_EVENT_RECORD.
		var record [20]byte
		var read uint32
		ok, _, err := readConsoleInput.Call(uintptr(handle), uintptr(unsafe.Pointer(&record[0])), 1, uintptr(unsafe.Pointer(&read)))
		if ok == 0 {
			return nil, err
		}
		if record[0] != 1 || *(*int32)(unsafe.Pointer(&record[4])) == 0 {
			return nil, nil
		}
		char := *(*uint16)(unsafe.Pointer(&record[14]))
		repeat := *(*uint16)(unsafe.Pointer(&record[8]))
		if repeat < 1 || repeat > 256 {
			return nil, windows.ERROR_INVALID_DATA
		}
		if char != 0 {
			if char >= 0xd800 && char <= 0xdfff {
				return nil, windows.ERROR_NO_UNICODE_TRANSLATION
			}
			if char == 8 {
				return []byte(strings.Repeat("\x7f", int(repeat))), nil
			}
			return []byte(strings.Repeat(string(utf8.AppendRune(nil, rune(char))), int(repeat))), nil
		}
		key := *(*uint16)(unsafe.Pointer(&record[10]))
		if key == 0x10 || key == 0x11 || key == 0x12 || key == 0x14 {
			return nil, nil
		}
		sequence := map[uint16]string{0x26: "\x1b[A", 0x28: "\x1b[B", 0x27: "\x1b[C", 0x25: "\x1b[D"}[key]
		if sequence == "" {
			return nil, windows.ERROR_NOT_SUPPORTED
		}
		return []byte(strings.Repeat(sequence, int(repeat))), nil
	}
	var available uint32
	ok, _, pipeErr := peekNamedPipe.Call(uintptr(handle), 0, 0, 0, uintptr(unsafe.Pointer(&available)), 0)
	if ok != 0 && available == 0 {
		return nil, nil
	}
	if ok == 0 && pipeErr == windows.ERROR_BROKEN_PIPE {
		return nil, io.EOF
	}
	// Regular redirected files are immediately readable; unknown pipe errors fail.
	if ok == 0 {
		info, err := file.Stat()
		if err != nil {
			return nil, err
		}
		if !info.Mode().IsRegular() {
			return nil, pipeErr
		}
	}
	buffer := make([]byte, 4096)
	n, err := file.Read(buffer)
	return buffer[:n], err
}
