"""Materialize and execute Pick's frozen public v3 keyboard workflows."""
import argparse
import asyncio
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shlex
import shutil

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256

PROJECT = DOC / "pick"
PIN = "caae95938359b2e814b3e7406f396f486c9d99fb"
ARCHIVE_SHA256 = "e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653"
SERIES = "native-exit-v2"
HOSTS = {"linux": "Linux", "darwin": "Darwin"}


def _case(identity, kind, title, fixture, actions, expected_exit=0, *, query=None, options=(), width=80, height=24):
    args = ["pick", *options]
    if query is not None:
        args.extend(["-q", query])
    command_line = "exec " + " ".join(shlex.quote(value) for value in args) + " < choices.txt"
    return {"id": identity, "kind": kind, "title": title, "fixture": fixture,
            "actions": actions, "expected_exit": expected_exit, "command_line": command_line,
            "width": width, "height": height}


def cases():
    """Twenty useful, reviewed Pick workflows with exact deterministic inputs."""
    return [
        _case("N01", "normal", "Select the first supplied option", b"amber\nblue\ncedar\n",
              [{"expect": "amber"}, {"key": "Enter"}, {"expect": "amber"}]),
        _case("N02", "normal", "Move down and select the second option", b"amber\nblue\ncedar\n",
              [{"expect": "amber"}, {"key": "ArrowDown"}, {"expect": "blue"},
               {"key": "Enter"}, {"expect": "blue"}]),
        _case("N03", "normal", "Start from a reviewed initial query", b"amber\nblue\ncedar\n",
              [{"expect": "cedar"}, {"key": "Enter"}, {"expect": "cedar"}], query="cedar"),
        _case("N04", "normal", "Match a query without case sensitivity", b"alpha\nbeta\n",
              [{"expect": "alpha"}, {"key": "Enter"}, {"expect": "alpha"}], query="ALP"),
        _case("N05", "normal", "Use a subsequence query to select one choice", b"cart\nthing\n",
              [{"expect": "cart"}, {"key": "Enter"}, {"expect": "cart"}], query="ct"),
        _case("N06", "normal", "Replace the query and select the new match", b"amber\nblue\n",
              [{"text": "b"}, {"expect": "blue"}, {"key": "CtrlU"}, {"text": "a"},
               {"expect": "amber"}, {"key": "Enter"}, {"expect": "amber"}]),
        _case("N07", "normal", "Rank the exact shortest query match first", b"test\nthis is a test\n",
              [{"expect": "test"}, {"key": "Enter"}, {"expect": "test"}], query="test"),
        _case("N08", "normal", "Select and return a displayed description", b"red fruit\nblue berry\n",
              [{"text": "blue"}, {"expect": "blue berry"}, {"key": "Enter"},
               {"expect": "blue"}, {"expect": "berry"}], options=("-d", "-o")),
        _case("E01", "edge", "Select the only available option", b"single\n",
              [{"expect": "single"}, {"key": "Enter"}, {"expect": "single"}], query="single"),
        _case("E02", "edge", "Cancel without emitting a selected option", b"amber\nblue\n",
              [{"expect": "amber"}, {"key": "CtrlC"}, {"exit": 1}], expected_exit=1),
        _case("E03", "edge", "Refuse confirmation when the query has no match", b"amber\nblue\n",
              [{"expect": "zzq"}, {"key": "Enter"}, {"key": "CtrlC"}, {"exit": 1}],
              expected_exit=1, query="zzq"),
        _case("E04", "edge", "Distinguish duplicate labels using descriptions", b"same first\nsame second\n",
              [{"text": "second"}, {"expect": "same second"}, {"key": "Enter"},
               {"expect": "same"}, {"expect": "second"}], options=("-d", "-o")),
        _case("E05", "edge", "Filter UTF-8 choices by a non-ASCII query", "雪山\n雨\n".encode("utf-8"),
              [{"expect": "雪山"}, {"key": "Enter"}, {"expect": "雪山"}], query="雪"),
        _case("E06", "edge", "Return a selected accented and CJK label", "café 雪\nplain\n".encode("utf-8"),
              [{"text": "caf"}, {"expect": "café 雪"}, {"key": "Enter"}, {"expect": "café 雪"}]),
        _case("E07", "edge", "Read CRLF-separated choices", b"alpha\r\nbeta\r\n",
              [{"text": "bet"}, {"expect": "beta"}, {"key": "Enter"}, {"expect": "beta"}]),
        _case("E08", "edge", "Exit cleanly when there are no choices", b"",
              [{"key": "CtrlC"}, {"exit": 1}], expected_exit=1),
        _case("E09", "edge", "Ignore an empty candidate while selecting a real option", b"\nalpha\n",
              [{"text": "alpha"}, {"expect": "alpha"}, {"key": "Enter"}, {"expect": "alpha"}]),
        _case("E10", "edge", "Disable score sorting and preserve filtered input order",
              b"match-long\nmatch\n", [{"expect": "match-long"}, {"key": "Enter"}, {"expect": "match-long"}],
              query="match", options=("-S",)),
        _case("E11", "edge", "Move to the final item in a list longer than the viewport",
              "".join(f"item{i:02d}\n" for i in range(30)).encode(),
              [{"text": "item"}, {"key": "End"}, {"expect": "item29"},
               {"key": "Enter"}, {"expect": "item29"}], height=8),
        _case("E12", "edge", "Delete the query and select the restored first result", b"amber\nblue\n",
              [{"text": "blue"}, {"expect": "blue"}, {"key": "Backspace"}, {"key": "Backspace"},
               {"key": "Backspace"}, {"key": "Backspace"}, {"expect": "amber"},
               {"key": "Enter"}, {"expect": "amber"}]),
    ]


