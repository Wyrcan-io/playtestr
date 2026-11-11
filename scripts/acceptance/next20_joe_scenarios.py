"""Execute frozen public-spec scenarios against the pinned native JOE build."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import time
import uuid

from next20_candidate import executable
from next20_check import DOC, RAW, ROOT
from next20_mg_build import MAX_OUTPUT, run_bounded
from readiness_evidence import immutable_json, sha256
from next20_target_cleanup import workspace_setup_failure_before_launch

PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
PROJECT = DOC / "joe"
SCENARIOS = PROJECT / "scenarios-v3"
DECLARATION = PROJECT / "scenario-declaration-v3.json"
PRELAUNCH = PROJECT / "scenario-attempt-v4.json"


def _state(path, data):
    return {"state": {"path": path, "kind": "file",
                      "bytes_base64": base64.b64encode(data).decode("ascii")}}


def _case(identity, title, risk, files, command_file, actions, expected, *, width=80, height=24,
          kind="normal", absent=(), pair=None, command_args=None):
    return {"id": identity, "title": title, "risk": risk, "kind": kind,
            "files": files, "command_file": command_file, "actions": actions,
            "expected": expected, "absent": list(absent), "width": width,
            "height": height, "risk_pair": pair, "command_args": command_args}


def cases():
    """Twenty source-reviewed JOE workflows; exact bytes are independently declared."""
    save = [{"key": "CtrlK"}, {"text": "x"}, {"exit": 0}]
    return [
        _case("N01", "Append a reviewed line to an existing note", "append-save-readback",
              {"note.txt": b"reviewed seed\n"}, "note.txt",
              [{"expect": "reviewed seed"}, {"key": "End"}, {"text": " + appended"},
               {"expect": "reviewed seed + appended"}, *save],
              {"note.txt": b"reviewed seed + appended\n"}),
        _case("N02", "Create and save a named note", "new-file-create-and-save",
              {".keep": b""}, "new-note.txt", [{"expect": "new-note.txt"}, {"text": "fresh note"},
                                    {"expect": "fresh note"}, *save],
              {"new-note.txt": b"fresh note", ".keep": b""}),
        _case("N03", "Correct a selected line without changing its neighbors", "line-navigation-and-edit",
              {"note.txt": b"alpha\nbravo\ncharlie\n"}, "note.txt",
              [{"expect": "alpha"}, {"key": "ArrowDown"}, {"key": "Home"}, {"expect": "bravo"},
               {"text": "reviewed "}, {"expect": "reviewed bravo"}, *save],
              {"note.txt": b"alpha\nreviewed bravo\ncharlie\n"}),
        _case("N04", "Remove the previous character and save", "backspace-boundary",
              {"note.txt": b"alphx\n"}, "note.txt",
              [{"expect": "alphx"}, {"key": "End"}, {"key": "Backspace"},
               {"expect": "alph"}, *save], {"note.txt": b"alph\n"}),
        _case("N05", "Delete the character under the cursor", "forward-delete",
              {"note.txt": b"alpha\n"}, "note.txt",
              [{"expect": "alpha"}, {"key": "CtrlA"}, {"key": "ArrowRight"},
               {"key": "CtrlD"}, {"expect": "apha"}, *save], {"note.txt": b"apha\n"}),
        _case("N06", "Replace the current line with a corrected line", "line-delete-and-replace",
              {"note.txt": b"obsolete line\nkeep this line\n"}, "note.txt",
              [{"expect": "obsolete line"}, {"key": "CtrlY"}, {"text": "corrected line"},
               {"key": "Enter"},
               {"expect": "corrected line"}, {"expect": "keep this line"}, *save],
              {"note.txt": b"corrected line\nkeep this line\n"}),
        _case("N07", "Insert a new heading before existing content", "line-split-and-order",
              {"note.txt": b"body text\n"}, "note.txt",
              [{"expect": "body text"}, {"key": "Home"}, {"text": "Heading"}, {"key": "Enter"},
               {"expect": "Heading"}, {"expect": "body text"}, *save],
              {"note.txt": b"Heading\nbody text\n"}),
        _case("N08", "Append a summary to a multi-line document", "end-of-buffer-navigation",
              {"note.txt": b"first paragraph\nsecond paragraph\n"}, "note.txt",
              [{"expect": "first paragraph"}, {"key": "CtrlK"}, {"text": "v"},
               {"text": "Summary"}, {"key": "Enter"}, {"expect": "Summary"}, *save],
              {"note.txt": b"first paragraph\nsecond paragraph\nSummary\n"}),
        _case("E01", "Abort an unsaved edit and preserve the original file", "dirty-abort-preserves-bytes",
              {"note.txt": b"approved text\n"}, "note.txt",
              [{"expect": "approved text"}, {"key": "End"}, {"text": " uncommitted"},
               {"expect": "uncommitted"}, {"key": "CtrlC"}, {"text": "y"}, {"exit": 0}],
              {"note.txt": b"approved text\n"}, kind="edge", pair="dirty-edit-plus-abort"),
        _case("E02", "Leave an empty file empty on clean save", "zero-byte-boundary",
              {"empty.txt": b""}, "empty.txt",
              [{"expect": "empty.txt"}, *save], {"empty.txt": b""}, kind="edge"),
        _case("E03", "Preserve CRLF line endings during an edit", "line-ending-preservation",
              {"note.txt": b"first\r\nsecond\r\n"}, "note.txt",
              [{"expect": "first"}, {"key": "End"}, {"text": "!"}, {"expect": "first!"}, *save],
              {"note.txt": b"first!\r\nsecond\r\n"}, kind="edge"),
        _case("E04", "Preserve a file with no final newline", "missing-final-newline",
              {"note.txt": b"tail"}, "note.txt",
              [{"expect": "tail"}, {"key": "End"}, {"text": "!"}, {"expect": "tail!"}, *save],
              {"note.txt": b"tail!"}, kind="edge"),
        _case("E05", "Save UTF-8 text at a spaced Unicode path", "unicode-content-and-path",
              {"folder café/note 雪.txt": "starter\n".encode()}, "folder café/note 雪.txt",
              [{"expect": "starter"}, {"key": "End"}, {"text": " café 雪"},
               {"expect": "starter café 雪"}, *save],
              {"folder café/note 雪.txt": "starter café 雪\n".encode()}, kind="edge",
              pair="unicode-path-plus-exact-state"),
        _case("E06", "Edit one file while preserving an unrelated sentinel", "selective-state-preservation",
              {"note.txt": b"main note\n", "sentinel.txt": b"preserve exactly\x00\r\n"}, "note.txt",
              [{"expect": "main note"}, {"key": "End"}, {"text": " updated"},
               {"expect": "main note updated"}, *save],
              {"note.txt": b"main note updated\n", "sentinel.txt": b"preserve exactly\x00\r\n"}, kind="edge"),
        _case("E07", "Edit the final line after scrolling through a short viewport", "scroll-redraw-small-viewport",
              {"note.txt": ("".join("line %02d\n" % i for i in range(1, 36))).encode()}, "note.txt",
              [{"key": "CtrlK"}, {"text": "v"}, {"expect": "line 35"}, {"key": "CtrlP"}, {"key": "End"},
               {"text": "!"}, {"expect": "line 35!"}, *save],
              {"note.txt": ("".join("line %02d\n" % i for i in range(1, 35)) + "line 35!\n").encode()},
              width=60, height=12, kind="edge", pair="small-viewport-plus-state-output"),
        _case("E08", "Append to a long wrapped line without losing its prefix", "long-line-wrap-and-edit",
              {"note.txt": ("prefix " + "0123456789" * 9 + "\n").encode()}, "note.txt",
              [{"expect": "prefix"}, {"key": "End"}, {"text": " suffix"}, {"expect": "suffix"}, *save],
              {"note.txt": ("prefix " + "0123456789" * 9 + " suffix\n").encode()},
              width=40, height=18, kind="edge", pair="wrapped-content-plus-exact-save"),
        _case("E09", "Append to the second line while keeping the first line unchanged", "multi-line-transition",
              {"note.txt": b"first\nsecond\n"}, "note.txt",
              [{"expect": "first"}, {"key": "ArrowDown"}, {"key": "End"}, {"text": " updated"},
               {"expect": "second updated"}, *save], {"note.txt": b"first\nsecond updated\n"}, kind="edge",
              pair="line-transition-plus-neighbor-preservation"),
        _case("E10", "Create a nested document in an existing directory", "nested-path-create",
              {"drafts/README.txt": b"existing folder\n"}, "drafts/new note.txt",
              [{"expect": "new note.txt"}, {"text": "nested draft"}, {"expect": "nested draft"}, *save],
              {"drafts/README.txt": b"existing folder\n", "drafts/new note.txt": b"nested draft"}, kind="edge",
              pair="nested-spaced-path-plus-created-state"),
        _case("E11", "Preserve a tab and following fields while editing a row", "tab-byte-preservation",
              {"table.txt": b"name\tvalue\nalpha\t1\n"}, "table.txt",
              [{"expect": "name"}, {"key": "CtrlK"}, {"text": "v"}, {"text": "review"}, {"key": "Enter"},
               {"expect": "review"}, *save],
              {"table.txt": b"name\tvalue\nalpha\t1\nreview\n"}, kind="edge"),
        _case("E12", "Edit a final line when launched at a high line number", "position-clamp-and-exit",
              {"note.txt": b"one\ntwo\nthree\n"}, "note.txt",
              [{"expect": "three"}, {"key": "CtrlP"}, {"key": "End"}, {"text": "!"}, {"expect": "three!"}, *save],
              {"note.txt": b"one\ntwo\nthree!\n"}, kind="edge",
              pair="out-of-range-position-plus-last-line-state", command_args=["+999", "note.txt"]),
    ]


def materialize():
    """Create frozen spec/fixture inputs once; refuses any pre-existing file."""
    for case in cases():
        case_dir = SCENARIOS / case["id"]
        fixture = case_dir / "fixtures"
        fixture.mkdir(parents=True, exist_ok=False)
        for name, value in case["files"].items():
            path = fixture / name
            path.parent.mkdir(parents=True, exist_ok=True)
            data = value if isinstance(value, bytes) else b"".join(value)
            path.write_bytes(data)
        command_file = case["command_file"]
        command = ["joe", "-nobackups", *(case["command_args"] or [command_file])]
        steps = list(case["actions"])
        for name, value in case["expected"].items():
            steps.append(_state(name, value))
        steps.append({"exit": 0}) if not any("exit" in step for step in steps) else None
        spec = {"version": 3, "name": case["title"], "command": command,
                "workspace": {"fixture": "fixtures", "cwd": ".", "home": "temporary", "temp": "temporary"},
                "env": {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TERM": "xterm-256color"},
                "inherit_env": ["PATH"], "width": case["width"], "height": case["height"],
                "timeout_ms": 12000, "run_timeout_ms": 60000, "max_output_bytes": 2000000,
                "steps": steps}
        case_dir.mkdir(parents=True, exist_ok=True) if not case_dir.exists() else None
        (case_dir / "scenario.json").write_text(json.dumps(spec, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
    rows = []
    for case in cases():
        spec_path = SCENARIOS / case["id"] / "scenario.json"
        spec_bytes = spec_path.read_bytes()
        fixture_rows = []
        for name, value in sorted(case["files"].items()):
            data = value if isinstance(value, bytes) else b"".join(value)
            fixture_rows.append({"path": name, "bytes": len(data),
                                 "sha256": hashlib.sha256(data).hexdigest(),
                                 "bytes_base64": base64.b64encode(data).decode("ascii")})
        expected_rows = [{"path": name, "bytes": len(value),
                          "sha256": hashlib.sha256(value).hexdigest(),
                          "bytes_base64": base64.b64encode(value).decode("ascii")}
                         for name, value in sorted(case["expected"].items())]
        rows.append({"id": case["id"], "title": case["title"], "kind": case["kind"],
                     "risk": case["risk"], "risk_pair": case["risk_pair"],
                     "preconditions": fixture_rows, "expected_state": expected_rows,
                     "host_applicability": ["linux-amd64", "macos-arm64"],
                     "viewport": {"width": case["width"], "height": case["height"]},
                     "input_profile": "documented JOE keys and bounded UTF-8 text; no shell, pipe or external command",
                     "positive_evidence": "specific rendered JOE text followed by exact in-run saved-file state and exit 0",
                     "oracle_independence": "literal fixture and expected byte strings independently declared in this source; no target writer computes expectations",
                     "cleanup": "runner report must confirm JOE exit and managed workspace removal; harness process group must be absent",
                     "spec": spec_path.relative_to(ROOT).as_posix(),
                     "spec_sha256": hashlib.sha256(spec_bytes).hexdigest()})
    declaration = {"schema_version": 1, "project": "joe", "repository": "joe-editor/joe", "pin": PIN,
                   "candidate": "v0.4.0-rc.6", "project_admission_credit": 0,
                   "status": "frozen-development-declaration-not-qualified",
                   "minimums": {"normal": 8, "edge": 12, "distinct": 20,
                                "native_cells": ["linux-amd64", "macos-arm64"]},
                   "risk_pairs": [row["risk_pair"] for row in rows if row["risk_pair"]],
                   "scenarios": rows,
                   "scope": "Frozen scenario contract inputs only. Development attempts do not constitute final candidate qualification or project admission."}
    declaration_path = DECLARATION
    if declaration_path.exists():
        raise FileExistsError("refusing to overwrite frozen JOE scenario declaration")
    declaration_path.write_text(json.dumps(declaration, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def verify_declarations():
    declared = cases()
    if len(declared) != 20 or sum(row["kind"] == "normal" for row in declared) != 8:
        raise ValueError("JOE scenario declaration must contain eight normal and twelve edge cases")
    declaration_path = DECLARATION
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    for row in declared:
        path = SCENARIOS / row["id"] / "scenario.json"
        fixture_root=SCENARIOS/row["id"]/"fixtures"
        if path.is_symlink() or not path.is_file():
            raise ValueError("missing regular frozen scenario: " + str(path))
        if fixture_root.is_symlink() or not fixture_root.is_dir():
            raise ValueError("missing regular JOE fixture directory: " + str(fixture_root))
        spec = json.loads(path.read_text(encoding="utf-8"))
        expected_command = ["joe", "-nobackups", *(row["command_args"] or [row["command_file"]])]
        if spec.get("version") != 3 or spec.get("command") != expected_command:
            raise ValueError("scenario identity or public spec version differs: " + row["id"])
        if spec.get("steps", []) != row["actions"] + [_state(name, value) for name, value in row["expected"].items()]:
            raise ValueError("scenario steps/state differ from independent declaration: " + row["id"])
        expected_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        manifest_row = next((item for item in declaration.get("scenarios", []) if item.get("id") == row["id"]), None)
        if manifest_row is None or manifest_row.get("spec_sha256") != expected_sha:
            raise ValueError("scenario spec hash differs from the frozen project declaration: " + row["id"])
        for rel, data in row["files"].items():
            item = SCENARIOS / row["id"] / "fixtures" / rel
            if item.is_symlink() or not item.is_file() or item.read_bytes() != data:
                raise ValueError("missing regular JOE fixture: " + str(item))
    if declaration.get("project") != "joe" or declaration.get("pin") != PIN or len(declaration.get("scenarios", [])) != 20:
        raise ValueError("frozen JOE scenario catalog identity or denominator differs")
    attempt_path = PRELAUNCH
    attempt = json.loads(attempt_path.read_text(encoding="utf-8"))
    declaration_hash = hashlib.sha256(declaration_path.read_bytes()).hexdigest()
    if (attempt.get("scenario_declaration_sha256") != declaration_hash or
            attempt.get("phase") != "scenario-development" or attempt.get("project_admission_credit") != 0):
        raise ValueError("prelaunch JOE scenario attempt does not bind the frozen declaration")


def run_one(case, host, phase, repetition=0):
    build_root = RAW / "active/joe"
    build_path = build_root / "build.json"
    target = build_root / "install/bin/joe"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if build.get("project") != PROJECT.name or build.get("pin") != PIN or build.get("host") != host:
        raise ValueError("native JOE build identity differs from the reviewed source pin and host")
    if target.is_symlink() or sha256(target) != build.get("binary_sha256"):
        raise ValueError("JOE executable differs from its native build receipt")
    contract = SCENARIOS / case["id"] / "scenario.json"
    spec_bytes = contract.read_bytes()
    spec = json.loads(spec_bytes)
    fixture = SCENARIOS / case["id"] / "fixtures"
    for p in (fixture, *fixture.rglob("*")):
        if p.is_symlink():
            raise ValueError("linked JOE fixture path")
    candidate = executable("native-exit-v1", host)
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v1.json").read_text(encoding="utf-8"))
    frozen = next(row for row in freeze["cells"] if row["host"] == host)
    attempt_id = uuid.uuid4().hex
    attempt_dir = RAW / f"joe/{phase}/{host}/{case['id']}/r{repetition:02d}-{attempt_id}"
    attempt_dir.mkdir(parents=True, exist_ok=False)
    env_root = attempt_dir / "environment"
    home, temp = env_root / "home", env_root / "temp"
    home.mkdir(parents=True)
    temp.mkdir(parents=True)
    env = {"PATH": str(target.parent) + os.pathsep + os.environ.get("PATH", ""),
           "HOME": str(home), "TMP": str(temp), "TEMP": str(temp), "TMPDIR": str(temp),
           "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TERM": "xterm-256color"}
    attempt = {"schema_version": 1, "attempt_id": attempt_id, "project": "joe", "phase": phase,
               "repetition": repetition, "scenario_id": case["id"], "candidate": freeze["version"],
               "candidate_archive_sha256": frozen["archive_sha256"],
               "candidate_binary_sha256": frozen["binary_sha256"], "target_pin": PIN,
               "target_binary_sha256": build["binary_sha256"], "target_build_receipt_sha256": sha256(build_path),
               "host": host, "architecture": build["architecture"],
               "contract": contract.relative_to(ROOT).as_posix(),
               "contract_sha256": hashlib.sha256(spec_bytes).hexdigest(),
               "fixture": fixture.relative_to(ROOT).as_posix(), "fixture_file_count": len(case["files"]),
               "limits": {"command_seconds": 120, "runner_output_bytes": MAX_OUTPUT,
                          "step_timeout_ms": spec["timeout_ms"], "run_timeout_ms": spec["run_timeout_ms"]},
               "expected": "all declared JOE interaction and exact saved-state assertions pass",
               "started_at_utc": datetime.now(timezone.utc).isoformat()}
    immutable_json(attempt_dir / "attempt.json", attempt)
    immutable_json(attempt_dir / "started.json", {"schema_version": 1, "attempt_id": attempt_id,
                    "event": "started", "at_utc": attempt["started_at_utc"]})
    immutable_json(attempt_dir / "identified.json", {"schema_version": 1, "attempt_id": attempt_id,
                    "event": "identified", "candidate_sha256": frozen["binary_sha256"],
                    "target_sha256": build["binary_sha256"], "contract_sha256": attempt["contract_sha256"]})
    report = attempt_dir / "report.json"
    evidence = attempt_dir / "report-artifacts"
    log = attempt_dir / "runner.log"
    commands = []
    failure = None
    result = None
    report_data = None
    def record_launch(process):
        immutable_json(attempt_dir / "launched.json", {"schema_version": 1, "attempt_id": attempt_id,
                        "event": "launched", "runner_pid": process.pid,
                        "process_group": process.pid, "at_utc": datetime.now(timezone.utc).isoformat(),
                        "candidate_sha256": frozen["binary_sha256"], "target_pin": PIN,
                        "contract_sha256": attempt["contract_sha256"]})

    try:
        result = run_bounded([str(candidate), "test", "--report", report.relative_to(ROOT).as_posix(),
                              "--artifacts-dir", evidence.relative_to(ROOT).as_posix(),
                              contract.relative_to(ROOT).as_posix()], ROOT, env, log,
                             time.monotonic() + 120, commands, operation=f"JOE {case['id']} rc.6 scenario",
                             on_start=record_launch)
        report_data = json.loads(report.read_text(encoding="utf-8"))
        rows = report_data.get("results", [])
        row = rows[0] if len(rows) == 1 else {}
        if (report_data.get("runner_version") != freeze["version"] or
            report_data.get("summary") != {"total": 1, "passed": 1, "failed": 0, "cancelled": 0, "not_run": 0} or
            row.get("status") != "passed" or not row.get("cleanup", {}).get("confirmed_exited") or
            not row.get("workspace", {}).get("cleaned")):
            raise RuntimeError("report lacks a passing exact-state case with confirmed target and workspace cleanup")
        states = {step.get("state", {}).get("path"): step.get("status")
                  for step in row.get("steps", []) if "state" in step}
        expected_state_paths = set(case["expected"])
        if set(states) != expected_state_paths or any(states[name] != "passed" for name in expected_state_paths):
            raise RuntimeError("exact state assertions do not match the independently declared output set")
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    finish = {"schema_version": 1, "attempt_id": attempt_id, "event": "finished",
              "at_utc": datetime.now(timezone.utc).isoformat(),
              "runner_command": commands[-1] if commands else None,
              "report_sha256": sha256(report) if report.is_file() else None,
              "runner_log_sha256": sha256(log) if log.is_file() else None,
              "process_tree_cleanup": result.get("process_tree_cleanup") if result else None,
              "failure": failure}
    immutable_json(attempt_dir / "finished.json", finish)
    if failure:
        raise RuntimeError(f"{case['id']} attempt {attempt_id} failed: {failure}; evidence retained at {attempt_dir.relative_to(ROOT)}")
    immutable_json(attempt_dir / "receipt.json", {"schema_version": 1, "attempt_id": attempt_id,
                    "project": "joe", "scenario_id": case["id"], "host": host, "phase": phase,
                    "repetition": repetition, "status": "passed", "report_sha256": sha256(report),
                    "runner_log_sha256": sha256(log), "candidate_archive_sha256": frozen["archive_sha256"],
                    "runner_binary_sha256": frozen["binary_sha256"], "target_pin": PIN,
                    "target_binary_sha256": build["binary_sha256"],
                    "target_cleanup": report_data["results"][0]["cleanup"],
                    "workspace_cleanup": report_data["results"][0]["workspace"],
                    "runner_process_group_cleanup": result["process_tree_cleanup"]})
    print(case["id"], phase, host, "r", repetition, "passed", attempt_id, flush=True)


def retain_build_evidence(host):
    """Copy the exact native target identity and logs before owned-tree cleanup."""
    build_root = RAW / "active/joe"
    build_path = build_root / "build.json"
    runtime_path = build_root / "runtime.json"
    acquisition_path = build_root / "acquisition.json"
    target = build_root / "install/bin/joe"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
    if build.get("project") != "joe" or build.get("pin") != PIN or acquisition.get("pin") != PIN:
        raise ValueError("native build/source evidence identity differs")
    if target.is_symlink() or sha256(target) != build.get("binary_sha256"):
        raise ValueError("native JOE binary differs from the build receipt")
    if acquisition.get("archive_sha256") != "5e00e2621225a304061c70903ef6490a700a4bbf1fa600c096b5bbb6746f2312":
        raise ValueError("native source acquisition archive differs from the reviewed pin")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if not run_id or not run_id.isdecimal():
        raise ValueError("build evidence retention requires the hosted workflow run ID")
    destination = RAW / f"joe/scenario-development/build-readback/{host}/{run_id}"
    destination.mkdir(parents=True, exist_ok=False)
    files = {"build.json": build_path, "runtime.json": runtime_path,
             "acquisition.json": acquisition_path, "source.tar.gz": build_root / "source.tar.gz",
             "target-joe": target}
    rows = []
    for name, source in files.items():
        if source.is_symlink() or not source.is_file():
            raise ValueError("required regular build evidence is absent: " + str(source))
        copied = destination / name
        shutil.copyfile(source, copied)
        if sha256(source) != sha256(copied):
            raise ValueError("build evidence copy hash mismatch: " + name)
        rows.append({"path": name, "bytes": copied.stat().st_size, "sha256": sha256(copied)})
    log_rows = []
    for source in sorted((build_root / "build-logs").glob("*.log")):
        if source.is_symlink() or not source.is_file():
            raise ValueError("native build log is not a regular file")
        copied = destination / "build-logs" / source.name
        copied.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, copied)
        log_rows.append({"path": copied.relative_to(destination).as_posix(),
                         "bytes": copied.stat().st_size, "sha256": sha256(copied)})
    if len(log_rows) != 7:
        raise ValueError("expected all seven native JOE build command logs")
    immutable_json(destination / "retained-build-evidence.json", {
        "schema_version": 1, "project": "joe", "pin": PIN, "host": host,
        "architecture": build["architecture"], "binary_sha256": build["binary_sha256"],
        "build_receipt_sha256": sha256(build_path), "runtime_receipt_sha256": sha256(runtime_path),
        "acquisition_receipt_sha256": sha256(acquisition_path), "archive_sha256": acquisition["archive_sha256"],
        "files": rows, "build_logs": log_rows, "command_count": len(build.get("commands", [])),
        "source_cleanup_pending": True, "project_admission_credit": 0})
    print("Retained exact JOE native build identity, binary and seven command logs:", destination, flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--materialize", action="store_true")
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    parser.add_argument("--phase", choices=("scenario-development", "final-qualification"), default="scenario-development")
    parser.add_argument("--case", action="append")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--retain-build-evidence", action="store_true")
    args = parser.parse_args()
    if args.materialize:
        materialize()
        print("Materialized the twenty frozen JOE specs and fixtures")
        return
    if args.verify_only:
        verify_declarations()
        print("Frozen JOE scenario declaration verified")
        return
    actual = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    if actual != args.host:
        raise RuntimeError(f"native host mismatch: expected {args.host}, got {actual}")
    if not 1 <= args.repetitions <= 12:
        raise ValueError("scenario repetition count must be from one through twelve")
    verify_declarations()
    if args.retain_build_evidence:
        retain_build_evidence(args.host)
        return
    declared = cases()
    selected = [case for case in declared if not args.case or case["id"] in args.case]
    if args.case and {case["id"] for case in selected} != set(args.case):
        raise ValueError("unknown case ID")
    outcomes=[]
    unlaunched_hashes=[]
    for repetition in range(args.repetitions):
        for case in selected:
            case_root=RAW/f"joe/{args.phase}/{args.host}/{case['id']}"
            before=set(case_root.iterdir()) if case_root.is_dir() else set()
            try:
                run_one(case,args.host,args.phase,repetition)
                outcomes.append({"scenario_id":case["id"],"repetition":repetition,"status":"passed"})
            except Exception as error:
                created=sorted((case_root.iterdir() if case_root.is_dir() else []),key=lambda p:p.name)
                created=[path for path in created if path not in before]
                row={"scenario_id":case["id"],"repetition":repetition,"status":"failed",
                     "error":f"{type(error).__name__}: {error}"}
                if len(created)==1 and created[0].is_dir():
                    attempt_dir=created[0]
                    attempt=json.loads((attempt_dir/"attempt.json").read_text(encoding="utf-8"))
                    finished=json.loads((attempt_dir/"finished.json").read_text(encoding="utf-8"))
                    report_path=attempt_dir/"report.json"
                    if report_path.is_file():
                        report=json.loads(report_path.read_text(encoding="utf-8"))
                        results=report.get("results",[])
                        if (not (attempt_dir/"launched.json").exists() and len(results)==1 and
                                workspace_setup_failure_before_launch(report,results[0])):
                            report_hash=sha256(report_path)
                            unlaunched_hashes.append(report_hash)
                            row.update({"attempt_id":attempt["attempt_id"],"report_sha256":report_hash,
                                        "prelaunch_workspace_setup_failure":True})
                    row.setdefault("attempt_id",attempt.get("attempt_id"))
                    row.setdefault("report_sha256",finished.get("report_sha256"))
                outcomes.append(row)
                print(case["id"],"retained first failure:",row.get("error"),flush=True)
    run_id=os.environ.get("GITHUB_RUN_ID")
    if not run_id or not run_id.isdecimal():
        raise ValueError("development batch accounting requires a hosted workflow run ID")
    batch_path=RAW/f"joe/scenario-development-batches/{args.host}/{run_id}.json"
    immutable_json(batch_path,{"schema_version":1,"project":"joe","host":args.host,
        "workflow_run":int(run_id),"phase":args.phase,"candidate":"v0.4.0-rc.6",
        "scenario_declaration_sha256":hashlib.sha256(DECLARATION.read_bytes()).hexdigest(),
        "selected_scenarios":len(selected),"repetitions":args.repetitions,
        "outcomes":outcomes,"unlaunched_report_sha256":unlaunched_hashes,
        "passed":sum(row["status"]=="passed" for row in outcomes),
        "failed":sum(row["status"]=="failed" for row in outcomes),
        "project_admission_credit":0})
    if any(row["status"]!="passed" for row in outcomes):
        raise RuntimeError(f"JOE scenario development had {sum(row['status']=='failed' for row in outcomes)} retained failures on {args.host}; batch={batch_path.relative_to(ROOT)}")
    print(f"JOE {args.phase}: {len(selected)} scenarios x {args.repetitions} repetitions passed on {args.host}; no admission credit", flush=True)


if __name__ == "__main__":
    main()
