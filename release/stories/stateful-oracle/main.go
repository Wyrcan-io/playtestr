package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"
)

func main() {
	if len(os.Args) != 2 {
		fmt.Fprintln(os.Stderr, "usage: stateful-oracle TARGET")
		os.Exit(2)
	}
	command := exec.Command(os.Args[1])
	command.Stdin, command.Stdout, command.Stderr = os.Stdin, os.Stdout, os.Stderr
	if err := command.Run(); err != nil {
		if exit, ok := err.(*exec.ExitError); ok {
			os.Exit(exit.ExitCode())
		}
		fmt.Fprintf(os.Stderr, "run target: %v\n", err)
		os.Exit(3)
	}
	path := os.Getenv("C2_CONFIG_PATH")
	data, err := os.ReadFile(path)
	if err != nil || strings.TrimSpace(string(data)) != "port=4242" {
		fmt.Fprintf(os.Stderr, "PLAYTESTR_STATEFUL_ORACLE=failed path=%q value=%q error=%v\n", path, data, err)
		os.Exit(90)
	}
	fmt.Println("PLAYTESTR_STATEFUL_ORACLE=passed")
}