def materialize():
    package = PROJECT / "scenarios-v1"
    if package.exists() or (PROJECT / "scenario-declaration-v1.json").exists():
        raise ValueError("preserve existing Pick scenario contract artifacts")
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v2.json").read_text(encoding="utf-8"))
    scenario_rows = []
    for case in cases():
        case_dir = package / case["id"]
        fixture_dir = case_dir / "fixtures"
        fixture_dir.mkdir(parents=True)
        with (fixture_dir / "choices.txt").open("xb") as stream:
            stream.write(case["fixture"])
        spec = {
            "version": 3, "name": case["title"], "command": ["/bin/sh", "-c", case["command_line"]],
            "workspace": {"fixture": "fixtures", "cwd": ".", "home": "temporary", "temp": "temporary"},
            "env": {"TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            "inherit_env": ["PATH"], "width": case["width"], "height": case["height"],
            "timeout_ms": 12000, "run_timeout_ms": 60000, "max_output_bytes": 1048576,
            "steps": case["actions"],
        }
        spec_path = case_dir / "scenario.json"
        immutable_json(spec_path, spec)
        scenario_rows.append({
            "id": case["id"], "kind": case["kind"], "title": case["title"],
            "spec_path": spec_path.relative_to(DOC).as_posix(), "spec_sha256": sha256(spec_path),
            "fixture_path": (fixture_dir / "choices.txt").relative_to(DOC).as_posix(),
            "fixture_sha256": sha256(fixture_dir / "choices.txt"),
            "fixture_bytes": len(case["fixture"]),
            "fixture_base64": base64.b64encode(case["fixture"]).decode("ascii"),
            "expected_target_exit": case["expected_exit"], "shell_launch_adapter": "POSIX shell exec with fixture stdin redirection",
        })
    require_count = len(scenario_rows) == 20 and sum(row["kind"] == "normal" for row in scenario_rows) == 8 and sum(
        row["kind"] == "edge" for row in scenario_rows) == 12
    if not require_count:
        raise ValueError("Pick scenario declaration must contain exactly eight normal and twelve edge cases")
    declaration = {
        "schema_version": 1, "project": "pick", "repository": "mptre/pick", "pin": PIN,
        "source_archive_sha256": ARCHIVE_SHA256, "candidate": freeze["version"],
        "candidate_series": "native-exit-v2", "candidate_freeze_sha256": sha256(
            DOC / "replacement-candidate-freeze-native-exit-v2.json"),
        "normal_scenarios": 8, "edge_scenarios": 12, "distinct_scenarios": 20,
        "native_cells": ["linux-amd64", "macos-arm64"],
        "risk_dimensions": ["stdin data with controlling-PTY input", "Unicode fuzzy matching",
                             "cancel versus no-match status", "scored and unsorted selection",
                             "description output", "long-list viewport navigation"],
        "stateful": False, "saved_state_coverage_credit": 0,
        "oracle": "Reviewed rendered-screen checkpoints, exact target exit status, and selected line printed to the same PTY after curses teardown; no filesystem state is claimed.",
        "shell_adapter_scope": "The POSIX shell only redirects the reviewed workspace choices.txt fixture to Pick stdin and execs Pick; all keyboard input remains on the controlling PTY, and no assertion logic or application behavior is in the shell.",
        "scenarios": scenario_rows, "project_admission_credit": 0,
    }
    immutable_json(PROJECT / "scenario-declaration-v1.json", declaration)
    return declaration


def report_result(path, expected_exit):
    report = json.loads(path.read_text(encoding="utf-8"))
    if (report.get("report_version") != 3 or report.get("runner_version") != "v0.4.0-rc.7" or
            report.get("summary", {}).get("total") != 1 or len(report.get("results", [])) != 1):
        raise ValueError("Pick report candidate/version/denominator differs")
    result = report["results"][0]
    if (result.get("status") != "passed" or result.get("target", {}).get("exit_code") != expected_exit or
            not result.get("cleanup", {}).get("confirmed_exited") or
            not result.get("workspace", {}).get("cleaned") or
            any(step.get("status") != "passed" for step in result.get("steps", []))):
        raise ValueError("Pick scenario failed its frozen steps, exit or cleanup contract")
    return result


async def run_scenarios(host, *, repetitions=1, phase="development"):
    if platform.system() != HOSTS[host]:
        raise RuntimeError("actual native host differs from declared Pick host")
    declaration = json.loads((PROJECT / "scenario-declaration-v1.json").read_text(encoding="utf-8"))
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v2.json").read_text(encoding="utf-8"))
    cell = next(row for row in freeze["cells"] if row["host"] == host)
    build = json.loads((RAW / "active/pick/build.json").read_text(encoding="utf-8"))
    binary = RAW / "active/pick/install/bin/pick"
    if (declaration.get("candidate") != freeze["version"] or declaration.get("pin") != PIN or
            build.get("host") != host or build.get("pin") != PIN or
            build.get("binary_sha256") != sha256(binary)):
        raise ValueError("Pick native target, scenario contract or candidate freeze identity differs")
    runner = executable(SERIES, host)
    installed = json.loads((runner.parent / "installed.json").read_text(encoding="utf-8"))
    if installed.get("archive_sha256") != cell["archive_sha256"]:
        raise ValueError("Pick scenarios require the exact frozen native runner archive")

    env = {key: os.environ[key] for key in ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT")
           if key in os.environ}
    env.update({"PATH": str(binary.parent) + os.pathsep + env.get("PATH", ""),
                "TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "TMPDIR": str(RAW / "tmp"), "TMP": str(RAW / "tmp"), "TEMP": str(RAW / "tmp")})
    (RAW / "tmp").mkdir(parents=True, exist_ok=True)
    campaign = NextCampaign(phase=phase)
    receipts = []
    for repetition in range(1, repetitions + 1):
        for row in declaration["scenarios"]:
            spec = DOC / row["spec_path"]
            report = RAW / "pick" / phase / host / f"r{repetition:02d}" / row["id"] / "report.json"
            artifacts = RAW / "pick" / phase / host / f"r{repetition:02d}" / row["id"] / "artifacts"
            report.parent.mkdir(parents=True, exist_ok=True)
            argv = [runner, "test", "--report", report.relative_to(ROOT), "--artifacts-dir",
                    artifacts.relative_to(ROOT), spec.relative_to(ROOT)]
            attempt = await execute(argv, "pick", f"pick-{phase}-{host}-r{repetition:02d}-{row['id']}",
                                    cwd=ROOT, env=env, timeout=180, campaign=campaign)
            result = report_result(report, row["expected_target_exit"])
            receipts.append({"attempt_id": attempt["id"], "scenario": row["id"],
                             "repetition": repetition, "phase": phase,
                             "report_sha256": sha256(report), "invocation_id": result["invocation_id"],
                             "target_exit": row["expected_target_exit"],
                             "cleanup_confirmed": result["cleanup"]["confirmed_exited"],
                             "workspace_cleaned": result["workspace"]["cleaned"]})
    result_path = RAW / "pick" / f"{phase}-{host}-run-{os.environ.get('GITHUB_RUN_ID', 'local')}.json"
    immutable_json(result_path, {"schema_version": 1, "project": "pick", "host": host,
                                 "candidate": freeze["version"], "phase": phase,
                                 "repetitions": repetitions, "attempts": receipts,
                                 "attempt_count": len(receipts), "admission_credit": 0})
    print(json.dumps({"project": "pick", "host": host, "phase": phase,
                      "repetitions": repetitions, "attempt_count": len(receipts)}, sort_keys=True))
    return receipts


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialize", action="store_true")
    parser.add_argument("--host", choices=tuple(HOSTS))
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--phase", default="development")
    args = parser.parse_args()
    if args.materialize:
        print("Pick scenario contract frozen:", len(materialize()["scenarios"]), "cases; no target launch.")
        return
    if args.host is None or not 1 <= args.repetitions <= 12:
        parser.error("--host is required and --repetitions must be between 1 and 12")
    asyncio.run(run_scenarios(args.host, repetitions=args.repetitions, phase=args.phase))


if __name__ == "__main__":
    main()
