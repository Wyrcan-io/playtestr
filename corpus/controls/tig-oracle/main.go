package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "PLAYTESTR-TIG-ORACLE: "+format+"\n", args...)
	os.Exit(1)
}

func git(cwd string, args ...string) string {
	command := exec.Command("git", append([]string{"-c", "commit.gpgsign=false"}, args...)...)
	command.Dir = cwd
	command.Env = append(os.Environ(), "GIT_CONFIG_GLOBAL=NUL")
	output, err := command.CombinedOutput()
	if err != nil {
		fail("git %s: %v: %s", strings.Join(args, " "), err, output)
	}
	return strings.TrimSpace(string(output))
}

func write(path, body string) {
	if err := os.WriteFile(path, []byte(body), 0o600); err != nil {
		fail("write fixture: %v", err)
	}
}

func linuxPath(path string) string {
	output, err := exec.Command("wsl.exe", "-e", "wslpath", "-a", path).CombinedOutput()
	if err != nil {
		fail("translate workspace path: %v: %s", err, output)
	}
	return strings.TrimSpace(string(output))
}

func main() {
	if len(os.Args) != 2 {
		fail("usage: tig-oracle PROFILE")
	}
	profile := os.Args[1]
	cwd, err := os.Getwd()
	if err != nil {
		fail("working directory: %v", err)
	}
	_ = os.Remove(filepath.Join(cwd, "README.txt"))
	git(cwd, "init", "-b", "main")
	git(cwd, "config", "user.name", "Playtestr Corpus")
	git(cwd, "config", "user.email", "corpus@example.invalid")
	git(cwd, "config", "core.autocrlf", "false")
	for _, item := range []struct{ file, body, subject string }{
		{"alpha.txt", "PLAYTESTR-TIG alpha body\n", "PLAYTESTR-TIG alpha"},
		{"beta.txt", "PLAYTESTR-TIG beta body\n", "PLAYTESTR-TIG beta"},
		{"gamma.txt", "PLAYTESTR-TIG gamma body\n", "PLAYTESTR-TIG gamma"},
	} {
		write(filepath.Join(cwd, item.file), item.body)
		git(cwd, "add", item.file)
		git(cwd, "commit", "-m", item.subject)
	}
	baseline := git(cwd, "rev-parse", "HEAD")
	git(cwd, "switch", "-c", "trial-branch")
	write(filepath.Join(cwd, "branch.txt"), "PLAYTESTR-TIG branch body\n")
	git(cwd, "add", "branch.txt")
	git(cwd, "commit", "-m", "PLAYTESTR-TIG branch-only")
	branchHead := git(cwd, "rev-parse", "HEAD")
	git(cwd, "switch", "main")

	target := "/home/abhir/playtestr-corpus/install/tig/bin/tig"
	if os.Getenv("PLAYTESTR_TIG_MUTATION") == "1" {
		target = "/home/abhir/playtestr-corpus/install/tig-mutated/bin/tig"
	}
	args := []string{"--cd", linuxPath(cwd), "-e", "env", "TERM=xterm-256color", target}
	if profile == "branch" {
		args = append(args, "trial-branch")
	}
	command := exec.Command("wsl.exe", args...)
	command.Stdin, command.Stdout, command.Stderr = os.Stdin, os.Stdout, os.Stderr
	if err := command.Run(); err != nil {
		fail("tig: %v", err)
	}
	if got := git(cwd, "status", "--porcelain=v1"); got != "" {
		fail("repository changed: %q", got)
	}
	if got := git(cwd, "rev-parse", "main"); got != baseline {
		fail("main moved")
	}
	if got := git(cwd, "rev-parse", "trial-branch"); got != branchHead {
		fail("trial branch moved")
	}
	fmt.Printf("PLAYTESTR-TIG-ORACLE %s OK\n", profile)
}
