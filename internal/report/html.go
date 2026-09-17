package report

import (
	"bytes"
	"errors"
	"fmt"
	"html/template"
	"io"
	"io/fs"
	"net/url"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"unicode/utf8"

	"github.com/Wyrcan-io/playtestr/internal/runner"
)

const (
	maxHTMLResults        = 1_000
	maxHTMLSteps          = 10_000
	maxEvidenceFileBytes  = 256 * 1024
	maxAggregateEvidence  = 24 * 1024 * 1024
	maxGeneratedHTMLBytes = 32 * 1024 * 1024
)

// HTMLLimits describes the fixed resource contract of the offline renderer.
type HTMLLimits struct {
	ReportBytes            int
	EvidenceFileBytes      int
	AggregateEvidenceBytes int
	GeneratedHTMLBytes     int
}

// OfflineHTMLLimits returns the renderer's public, fixed input/output limits.
func OfflineHTMLLimits() HTMLLimits {
	return HTMLLimits{maxReportBytes, maxEvidenceFileBytes, maxAggregateEvidence, maxGeneratedHTMLBytes}
}

// HTMLOptions identifies the captured input, its admitted evidence root, and
// the atomic output. WorkingDirectory is used only to resolve relative report
// references; the CLI leaves it empty to use the process working directory.
type HTMLOptions struct {
	InputPath        string
	EvidenceRoot     string
	OutputPath       string
	WorkingDirectory string
}

type evidenceView struct {
	State string
	Text  string
	Path  string
}

type evidenceClaims struct {
	paths map[string]string
	files []evidenceClaim
}

type evidenceClaim struct {
	identity string
	path     string
	info     fs.FileInfo
}

type resultView struct {
	ID         string
	Identity   string
	Result     runner.RunResult
	FailedStep *runner.StepResult
	Screen     evidenceView
	Diff       evidenceView
	DiffLines  []diffView
	IsProblem  bool
}

type diffView struct {
	Class string
	Text  string
}

type htmlView struct {
	Document    Document
	Results     []resultView
	Limits      HTMLLimits
	HasProblems bool
}

// RenderHTML turns a captured report and admitted evidence into one portable,
// script-free HTML file. It never reads specs, starts targets, or writes
// baselines, and it preserves an existing output if rendering fails.
func RenderHTML(options HTMLOptions) error {
	if options.InputPath == "" || options.EvidenceRoot == "" || options.OutputPath == "" {
		return fmt.Errorf("input, evidence root, and output are required")
	}
	workingDirectory := options.WorkingDirectory
	if workingDirectory == "" {
		var err error
		workingDirectory, err = os.Getwd()
		if err != nil {
			return fmt.Errorf("resolve working directory: %w", err)
		}
	}
	workingDirectory, err := filepath.Abs(workingDirectory)
	if err != nil {
		return fmt.Errorf("resolve working directory: %w", err)
	}
	workingDirectory = canonicalMissing(workingDirectory)
	root, err := existingDirectory(options.EvidenceRoot)
	if err != nil {
		return fmt.Errorf("resolve evidence root: %w", err)
	}
	if samePath(options.InputPath, options.OutputPath) {
		return fmt.Errorf("output %q aliases input report", options.OutputPath)
	}
	document, err := Read(options.InputPath)
	if err != nil {
		return err
	}
	if err := validateHTMLDocument(document); err != nil {
		return err
	}

	view := htmlView{Document: document, Limits: OfflineHTMLLimits()}
	claimed := evidenceClaims{paths: make(map[string]string)}
	aggregate := 0
	for index := range document.Results {
		result := document.Results[index]
		item := resultView{
			ID:        fmt.Sprintf("result-%d", index+1),
			Identity:  result.SpecPath,
			Result:    result,
			IsProblem: result.Status != "passed",
		}
		if item.Identity == "" {
			item.Identity = fmt.Sprintf("result %d", index+1)
		}
		if item.IsProblem {
			view.HasProblems = true
		}
		for stepIndex := range result.Steps {
			if result.Steps[stepIndex].Status == "failed" {
				item.FailedStep = &result.Steps[stepIndex]
				break
			}
		}
		prefix := ""
		if result.Evidence.ScreenPath != "" {
			prefix, err = evidencePrefix(result.Evidence.ScreenPath, ".actual.txt")
			if err != nil {
				return fmt.Errorf("result %q screen reference: %w", item.Identity, err)
			}
		}
		if result.Evidence.DiffPath != "" {
			diffPrefix, prefixErr := evidencePrefix(result.Evidence.DiffPath, ".diff.txt")
			if prefixErr != nil {
				return fmt.Errorf("result %q diff reference: %w", item.Identity, prefixErr)
			}
			if prefix != "" && canonicalCase(filepath.FromSlash(prefix)) != canonicalCase(filepath.FromSlash(diffPrefix)) {
				return fmt.Errorf("result %q has inconsistent screen and diff artifact references", item.Identity)
			}
			prefix = diffPrefix
		}
		item.Screen, err = readEvidence(root, workingDirectory, result.Evidence.ScreenPath, "screen", &claimed, item.Identity, &aggregate)
		if err != nil {
			return err
		}
		item.Diff, err = readEvidence(root, workingDirectory, result.Evidence.DiffPath, "diff", &claimed, item.Identity, &aggregate)
		if err != nil {
			return err
		}
		if item.Screen.Path != "" && samePath(item.Screen.Path, options.OutputPath) || item.Diff.Path != "" && samePath(item.Diff.Path, options.OutputPath) {
			return fmt.Errorf("output %q aliases admitted evidence", options.OutputPath)
		}
		item.DiffLines = classifyDiff(item.Diff.Text)
		view.Results = append(view.Results, item)
	}
	ordered := make([]resultView, 0, len(view.Results))
	for _, status := range []string{"failed", "cancelled", "not_run", "passed"} {
		for _, item := range view.Results {
			if item.Result.Status == status {
				ordered = append(ordered, item)
			}
		}
	}
	view.Results = ordered

	var output limitedBuffer
	output.limit = maxGeneratedHTMLBytes
	if err := offlineTemplate.Execute(&output, view); err != nil {
		if errors.Is(err, errHTMLLimit) {
			return fmt.Errorf("generated report exceeds %d bytes", maxGeneratedHTMLBytes)
		}
		return fmt.Errorf("render offline report: %w", err)
	}
	if err := writeHTMLAtomic(options.OutputPath, output.Bytes()); err != nil {
		return err
	}
	return nil
}

