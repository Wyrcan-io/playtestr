#!/usr/bin/env python3
"""Render bounded Playtestr report v1/v2/v3 metadata for an Actions job summary.

Uses only Python's standard library. Never reads a spec or screen, launches a
target, changes a baseline, or decides the test step's exit status.
"""

import argparse
import json
from pathlib import Path
import re
import sys
import unicodedata

MAX_REPORT_BYTES = 8 * 1024 * 1024
MAX_SUMMARY_BYTES = 256 * 1024
MAX_RESULTS = 1000
MAX_STEPS = 10000
MAX_ROWS = 100
STATUSES = ("passed", "failed", "cancelled", "not_run")
OUTCOMES = ("success", "failure", "cancelled", "skipped", "unknown")
CATEGORIES = frozenset((
    "invalid_spec", "launch_failure", "assertion_timeout", "run_timeout",
    "unexpected_exit", "snapshot_mismatch", "output_limit", "cancelled",
    "cleanup_failure", "artifact_failure", "snapshot_update_failure",
    "workspace_setup_failure", "workspace_cleanup_failure", "internal_error",
    "state_assertion_failure",
))


class InvalidReport(ValueError):
    """An unusable report; messages intentionally exclude untrusted values."""


def require(condition, message):
    if not condition:
        raise InvalidReport(message)


def integer(value):
    return type(value) is int and value >= 0


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON field")
        result[key] = value
    return result


def reject_constant(_value):
    raise InvalidReport("non-finite JSON number")


def failure(value):
    if value is None:
        return
    require(isinstance(value, dict), "invalid failure metadata")
    require(isinstance(value.get("category"), str) and value["category"] in CATEGORIES,
            "unsupported failure category")
    require(isinstance(value.get("message"), str), "invalid failure message")


