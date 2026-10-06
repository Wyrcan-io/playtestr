package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

var fullRevision = regexp.MustCompile(`^[a-f0-9]{40}$`)
var exactRelease = regexp.MustCompile(`^v[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?$`)

func runWorkflow(args []string, stdout, stderr io.Writer) int {
	f := flag.NewFlagSet("workflow", flag.ContinueOnError)
	f.SetOutput(stderr)
	output := f.String("output", ".github/workflows/playtestr.yml", "new workflow path; existing files refused")
	printOnly := f.Bool("print", false, "preview YAML without writing")
	source := f.String("source-revision", "", "exact 40-character Playtestr candidate source commit")
	version := f.String("runner-version", "", "exact published runner version (alternative to candidate source)")
	tooling := f.String("tooling-revision", "", "exact source commit for summary/context helpers; defaults to source revision")
	platforms := f.String("os", "linux", "comma-separated linux,macos,windows standard hosted runners")
	retention := f.Int("retention-days", 14, "artifact retention, 1-30 days")
	jobTimeout := f.Int("job-timeout-minutes", 15, "bounded job deadline, 1-60 minutes")
	var suites, setup, build stringFlags
	f.Var(&suites, "suite", "committed spec/directory, repeatable, relative repository path")
	f.Var(&setup, "setup", "explicit bash prerequisite command, repeatable")
	f.Var(&build, "build", "explicit bash target build command, repeatable; use true only if intentionally unnecessary")
	if err := f.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return 0
		}
		return 2
	}
	if f.NArg() != 0 || len(suites) == 0 || len(build) == 0 || (*source == "") == (*version == "") {
		fmt.Fprintln(stderr, "provide --suite, --build, and exactly one of --source-revision / --runner-version")
		return 2
	}
	if *source != "" && !fullRevision.MatchString(*source) || *version != "" && !exactRelease.MatchString(*version) {
		fmt.Fprintln(stderr, "runner source must be a full lowercase SHA; version must be exact vX.Y.Z[-suffix]")
		return 2
	}
	if *tooling == "" {
		*tooling = *source
	}
	if !fullRevision.MatchString(*tooling) {
		fmt.Fprintln(stderr, "helpers require a pinned --tooling-revision")
		return 2
	}
	if *retention < 1 || *retention > 30 || *jobTimeout < 1 || *jobTimeout > 60 {
		fmt.Fprintln(stderr, "invalid retention or job timeout")
		return 2
	}
	osNames := map[string]string{"linux": "ubuntu-24.04", "macos": "macos-15", "windows": "windows-2025"}
	matrix := []string{}
	seen := map[string]bool{}
	for _, name := range strings.Split(*platforms, ",") {
		runner, ok := osNames[name]
		if !ok || seen[name] {
			fmt.Fprintln(stderr, "unsupported or duplicate --os choice")
			return 2
		}
		seen[name] = true
		matrix = append(matrix, runner)
	}
	quoted := []string{}
	for _, suite := range suites {
		clean := filepath.Clean(suite)
		if suite == "" || filepath.IsAbs(suite) || clean == ".." || strings.HasPrefix(clean, ".."+string(os.PathSeparator)) || strings.HasPrefix(suite, "-") || strings.ContainsAny(suite, "\r\n\x00") || strings.Contains(suite, "${{") {
			fmt.Fprintln(stderr, "suite must be a relative repository path without newline/options")
			return 2
		}
		quoted = append(quoted, bashQuote(filepath.ToSlash(clean)))
	}
	for _, command := range append(append([]string{}, setup...), build...) {
		if strings.TrimSpace(command) == "" || strings.ContainsRune(command, 0) || len(command) > 16384 || strings.Contains(command, "${{") {
			fmt.Fprintln(stderr, "setup/build command invalid or too large")
			return 2
		}
	}
	installation := `      - name: Build exact candidate runner
        id: setup
        env:
          SOURCE_REVISION: '@SOURCE@'
        run: |
          mkdir -p .playtestr-bin
          ext=''
          if [ "$RUNNER_OS" = Windows ]; then ext='.exe'; fi
          cd .playtestr-tooling
          go build -trimpath -ldflags "-X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=source-$SOURCE_REVISION" -o "$GITHUB_WORKSPACE/.playtestr-bin/playtestr$ext" ./cmd/playtestr
          cd "$GITHUB_WORKSPACE"
          echo "PLAYTESTR_BIN=$GITHUB_WORKSPACE/.playtestr-bin/playtestr$ext" >> "$GITHUB_ENV"
          test "$(".playtestr-bin/playtestr$ext" --version)" = "playtestr source-$SOURCE_REVISION"
`
	// Source helpers and runner must come from the same candidate during candidate validation.
	if *source != "" && *source != *tooling {
		fmt.Fprintln(stderr, "candidate source and helper revision must match")
		return 2
	}
	if *version != "" {
		installation = `      - uses: Wyrcan-io/playtestr/setup-playtestr@ae97c62022966cde9699b26169b4dc6ef0a12439
        id: setup
        with:
          version: '@VERSION@'
      - name: Verify installed runner
        env:
          PLAYTESTR_INSTALLED_BIN: ${{ steps.setup.outputs.binary-path }}
          EXPECTED_VERSION: '@VERSION@'
        run: |
          test "$("$PLAYTESTR_INSTALLED_BIN" --version)" = "playtestr $EXPECTED_VERSION"
          echo "PLAYTESTR_BIN=$PLAYTESTR_INSTALLED_BIN" >> "$GITHUB_ENV"
`
	}
	prerequisites := ""
	if len(setup) > 0 {
		prerequisites = "      - name: Explicit target prerequisites\n        run: |\n" + indentCommands(setup)
	}
	installation = strings.ReplaceAll(strings.ReplaceAll(installation, "@SOURCE@", *source), "@VERSION@", *version)
	replacements := []string{}
	for _, pair := range [][2]string{{"@MATRIX@", strings.Join(matrix, ", ")}, {"@TIMEOUT@", fmt.Sprint(*jobTimeout)}, {"@RETENTION@", fmt.Sprint(*retention)}, {"@TOOLING@", *tooling}, {"@INSTALLATION@", installation}, {"@PREREQUISITES@", prerequisites}, {"@BUILD@", indentCommands(build)}, {"@SUITES@", strings.Join(quoted, " ")}, {"@SOURCE@", *source}, {"@VERSION@", *version}} {
		replacements = append(replacements, pair[0], pair[1])
	}
	yaml := strings.NewReplacer(replacements...).Replace(workflowTemplate)
	if *printOnly {
		fmt.Fprint(stdout, yaml)
		return 0
	}
	if err := os.MkdirAll(filepath.Dir(*output), 0755); err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	file, err := os.OpenFile(*output, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0644)
	if err != nil {
		fmt.Fprintln(stderr, "workflow output refused:", err)
		return 1
	}
	_, err = io.WriteString(file, yaml)
	if err == nil {
		err = file.Sync()
	}
	closeErr := file.Close()
	if err == nil {
		err = closeErr
	}
	if err != nil {
		_ = os.Remove(*output)
		fmt.Fprintln(stderr, err)
		return 1
	}
	fmt.Fprintf(stdout, "Created %s. Review explicit commands and commit the workflow and suite.\n", *output)
	return 0
}