func validateHTMLDocument(document Document) error {
	if document.ReportVersion != Version {
		return fmt.Errorf("unsupported report version %d; this renderer supports version %d", document.ReportVersion, Version)
	}
	if len(document.Results) > maxHTMLResults {
		return fmt.Errorf("report exceeds limit of %d results", maxHTMLResults)
	}
	actual := Summary{Total: len(document.Results)}
	identities := make(map[string]struct{})
	steps := 0
	for index, result := range document.Results {
		if result.SpecPath == "" {
			return fmt.Errorf("result %d has no stable spec_path identity", index+1)
		}
		if _, exists := identities[result.SpecPath]; exists {
			return fmt.Errorf("result %d duplicates spec_path identity %q", index+1, result.SpecPath)
		}
		identities[result.SpecPath] = struct{}{}
		switch result.Status {
		case "passed":
			actual.Passed++
		case "failed":
			actual.Failed++
		case "cancelled":
			actual.Cancelled++
		case "not_run":
			actual.NotRun++
		default:
			return fmt.Errorf("result %q has unsupported status %q", result.SpecPath, result.Status)
		}
		steps += len(result.Steps)
		if steps > maxHTMLSteps {
			return fmt.Errorf("report exceeds limit of %d aggregate steps", maxHTMLSteps)
		}
		for stepIndex, step := range result.Steps {
			if step.Number != stepIndex+1 {
				return fmt.Errorf("result %q has inconsistent step number %d at position %d", result.SpecPath, step.Number, stepIndex+1)
			}
			if !oneOf(step.Action, "key", "text", "expect", "expect_not", "wait_for_redraw", "snapshot", "exit", "resize", "invalid") {
				return fmt.Errorf("result %q step %d has unsupported action %q", result.SpecPath, step.Number, step.Action)
			}
			if !oneOf(step.Status, "not_run", "running", "passed", "failed") || step.DurationMS < 0 {
				return fmt.Errorf("result %q step %d has invalid status or duration", result.SpecPath, step.Number)
			}
			if err := validateFailure(step.Failure); err != nil {
				return fmt.Errorf("result %q step %d: %w", result.SpecPath, step.Number, err)
			}
		}
		if result.DurationMS < 0 || result.Target.ExitCode != nil && (*result.Target.ExitCode < 0 || *result.Target.ExitCode > 255) {
			return fmt.Errorf("result %q has invalid duration or exit code", result.SpecPath)
		}
		if err := validateFailure(result.Failure); err != nil {
			return fmt.Errorf("result %q: %w", result.SpecPath, err)
		}
		if err := validateFailure(result.Cleanup.Failure); err != nil {
			return fmt.Errorf("result %q cleanup: %w", result.SpecPath, err)
		}
		for _, failure := range result.Evidence.Failures {
			copy := failure
			if err := validateFailure(&copy); err != nil {
				return fmt.Errorf("result %q evidence: %w", result.SpecPath, err)
			}
		}
	}
	if document.Summary != actual {
		return fmt.Errorf("report summary is inconsistent with results: recorded %+v, calculated %+v", document.Summary, actual)
	}
	return nil
}

