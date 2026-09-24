package main

import (
	"bytes"
	"crypto/sha256"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "PLAYTESTR-MITM-ORACLE: "+format+"\n", args...)
	os.Exit(1)
}

func main() {
	exe, err := os.Executable()
	if err != nil {
		fail("locate oracle: %v", err)
	}
	tools := filepath.Dir(exe)
	retained := filepath.Clean(filepath.Join(tools, "..", "r3c", "windows", "py-03-mitmproxy"))
	cwd, err := os.Getwd()
	if err != nil {
		fail("working directory: %v", err)
	}
	source := filepath.Join(retained, "fixture with spaces", "good.mitm")
	flow := filepath.Join(cwd, "trial.mitm")
	data, err := os.ReadFile(source)
	if err != nil {
		fail("read retained flow: %v", err)
	}
	if err := os.WriteFile(flow, data, 0o600); err != nil {
		fail("prepare flow: %v", err)
	}
	before := sha256.Sum256(data)
	args := []string{"--no-server", "--rfile", "trial.mitm", "--set", "confdir=" + filepath.Join(cwd, "config"), "--console-layout", "single"}
	target := filepath.Join(retained, "venv", "Scripts", "mitmproxy.exe")
	if os.Getenv("PLAYTESTR_MITM_MUTATION") == "1" {
		target = filepath.Join(retained, "venv", "Scripts", "python.exe")
		mutationPath := filepath.Join(tools, "mitmproxy-mutated")
		fmt.Fprintln(os.Stderr, "PLAYTESTR-MITM-MUTATED-TARGET")
		bootstrap := fmt.Sprintf("import sys;sys.path.insert(0,%q);from mitmproxy.tools.main import mitmproxy;mitmproxy()", mutationPath)
		args = append([]string{"-c", bootstrap}, args...)
	}
	command := exec.Command(target, args...)
	command.Stdin, command.Stdout, command.Stderr = os.Stdin, os.Stdout, os.Stderr
	command.Env = os.Environ()
	if os.Getenv("PLAYTESTR_MITM_MUTATION") == "1" {
		filtered := command.Env[:0]
		for _, value := range command.Env {
			if !strings.HasPrefix(strings.ToUpper(value), "PYTHONPATH=") {
				filtered = append(filtered, value)
			}
		}
		command.Env = append(filtered, "PYTHONPATH="+filepath.Join(tools, "mitmproxy-mutated"))
	}
	if err := command.Run(); err != nil {
		if exit, ok := err.(*exec.ExitError); ok {
			os.Exit(exit.ExitCode())
		}
		fail("run mitmproxy: %v", err)
	}
	after, err := os.ReadFile(flow)
	if err != nil {
		fail("read flow after run: %v", err)
	}
	if sha256.Sum256(after) != before || !bytes.Equal(after, data) {
		fail("input flow changed")
	}
	check := exec.Command(filepath.Join(retained, "venv", "Scripts", "python.exe"), "-c", "from mitmproxy import io;f=open('trial.mitm','rb');x=next(io.FlowReader(f).stream());assert x.request.pretty_url=='http://fixture.invalid/PLAYTESTR-PY03';assert x.request.headers['X-Playtestr']=='PLAYTESTR-PY03';assert x.response.get_text()=='PLAYTESTR-PY03 λ detail';f.close()")
	check.Dir = cwd
	check.Env = os.Environ()
	check.Stdout, check.Stderr = io.Discard, os.Stderr
	if err := check.Run(); err != nil {
		fail("independent flow verification: %v", err)
	}
	fmt.Println("PLAYTESTR-MITM-ORACLE OK")
}
