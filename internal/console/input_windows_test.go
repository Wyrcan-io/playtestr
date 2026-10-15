//go:build windows

package console

import "testing"

func TestWindowsNativeNavigationModifiersRejected(t *testing.T) {
	for _, key := range []uint16{0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28} {
		if nativeNavigationSequence(key, 0) == "" || nativeNavigationSequence(key, 0x100) == "" {
			t.Fatalf("unmodified/enhanced navigation key %x was rejected", key)
		}
		for _, modifier := range []uint32{1, 2, 4, 8, 16} {
			if sequence := nativeNavigationSequence(key, modifier); sequence != "" {
				t.Fatalf("unsupported modified key %x state=%x silently became %q", key, modifier, sequence)
			}
		}
	}
}