func oneOf(value string, values ...string) bool {
	for _, allowed := range values {
		if value == allowed {
			return true
		}
	}
	return false
}

func validateFailure(failure *runner.Failure) error {
	if failure == nil {
		return nil
	}
	if !oneOf(string(failure.Category),
		string(runner.FailureInvalidSpec), string(runner.FailureLaunch), string(runner.FailureAssertionTimeout),
		string(runner.FailureRunTimeout), string(runner.FailureUnexpectedExit), string(runner.FailureSnapshotMismatch),
		string(runner.FailureOutputLimit), string(runner.FailureCancellation), string(runner.FailureCleanup),
		string(runner.FailureArtifact), string(runner.FailureSnapshotUpdate), string(runner.FailureInternal)) {
		return fmt.Errorf("unsupported failure category %q", failure.Category)
	}
	return nil
}

func evidencePrefix(reference, suffix string) (string, error) {
	if !strings.HasSuffix(strings.ToLower(reference), suffix) || len(reference) == len(suffix) {
		return "", fmt.Errorf("expected an existing report-v1 %s artifact name", suffix)
	}
	return reference[:len(reference)-len(suffix)], nil
}

func readEvidence(root, workingDirectory, reference, kind string, claimed *evidenceClaims, identity string, aggregate *int) (evidenceView, error) {
	if reference == "" {
		return evidenceView{State: "not-captured"}, nil
	}
	path, err := resolveEvidence(root, workingDirectory, reference)
	if err != nil {
		return evidenceView{}, fmt.Errorf("result %q %s reference %q: %w", identity, kind, reference, err)
	}
	key := canonicalCase(path)
	if owner, exists := claimed.paths[key]; exists && owner != identity {
		return evidenceView{}, fmt.Errorf("evidence reference %q is associated with both %q and %q", reference, owner, identity)
	}
	claimed.paths[key] = identity
	info, err := os.Stat(path)
	if errors.Is(err, fs.ErrNotExist) {
		return evidenceView{State: "missing", Path: path}, nil
	}
	if err != nil {
		return evidenceView{}, fmt.Errorf("inspect evidence %q: %w", reference, err)
	}
	if !info.Mode().IsRegular() {
		return evidenceView{}, fmt.Errorf("evidence %q is not a regular file", reference)
	}
	for _, previous := range claimed.files {
		if os.SameFile(info, previous.info) {
			return evidenceView{}, fmt.Errorf("evidence %q aliases evidence %q already associated with %q", reference, previous.path, previous.identity)
		}
	}
	claimed.files = append(claimed.files, evidenceClaim{identity: identity, path: reference, info: info})
	if info.Size() > maxEvidenceFileBytes {
		return evidenceView{}, fmt.Errorf("evidence %q exceeds %d bytes", reference, maxEvidenceFileBytes)
	}
	file, err := os.Open(path)
	if err != nil {
		return evidenceView{}, fmt.Errorf("open evidence %q: %w", reference, err)
	}
	data, readErr := io.ReadAll(io.LimitReader(file, maxEvidenceFileBytes+1))
	closeErr := file.Close()
	if readErr != nil {
		return evidenceView{}, fmt.Errorf("read evidence %q: %w", reference, readErr)
	}
	if closeErr != nil {
		return evidenceView{}, fmt.Errorf("close evidence %q: %w", reference, closeErr)
	}
	if len(data) > maxEvidenceFileBytes {
		return evidenceView{}, fmt.Errorf("evidence %q exceeds %d bytes", reference, maxEvidenceFileBytes)
	}
	if !utf8.Valid(data) {
		return evidenceView{}, fmt.Errorf("evidence %q is not valid UTF-8", reference)
	}
	*aggregate += len(data)
	if *aggregate > maxAggregateEvidence {
		return evidenceView{}, fmt.Errorf("evidence exceeds aggregate limit of %d bytes", maxAggregateEvidence)
	}
	return evidenceView{State: "available", Text: string(data), Path: path}, nil
}

