package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
)

type oracle struct {
	Files map[string]string `json:"files"`
}

func main() {
	if len(os.Args) < 4 || os.Args[2] != "--" {
		fmt.Fprintln(os.Stderr, "usage: micro-oracle ORACLE.json -- MICRO [ARG ...]")
		os.Exit(2)
	}

	data, err := os.ReadFile(os.Args[1])
	if err != nil {
		fail("read oracle", err)
	}
	var expected oracle
	if err := json.Unmarshal(data, &expected); err != nil {
		fail("decode oracle", err)
	}
	if len(expected.Files) == 0 {
		fail("validate oracle", fmt.Errorf("files must not be empty"))
	}

	target := os.Args[3]
	if filepath.Base(target) == target {
		executable, err := os.Executable()
		if err != nil {
			fail("locate oracle executable", err)
		}
		target = filepath.Join(filepath.Dir(executable), target)
	}
	command := exec.Command(target, os.Args[4:]...)
	command.Stdin = os.Stdin
	command.Stdout = os.Stdout
	command.Stderr = os.Stderr
	err = command.Run()
	exitCode := 0
	if err != nil {
		var exitErr *exec.ExitError
		if !asExitError(err, &exitErr) {
			fail("run micro", err)
		}
		exitCode = exitErr.ExitCode()
	}
	fmt.Printf("PLAYTESTR_MICRO_TARGET_EXIT=%d\n", exitCode)
	if exitCode != 0 {
		os.Exit(exitCode)
	}

	for name, want := range expected.Files {
		path, err := localPath(name)
		if err != nil {
			fail("validate oracle path", err)
		}
		got, err := os.ReadFile(path)
		if err != nil {
			fail("read oracle file", err)
		}
		if !bytes.Equal(got, []byte(want)) {
			fail("check oracle file", fmt.Errorf("%s bytes differ", name))
		}
	}
	fmt.Println("PLAYTESTR_MICRO_ORACLE=passed")
}

func asExitError(err error, target **exec.ExitError) bool {
	exitErr, ok := err.(*exec.ExitError)
	if ok {
		*target = exitErr
	}
	return ok
}

func localPath(name string) (string, error) {
	if name == "" || filepath.IsAbs(name) || filepath.Clean(name) != name {
		return "", fmt.Errorf("unsafe relative path %q", name)
	}
	root, err := os.Getwd()
	if err != nil {
		return "", err
	}
	path := filepath.Join(root, name)
	relative, err := filepath.Rel(root, path)
	if err != nil || relative == ".." || filepath.IsAbs(relative) {
		return "", fmt.Errorf("path escapes working directory: %q", name)
	}
	return path, nil
}

func fail(operation string, err error) {
	fmt.Fprintf(os.Stderr, "PLAYTESTR_MICRO_ORACLE=failed: %s: %v\n", operation, err)
	os.Exit(90)
}
