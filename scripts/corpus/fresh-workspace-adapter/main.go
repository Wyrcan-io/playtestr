// Command fresh-workspace-adapter proves a copied Git fixture is fresh before
// launching a real target and unchanged after it exits. It is Sprint 11 test
// infrastructure; target-specific state checks do not belong in the runner.
package main

import (
	"bytes"
	"crypto/sha256"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

func main() {
	target := flag.String("target", "", "absolute path to the real target")
	required := flag.String("required-file", "", "fixture-relative file that must remain unchanged")
	flag.Parse()
	if *target == "" || !filepath.IsAbs(*target) || *required == "" || filepath.IsAbs(*required) {
		fmt.Fprintln(os.Stderr, "target must be absolute and required-file must be relative")
		os.Exit(2)
	}
	before, err := validateFresh(*required, true)
	if err != nil {
		fmt.Fprintf(os.Stderr, "pre-launch workspace oracle: %v\n", err)
		os.Exit(3)
	}
	command := exec.Command(*target, flag.Args()...)
	command.Stdin = os.Stdin
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr
	if err := command.Run(); err != nil {
		if exit, ok := err.(*exec.ExitError); ok {
			os.Exit(exit.ExitCode())
		}
		fmt.Fprintf(os.Stderr, "run target: %v\n", err)
		os.Exit(4)
	}
	after, err := validateFresh(*required, false)
	if err != nil {
		fmt.Fprintf(os.Stderr, "post-exit workspace oracle: %v\n", err)
		os.Exit(5)
	}
	if before != after {
		fmt.Fprintln(os.Stderr, "post-exit workspace oracle: required file changed")
		os.Exit(5)
	}
	fmt.Println("PLAYTESTR_FRESH_ORACLE=passed")
}

func validateFresh(required string, requireEmptyHome bool) ([sha256.Size]byte, error) {
	var zero [sha256.Size]byte
	data, err := os.ReadFile(required)
	if err != nil {
		return zero, fmt.Errorf("read required file: %w", err)
	}
	index := exec.Command("git", "diff", "--cached", "--name-only")
	output, err := index.Output()
	if err != nil {
		return zero, fmt.Errorf("read Git index: %w", err)
	}
	if len(bytes.TrimSpace(output)) != 0 {
		return zero, fmt.Errorf("Git index is not empty")
	}
	if requireEmptyHome {
		home, err := os.UserHomeDir()
		if err != nil {
			return zero, fmt.Errorf("resolve managed home: %w", err)
		}
		var unexpected string
		err = filepath.WalkDir(home, func(path string, entry os.DirEntry, walkErr error) error {
			if walkErr != nil {
				return walkErr
			}
			if path != home && !entry.IsDir() {
				unexpected = path
				return filepath.SkipAll
			}
			return nil
		})
		if err != nil {
			return zero, fmt.Errorf("read managed home: %w", err)
		}
		if unexpected != "" {
			return zero, fmt.Errorf("managed home contains file %q", unexpected)
		}
	}
	return sha256.Sum256(data), nil
}