func resolveEvidence(root, workingDirectory, reference string) (string, error) {
	if strings.ContainsRune(reference, 0) {
		return "", fmt.Errorf("contains a NUL byte")
	}
	parsed, err := url.Parse(reference)
	if err != nil || parsed.Scheme != "" || parsed.Host != "" || strings.HasPrefix(reference, "//") || strings.HasPrefix(reference, `\\`) {
		return "", fmt.Errorf("remote or URI references are not allowed")
	}
	reference = filepath.FromSlash(reference)
	if filepath.IsAbs(reference) || filepath.VolumeName(reference) != "" {
		return "", fmt.Errorf("absolute references are not allowed")
	}
	cleaned := filepath.Clean(reference)
	if cleaned == "." || cleaned == ".." || strings.HasPrefix(cleaned, ".."+string(os.PathSeparator)) {
		return "", fmt.Errorf("reference escapes its working directory")
	}
	candidate, err := filepath.Abs(filepath.Join(workingDirectory, cleaned))
	if err != nil {
		return "", fmt.Errorf("resolve reference: %w", err)
	}
	if !within(root, candidate) {
		return "", fmt.Errorf("reference resolves outside evidence root")
	}
	if err := rejectPathLinks(root, candidate); err != nil {
		return "", err
	}
	candidate = canonicalMissing(candidate)
	if !within(root, candidate) {
		return "", fmt.Errorf("reference resolves outside evidence root")
	}
	return candidate, nil
}

func existingDirectory(path string) (string, error) {
	absolute, err := filepath.Abs(path)
	if err != nil {
		return "", err
	}
	linkInfo, err := os.Lstat(absolute)
	if err != nil {
		return "", err
	}
	if linkInfo.Mode()&os.ModeSymlink != 0 {
		return "", fmt.Errorf("%q is a symbolic link or junction; pass its resolved directory", path)
	}
	if platformReparsePoint(linkInfo) {
		return "", fmt.Errorf("%q is a symbolic link or junction; pass its resolved directory", path)
	}
	info, err := os.Stat(absolute)
	if err != nil {
		return "", err
	}
	if !info.IsDir() {
		return "", fmt.Errorf("%q is not a directory", path)
	}
	return canonicalMissing(absolute), nil
}

func rejectPathLinks(root, candidate string) error {
	relative, err := filepath.Rel(root, candidate)
	if err != nil {
		return fmt.Errorf("resolve evidence path: %w", err)
	}
	cursor := root
	for _, component := range strings.Split(relative, string(os.PathSeparator)) {
		cursor = filepath.Join(cursor, component)
		info, err := os.Lstat(cursor)
		if errors.Is(err, fs.ErrNotExist) {
			return nil
		}
		if err != nil {
			return fmt.Errorf("inspect evidence path component: %w", err)
		}
		if info.Mode()&os.ModeSymlink != 0 || platformReparsePoint(info) {
			return fmt.Errorf("reference uses a symbolic link or junction")
		}
	}
	return nil
}

func canonicalMissing(path string) string {
	path = filepath.Clean(path)
	missing := make([]string, 0, 4)
	for cursor := path; ; cursor = filepath.Dir(cursor) {
		if resolved, err := platformCanonicalExisting(cursor); err == nil {
			for index := len(missing) - 1; index >= 0; index-- {
				resolved = filepath.Join(resolved, missing[index])
			}
			return filepath.Clean(resolved)
		}
		parent := filepath.Dir(cursor)
		if parent == cursor {
			return path
		}
		missing = append(missing, filepath.Base(cursor))
	}
}

func within(root, path string) bool {
	relative, err := filepath.Rel(canonicalCase(root), canonicalCase(path))
	return err == nil && relative != ".." && !strings.HasPrefix(relative, ".."+string(os.PathSeparator))
}

func canonicalCase(path string) string {
	path = filepath.Clean(path)
	if runtime.GOOS == "windows" {
		return strings.ToLower(path)
	}
	return path
}

