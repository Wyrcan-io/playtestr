package runner

import (
	"os"
	"path/filepath"
	"testing"

	"github.com/hinshun/vt10x"
)

func TestScreenRedraw(t *testing.T) {
	terminal := vt10x.New(vt10x.WithSize(30, 5))
	terminal.Write([]byte("old content\x1b[2J\x1b[H\x1b[32mready\x1b[0m"))
	if got := normalize(terminal.String()); got != "ready\n" {
		t.Fatalf("got %q", got)
	}
}

func TestRejectInvalidSpecs(t *testing.T) {
	for _, data := range []string{
		`{"command":["demo"],"steps":[{"key":"Wrong"}]}`,
		`{"command":["demo"],"steps":[{"snapshot":"../escape"}]}`,
		`{"command":["demo"],"steps":[{"key":"Enter","expect":"ok"}]}`,
		`{"command":["demo"],"width":-1,"steps":[{"expect":"ok"}]}`,
		`{"command":["demo"],"steps":[{"expect":"ok"}],"typo":true}`,
	} {
		path := filepath.Join(t.TempDir(), "test.json")
		if e := os.WriteFile(path, []byte(data), 0600); e != nil {
			t.Fatal(e)
		}
		if _, e := Load(path); e == nil {
			t.Fatalf("accepted %s", data)
		}
	}
}
