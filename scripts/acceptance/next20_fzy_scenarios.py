"""Freeze and run fzy's public interactive selection contract on native hosts."""
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


PROJECT = DOC / "fzy"
PIN = "34b88869d022e861da4846c4463aea3ddfb3ff30"
HOSTS = {"linux": "Linux", "darwin": "Darwin"}
SERIES = "native-exit-v3"
SCENARIO_VERSION = 1


def make_case(identity, kind, title, fixture, actions, *, options=(), path="choices.txt"):
    command = "exec fzy " + " ".join(shlex.quote(value) for value in options)
    command += " < " + shlex.quote(path) + " > result.txt"
    stdout = {
        "N01": b"apple\n", "N02": b"blue\n", "N03": b"cart\n", "N04": b"test\n",
        "N05": b"blue\n", "N06": b"blue\n", "N07": b"apple\n",
        "N08": b"cat\ncart\n", "E01": b"", "E02": b"", "E03": b"", "E04": b"",
        "E05": b"zzq\n", "E06": b"alpha\n", "E07": "café 雪\n".encode("utf-8"),
        "E08": b"blue\n", "E09": b"item03\n", "E10": b"alpha\n",
        "E11": b"nothing\n", "E12": b"",
    }[identity]
    expected_exit = next(action["exit"] for action in reversed(actions) if "exit" in action)
    observed = []
    after_enter = False
    for action in actions:
        if action == {"key": "Enter"}:
            observed.append(action)
            after_enter = True
        elif "exit" in action:
            observed.append(action)
        elif after_enter and "expect" in action:
            # stdout is captured separately, so the screen no longer contains
            # the emitted value after fzy closes its controlling TTY.
            continue
        else:
            observed.append(action)
    observed.append({"state": {"path": "result.txt", "kind": "file",
                                "bytes_base64": base64.b64encode(stdout).decode("ascii")}})
    return {"id": identity, "kind": kind, "title": title,
            "fixture": fixture, "fixture_path": path, "command": command,
            "options": list(options), "actions": observed, "expected_exit": expected_exit,
            "expected_stdout_base64": base64.b64encode(stdout).decode("ascii")}


