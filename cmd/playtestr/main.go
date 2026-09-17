package main

import (
	"context"
	"crypto/sha256"
	"flag"
	"fmt"
	"io"
	"os"
	"os/signal"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/Wyrcan-io/playtestr/internal/buildinfo"
	"github.com/Wyrcan-io/playtestr/internal/discovery"
	"github.com/Wyrcan-io/playtestr/internal/report"
	"github.com/Wyrcan-io/playtestr/internal/runner"
)

const maxSuiteSteps = 10_000

var unsafeArtifactCharacter = regexp.MustCompile(`[^A-Za-z0-9._-]+`)

func main() {
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt)
	defer stop()
	os.Exit(run(ctx, os.Args[1:], os.Stdout, os.Stderr))
}

func usage(out io.Writer) {
	fmt.Fprintln(out, "Playtestr drives trusted interactive CLIs through a real terminal.")
	fmt.Fprintln(out)
	fmt.Fprintln(out, "Usage:")
	fmt.Fprintln(out, "  playtestr test [--list] path [...]")
	fmt.Fprintln(out, "  playtestr test [--artifacts-dir dir] [--report results.json] [--update [--snapshot name]] path [...]")
	fmt.Fprintln(out, "  playtestr report --input results.json --evidence-root dir --output report.html")
	fmt.Fprintln(out, "  playtestr --version")
	fmt.Fprintln(out)
	fmt.Fprintln(out, "Run 'playtestr test --help' or 'playtestr report --help' for command options.")
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
	if args[0] == "report" {
		return runReport(args[1:], stdout, stderr)
	}
	if args[0] != "test" {
		fmt.Fprintf(stderr, "unknown command %q\n\n", args[0])
		usage(stderr)
		return 2
	}
	flags := flag.NewFlagSet("test", flag.ContinueOnError)
	flags.SetOutput(stderr)
	flags.Usage = func() {
		fmt.Fprintln(flags.Output(), "Usage: playtestr test [options] path [...]")
		fmt.Fprintln(flags.Output())
		fmt.Fprintln(flags.Output(), "Options:")
		flags.PrintDefaults()
	}
	update := flags.Bool("update", false, "write snapshot baselines after a successful run")
	snapshot := flags.String("snapshot", "", "with --update, update only this snapshot")
	reportPath := flags.String("report", "", "atomically write a versioned JSON report")
	artifactsDir := flags.String("artifacts-dir", "", "write evidence beneath a unique directory for this suite run")
	listOnly := flags.Bool("list", false, "list selected specs without launching targets")
	if err := flags.Parse(args[1:]); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}
	if flags.NArg() == 0 {
		fmt.Fprintln(stderr, "provide at least one spec file or directory")
		return 2
	}
	if *snapshot != "" && !*update {
		fmt.Fprintln(stderr, "--snapshot requires --update")
		return 2
	}
	if *listOnly && (*update || *snapshot != "" || *reportPath != "" || *artifactsDir != "") {
		fmt.Fprintln(stderr, "--list cannot be combined with --update, --snapshot, --report, or --artifacts-dir")
		return 2
	}
	selected, err := discovery.ResolveExcluding(flags.Args(), []string{*artifactsDir})
	if err != nil {
		fmt.Fprintln(stderr, "selection error:", err)
		return 2
	}
	if *snapshot != "" && len(selected) != 1 {
		fmt.Fprintln(stderr, "--snapshot requires exactly one resolved spec")
		return 2
	}
	if *listOnly {
		fmt.Fprintf(stdout, "Selected %d specs:\n", len(selected))
		for _, spec := range selected {
			fmt.Fprintln(stdout, filepath.ToSlash(spec.DisplayPath))
		}
		return 0
	}
	if err := validateSuiteDestinations(selected, *reportPath, *artifactsDir, *update); err != nil {
		fmt.Fprintln(stderr, "selection error:", err)
		return 2
	}

	runArtifactsDir := ""
	if *artifactsDir != "" {
		if err := os.MkdirAll(*artifactsDir, 0755); err != nil {
			fmt.Fprintln(stderr, "FAIL create artifacts directory:", err)
			return 1
		}
		prefix := time.Now().UTC().Format("20060102T150405Z") + "-"
		runArtifactsDir, err = os.MkdirTemp(*artifactsDir, prefix)
		if err != nil {
			fmt.Fprintln(stderr, "FAIL create suite artifact directory:", err)
			return 1
		}
		fmt.Fprintln(stdout, "Artifacts:", runArtifactsDir)
	}

	paths := make([]string, len(selected))
	for i := range selected {
		paths[i] = selected[i].Path
	}
	results := make([]runner.RunResult, 0, len(paths))
	failed := false
	cancelled := false
	for index, path := range paths {
		options := runner.RunOptions{Update: *update, Snapshot: *snapshot}
		if runArtifactsDir != "" {
			options.ArtifactPrefix = filepath.Join(runArtifactsDir, artifactID(selected[index]))
		}
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
	printSuiteSummary(stdout, results)
	if cancelled {
		return 130
	}
	if failed {
		return 1
	}
	return 0
}

