package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

type task struct {
	Description string `json:"description"`
	Status      string `json:"status"`
}

func fail(format string, args ...any) {
	fmt.Fprintf(os.Stderr, "PLAYTESTR-TASK-ORACLE: "+format+"\n", args...)
	os.Exit(1)
}

func linuxPath(path string) string {
	volume := filepath.VolumeName(path)
	if len(volume) != 2 || volume[1] != ':' {
		fail("workspace path has no Windows drive: %q", path)
	}
	rest := strings.ReplaceAll(strings.TrimPrefix(path, volume), `\`, "/")
	return "/mnt/" + strings.ToLower(volume[:1]) + rest
}

func localTasks(cwd string) []task {
	description := regexp.MustCompile(`description:"([^"]*)"`)
	status := regexp.MustCompile(`status:"([^"]*)"`)
	var tasks []task
	for _, name := range []string{"pending.data", "completed.data"} {
		data, err := os.ReadFile(filepath.Join(cwd, ".task", name))
		if err != nil && !os.IsNotExist(err) {
			fail("read %s: %v", name, err)
		}
		for _, line := range strings.Split(string(data), "\n") {
			descMatch, statusMatch := description.FindStringSubmatch(line), status.FindStringSubmatch(line)
			if len(descMatch) == 2 && len(statusMatch) == 2 {
				tasks = append(tasks, task{Description: descMatch[1], Status: statusMatch[1]})
			}
		}
	}
	sort.Slice(tasks, func(i, j int) bool { return tasks[i].Description < tasks[j].Description })
	return tasks
}

func runTarget(cwd, taskrc, target, profile string) {
	args := []string{"--cd", cwd, "-e", "env", "TERM=xterm-256color", "TASKRC=" + taskrc, target, "--taskrc", taskrc}
	if profile == "filter" || profile == "empty" {
		args = append(args, "--report", "playtestr")
	}
	for attempt := 0; attempt < 10; attempt++ {
		command := exec.Command("wsl.exe", args...)
		command.Stdin, command.Stdout, command.Stderr = os.Stdin, os.Stdout, os.Stderr
		err := command.Run()
		if err == nil {
			return
		}
		if !strings.Contains(err.Error(), "invalid argument") {
			fail("taskwarrior-tui: %v", err)
		}
		time.Sleep(time.Second)
	}
	fail("taskwarrior-tui: WSL launch returned invalid argument ten times")
}

func main() {
	if len(os.Args) != 2 {
		fail("usage: task-oracle PROFILE")
	}
	profile := os.Args[1]
	cwd, err := os.Getwd()
	if err != nil {
		fail("working directory: %v", err)
	}
	_ = os.Remove(filepath.Join(cwd, "README.txt"))
	lcwd := linuxPath(cwd)
	taskrc := lcwd + "/.taskrc"
	rc := "data.location=" + lcwd + "/.task\nconfirmation=no\nverbose=nothing\nuda.taskwarrior-tui.task-report.prompt-on-done=yes\nuda.taskwarrior-tui.task-report.prompt-on-delete=yes\n"
	if profile == "filter" || profile == "empty" {
		match := "beta"
		if profile == "empty" {
			match = "NO-SUCH-TASK"
		}
		rc += "report.playtestr.description=Playtestr exact corpus filter\nreport.playtestr.columns=id,description\nreport.playtestr.labels=ID,Description\nreport.playtestr.filter=status:pending description.contains:" + match + "\n"
	}
	if err := os.WriteFile(filepath.Join(cwd, ".taskrc"), []byte(rc), 0o600); err != nil {
		fail("write taskrc: %v", err)
	}
	if err := os.MkdirAll(filepath.Join(cwd, ".task"), 0o700); err != nil {
		fail("create task data: %v", err)
	}
	pending := "" +
		`[description:"PLAYTESTR-TASK alpha" entry:"1790195000" modified:"1790195000" status:"pending" uuid:"10000000-0000-4000-8000-000000000001"]` + "\n" +
		`[description:"PLAYTESTR-TASK beta" entry:"1790195001" modified:"1790195001" status:"pending" uuid:"10000000-0000-4000-8000-000000000002"]` + "\n" +
		`[description:"PLAYTESTR-TASK gamma" entry:"1790195002" modified:"1790195002" status:"pending" uuid:"10000000-0000-4000-8000-000000000003"]` + "\n"
	if err := os.WriteFile(filepath.Join(cwd, ".task", "pending.data"), []byte(pending), 0o600); err != nil {
		fail("write pending tasks: %v", err)
	}
	before := localTasks(cwd)
	target := "/home/abhir/playtestr-corpus/bin/taskwarrior-tui"
	if os.Getenv("PLAYTESTR_TASK_MUTATION") == "1" {
		target = "/home/abhir/playtestr-corpus/bin/taskwarrior-tui-mutated"
	}
	time.Sleep(time.Second)
	runTarget(lcwd, taskrc, target, profile)
	if profile == "reopen" {
		fmt.Println("PLAYTESTR-TASK-SECOND")
		runTarget(lcwd, taskrc, target, profile)
	}
	after := localTasks(cwd)
	switch profile {
	case "filter", "empty", "help", "reopen":
		if len(after) != 3 || fmt.Sprint(after) != fmt.Sprint(before) {
			fail("read-only profile changed tasks: before=%v after=%v", before, after)
		}
	case "add":
		if len(after) != 4 || after[2].Description != "PLAYTESTR-TASK delta" || after[2].Status != "pending" {
			fail("add result is not exact: %v", after)
		}
	case "complete":
		completed := 0
		for _, item := range after {
			if item.Status == "completed" {
				completed++
			}
		}
		if len(after) != 3 || completed != 1 {
			fail("completion result is not exact: %v", after)
		}
	case "cancel":
		if len(after) != 3 || fmt.Sprint(after) != fmt.Sprint(before) {
			fail("cancel changed tasks: %v", after)
		}
	case "edit":
		found := false
		for _, item := range after {
			if item.Description == "PLAYTESTR-TASK edited" && item.Status == "pending" {
				found = true
			}
		}
		if len(after) != 3 || !found {
			fail("edit result is not exact: %v", after)
		}
	default:
		fail("unknown profile %q", profile)
	}
	fmt.Printf("PLAYTESTR-TASK-ORACLE %s OK\n", profile)
}
