package vt10x

import (
	"bytes"
	"testing"
)

func TestPrimaryDeviceAttributesContract(t *testing.T) {
	for _, test := range []struct{ request, response string }{
		{"\x1b[c", "\x1b[?6c"},
		{"\x1b[0c", "\x1b[?6c"},
		{"\x1b[1c", ""},
		{"\x1b[?0c", ""},
		{"\x1b[>c", ""},
		{"\x1b[=c", ""},
		{"\x1b[0;1c", ""},
		{"\x1b]0;request-like [c text\x07", ""},
	} {
		for split := 0; split <= len(test.request); split++ {
			var replies bytes.Buffer
			terminal := New(WithWriter(&replies))
			terminal.Write([]byte(test.request[:split]))
			terminal.Write([]byte(test.request[split:]))
			if got := replies.String(); got != test.response {
				t.Fatalf("request %q split %d: reply %q, want %q", test.request, split, got, test.response)
			}
		}
	}
}
