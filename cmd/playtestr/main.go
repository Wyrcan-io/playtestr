package main

import (
	"flag"
	"fmt"
	"github.com/Wyrcan-io/playtestr/internal/runner"
	"os"
)

func main() {
	if len(os.Args) < 2 || os.Args[1] != "test" {
		fmt.Fprintln(os.Stderr, "Usage: playtestr test [--update] spec.json [...]")
		os.Exit(2)
	}
	flags := flag.NewFlagSet("test", flag.ExitOnError)
	update := flags.Bool("update", false, "write snapshot baselines")
	flags.Parse(os.Args[2:])
	if flags.NArg() == 0 {
		fmt.Fprintln(os.Stderr, "provide at least one spec.json")
		os.Exit(2)
	}
	failed := false
	for _, path := range flags.Args() {
		if err := runner.Run(path, *update, os.Stdout); err != nil {
			fmt.Fprintln(os.Stderr, "FAIL", err)
			failed = true
		}
	}
	if failed {
		os.Exit(1)
	}
}
