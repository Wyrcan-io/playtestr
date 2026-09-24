package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: node-target PACKAGE_RELATIVE_JS [ARG ...]")
		os.Exit(2)
	}
	relative := filepath.Clean(os.Args[1])
	if filepath.IsAbs(relative) || relative == ".." || strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		fmt.Fprintf(os.Stderr, "unsafe package path %q\n", os.Args[1])
		os.Exit(2)
	}
	executable, err := os.Executable()
	if err != nil {
		fmt.Fprintf(os.Stderr, "locate launcher: %v\n", err)
		os.Exit(90)
	}
	runtimeDir := "npkill-runtime"
	if override := os.Getenv("PLAYTESTR_NODE_RUNTIME"); override != "" {
		if filepath.Base(override) != override {
			fmt.Fprintf(os.Stderr, "unsafe runtime directory %q\n", override)
			os.Exit(2)
		}
		runtimeDir = override
	}
	target := filepath.Join(filepath.Dir(executable), runtimeDir, "node_modules", relative)
	node, err := exec.LookPath("node")
	if err != nil {
		fmt.Fprintf(os.Stderr, "locate node: %v\n", err)
		os.Exit(90)
	}
	command := exec.Command(node, append([]string{target}, os.Args[2:]...)...)
	command.Stdin = os.Stdin
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr
	if err := command.Run(); err != nil {
		if exitErr, ok := err.(*exec.ExitError); ok {
			os.Exit(exitErr.ExitCode())
		}
		fmt.Fprintf(os.Stderr, "run node target: %v\n", err)
		os.Exit(90)
	}
}
