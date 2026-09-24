package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

var ownedRun string

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "PLAYTESTR-GITUI-ORACLE: "+format+"\n", args...)
	if ownedRun != "" {
		_ = os.RemoveAll(ownedRun)
	}
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

func main() {
	if len(os.Args) != 2 {
		fail("usage: gitui-oracle PROFILE")
	}
	profile := os.Args[1]
	exe, err := os.Executable()
	if err != nil {
		fail("locate oracle: %v", err)
	}
	tools := filepath.Dir(exe)
	runs := filepath.Join(tools, "gitui-runs")
	if err := os.MkdirAll(runs, 0o700); err != nil {
		fail("create owned run root: %v", err)
	}
	cwd, err := os.MkdirTemp(runs, "repo-")
	if err != nil {
		fail("create owned repository: %v", err)
	}
	ownedRun = cwd
	defer os.RemoveAll(ownedRun)
	git(cwd, "init", "-b", "main")
	git(cwd, "config", "user.name", "Playtestr Corpus")
	git(cwd, "config", "user.email", "corpus@example.invalid")
	git(cwd, "config", "core.autocrlf", "false")
	globalConfig := filepath.Join(cwd, ".git", "playtestr-global-config")
	if err := os.WriteFile(globalConfig, []byte("[user]\n\tname = Playtestr Corpus\n\temail = corpus@example.invalid\n"), 0o600); err != nil {
		fail("write isolated Git config: %v", err)
	}
	if err := os.WriteFile(filepath.Join(cwd, "selected.txt"), []byte("PLAYTESTR-GUI baseline\n"), 0o600); err != nil {
		fail("write baseline: %v", err)
	}
	if err := os.WriteFile(filepath.Join(cwd, "neighbor.txt"), []byte("PLAYTESTR-GUI neighbor\n"), 0o600); err != nil {
		fail("write neighbor: %v", err)
	}
	git(cwd, "add", "selected.txt", "neighbor.txt")
	git(cwd, "commit", "-m", "PLAYTESTR-GUI initial")
	initial := git(cwd, "rev-parse", "HEAD")
	if profile == "history" {
		if err := os.WriteFile(filepath.Join(cwd, "history.txt"), []byte("PLAYTESTR-GUI history marker\n"), 0o600); err != nil {
			fail("write history: %v", err)
		}
		git(cwd, "add", "history.txt")
		git(cwd, "commit", "-m", "PLAYTESTR-GUI reviewed history")
	} else if profile != "empty" {
		if err := os.WriteFile(filepath.Join(cwd, "selected.txt"), []byte("PLAYTESTR-GUI selected changed\n"), 0o600); err != nil {
			fail("write selected: %v", err)
		}
		if profile == "stage" || profile == "diff" || profile == "help" {
			if err := os.WriteFile(filepath.Join(cwd, "neighbor.txt"), []byte("PLAYTESTR-GUI neighbor changed\n"), 0o600); err != nil {
				fail("write neighbor: %v", err)
			}
		}
		if profile == "unstage" || profile == "commit" || profile == "cancel" {
			git(cwd, "add", "selected.txt")
		}
	}
	target := filepath.Clean(filepath.Join(tools, "..", "r3c", "windows", "rs-02-gitui", "bin", "gitui.exe"))
	if os.Getenv("PLAYTESTR_GITUI_MUTATION") == "1" {
		target = filepath.Join(tools, "gitui-mutated.exe")
	}
	command := exec.Command(target)
	command.Dir = cwd
	command.Stdin, command.Stdout, command.Stderr = os.Stdin, os.Stdout, os.Stderr
	command.Env = append(os.Environ(), "GIT_CONFIG_GLOBAL="+globalConfig)
	if err := command.Run(); err != nil {
		if exit, ok := err.(*exec.ExitError); ok {
			fail("gitui exited with code %d", exit.ExitCode())
		}
		fail("run gitui: %v", err)
	}
	cached := git(cwd, "diff", "--cached", "--name-only")
	work := git(cwd, "diff", "--name-only")
	head := git(cwd, "rev-parse", "HEAD")
	switch profile {
	case "stage":
		if cached != "selected.txt" || work != "neighbor.txt" {
			fail("stage state cached=%q work=%q", cached, work)
		}
	case "unstage":
		if cached != "" || work != "selected.txt" {
			fail("unstage state cached=%q work=%q", cached, work)
		}
	case "commit":
		if head == initial || git(cwd, "log", "-1", "--pretty=%s") != "PLAYTESTR-GUI commit" || cached != "" || work != "" {
			fail("commit state is not exact")
		}
	case "cancel":
		if head != initial || cached != "selected.txt" {
			fail("cancel changed HEAD or index")
		}
	case "history", "empty":
		if git(cwd, "status", "--porcelain") != "" {
			fail("read-only profile changed repository")
		}
	case "diff", "help":
		if cached != "" || !strings.Contains(work, "selected.txt") {
			fail("read-only profile changed expected worktree state")
		}
	default:
		fail("unknown profile %q", profile)
	}
	fmt.Printf("PLAYTESTR-GITUI-ORACLE %s OK\n", profile)
}
