"""Freeze and run Percol's real controlling-terminal selection contract."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import platform
import shlex
import sys

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256


PROJECT = DOC / "percol"
PIN = "4b28037e328da3d0fe8165c11b800cbaddcb525e"
HOSTS = {"linux": "Linux", "darwin": "Darwin"}
SERIES = "native-exit-v3"
SCENARIO_VERSION = 1


def make_case(identity, kind, title, fixture, steps, stdout, *, options=(), filename=False,
              fixture_name="choices.txt"):
    args = " ".join(shlex.quote(value) for value in options)
    command = 'exec "$PERCOL_PYTHON" "$PERCOL_SOURCE/bin/percol"'
    if args:
        command += " " + args
    if filename:
        command += " " + shlex.quote(fixture_name)
    else:
        command += " < " + shlex.quote(fixture_name)
    command += " > result.txt"
    actions = list(steps) + [{"state": {"path": "result.txt", "kind": "file",
                                         "bytes_base64": base64.b64encode(stdout).decode("ascii")}}]
    expected_exit = next(action["exit"] for action in reversed(steps) if "exit" in action)
    return {"id": identity, "kind": kind, "title": title, "fixture": fixture,
            "fixture_path": fixture_name, "command": command, "options": list(options),
            "actions": actions, "expected_exit": expected_exit,
            "expected_stdout": stdout,
            "expected_stdout_base64": base64.b64encode(stdout).decode("ascii")}


def cases():
    """Twenty focused outcomes over Percol's documented CLI and TUI behavior."""
    return [
        make_case("N01", "normal", "Select the first candidate from stdin",
                  b"apple\nbanana\n", [{"expect": "apple"}, {"key": "Enter"}, {"exit": 0}], b"apple\n"),
        make_case("N02", "normal", "Select an initial query match",
                  b"red\nblue\ngreen\n", [{"expect": "blue"}, {"key": "Enter"}, {"exit": 0}],
                  b"blue\n", options=("--query=blue",)),
        make_case("N03", "normal", "Match a subsequence query",
                  b"cart\nplain\n", [{"expect": "cart"}, {"key": "Enter"}, {"exit": 0}],
                  b"cart\n", options=("--query=ct",)),
        make_case("N04", "normal", "Move the selected row down",
                  b"amber\nblue\ncedar\n", [{"expect": "amber"}, {"key": "ArrowDown"},
                  {"expect": "blue"}, {"key": "Enter"}, {"exit": 0}], b"blue\n"),
        make_case("N05", "normal", "Backspace edits the live query",
                  b"blue\nblack\n", [{"expect": "blx"}, {"key": "Backspace"},
                  {"expect": "blue"}, {"key": "Enter"}, {"exit": 0}], b"blue\n",
                  options=("--query=blx",)),
        make_case("N06", "normal", "Mark and emit two candidates",
                  b"apple\nbanana\ncherry\n", [{"expect": "apple"}, {"key": "CtrlSpace"},
                  {"expect": "banana"}, {"key": "CtrlSpace"}, {"key": "Enter"}, {"exit": 0}],
                  b"apple\nbanana\n"),
        make_case("N07", "normal", "Invert the matching candidates",
                  b"apple\nbanana\n", [{"expect": "banana"}, {"key": "Enter"}, {"exit": 0}],
                  b"banana\n", options=("--query=ap", "--invert-match")),
        make_case("N08", "normal", "Start at the last candidate",
                  b"alpha\nbeta\ngamma\n", [{"expect": "gamma"}, {"key": "Enter"}, {"exit": 0}],
                  b"gamma\n", options=("--initial-index=last",)),
        make_case("E01", "edge", "Insert query text at the configured caret",
                  b"xalpha\nalpha\n", [{"text": "x"}, {"expect": "xalpha"},
                  {"key": "Enter"}, {"exit": 0}], b"xalpha\n",
                  options=("--query=a", "--caret-position=0")),
        make_case("E02", "edge", "Ctrl-C cancels without output",
                  b"amber\nblue\n", [{"expect": "amber"}, {"key": "CtrlC"}, {"exit": 1}], b""),
        make_case("E03", "edge", "Ignore Ctrl-D and remain cancellable",
                  b"alpha\n", [{"expect": "alpha"}, {"key": "CtrlD"},
                  {"expect": "alpha"}, {"key": "CtrlC"}, {"exit": 1}], b""),
        make_case("E04", "edge", "Emit exact accented and CJK output bytes",
                  "caf\u00e9 \u96ea\nplain\n".encode("utf-8"),
                  [{"expect": "caf\u00e9 \u96ea"}, {"key": "Enter"}, {"exit": 0}],
                  "caf\u00e9 \u96ea\n".encode("utf-8")),
        make_case("E05", "edge", "Keep an unmatched query interactive and cancellable",
                  b"", [{"text": "missing"}, {"expect": "missing"},
                  {"key": "CtrlC"}, {"exit": 1}], b""),
        make_case("E06", "edge", "Auto-select the only candidate",
                  b"unique\n", [{"exit": 0}], b"unique\n", options=("--auto-match",)),
        make_case("E07", "edge", "Respect case-sensitive matching",
                  b"Blue\nblue\n", [{"expect": "blue"}, {"key": "Enter"}, {"exit": 0}],
                  b"blue\n", options=("--case-sensitive", "--query=blue")),
        make_case("E08", "edge", "Use the documented regular-expression finder",
                  b"pine\npineapple\napple\n", [{"expect": "pine"}, {"key": "Enter"}, {"exit": 0}],
                  b"pine\n", options=("--match-method=regex", "--query=^pine$")),
        make_case("E09", "edge", "Reverse input order before selection",
                  b"first\nsecond\nthird\n", [{"expect": "third"}, {"key": "Enter"}, {"exit": 0}],
                  b"third\n", options=("--reverse",)),
        make_case("E10", "edge", "Quote the selected output line",
                  b"say \"hello\"\n", [{"expect": "say \"hello\""}, {"key": "Enter"}, {"exit": 0}],
                  b'"say \\\"hello\\\""\n', options=("--quote",)),
        make_case("E11", "edge", "Read candidates from a named file",
                  b"from-file\nother\n", [{"expect": "from-file"}, {"key": "Enter"}, {"exit": 0}],
                  b"from-file\n", filename=True),
        make_case("E12", "edge", "Show the prompt at the bottom of the viewport",
                  b"bottom-prompt\nother\n", [{"expect": "bottom-prompt"},
                  {"key": "Enter"}, {"exit": 0}], b"bottom-prompt\n",
                  options=("--prompt-bottom",)),
    ]