def read_report(path):
    try:
        require(path.is_file(), "report is missing or is not a regular file")
        with path.open("rb") as stream:
            raw = stream.read(MAX_REPORT_BYTES + 1)
    except OSError as exc:
        raise InvalidReport("report is missing or unreadable") from exc
    require(len(raw) <= MAX_REPORT_BYTES, "report exceeds 8 MiB")
    try:
        document = json.loads(raw, object_pairs_hook=unique_object,
                              parse_constant=reject_constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InvalidReport("report is malformed JSON") from exc
    validate(document)
    return document


def validate(document):
    require(isinstance(document, dict), "report must be an object")
    version = document.get("report_version")
    require(type(version) is int and version in (1, 2, 3), "unsupported report version")
    for field in ("runner_version", "os", "arch"):
        require(isinstance(document.get(field), str) and bool(document[field]),
                "missing runner identity")
    results = document.get("results")
    require(isinstance(results, list) and 0 < len(results) <= MAX_RESULTS,
            "report must contain 1–1000 results")
    summary = document.get("summary")
    counts = {"total": len(results), **{status: 0 for status in STATUSES}}
    require(isinstance(summary, dict) and set(summary) == set(counts),
            "invalid report summary")
    require(all(integer(value) for value in summary.values()), "invalid report counts")
    identities = set()
    steps_count = 0
    for result in results:
        require(isinstance(result, dict), "invalid result")
        identity = result.get("spec_path")
        require(isinstance(identity, str) and bool(identity) and identity not in identities,
                "missing or duplicate spec identity")
        identities.add(identity)
        status = result.get("status")
        require(status in STATUSES, "unsupported result status")
        counts[status] += 1
        require(integer(result.get("duration_ms")), "invalid result duration")
        failure(result.get("failure"))
        cleanup = result.get("cleanup")
        evidence = result.get("evidence")
        require(isinstance(cleanup, dict) and isinstance(evidence, dict),
                "missing cleanup or evidence metadata")
        for field in ("attempted", "graceful", "forced", "confirmed_exited"):
            require(type(cleanup.get(field)) is bool, "invalid cleanup metadata")
        failure(cleanup.get("failure"))
        for field in ("screen_path", "diff_path"):
            require(isinstance(evidence.get(field, ""), str), "invalid evidence path")
        evidence_failures = evidence.get("failures", [])
        require(isinstance(evidence_failures, list), "invalid evidence failures")
        for item in evidence_failures:
            failure(item)
        steps = result.get("steps", [])
        require(isinstance(steps, list), "invalid steps")
        steps_count += len(steps)
        require(steps_count <= MAX_STEPS, "report exceeds 10000 steps")
        for number, step in enumerate(steps, 1):
            require(isinstance(step, dict) and type(step.get("number")) is int
                    and step["number"] == number, "invalid step numbering")
            require(step.get("status") in ("passed", "failed", "running", "not_run")
                    and integer(step.get("duration_ms")), "invalid step outcome")
            failure(step.get("failure"))
            if step.get('action') == 'state':
                require(version == 3 and result.get('spec_version') == 3,
                        'state action requires report/spec v3')
                state = step.get('state')
                if step['status'] in ('passed', 'failed'):
                    workspace = result.get('workspace')
                    identity = result.get('invocation_id')
                    require(isinstance(state, dict) and isinstance(workspace, dict)
                            and isinstance(identity, str) and bool(identity)
                            and state.get('invocation_id') == identity
                            and state.get('workspace_id') == workspace.get('id') == identity,
                            'inconsistent same-execution state identity')
                    require(state.get('outcome') == ('matched' if step['status'] == 'passed' else 'rejected'),
                            'inconsistent state outcome')
        workspace = result.get("workspace")
        if workspace is not None:
            require(version in (2, 3) and isinstance(workspace, dict),
                    "invalid workspace version or metadata")
            failure(workspace.get("setup_failure"))
            failure(workspace.get("cleanup_failure"))
        if status == "passed":
            require(bool(steps), "passed result has no completed steps")
            require(not result.get("failure") and not cleanup.get("failure")
                    and not evidence_failures and all(step["status"] == "passed" for step in steps),
                    "passed result contains a failed or incomplete operation")
            if cleanup["attempted"]:
                require(cleanup["confirmed_exited"], "passed result has unconfirmed cleanup")
            if workspace is not None:
                require(not workspace.get("setup_failure") and not workspace.get("cleanup_failure"),
                        "passed result contains workspace failure")
    require(summary == counts, "report counts disagree with results")


def cell(value, limit=200):
    # Numeric entities keep Markdown punctuation, HTML, workflow commands,
    # newlines and bidi/control characters from acquiring syntax in a table.
    value = "".join(" " if unicodedata.category(c).startswith("C")
                    or c in "\u2028\u2029" else c for c in str(value))
    value = value[:limit] + ("…" if len(value) > limit else "")
    return "".join(c if c.isalnum() or c == " " or ord(c) > 127
                   else f"&#{ord(c)};" for c in value)


def evidence_state(reference, root):
    if not reference:
        return "not recorded"
    try:
        # Paths are relative to the invocation directory, as in report v1/v2.
        path = Path(reference).resolve()
        if not path.is_relative_to(root.resolve()):
            return "outside evidence root"
        return "available locally" if path.is_file() else "missing locally"
    except (OSError, ValueError, RuntimeError):
        return "unavailable locally"


def render(document, args, error=None):
    lines = ["## Playtestr terminal tests", "",
             "| Workflow step | Outcome |", "| --- | --- |"]
    for label, value in (("Installation", args.setup_outcome),
                         ("Target preparation", args.prepare_outcome),
                         ("Test command", args.test_outcome),
                         ("Offline report rendering", args.html_outcome)):
        lines.append(f"| {label} | {value} |")
    lines.append("")
    if error:
        lines += ["**No usable test report. Test success is not established.**", "",
                  f"Reason: {cell(error)}.", ""]
    else:
        counts = document["summary"]
        lines += [f"Captured results: {counts['total']} total; {counts['passed']} passed; "
                  f"{counts['failed']} failed; {counts['cancelled']} cancelled; "
                  f"{counts['not_run']} not run.", "",
                  f"Runner: {cell(document['runner_version'])}; "
                  f"host: {cell(document['os'])}/{cell(document['arch'])}; "
                  f"report v{document['report_version']}.", ""]
        if args.test_outcome in ("failure", "cancelled", "skipped"):
            lines += ["**The test command did not complete successfully. "
                      "Captured counts do not override its workflow outcome.**", ""]
        problems = [r for r in document["results"] if r["status"] != "passed"]
        if problems:
            lines += ["| Spec | Outcome | Category | Cleanup | Screen / diff |",
                      "| --- | --- | --- | --- | --- |"]
            for result in problems[:MAX_ROWS]:
                category = (result.get("failure") or {}).get("category", "not recorded")
                cleanup = result["cleanup"]
                clean = "failed" if cleanup.get("failure") else (
                    "confirmed exited" if cleanup["confirmed_exited"] else (
                        "unconfirmed" if cleanup["attempted"] else "not attempted"))
                evidence = result["evidence"]
                screen = evidence_state(evidence.get("screen_path"), args.evidence_root)
                diff = evidence_state(evidence.get("diff_path"), args.evidence_root)
                lines.append(f"| {cell(result['spec_path'])} | {result['status']} | "
                             f"{cell(category)} | {clean} | {screen} / {diff} |")
            if len(problems) > MAX_ROWS:
                lines += ["", f"{len(problems) - MAX_ROWS} further problem results "
                          "are omitted here; inspect results.json."]
            lines.append("")
        if args.html_outcome == "success":
            available = evidence_state(str(args.evidence_root / "report.html"), args.evidence_root)
            lines += [f"Offline report: {available}.", ""]
    if args.run_url:
        lines += [f"[Workflow run and artifacts]({args.run_url})", ""]
    lines += [f"In the run's Artifacts section, look for **{cell(args.artifact_name)}**. "
              "Upload may still be pending or may have failed; verify its outcome.", "",
              "Download and extract the artifact; open report.html if present, or inspect "
              "results.json and the screen/diff files. Local availability does not prove upload.", "",
              "This summary omits screens, command arguments, environment values and failure "
              "messages. Target output in downloadable evidence can contain sensitive data.", ""]
    result = "\n".join(lines)
    require(len(result.encode("utf-8")) <= MAX_SUMMARY_BYTES, "summary exceeds 256 KiB")
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True,
                        help="append to this file; use GITHUB_STEP_SUMMARY in Actions")
    parser.add_argument("--evidence-root", type=Path, required=True)
    for step in ("setup", "prepare", "test", "html"):
        parser.add_argument(f"--{step}-outcome", choices=OUTCOMES, default="unknown")
    parser.add_argument("--artifact-name", default="playtestr-evidence")
    parser.add_argument("--run-url", default="")
    parser.add_argument("--context", type=Path)
    args = parser.parse_args(argv)
    if args.run_url and not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[0-9]+", args.run_url):
        parser.error("run URL must be a github.com Actions run URL")
    if args.input.resolve() == args.output.resolve():
        parser.error("output must not alias the input report")
    error, document = None, None
    try:
        document = read_report(args.input)
    except InvalidReport as exc:
        error = str(exc)
    text = render(document, args, error)
    if args.context:
        try:
            with args.context.open("rb") as stream:
                raw = stream.read(256 * 1024 + 1)
            require(len(raw) <= 256 * 1024, "context exceeds bound")
            metadata = json.loads(raw, object_pairs_hook=unique_object, parse_constant=reject_constant)
            require(metadata.get("context_version") == 1, "unknown context")
            for field in ("tested_sha", "head_sha", "base_sha"):
                value = metadata.get(field)
                require(value is None or isinstance(value, str) and re.fullmatch(r"[a-f0-9]{40}", value), "invalid revision")
            require(metadata.get("tested_sha") is not None, "missing tested revision")
            text += "\nPR/build context (customer-controlled CI evidence):\n\n"
            for field in ("head_sha", "base_sha", "tested_sha", "checkout_strategy"):
                text += f"- {field}: {cell(metadata.get(field) or 'not applicable')}\n"
            text += ("\nLocal reproduction: checkout the tested SHA, run the explicit prerequisite/build "
                     "commands in the committed workflow, install the same pinned runner, then "
                     "`playtestr test` with the selected paths in context.json. No automatic retry "
                     "or baseline update is needed.\n")
        except (OSError, ValueError, TypeError, InvalidReport):
            text += "\n**PR/build context unavailable; exact reproduction is not established.**\n"
            error = error or "context unavailable"
    try:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        # Bound the append as well as the generated text, below GitHub's 1 MiB limit.
        size = args.output.stat().st_size if args.output.exists() else 0
        require(size + len(text.encode("utf-8")) <= MAX_SUMMARY_BYTES,
                "summary destination would exceed 256 KiB")
        with args.output.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    except (OSError, InvalidReport):
        print("Playtestr summary could not be written; inspect step logs and artifacts.", file=sys.stderr)
        return 2
    if error:
        print("Playtestr summary: no usable report; test success is not established.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
