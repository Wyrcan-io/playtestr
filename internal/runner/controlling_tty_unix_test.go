//go:build !windows

package runner

import "testing"

func TestControllingTerminalAvailable(t *testing.T) {
	err := runHelperSpec(t, "controlling-tty", []Step{{Expect: "controlling tty ready"}, {Exit: intPointer(0)}}, 5000)
	if err != nil {
		t.Fatal(err)
	}
}