def expected_spec(case):
    return {
        "version": 3, "name": case["title"],
        "command": ["/bin/sh", "-c", case["command"]],
        "workspace": {"fixture": "fixtures", "cwd": ".", "home": "temporary", "temp": "temporary"},
        "env": {"TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        "inherit_env": ["PATH", "PERCOL_PYTHON", "PERCOL_SOURCE", "PYTHONPATH",
                        "DYLD_LIBRARY_PATH"],
        "width": 80, "height": 12,
        "timeout_ms": 20000, "run_timeout_ms": 60000, "max_output_bytes": 1048576,
        "steps": case["actions"],
    }


def materialize():
    package = PROJECT / f"scenarios-v{SCENARIO_VERSION}"
    declaration_path = PROJECT / f"scenario-declaration-v{SCENARIO_VERSION}.json"
    if package.exists() or declaration_path.exists():
        raise ValueError("preserve existing Percol scenario contract")
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v3.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    acquisition = json.loads((RAW / "active/percol/acquisition.json").read_text(encoding="utf-8"))
    if acquisition.get("repository") != "mooz/percol" or acquisition.get("pin") != PIN:
        raise ValueError("scenario contract must bind the reviewed Percol source acquisition")
    rows = []
    for case in cases():
        folder = package / case["id"]
        fixtures = folder / "fixtures"
        fixtures.mkdir(parents=True)
        fixture_path = fixtures / Path(case["fixture_path"]).name
        fixture_path.write_bytes(case["fixture"])
        spec = expected_spec(case)
        spec_path = folder / "scenario.json"
        immutable_json(spec_path, spec)
        rows.append({"id": case["id"], "kind": case["kind"], "title": case["title"],
                     "spec_path": spec_path.relative_to(DOC).as_posix(),
                     "spec_sha256": sha256(spec_path),
                     "fixture_path": fixture_path.relative_to(DOC).as_posix(),
                     "fixture_sha256": sha256(fixture_path), "fixture_bytes": len(case["fixture"]),
                     "fixture_base64": base64.b64encode(case["fixture"]).decode("ascii"),
                     "expected_stdout_base64": case["expected_stdout_base64"],
                     "expected_target_exit": case["expected_exit"]})
    if (len(rows) != 20 or sum(row["kind"] == "normal" for row in rows) != 8
            or sum(row["kind"] == "edge" for row in rows) != 12):
        raise ValueError("Percol contract must contain exactly eight normal and twelve edge cases")
    declaration = {
        "schema_version": 1, "scenario_contract_version": SCENARIO_VERSION,
        "project": "percol", "repository": "mooz/percol", "pin": PIN,
        "source_archive_sha256": acquisition["archive_sha256"],
        "candidate": freeze["version"], "candidate_series": SERIES,
        "candidate_freeze_sha256": sha256(freeze_path),
        "normal_scenarios": 8, "edge_scenarios": 12, "distinct_scenarios": 20,
        "native_cells": ["linux-amd64", "macos-arm64"], "stateful": False,
        "saved_state_coverage_credit": 0,
        "oracle": "Rendered PTY checkpoints, exact target exit status, and exact selected stdout bytes captured to a harness-owned file. The capture file is not target-managed saved-state coverage.",
        "shell_adapter_scope": "The POSIX shell only redirects the reviewed fixture into Percol, redirects Percol stdout to result.txt, and execs the reviewed Python 2 Percol entry point; the target owns terminal rendering and keyboard handling.",
        "risk_dimensions": ["query matching and edits", "row navigation", "multi-selection",
                            "filter inversion", "caret positioning", "Unicode output",
                            "cancel exits", "empty-input behavior",
                            "auto-match", "regex and case-sensitive modes", "reverse ordering",
                            "quoted output", "named-file input", "prompt placement"],
        "scenarios": rows, "project_admission_credit": 0,
    }
    immutable_json(declaration_path, declaration)
    return declaration


