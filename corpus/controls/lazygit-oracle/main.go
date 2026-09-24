package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "PLAYTESTR-LAZYGIT-ORACLE: "+format+"\n", args...)
	os.Exit(1)
}

func git(cwd string, args ...string) string {
	command := exec.Command("git", append([]string{"-c", "commit.gpgsign=false"}, args...)...)
	command.Dir = cwd
	command.Env = append(os.Environ(), "GIT_CONFIG_GLOBAL="+os.DevNull)
	output, err := command.CombinedOutput()
	if err != nil {
		fail("git %s: %v: %s", strings.Join(args, " "), err, output)
	}
	return strings.TrimSpace(string(output))
}

func runTarget(target, cwd, config string) {
	command := exec.Command(target, "--use-config-dir", config)
	command.Dir = cwd
	command.Stdin, command.Stdout, command.Stderr = os.Stdin, os.Stdout, os.Stderr
	command.Env = append(os.Environ(), "GIT_CONFIG_COUNT=1", "GIT_CONFIG_KEY_0=safe.directory", "GIT_CONFIG_VALUE_0=*")
	if err := command.Run(); err != nil {
		if exit, ok := err.(*exec.ExitError); ok {
			fail("lazygit exited with code %d", exit.ExitCode())
		}
		fail("run lazygit: %v", err)
	}
}

func main() {
	if len(os.Args) != 2 {
		fail("usage: lazygit-oracle PROFILE")
	}
	profile := os.Args[1]
	cwd, err := os.Getwd()
	if err != nil {
		fail("working directory: %v", err)
	}
	if err := os.Remove(filepath.Join(cwd, "README.txt")); err != nil && !os.IsNotExist(err) {
		fail("remove fixture note from working repository: %v", err)
	}
	git(cwd, "init", "-b", "main")
	git(cwd, "config", "user.name", "Playtestr Corpus")
	git(cwd, "config", "user.email", "corpus@example.invalid")
	git(cwd, "config", "core.autocrlf", "false")
	if err := os.WriteFile(filepath.Join(cwd, "alpha.txt"), []byte("PLAYTESTR-LG alpha baseline\n"), 0o600); err != nil {
		fail("write alpha: %v", err)
	}
	if err := os.WriteFile(filepath.Join(cwd, "beta.txt"), []byte("PLAYTESTR-LG beta baseline\n"), 0o600); err != nil {
		fail("write beta: %v", err)
	}
	git(cwd, "add", "alpha.txt", "beta.txt")
	git(cwd, "commit", "-m", "PLAYTESTR-LG initial")
	initial := git(cwd, "rev-parse", "HEAD")
	if profile == "branch" {
		git(cwd, "switch", "-c", "trial-branch")
		git(cwd, "switch", "main")
	} else {
		if err := os.WriteFile(filepath.Join(cwd, "alpha.txt"), []byte("PLAYTESTR-LG alpha changed\n"), 0o600); err != nil {
			fail("change alpha: %v", err)
		}
		if profile == "navigate" || profile == "help" {
			if err := os.WriteFile(filepath.Join(cwd, "beta.txt"), []byte("PLAYTESTR-LG beta changed\n"), 0o600); err != nil {
				fail("change beta: %v", err)
			}
		}
		if profile == "unstage" || profile == "cancel" {
			git(cwd, "add", "alpha.txt")
		}
	}
	exe, err := os.Executable()
	if err != nil {
		fail("locate oracle: %v", err)
	}
	tools := filepath.Dir(exe)
	targetName := "lazygit"
	if runtime.GOOS == "windows" {
		targetName += ".exe"
	}
	target := filepath.Join(tools, "lazygit-target", targetName)
	if os.Getenv("PLAYTESTR_LAZYGIT_MUTATION") == "1" {
		target = filepath.Join(tools, "lazygit-mutated.exe")
	}
	config := filepath.Join(os.TempDir(), "playtestr-lazygit-config")
	if err := os.MkdirAll(config, 0o700); err != nil {
		fail("create config: %v", err)
	}
	if err := os.WriteFile(filepath.Join(config, "config.yml"), []byte("disableStartupPopups: true\ngui:\n  showRandomTip: false\n"), 0o600); err != nil {
		fail("write config: %v", err)
	}
	runTarget(target, cwd, config)
	if profile == "fresh" {
		fmt.Println("PLAYTESTR-LAZYGIT-SECOND")
		runTarget(target, cwd, config)
	}
	cached := git(cwd, "diff", "--cached", "--name-only")
	work := git(cwd, "diff", "--name-only")
	head := git(cwd, "rev-parse", "HEAD")
	switch profile {
	case "stage":
		if cached != "alpha.txt" || work != "" {
			fail("stage state cached=%q work=%q", cached, work)
		}
	case "unstage":
		if cached != "" || work != "alpha.txt" {
			fail("unstage state cached=%q work=%q", cached, work)
		}
	case "commit":
		if head == initial || git(cwd, "log", "-1", "--pretty=%s") != "PLAYTESTR-LG commit" || cached != "" || work != "" {
			fail("commit state is not exact")
		}
	case "cancel":
		if head != initial || cached != "alpha.txt" {
			fail("cancel changed HEAD or index")
		}
	case "branch":
		current := git(cwd, "branch", "--show-current")
		if current != "trial-branch" || head != initial {
			fail("branch switch state current=%q head_unchanged=%v", current, head == initial)
		}
	case "navigate", "help":
		if cached != "" || work != "alpha.txt\nbeta.txt" {
			fail("read-only profile changed repository")
		}
	case "fresh":
		if cached != "" || work != "alpha.txt" || head != initial {
			fail("fresh sessions changed repository")
		}
	default:
		fail("unknown profile %q", profile)
	}
	fmt.Printf("PLAYTESTR-LAZYGIT-ORACLE %s OK\n", profile)
}
