package main

import (
	"context"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"
	"path/filepath"

	"github.com/Wyrcan-io/playtestr/internal/buildinfo"
	"github.com/Wyrcan-io/playtestr/internal/report"
	"github.com/Wyrcan-io/playtestr/internal/runner"
)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	os.Exit(run(ctx, os.Args[1:], os.Stdout, os.Stderr))
}

func usage(out io.Writer) {
	fmt.Fprintln(out, "Playtestr drives trusted interactive CLIs through a real terminal.")
	fmt.Fprintln(out)
	fmt.Fprintln(out, "Usage:")
	fmt.Fprintln(out, "  playtestr test [--report results.json] [--update [--snapshot name]] spec.json [...]")
	fmt.Fprintln(out, "  playtestr --version")
	fmt.Fprintln(out)
	fmt.Fprintln(out, "Run 'playtestr test --help' for test options.")
}

func run(ctx context.Context, args []string, stdout, stderr io.Writer) int {
	if len(args) == 1 && (args[0] == "--version" || args[0] == "version") {
		fmt.Fprintf(stdout, "playtestr %s\n", buildinfo.Version)
		return 0
	}
	if len(args) == 0 || (len(args) == 1 && (args[0] == "--help" || args[0] == "-h" || args[0] == "help")) {
		usage(stdout)
		return 0
	}
	if args[0] != "test" {
		fmt.Fprintf(stderr, "unknown command %q\n\n", args[0])
		usage(stderr)
		return 2
	}
	flags := flag.NewFlagSet("test", flag.ContinueOnError)
	flags.SetOutput(stderr)
	flags.Usage = func() {
		fmt.Fprintln(flags.Output(), "Usage: playtestr test [options] spec.json [...]")
		fmt.Fprintln(flags.Output())
		fmt.Fprintln(flags.Output(), "Options:")
		flags.PrintDefaults()
	}
	update := flags.Bool("update", false, "write snapshot baselines after a successful run")
	snapshot := flags.String("snapshot", "", "with --update, update only this snapshot")
	reportPath := flags.String("report", "", "atomically write a versioned JSON report")
	if err := flags.Parse(args[1:]); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}
	if flags.NArg() == 0 {
		fmt.Fprintln(stderr, "provide at least one spec.json")
		return 2
	}
	if *snapshot != "" && !*update {
		fmt.Fprintln(stderr, "--snapshot requires --update")
		return 2
	}
	if *snapshot != "" && flags.NArg() != 1 {
		fmt.Fprintln(stderr, "--snapshot requires exactly one spec.json")
		return 2
	}
	paths := flags.Args()
	results := make([]runner.RunResult, 0, len(paths))
	failed := false
	cancelled := false
	for index, path := range paths {
		options := runner.RunOptions{Update: *update, Snapshot: *snapshot}
		result := runner.RunDetailedContext(ctx, path, options, stdout)
		results = append(results, result)
		if err := result.Err(); err != nil {
			fmt.Fprintln(stderr, "FAIL", err)
			failed = true
		}
		if ctx.Err() != nil || result.Status == "cancelled" {
			cancelled = true
			for _, skipped := range paths[index+1:] {
				results = append(results, runner.RunResult{
					Name: filepath.Base(skipped), SpecPath: filepath.Clean(skipped), Status: "not_run",
				})
			}
			break
		}
	}
	if *reportPath != "" {
		document := report.New(buildinfo.Version, results)
		if err := report.Write(*reportPath, document); err != nil {
			fmt.Fprintln(stderr, "FAIL write report:", err)
			failed = true
		} else {
			fmt.Fprintln(stdout, "Report saved:", *reportPath)
		}
	}
	if cancelled {
		return 130
	}
	if failed {
		return 1
	}
	return 0
}