def verify_materialized():
    declaration_path = PROJECT / f"scenario-declaration-v{SCENARIO_VERSION}.json"
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v3.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    provenance_path = PROJECT / "source-provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    rows = {row["id"]: row for row in declaration.get("scenarios", [])}
    if (len(rows) != 20 or declaration.get("project") != "percol" or declaration.get("pin") != PIN
            or declaration.get("candidate") != freeze["version"]
            or declaration.get("candidate_series") != SERIES
            or declaration.get("candidate_freeze_sha256") != sha256(freeze_path)
            or provenance.get("project") != "percol" or provenance.get("pin") != PIN
            or declaration.get("source_archive_sha256") != provenance.get("source_archive_sha256")):
        raise ValueError("Percol declaration differs from its source or exact candidate identity")
    for case in cases():
        row = rows.get(case["id"])
        if row is None:
            raise ValueError("Percol declaration omits " + case["id"])
        folder = PROJECT / f"scenarios-v{SCENARIO_VERSION}" / case["id"]
        fixture = folder / "fixtures" / Path(case["fixture_path"]).name
        spec_path = folder / "scenario.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        if (fixture.is_symlink() or fixture.read_bytes() != case["fixture"]
                or spec != expected_spec(case)
                or row.get("spec_sha256") != sha256(spec_path)
                or row.get("fixture_sha256") != sha256(fixture)
                or row.get("fixture_bytes") != len(case["fixture"])
                or row.get("expected_stdout_base64") != case["expected_stdout_base64"]
                or row.get("expected_target_exit") != case["expected_exit"]):
            raise ValueError("Percol frozen case differs from reviewed definition: " + case["id"])
    return declaration


def check_report(path, expected_exit):
    report = json.loads(path.read_text(encoding="utf-8"))
    result = report["results"][0]
    if (result.get("status") != "passed" or result.get("target", {}).get("exit_code") != expected_exit
            or result.get("cleanup", {}).get("confirmed_exited") is not True
            or result.get("workspace", {}).get("cleaned") is not True
            or any(step.get("status") != "passed" for step in result.get("steps", []))):
        raise ValueError("Percol scenario failed expected screen, output, exit, or cleanup")
    return result


def source_manifest(root):
    files = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("linked path in the acquired Percol source")
        if path.is_file():
            files[path.relative_to(root).as_posix()] = sha256(path)
    return files