def cases():
    """Twenty reviewed outcomes for fzy's real controlling-terminal interface."""
    return [
        make_case("N01", "normal", "Select the first candidate with an empty query",
                  b"apple\nbanana\n", [{"expect": "apple"}, {"key": "Enter"},
                  {"expect": "apple"}, {"exit": 0}]),
        make_case("N02", "normal", "Select the unique initial query match",
                  b"red\nblue\ngreen\n", [{"expect": "blue"}, {"key": "Enter"},
                  {"expect": "blue"}, {"exit": 0}], options=("--query=blue",)),
        make_case("N03", "normal", "Select a subsequence match",
                  b"cart\nplain\n", [{"expect": "cart"}, {"key": "Enter"},
                  {"expect": "cart"}, {"exit": 0}], options=("--query=ct",)),
        make_case("N04", "normal", "Prefer the exact candidate over its longer prefix",
                  b"tests\ntest\n", [{"expect": "test"}, {"key": "Enter"},
                  {"expect": "test"}, {"exit": 0}], options=("--query=test",)),
        make_case("N05", "normal", "Move to the next candidate and emit it",
                  b"amber\nblue\ncedar\n", [{"expect": "amber"}, {"key": "ArrowDown"},
                  {"expect": "blue"}, {"key": "Enter"}, {"expect": "blue"}, {"exit": 0}]),
        make_case("N06", "normal", "Edit the query with backspace before selection",
                  b"blue\nblack\n", [{"text": "blue"}, {"expect": "blue"},
                  {"key": "Backspace"}, {"expect": "blue"}, {"key": "Enter"},
                  {"expect": "blue"}, {"exit": 0}]),
        make_case("N07", "normal", "Complete the selected candidate with Tab",
                  b"apple\n", [{"text": "ap"}, {"key": "Tab"}, {"expect": "apple"},
                  {"key": "Enter"}, {"expect": "apple"}, {"exit": 0}]),
        make_case("N08", "normal", "Emit sorted line matches in filter mode",
                  b"dog\ncart\ncat\n", [{"exit": 0}],
                  options=("--show-matches", "cat")),
        make_case("E01", "edge", "Escape cancels without a chosen result",
                  b"amber\nblue\n", [{"expect": "amber"}, {"key": "Escape"}, {"exit": 1}]),
        make_case("E02", "edge", "Ctrl-C cancels without a chosen result",
                  b"amber\nblue\n", [{"expect": "amber"}, {"key": "CtrlC"}, {"exit": 1}]),
        make_case("E03", "edge", "Ctrl-D cancels without a chosen result",
                  b"amber\nblue\n", [{"expect": "amber"}, {"key": "CtrlD"}, {"exit": 1}]),
        make_case("E04", "edge", "Ctrl-G cancels without a chosen result",
                  b"amber\nblue\n", [{"expect": "amber"}, {"key": "CtrlG"}, {"exit": 1}]),
        make_case("E05", "edge", "Enter emits the query when no candidate matches",
                  b"amber\nblue\n", [{"text": "zzq"}, {"expect": "zzq"},
                  {"key": "Enter"}, {"expect": "zzq"}, {"exit": 0}]),
        make_case("E06", "edge", "Skip an empty input line and choose the real candidate",
                  b"\nalpha\n", [{"text": "alpha"}, {"expect": "alpha"},
                  {"key": "Enter"}, {"expect": "alpha"}, {"exit": 0}]),
        make_case("E07", "edge", "Emit an accented and CJK candidate byte sequence",
                  "café 雪\nplain\n".encode("utf-8"), [{"text": "caf"}, {"expect": "café 雪"},
                  {"key": "Enter"}, {"expect": "café 雪"}, {"exit": 0}]),
        make_case("E08", "edge", "Read NUL-delimited input and emit the second choice",
                  b"amber\0blue\0", [{"expect": "amber"}, {"key": "ArrowDown"},
                  {"expect": "blue"}, {"key": "Enter"}, {"expect": "blue"}, {"exit": 0}],
                  options=("--read-null",), path="choices.bin"),
        make_case("E09", "edge", "Page one short viewport through the long list",
                  "".join(f"item{i:02d}\n" for i in range(20)).encode("ascii"),
                  [{"expect": "item00"}, {"key": "PageDown"}, {"expect": "item03"},
                   {"key": "Enter"}, {"expect": "item03"}, {"exit": 0}], options=("--lines=3",)),
        make_case("E10", "edge", "Show scores and still emit the selected candidate",
                  b"alpha\nbeta\n", [{"expect": "alpha"}, {"key": "Enter"},
                  {"expect": "alpha"}, {"exit": 0}], options=("--show-scores",)),
        make_case("E11", "edge", "Emit the query as a successful empty-candidate result",
                  b"", [{"text": "nothing"}, {"expect": "nothing"},
                  {"key": "Enter"}, {"expect": "nothing"}, {"exit": 0}]),
        make_case("E12", "edge", "Reject an interactive result count below the documented minimum",
                  b"alpha\n", [{"exit": 1}], options=("--lines=2",)),
    ]