func samePath(left, right string) bool {
	leftInfo, leftErr := os.Stat(left)
	rightInfo, rightErr := os.Stat(right)
	if leftErr == nil && rightErr == nil && os.SameFile(leftInfo, rightInfo) {
		return true
	}
	leftAbs, leftErr := filepath.Abs(left)
	rightAbs, rightErr := filepath.Abs(right)
	return leftErr == nil && rightErr == nil && canonicalCase(canonicalMissing(leftAbs)) == canonicalCase(canonicalMissing(rightAbs))
}

func classifyDiff(value string) []diffView {
	if value == "" {
		return nil
	}
	lines := strings.Split(strings.ReplaceAll(value, "\r\n", "\n"), "\n")
	result := make([]diffView, 0, len(lines))
	for _, line := range lines {
		class := "context"
		switch {
		case strings.HasPrefix(line, "@@"):
			class = "hunk"
		case strings.HasPrefix(line, "---") || strings.HasPrefix(line, "+++"):
			class = "header"
		case strings.HasPrefix(line, "+"):
			class = "added"
		case strings.HasPrefix(line, "-"):
			class = "removed"
		}
		result = append(result, diffView{Class: class, Text: line})
	}
	return result
}

var errHTMLLimit = errors.New("HTML output limit exceeded")

type limitedBuffer struct {
	bytes.Buffer
	limit int
}

func (buffer *limitedBuffer) Write(data []byte) (int, error) {
	if buffer.Len()+len(data) > buffer.limit {
		return 0, errHTMLLimit
	}
	return buffer.Buffer.Write(data)
}

func writeHTMLAtomic(path string, data []byte) (returnErr error) {
	directory := filepath.Dir(path)
	if err := os.MkdirAll(directory, 0755); err != nil {
		return fmt.Errorf("create report directory: %w", err)
	}
	temporary, err := os.CreateTemp(directory, ".playtestr-html-*")
	if err != nil {
		return fmt.Errorf("create temporary HTML report: %w", err)
	}
	temporaryPath := temporary.Name()
	defer func() { _ = temporary.Close(); _ = os.Remove(temporaryPath) }()
	if err := temporary.Chmod(0644); err != nil {
		return fmt.Errorf("set HTML report permissions: %w", err)
	}
	if _, err := temporary.Write(data); err != nil {
		return fmt.Errorf("write temporary HTML report: %w", err)
	}
	if err := temporary.Sync(); err != nil {
		return fmt.Errorf("sync temporary HTML report: %w", err)
	}
	if err := temporary.Close(); err != nil {
		return fmt.Errorf("close temporary HTML report: %w", err)
	}
	if err := os.Rename(temporaryPath, path); err != nil {
		return fmt.Errorf("replace HTML report %s: %w", path, err)
	}
	return nil
}

var offlineTemplate = template.Must(template.New("offline").Funcs(template.FuncMap{
	"category": func(result runner.RunResult) string {
		if result.Failure != nil {
			return string(result.Failure.Category)
		}
		return "none"
	},
	"assertionTimeout": func(result runner.RunResult) bool {
		return result.Failure != nil && result.Failure.Category == runner.FailureAssertionTimeout
	},
}).Parse(offlineHTML))