async def run(host, repetitions=1, phase="development"):
    if platform.system() != HOSTS[host]:
        raise RuntimeError("actual native host differs from declared Percol host")
    declaration = verify_materialized()
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v3.json").read_text())
    cell = next(row for row in freeze["cells"] if row["host"] == host)
    target = RAW / "active/percol"
    acquisition = json.loads((target / "acquisition.json").read_text(encoding="utf-8"))
    runtime = json.loads((target / "runtime.json").read_text(encoding="utf-8"))
    build = json.loads((target / "build.json").read_text(encoding="utf-8"))
    source_archive = target / "source.tar.gz"
    python_path = Path(runtime["python"]).resolve(strict=True)
    source = target / "src"
    wheels = json.loads((target / "wheels.json").read_text(encoding="utf-8"))
    actual_six_files = source_manifest(target / "six-site")
    source_files = source_manifest(source)
    if (acquisition.get("repository") != "mooz/percol" or acquisition.get("pin") != PIN
            or acquisition.get("archive_sha256") != declaration["source_archive_sha256"]
            or sha256(source_archive) != declaration["source_archive_sha256"]
            or source_files != acquisition.get("source_files")
            or build.get("host") != host or build.get("pin") != PIN
            or build.get("python_sha256") != runtime.get("python_sha256")
            or sha256(python_path) != runtime["python_sha256"]
            or wheels.get("six_version") != "1.16.0"
            or wheels.get("wheel_sha256") != build.get("six_wheel_sha256")
            or wheels.get("installed_files") != actual_six_files
            or declaration["candidate"] != freeze["version"]):
        raise ValueError("Percol target, runtime or source identity differs from the reviewed contract")
    python_path.relative_to(target.resolve(strict=True))
    runner = executable(SERIES, host)
    installed = json.loads((runner.parent / "installed.json").read_text())
    if installed.get("archive_sha256") != cell["archive_sha256"]:
        raise ValueError("Percol scenarios require the exact frozen native runner archive")
    six_site = target / "six-site"
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env.update({"PATH": str(runner.parent) + os.pathsep + env.get("PATH", ""),
                "TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "PERCOL_PYTHON": str(python_path), "PERCOL_SOURCE": str(source),
                "PYTHONPATH": str(source) + os.pathsep + str(six_site),
                "TMPDIR": str(RAW / "tmp"), "TMP": str(RAW / "tmp"), "TEMP": str(RAW / "tmp")})
    (RAW / "tmp").mkdir(parents=True, exist_ok=True)
    campaign = NextCampaign(phase=phase)
    receipts = []
    for repetition in range(1, repetitions + 1):
        for row in declaration["scenarios"]:
            spec = DOC / row["spec_path"]
            base = RAW / "percol" / phase / host / f"r{repetition:02d}" / row["id"]
            report, artifacts = base / "report.json", base / "artifacts"
            report.parent.mkdir(parents=True, exist_ok=True)
            argv = [runner, "test", "--report", report.relative_to(ROOT), "--artifacts-dir",
                    artifacts.relative_to(ROOT), spec.relative_to(ROOT)]
            attempt = await execute(argv, "percol", f"percol-{phase}-{host}-r{repetition:02d}-{row['id']}",
                                    cwd=ROOT, env=env, timeout=240, campaign=campaign)
            result = check_report(report, row["expected_target_exit"])
            receipts.append({"attempt_id": attempt["id"], "scenario": row["id"],
                             "repetition": repetition, "phase": phase,
                             "report_sha256": sha256(report), "invocation_id": result["invocation_id"],
                             "target_exit": row["expected_target_exit"],
                             "cleanup_confirmed": True, "workspace_cleaned": True})
    result_path = RAW / "percol" / f"{phase}-{host}-run-{os.environ.get('GITHUB_RUN_ID', 'local')}.json"
    immutable_json(result_path, {"schema_version": 1, "project": "percol", "host": host,
                                 "candidate": freeze["version"], "phase": phase,
                                 "repetitions": repetitions, "attempts": receipts,
                                 "attempt_count": len(receipts), "admission_credit": 0})
    if source_manifest(source) != source_files:
        raise ValueError("Percol target or its helpers modified the pinned source tree")
    print(json.dumps({"project": "percol", "host": host, "phase": phase,
                      "repetitions": repetitions, "attempt_count": len(receipts)}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialize", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--host", choices=tuple(HOSTS))
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--phase", default="development")
    args = parser.parse_args()
    if args.materialize and args.verify:
        parser.error("--materialize and --verify are mutually exclusive")
    if args.materialize:
        print("Percol scenario contract frozen:", len(materialize()["scenarios"]), "cases; no target launch.")
        return
    if args.verify:
        print("Percol committed scenario contract verified:",
              len(verify_materialized()["scenarios"]), "cases; no target launch.")
        return
    if args.host is None or not 1 <= args.repetitions <= 12:
        parser.error("--host is required and --repetitions must be between 1 and 12")
    asyncio.run(run(args.host, args.repetitions, args.phase))


if __name__ == "__main__":
    main()