func runReport(args []string, stdout, stderr io.Writer) int {
	flags := flag.NewFlagSet("report", flag.ContinueOnError)
	flags.SetOutput(stderr)
	flags.Usage = func() {
		fmt.Fprintln(flags.Output(), "Usage: playtestr report --input results.json --evidence-root dir --output report.html")
		fmt.Fprintln(flags.Output())
		fmt.Fprintln(flags.Output(), "Creates one self-contained offline HTML file from captured report-v1 evidence.")
		fmt.Fprintln(flags.Output())
		fmt.Fprintln(flags.Output(), "Options:")
		flags.PrintDefaults()
	}
	input := flags.String("input", "", "read this report-v1 JSON file")
	evidenceRoot := flags.String("evidence-root", "", "admit referenced screen and diff files only from this directory")
	output := flags.String("output", "", "atomically write the self-contained HTML report")
	if err := flags.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}
	if flags.NArg() != 0 {
		fmt.Fprintln(stderr, "report does not accept positional arguments")
		return 2
	}
	if *input == "" || *evidenceRoot == "" || *output == "" {
		fmt.Fprintln(stderr, "--input, --evidence-root, and --output are required")
		return 2
	}
	if err := report.RenderHTML(report.HTMLOptions{InputPath: *input, EvidenceRoot: *evidenceRoot, OutputPath: *output}); err != nil {
		fmt.Fprintln(stderr, "FAIL render report:", err)
		return 1
	}
	fmt.Fprintln(stdout, "Offline report saved:", *output)
	return 0
}

func validateSuiteDestinations(selected []discovery.Spec, reportPath, artifactsDir string, update bool) error {
	outputs := make([]struct{ kind, path string }, 0, 2)
	if reportPath != "" {
		outputs = append(outputs, struct{ kind, path string }{"report", reportPath})
	}
	if artifactsDir != "" {
		outputs = append(outputs, struct{ kind, path string }{"artifacts directory", artifactsDir})
	}

	baselines := make(map[string]string)
	totalSteps := 0
	for _, selectedSpec := range selected {
		for _, output := range outputs {
			if samePath(output.path, selectedSpec.Path) {
				return fmt.Errorf("%s %q aliases selected spec %q", output.kind, output.path, selectedSpec.DisplayPath)
			}
			if output.kind == "artifacts directory" && pathContains(output.path, selectedSpec.Path) {
				return fmt.Errorf("artifacts directory %q contains selected spec %q", output.path, selectedSpec.DisplayPath)
			}
		}
		spec, err := runner.Load(selectedSpec.Path)
		if err != nil {
			continue // The runner reports invalid specs as ordinary failed results.
		}
		totalSteps += len(spec.Steps)
		if totalSteps > maxSuiteSteps {
			return fmt.Errorf("suite exceeds limit of %d aggregate steps", maxSuiteSteps)
		}
		for _, step := range spec.Steps {
			if step.Snapshot == "" {
				continue
			}
			baseline := filepath.Join(filepath.Dir(selectedSpec.Path), "snapshots", step.Snapshot)
			for _, output := range outputs {
				if samePath(output.path, baseline) {
					return fmt.Errorf("%s %q aliases snapshot baseline %q", output.kind, output.path, baseline)
				}
			}
			if update {
				identity := canonicalPath(baseline)
				if previous, exists := baselines[identity]; exists && previous != canonicalPath(selectedSpec.Path) {
					return fmt.Errorf("snapshot update is ambiguous: %q and %q share baseline %q", previous, selectedSpec.DisplayPath, baseline)
				}
				baselines[identity] = canonicalPath(selectedSpec.Path)
			}
		}
	}
	return nil
}