const offlineHTML = `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>Playtestr failure report</title><style>
:root{color-scheme:light;--paper:#fffdf9;--ink:#252323;--muted:#625e5c;--line:#d8d2cd;--rust:#652d3c;--wash:#f4e8e5;--terminal:#292728;--terminal-text:#eee9e4;--pass:#50613f;--danger:#8f3929;--add:#dfead7;--remove:#f4dcd7;--mono:Consolas,"Liberation Mono",monospace;--sans:Arial,Helvetica,sans-serif}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:1rem}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.55 var(--sans)}a{color:var(--rust)}a:focus-visible,summary:focus-visible{outline:3px solid #9b5d69;outline-offset:3px}.skip{position:absolute;left:-9999px}.skip:focus{left:1rem;top:1rem;background:#fff;padding:.5rem;z-index:2}.page{width:min(1120px,calc(100% - 2rem));margin:0 auto;padding:2rem 0 5rem}.eyebrow{color:var(--rust);font-weight:700;letter-spacing:.08em;text-transform:uppercase}.lede{max-width:70ch;color:var(--muted)}.summary{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:.75rem;margin:1.5rem 0}.metric{border:1px solid var(--line);border-radius:.5rem;padding:.75rem;background:#fff}.metric strong{display:block;font-size:1.5rem}.failure-nav{border:1px solid var(--line);border-left:5px solid var(--danger);background:#fff;padding:1rem 1.25rem;margin:1.5rem 0}.failure-nav li{margin:.4rem 0}.result{border-top:1px solid var(--line);padding:2rem 0}.result:target{background:var(--wash);box-shadow:0 0 0 100vmax var(--wash);clip-path:inset(0 -100vmax)}.status{display:inline-block;border-radius:999px;padding:.15rem .6rem;font-size:.85rem;font-weight:700;background:#eee}.status-passed{color:var(--pass);background:#e7eddf}.status-failed,.status-cancelled{color:var(--danger);background:#f4dcd7}.identity{font: .9rem/1.5 var(--mono);overflow-wrap:anywhere;color:var(--muted)}.facts{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.75rem;margin:1rem 0}.fact{border-left:3px solid var(--line);padding:.25rem .75rem}.fact b{display:block}.failure{border-left:5px solid var(--danger);padding:.75rem 1rem;background:#fff}.panes{display:grid;grid-template-columns:1fr 1fr;gap:1rem}.pane{min-width:0}.terminal,.diff{margin:0;background:var(--terminal);color:var(--terminal-text);font:14px/1.5 var(--mono);padding:1rem;border-radius:.4rem;overflow:auto;max-height:32rem;white-space:pre;tab-size:4}.diff-line{display:block;min-height:1.5em}.diff-line.added{background:#253321;color:#dbead3}.diff-line.removed{background:#492b28;color:#f3d9d4}.diff-line.hunk{color:#d8c3ef}.diff-line.header{font-weight:700}.missing{border:1px dashed var(--line);padding:1rem;color:var(--muted);background:#fff}.steps{width:100%;border-collapse:collapse}.steps th,.steps td{text-align:left;border-bottom:1px solid var(--line);padding:.5rem;vertical-align:top}.steps th{font-size:.85rem;color:var(--muted)}details{margin:1rem 0}summary{cursor:pointer;font-weight:700}.outcomes{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}.outcome{border:1px solid var(--line);padding:1rem;background:#fff}.callout{background:#fff3d8;border-left:5px solid #946b13;padding:1rem;margin:1.5rem 0}.source{font-size:.88rem;color:var(--muted)}@media(max-width:760px){.page{width:min(100% - 1rem,1120px);padding-top:1rem}.summary{grid-template-columns:repeat(2,1fr)}.panes,.facts,.outcomes{grid-template-columns:1fr}.steps{display:block;overflow-x:auto}.result{padding:1.5rem .25rem}.terminal,.diff{max-height:24rem}}@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
</style></head><body><a class="skip" href="#main">Skip to report</a><main class="page" id="main">
<p class="eyebrow">Playtestr offline report</p><h1>Run diagnosis</h1><p class="lede">Captured results only. This file does not rerun the target, read test specifications, compare a newer baseline, or infer a root cause.</p>
<section class="summary" aria-label="Run summary"><div class="metric"><strong>{{.Document.Summary.Total}}</strong>Total</div><div class="metric"><strong>{{.Document.Summary.Passed}}</strong>Passed</div><div class="metric"><strong>{{.Document.Summary.Failed}}</strong>Failed</div><div class="metric"><strong>{{.Document.Summary.Cancelled}}</strong>Cancelled</div><div class="metric"><strong>{{.Document.Summary.NotRun}}</strong>Not run</div></section>
{{if .HasProblems}}<nav class="failure-nav" aria-labelledby="failure-heading"><h2 id="failure-heading">Failures and incomplete tests</h2><ol>{{range .Results}}{{if .IsProblem}}<li><a href="#{{.ID}}">{{.Result.Name}} — <span class="identity">{{.Identity}}</span></a> <span class="status status-{{.Result.Status}}">{{.Result.Status}}</span>{{if .FailedStep}} · step {{.FailedStep.Number}}{{end}}</li>{{end}}{{end}}</ol></nav>{{else}}<p class="failure-nav">No failed, cancelled, or not-run result is present.</p>{{end}}
<div class="callout"><strong>Before sharing:</strong> this HTML embeds admitted terminal screens and diffs. They may contain application data. Playtestr does not automatically sanitize them.</div>
{{range .Results}}<article class="result" id="{{.ID}}" aria-labelledby="{{.ID}}-heading"><header><span class="status status-{{.Result.Status}}">{{.Result.Status}}</span><h2 id="{{.ID}}-heading">{{.Result.Name}}</h2><p class="identity">Stable identity: {{.Identity}}</p></header>
<div class="facts"><div class="fact"><b>Primary category</b>{{category .Result}}</div><div class="fact"><b>Viewport</b>{{.Result.Viewport.Width}} × {{.Result.Viewport.Height}}</div><div class="fact"><b>Duration</b>{{.Result.DurationMS}} ms</div></div>
{{if .Result.Failure}}<div class="failure"><b>Recorded failure</b><div>{{.Result.Failure.Message}}</div></div>{{end}}
{{if .FailedStep}}<h3>First failing step</h3><div class="facts"><div class="fact"><b>Step</b>{{.FailedStep.Number}}</div><div class="fact"><b>Action</b>{{.FailedStep.Action}}</div><div class="fact"><b>Category</b>{{if .FailedStep.Failure}}{{.FailedStep.Failure.Category}}{{else}}unavailable{{end}}</div></div>{{if assertionTimeout .Result}}<p class="missing"><b>Expected expression:</b> unavailable in report v1.</p>{{end}}{{else if .IsProblem}}<p class="missing">Failing step: unavailable in captured report.</p>{{end}}
<div class="panes"><section class="pane"><h3>Captured terminal</h3>{{if eq .Screen.State "available"}}<pre class="terminal" tabindex="0" aria-label="Captured terminal screen">{{.Screen.Text}}</pre>{{else if eq .Screen.State "missing"}}<p class="missing">Screen evidence is referenced but the file is missing.</p>{{else}}<p class="missing">Screen evidence was not captured.</p>{{end}}</section>
<section class="pane"><h3>Captured snapshot diff</h3>{{if eq .Diff.State "available"}}<pre class="diff" tabindex="0" aria-label="Captured unified diff">{{range .DiffLines}}<span class="diff-line {{.Class}}">{{.Text}}</span>{{end}}</pre>{{else if eq .Diff.State "missing"}}<p class="missing">Diff evidence is referenced but the file is missing.</p>{{else}}<p class="missing">Diff evidence is not available for this result.</p>{{end}}</section></div>
<h3>Separate outcomes</h3><div class="outcomes"><section class="outcome"><b>Target process</b><p>{{if .Result.Target.Exited}}Exited{{if .Result.Target.ExitCode}} with code {{.Result.Target.ExitCode}}{{else}}; exit code unavailable{{end}}{{else}}Exit was not observed{{end}}</p></section><section class="outcome"><b>Cleanup</b><p>Attempted: {{.Result.Cleanup.Attempted}}<br>Graceful: {{.Result.Cleanup.Graceful}}<br>Forced: {{.Result.Cleanup.Forced}}<br>Exit confirmed: {{.Result.Cleanup.ConfirmedExited}}{{if .Result.Cleanup.Mechanism}}<br>Mechanism: {{.Result.Cleanup.Mechanism}}{{end}}</p>{{if .Result.Cleanup.Failure}}<p>{{.Result.Cleanup.Failure.Message}}</p>{{end}}</section><section class="outcome"><b>Evidence writes</b>{{if .Result.Evidence.Failures}}<ul>{{range .Result.Evidence.Failures}}<li>{{.Category}}: {{.Message}}</li>{{end}}</ul>{{else}}<p>No evidence-write failure was recorded.</p>{{end}}</section></div>
<details><summary>All recorded steps and metadata</summary>{{if .Result.Steps}}<table class="steps"><thead><tr><th>#</th><th>Action</th><th>Status</th><th>Duration</th><th>Recorded failure</th></tr></thead><tbody>{{range .Result.Steps}}<tr><td>{{.Number}}</td><td>{{.Action}}{{if .Resize}} ({{.Resize.Width}} × {{.Resize.Height}}){{end}}</td><td>{{.Status}}</td><td>{{.DurationMS}} ms</td><td>{{if .Failure}}{{.Failure.Category}}: {{.Failure.Message}}{{else}}—{{end}}</td></tr>{{end}}</tbody></table>{{else}}<p>No step records are available.</p>{{end}}<p class="source">Runner {{$.Document.RunnerVersion}} · {{$.Document.OS}}/{{$.Document.Arch}} · report version {{$.Document.ReportVersion}}. Readable evidence is embedded, not cryptographically verified.</p></details></article>{{end}}
</main></body></html>`
