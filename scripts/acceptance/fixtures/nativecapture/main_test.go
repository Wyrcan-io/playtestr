package main

import (
	"bytes"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestChild(t *testing.T) {
	mode := os.Getenv("PLAYTESTR_CAPTURE_TEST_CHILD")
	if mode == "" {
		return
	}
	switch mode {
	case "success":
		fmt.Print("actual selected output\n")
		os.Exit(0)
	case "nonzero":
		fmt.Print("partial selected output\n")
		os.Exit(7)
	case "flood":
		_, _ = os.Stdout.Write(bytes.Repeat([]byte("x"), outputLimit+1))
		os.Exit(0)
	}
	os.Exit(9)
}

func TestRealTargetOutputAndExactExit(t *testing.T) {
	self, err := os.Executable()
	if err != nil {
		t.Fatal(err)
	}
	for _, test := range []struct {
		mode, output string
		code         int
	}{
		{"success", "actual selected output\n", 0},
		{"nonzero", "partial selected output\n", 7},
		{"flood", strings.Repeat("x", outputLimit), 125},
	} {
		t.Run(test.mode, func(t *testing.T) {
			t.Chdir(t.TempDir())
			t.Setenv("PLAYTESTR_CAPTURE_TEST_CHILD", test.mode)
			var diagnostics bytes.Buffer
			code := run([]string{"--app", filepath.Base(self), "--output", "selected.txt", "--", "-test.run=^TestChild$"}, filepath.Dir(self), nil, &diagnostics)
			if code != test.code {
				t.Fatalf("exit %d, want %d; %s", code, test.code, diagnostics.String())
			}
			body, err := os.ReadFile("selected.txt")
			if err != nil || string(body) != test.output {
				t.Fatalf("unexpected captured output: %d bytes, %v", len(body), err)
			}
		})
	}
}

func TestRefuseExistingOutputAndEscapingSibling(t *testing.T) {
	t.Chdir(t.TempDir())
	original := []byte("preserve original")
	if err := os.WriteFile("selected.txt", original, 0600); err != nil {
		t.Fatal(err)
	}
	var diagnostics bytes.Buffer
	if code := run([]string{"--app", "app", "--output", "selected.txt"}, ".", nil, &diagnostics); code != 125 {
		t.Fatal("existing output accepted")
	}
	body, _ := os.ReadFile("selected.txt")
	if !bytes.Equal(body, original) {
		t.Fatal("existing output changed")
	}
	if code := run([]string{"--app", "../outside", "--output", "new.txt"}, ".", nil, &diagnostics); code != 125 {
		t.Fatal("escaping sibling accepted")
	}
	if _, err := os.Stat("new.txt"); !os.IsNotExist(err) {
		t.Fatal("invalid app created output")
	}
}