func bashQuote(s string) string { return "'" + strings.ReplaceAll(s, "'", "'\"'\"'") + "'" }
func indentCommands(commands []string) string {
	var b strings.Builder
	for _, command := range commands {
		for _, line := range strings.Split(command, "\n") {
			b.WriteString("          " + line + "\n")
		}
	}
	return b.String()
}

const workflowTemplate = `# Generated by playtestr workflow. Review commands; no service secrets required.
name: Playtestr recorded regression
on:
  pull_request:
    types: [opened, synchronize, reopened, ready_for_review]
  workflow_dispatch:
permissions:
  contents: read
concurrency:
  group: playtestr-${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
jobs:
  terminal:
    name: Playtestr tests (${{ matrix.os }})
    timeout-minutes: @TIMEOUT@
    strategy:
      fail-fast: false
      matrix:
        os: [@MATRIX@]
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        shell: bash
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803
        with:
          persist-credentials: false
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803
        with:
          repository: Wyrcan-io/playtestr
          ref: '@TOOLING@'
          path: .playtestr-tooling
          persist-credentials: false
      - uses: actions/setup-go@b7ad1dad31e06c5925ef5d2fc7ad053ef454303e
        with:
          go-version-file: .playtestr-tooling/go.mod
          cache: false
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with:
          python-version: '3.12'
@INSTALLATION@@PREREQUISITES@      - name: Explicit target build
        id: prepare
        run: |
@BUILD@      - name: Select committed suite and capture exact context
        id: context
        run: |
          mkdir -p artifacts/playtestr
          "$PLAYTESTR_BIN" test --list @SUITES@ > artifacts/playtestr/selected.txt
          python .playtestr-tooling/scripts/ci/context_manifest.py --selection artifacts/playtestr/selected.txt --runner "$PLAYTESTR_BIN" --output artifacts/playtestr/context.json
      - name: Test recorded interactions
        id: tests
        run: |
          "$PLAYTESTR_BIN" test --artifacts-dir artifacts/playtestr/evidence --report artifacts/playtestr/results.json @SUITES@
      - name: Render offline evidence
        id: html
        if: always() && steps.tests.outcome != 'skipped'
        run: |
          "$PLAYTESTR_BIN" report --input artifacts/playtestr/results.json --evidence-root artifacts/playtestr --output artifacts/playtestr/report.html
      - name: Accessible outcome summary
        if: always()
        env:
          SETUP_OUTCOME: ${{ steps.setup.outcome }}
          PREPARE_OUTCOME: ${{ steps.prepare.outcome }}
          TEST_OUTCOME: ${{ steps.tests.outcome }}
          HTML_OUTCOME: ${{ steps.html.outcome }}
          RUN_URL: ${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}
        run: |
          if [ -f .playtestr-tooling/scripts/ci/report_summary.py ]; then
            python .playtestr-tooling/scripts/ci/report_summary.py --input artifacts/playtestr/results.json --output "$GITHUB_STEP_SUMMARY" --evidence-root artifacts/playtestr --setup-outcome "$SETUP_OUTCOME" --prepare-outcome "$PREPARE_OUTCOME" --test-outcome "$TEST_OUTCOME" --html-outcome "$HTML_OUTCOME" --artifact-name "playtestr-${RUNNER_OS}" --run-url "$RUN_URL" --context artifacts/playtestr/context.json
          else
            echo '**Playtestr evidence unavailable: setup/helper missing; test success is not established.**' >> "$GITHUB_STEP_SUMMARY"
            exit 1
          fi
      - uses: actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f
        if: always()
        with:
          name: playtestr-${{ runner.os }}
          path: artifacts/playtestr/
          if-no-files-found: error
          retention-days: @RETENTION@
`
