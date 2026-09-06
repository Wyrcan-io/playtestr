package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"

	"github.com/Wyrcan-io/playtestr/internal/runner"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	os.Exit(run(ctx, os.Args[1:], os.Stdout, os.Stderr))
}

func run(ctx context.Context, args []string, stdout, stderr io.Writer) int {
	if len(args) < 1 || args[0] != "test" {
		fmt.Fprintln(stderr, "Usage: playtestr test [--update] spec.json [...]")
		return 2
	}
	flags := flag.NewFlagSet("test", flag.ContinueOnError)
	flags.SetOutput(stderr)
	update := flags.Bool("update", false, "write snapshot baselines")
	if err := flags.Parse(args[1:]); err != nil {
		return 2
	}
	if flags.NArg() == 0 {
		fmt.Fprintln(stderr, "provide at least one spec.json")
		return 2
	}
	failed := false
	for _, path := range flags.Args() {
		if err := runner.RunContext(ctx, path, *update, stdout); err != nil {
			fmt.Fprintln(stderr, "FAIL", err)
			failed = true
		}
		if ctx.Err() != nil {
			return 130
		}
	}
	if failed {
		return 1
	}
	return 0
}