def materialize():
    package = PROJECT / f"scenarios-v{SCENARIO_VERSION}"
    declaration_path = PROJECT / f"scenario-declaration-v{SCENARIO_VERSION}.json"
    if package.exists() or declaration_path.exists():
        raise ValueError("preserve existing fzy scenario contract")
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v3.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    rows = []
    for case in cases():
        folder = package / case["id"]
        fixtures = folder / "fixtures"
        fixtures.mkdir(parents=True)
        fixture_path = fixtures / Path(case["fixture_path"]).name
        fixture_path.write_bytes(case["fixture"])
        spec = {
            "version": 3, "name": case["title"],
            "command": ["/bin/sh", "-c", case["command"]],
            "workspace": {"fixture": "fixtures", "cwd": ".", "home": "temporary", "temp": "temporary"},
            "env": {"TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            "inherit_env": ["PATH"], "width": 80, "height": 12,
            "timeout_ms": 12000, "run_timeout_ms": 60000, "max_output_bytes": 1048576,
            "steps": case["actions"],
        }
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
    if len(rows) != 20 or sum(row["kind"] == "normal" for row in rows) != 8 or sum(
            row["kind"] == "edge" for row in rows) != 12:
        raise ValueError("fzy contract must contain exactly eight normal and twelve edge cases")
    declaration = {
        "schema_version": 1, "scenario_contract_version": SCENARIO_VERSION,
        "project": "fzy", "repository": "jhawthorn/fzy", "pin": PIN,
        "source_archive_sha256": json.loads((RAW / "active/fzy/acquisition.json").read_text())["archive_sha256"],
        "candidate": freeze["version"], "candidate_series": freeze["series"],
        "candidate_freeze_sha256": sha256(freeze_path),
        "normal_scenarios": 8, "edge_scenarios": 12, "distinct_scenarios": 20,
        "native_cells": ["linux-amd64", "macos-arm64"], "stateful": False,
        "saved_state_coverage_credit": 0,
        "oracle": "Exact bytes emitted by fzy to a harness-owned stdout capture file, exact target exit status, and positive rendered-screen checkpoints for interactive cases in the same invocation. The capture file is not target-saved-state coverage.",
        "shell_adapter_scope": "POSIX shell only redirects the exact reviewed fixture to fzy stdin, redirects fzy stdout to the reviewed result.txt capture, and execs fzy; keyboard input remains on the controlling PTY and no assertion logic is in the shell.",
        "risk_dimensions": ["fuzzy query/ranking", "typed edit and completion", "cancel control paths",
                            "no-match emission", "NUL-delimited choices", "UTF-8 output",
                            "short viewport navigation", "filter and score options",
                            "invalid option boundary"],
        "scenarios": rows, "project_admission_credit": 0,
    }
    immutable_json(declaration_path, declaration)
    return declaration


def verify_materialized():
    """Check the committed contract against current reviewed case definitions."""
    package = PROJECT / f"scenarios-v{SCENARIO_VERSION}"
    declaration_path = PROJECT / f"scenario-declaration-v{SCENARIO_VERSION}.json"
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v3.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    require_rows = {row["id"]: row for row in declaration.get("scenarios", [])}
    expected_cases = cases()
    if (len(require_rows) != 20 or len(expected_cases) != 20
            or declaration.get("project") != "fzy" or declaration.get("pin") != PIN
            or declaration.get("candidate") != freeze["version"]
            or declaration.get("candidate_series") != SERIES
            or declaration.get("candidate_freeze_sha256") != sha256(freeze_path)
            or declaration.get("source_archive_sha256") != json.loads(
                (RAW / "active/fzy/acquisition.json").read_text(encoding="utf-8")).get("archive_sha256")):
        raise ValueError("committed fzy declaration differs from the exact reviewed source/candidate")
    for case in expected_cases:
        row = require_rows.get(case["id"])
        if row is None:
            raise ValueError("committed fzy declaration omits " + case["id"])
        folder = package / case["id"]
        fixture = folder / "fixtures" / Path(case["fixture_path"]).name
        spec_path = folder / "scenario.json"
        spec = {
            "version": 3, "name": case["title"],
            "command": ["/bin/sh", "-c", case["command"]],
            "workspace": {"fixture": "fixtures", "cwd": ".", "home": "temporary", "temp": "temporary"},
            "env": {"TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            "inherit_env": ["PATH"], "width": 80, "height": 12,
            "timeout_ms": 12000, "run_timeout_ms": 60000, "max_output_bytes": 1048576,
            "steps": case["actions"],
        }
        if (not fixture.is_file() or fixture.is_symlink() or fixture.read_bytes() != case["fixture"]
                or not spec_path.is_file() or spec_path.is_symlink()
                or json.loads(spec_path.read_text(encoding="utf-8")) != spec
                or row.get("spec_path") != spec_path.relative_to(DOC).as_posix()
                or row.get("spec_sha256") != sha256(spec_path)
                or row.get("fixture_sha256") != sha256(fixture)
                or row.get("fixture_bytes") != len(case["fixture"])
                or row.get("expected_stdout_base64") != case["expected_stdout_base64"]
                or row.get("expected_target_exit") != case["expected_exit"]):
            raise ValueError("committed fzy scenario/fixture/declaration differs: " + case["id"])
    return declaration


def check_report(path, expected_exit):
    report = json.loads(path.read_text(encoding="utf-8"))
    if (report.get("report_version") != 3 or report.get("runner_version") != "v0.4.0-rc.8"
            or report.get("summary", {}).get("total") != 1 or len(report.get("results", [])) != 1):
        raise ValueError("fzy report candidate/version/denominator differs")
    result = report["results"][0]
    if (result.get("status") != "passed" or result.get("target", {}).get("exit_code") != expected_exit
            or result.get("cleanup", {}).get("confirmed_exited") is not True
            or result.get("workspace", {}).get("cleaned") is not True
            or any(step.get("status") != "passed" for step in result.get("steps", []))):
        raise ValueError("fzy scenario failed expected screen, exit or cleanup")
    return result


async def run(host, repetitions=1, phase="development"):
    if platform.system() != HOSTS[host]:
        raise RuntimeError("actual native host differs from declared fzy host")
    declaration = json.loads((PROJECT / f"scenario-declaration-v{SCENARIO_VERSION}.json").read_text())
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v3.json").read_text())
    cell = next(row for row in freeze["cells"] if row["host"] == host)
    build = json.loads((RAW / "active/fzy/build.json").read_text())
    binary = RAW / "active/fzy/install/bin/fzy"
    if (declaration["candidate"] != freeze["version"] or declaration["pin"] != PIN
            or build["host"] != host or build["pin"] != PIN or build["binary_sha256"] != sha256(binary)
            or declaration["source_archive_sha256"] != build["source_archive_sha256"]):
        raise ValueError("fzy native target, scenario contract or candidate identity differs")
    runner = executable(SERIES, host)
    installed = json.loads((runner.parent / "installed.json").read_text())
    if installed.get("archive_sha256") != cell["archive_sha256"]:
        raise ValueError("fzy scenarios require the exact frozen native runner archive")
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env.update({"PATH": str(binary.parent) + os.pathsep + env.get("PATH", ""),
                "TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "TMPDIR": str(RAW / "tmp"), "TMP": str(RAW / "tmp"), "TEMP": str(RAW / "tmp")})
    (RAW / "tmp").mkdir(parents=True, exist_ok=True)
    campaign = NextCampaign(phase=phase)
    receipts = []
    for repetition in range(1, repetitions + 1):
        for row in declaration["scenarios"]:
            spec = DOC / row["spec_path"]
            base = RAW / "fzy" / phase / host / f"r{repetition:02d}" / row["id"]
            report, artifacts = base / "report.json", base / "artifacts"
            report.parent.mkdir(parents=True, exist_ok=True)
            argv = [runner, "test", "--report", report.relative_to(ROOT), "--artifacts-dir",
                    artifacts.relative_to(ROOT), spec.relative_to(ROOT)]
            attempt = await execute(argv, "fzy", f"fzy-{phase}-{host}-r{repetition:02d}-{row['id']}",
                                    cwd=ROOT, env=env, timeout=180, campaign=campaign)
            result = check_report(report, row["expected_target_exit"])
            receipts.append({"attempt_id": attempt["id"], "scenario": row["id"],
                             "repetition": repetition, "phase": phase,
                             "report_sha256": sha256(report), "invocation_id": result["invocation_id"],
                             "target_exit": row["expected_target_exit"],
                             "cleanup_confirmed": True, "workspace_cleaned": True})
    result_path = RAW / "fzy" / f"{phase}-{host}-run-{os.environ.get('GITHUB_RUN_ID', 'local')}.json"
    immutable_json(result_path, {"schema_version": 1, "project": "fzy", "host": host,
                                 "candidate": freeze["version"], "phase": phase,
                                 "repetitions": repetitions, "attempts": receipts,
                                 "attempt_count": len(receipts), "admission_credit": 0})
    print(json.dumps({"project": "fzy", "host": host, "phase": phase,
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
        print("fzy scenario contract frozen:", len(materialize()["scenarios"]), "cases; no target launch.")
        return
    if args.verify:
        print("fzy committed scenario contract verified:",
              len(verify_materialized()["scenarios"]), "cases; no target launch.")
        return
    if args.host is None or not 1 <= args.repetitions <= 12:
        parser.error("--host is required and --repetitions must be between 1 and 12")
    asyncio.run(run(args.host, args.repetitions, args.phase))


if __name__ == "__main__":
    main()