func pathContains(directory, path string) bool {
	relative, err := filepath.Rel(canonicalPath(directory), canonicalPath(path))
	return err == nil && relative != "." && relative != ".." && !strings.HasPrefix(relative, ".."+string(os.PathSeparator))
}

func samePath(left, right string) bool {
	leftInfo, leftErr := os.Stat(left)
	rightInfo, rightErr := os.Stat(right)
	if leftErr == nil && rightErr == nil && os.SameFile(leftInfo, rightInfo) {
		return true
	}
	return canonicalPath(left) == canonicalPath(right)
}

func canonicalPath(path string) string {
	absolute, err := filepath.Abs(path)
	if err == nil {
		path = absolute
	}
	path = filepath.Clean(path)
	missing := make([]string, 0, 4)
	for cursor := path; ; cursor = filepath.Dir(cursor) {
		if resolved, err := filepath.EvalSymlinks(cursor); err == nil {
			for i := len(missing) - 1; i >= 0; i-- {
				resolved = filepath.Join(resolved, missing[i])
			}
			path = resolved
			break
		}
		parent := filepath.Dir(cursor)
		if parent == cursor {
			break
		}
		missing = append(missing, filepath.Base(cursor))
	}
	if os.PathSeparator == '\\' {
		path = strings.ToLower(path)
	}
	return path
}

func artifactID(spec discovery.Spec) string {
	normalized := filepath.ToSlash(filepath.Clean(spec.DisplayPath))
	name := strings.Trim(unsafeArtifactCharacter.ReplaceAllString(normalized, "-"), ".-")
	if len(name) > 80 {
		name = name[len(name)-80:]
	}
	if name == "" {
		name = "spec"
	}
	hash := sha256.Sum256([]byte(canonicalPath(spec.Path)))
	return fmt.Sprintf("%s-%x", name, hash[:6])
}

func printSuiteSummary(out io.Writer, results []runner.RunResult) {
	document := report.New(buildinfo.Version, results)
	summary := document.Summary
	fmt.Fprintf(out, "Suite: total=%d passed=%d failed=%d cancelled=%d not-run=%d\n", summary.Total, summary.Passed, summary.Failed, summary.Cancelled, summary.NotRun)
	for _, result := range results {
		if result.Status == "passed" || result.Status == "not_run" {
			continue
		}
		category := runner.FailureInternal
		if result.Failure != nil {
			category = result.Failure.Category
		}
		location := ""
		for _, step := range result.Steps {
			if step.Status == "failed" {
				location = fmt.Sprintf(" step=%d", step.Number)
				break
			}
		}
		fmt.Fprintf(out, "  %s status=%s category=%s%s\n", filepath.ToSlash(result.SpecPath), result.Status, category, location)
		if result.Evidence.ScreenPath != "" {
			fmt.Fprintln(out, "    screen:", result.Evidence.ScreenPath)
		}
		if result.Evidence.DiffPath != "" {
			fmt.Fprintln(out, "    diff:", result.Evidence.DiffPath)
		}
	}
}
