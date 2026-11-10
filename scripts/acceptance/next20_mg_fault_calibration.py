"""Run one mg target mutation as native baseline, fault, and restoration phases."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import subprocess
import sys
import time
import uuid

from next20_check import DOC, RAW, ROOT
from next20_mg_build import MAX_OUTPUT, PIN, run_bounded
from readiness_evidence import immutable_json, sha256


MUTATIONS = {
    "save-no-write": {"contract": "n02-edit-append.json", "source_fault": "save-no-write",
                      "requires_state_failure": True},
    "delete-byte-corruption": {"contract": "n03-query-replace.json", "source_fault": "delete-byte-corruption",
                                "requires_state_failure": False},
    "readonly-edit-accepted": {"contract": "e06-readonly-buffer.json", "source_fault": "readonly-edit-accepted",
                               "requires_state_failure": False},
    "undo-delete-omitted": {"contract": "n05-undo-redo.json", "source_fault": "undo-delete-omitted",
                             "requires_state_failure": False},
}
MAX_CALIBRATION_SECONDS = 20 * 60
MAX_TREE_FILES = 10000
MAX_TREE_BYTES = 256 * 1024**2


def inventory(root):
    files = total = 0
    for directory, names, filenames in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in names + filenames:
            path = base / name
            mode = path.lstat().st_mode
            if not stat.S_ISDIR(mode) and not stat.S_ISREG(mode):
                raise ValueError(f"unexpected linked or special owned mg entry: {path}")
            if stat.S_ISREG(mode):
                files += 1
                total += path.stat().st_size
                if files > MAX_TREE_FILES or total > MAX_TREE_BYTES:
                    raise ValueError("owned mg cleanup inventory exceeded its fixed bound")
    return files, total


def remove_owned_target():
    active = RAW / "active"
    target = active / "mg"
    if active.is_symlink() or getattr(active, "is_junction", lambda: False)():
        raise ValueError("active target root is linked")
    active.mkdir(parents=True, exist_ok=True)
    active_resolved = active.resolve(strict=True)
    if target.is_symlink() or getattr(target, "is_junction", lambda: False)():
        raise ValueError("refusing linked mg cleanup root")
    if target.resolve() != active_resolved / "mg":
        raise ValueError("mg cleanup root differs from the exact active/mg path")
    if not target.exists():
        return {"present": False, "removed": True, "files": 0, "bytes": 0}
    if set(p.name for p in active.iterdir()) != {"mg"}:
        raise ValueError("refusing cleanup while another active target is present")
    owner_path = target / "task-owned.json"
    owner = json.loads(owner_path.read_text(encoding="utf-8"))
    if (owner.get("workspace") != str(ROOT) or owner.get("slug") != "mg" or
            owner.get("pin") != PIN or owner.get("project") != "troglobit/mg"):
        raise ValueError("refusing to remove an unowned or wrong-pin mg tree")
    files, size = inventory(target)
    shutil.rmtree(target)
    if target.exists():
        raise RuntimeError("owned mg source/build root remains after cleanup")
    return {"present": True, "removed": True, "files": files, "bytes": size}


def source_map(source):
    rows = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError(f"linked source path: {path.relative_to(source)}")
        if path.is_file():
            rows[path.relative_to(source).as_posix()] = sha256(path)
    return rows


def run_command(label, argv, log, deadline, commands, *, expected_failure=False):
    try:
        row = run_bounded(argv, ROOT, dict(os.environ), log, deadline, commands,
                          operation=f"mg fault {label}")
        if expected_failure:
            raise RuntimeError(f"fault scenario unexpectedly passed: {label}")
        return {"exit_code": row["exit_code"], "process_tree_cleanup": row["process_tree_cleanup"],
                "log_sha256": row["output_sha256"], "log_bytes": row["output_bytes"]}
    except RuntimeError:
        if not expected_failure:
            raise
        row = commands[-1] if commands else None
        if not row or row.get("exit_code") == 0:
            raise
        return {"exit_code": row["exit_code"], "process_tree_cleanup": row["process_tree_cleanup"],
                "log_sha256": row["output_sha256"], "log_bytes": row["output_bytes"],
                "expected_contract_rejection": True}


def find_new_attempt(host, scenario_id, before):
    parent = RAW / "mg" / "scenario-development" / host / scenario_id
    found = [p for p in parent.iterdir() if p.is_dir() and p.name not in before] if parent.exists() else []
    if len(found) != 1:
        raise RuntimeError(f"expected one new scenario attempt directory, found {len(found)}")
    return found[0]


def execute_scenario(host, contract, phase, fault, evidence, deadline, commands):
    scenario_id = Path(contract).stem
    parent = RAW / "mg" / "scenario-development" / host / scenario_id
    before = {p.name for p in parent.iterdir() if p.is_dir()} if parent.exists() else set()
    log = evidence / f"{phase}-scenario-command.log"
    argv = [sys.executable, "-B", "scripts/acceptance/next20_mg_scenario.py",
            "--host", host, "--mg-build-root", RAW.relative_to(ROOT).as_posix(),
            "--spec", (DOC / "mg" / contract).relative_to(ROOT).as_posix()]
    command_result = run_command(f"{phase} scenario", argv, log, deadline, commands,
                                 expected_failure=(phase == "fault"))
    attempt_dir = find_new_attempt(host, scenario_id, before)
    report_path = attempt_dir / "report.json"
    attempt = json.loads((attempt_dir / "attempt.json").read_text(encoding="utf-8"))
    report = json.loads(report_path.read_text(encoding="utf-8"))
    results = report.get("results", [])
    if len(results) != 1:
        raise RuntimeError(f"{phase} scenario did not produce exactly one result")
    result = results[0]
    steps = result.get("steps", [])
    cleanup = result.get("cleanup", {})
    target_result = result.get("target", {})
    workspace = result.get("workspace", {})
    if (not target_result.get("exited") or not cleanup.get("attempted") or
            not cleanup.get("confirmed_exited") or not workspace.get("cleaned")):
        raise RuntimeError(f"{phase} scenario lacks clean target exit and workspace cleanup evidence")
    if phase != "fault" and (target_result.get("exit_code") != 0 or cleanup.get("forced")):
        raise RuntimeError(f"{phase} pristine scenario did not exit cleanly without force")
    if phase == "fault":
        if result.get("status") != "failed" or not any(row.get("status") == "failed" for row in steps):
            raise RuntimeError("fault was not rejected by a public scenario assertion")
        launched_path = attempt_dir / "launched.json"
        launched = json.loads(launched_path.read_text(encoding="utf-8")) if launched_path.is_file() else {}
        if (attempt.get("target_pin") != PIN or not launched.get("target_attempted") or
                not launched.get("target_confirmed_exited")):
            raise RuntimeError("fault rejection lacks pinned target or launch evidence")
        if fault["requires_state_failure"]:
            state_rows = [row for row in steps if row.get("action") == "state"]
            if (len(state_rows) != 1 or state_rows[0].get("status") != "failed" or
                    any(row.get("status") != "passed" for row in steps[:state_rows[0]["number"] - 1])):
                raise RuntimeError("save fault did not preserve passing screen/exit evidence before state rejection")
    else:
        if (result.get("status") != "passed" or
                any(row.get("status") != "passed" for row in steps) or
                report.get("summary", {}).get("passed") != 1):
            raise RuntimeError(f"{phase} pristine scenario did not pass every public step")
    return {"phase": phase, "scenario_id": scenario_id, "attempt_id": attempt["attempt_id"],
            "attempt_path": attempt_dir.relative_to(ROOT).as_posix(),
            "attempt_sha256": sha256(attempt_dir / "attempt.json"),
            "report_sha256": sha256(report_path), "runner_log_sha256": sha256(attempt_dir / "runner.log"),
            "contract_sha256": attempt["contract_sha256"], "target_binary_sha256": attempt["target_binary_sha256"],
            "result": result.get("status"), "step_count": len(steps),
            "failed_steps": [row.get("number") for row in steps if row.get("status") == "failed"],
            "target_exit": result.get("target"), "target_cleanup": result.get("cleanup"),
            "workflow_command": command_result}


def phase(host, phase_name, fault, evidence, deadline, commands):
    start = time.monotonic()
    run_command(f"{phase_name} source acquisition",
                [sys.executable, "-B", "scripts/acceptance/next20_acquire.py", "mg"],
                evidence / f"{phase_name}-acquire.log", deadline, commands)
    source = RAW / "active" / "mg" / "src"
    acquired = json.loads((RAW / "active" / "mg" / "acquisition.json").read_text(encoding="utf-8"))
    original_map = source_map(source)
    if original_map != acquired.get("source_files"):
        raise RuntimeError("fresh source map differs from pinned acquisition receipt")
    if phase_name == "fault":
        mutation = fault["source_fault"]
        argv = [sys.executable, "-B", "scripts/acceptance/next20_mg_build.py",
                "--expected-host", host, "--fault-mutation", mutation]
    else:
        mutation = None
        argv = [sys.executable, "-B", "scripts/acceptance/next20_mg_build.py", "--expected-host", host]
    run_command(f"{phase_name} native build", argv, evidence / f"{phase_name}-build-command.log", deadline, commands)
    build_path = RAW / "active" / "mg" / "build.json"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    if (build.get("source_archive_sha256") != acquired.get("archive_sha256") or
            build.get("source_map_sha256") != sha_map(original_map)):
        raise RuntimeError("native build receipt does not bind the pristine pinned source map")
    mutation_row = build.get("source_mutation")
    if phase_name == "fault" and (not mutation_row or mutation_row.get("id") != mutation):
        raise RuntimeError("fault build receipt does not bind the selected source mutation")
    if phase_name == "fault":
        if (mutation_row.get("original_sha256") != original_map.get(mutation_row.get("path")) or
                sha256(source / mutation_row["path"]) != mutation_row.get("mutated_sha256")):
            raise RuntimeError("fault build mutation hashes do not match the acquired source and executed source")
    if phase_name != "fault" and mutation_row is not None:
        raise RuntimeError("baseline/recovery build unexpectedly contains a source mutation")
    scenario = execute_scenario(host, fault["contract"], phase_name, fault, evidence, deadline, commands)
    build_copy = evidence / f"{phase_name}-build-receipt.json"
    build_copy.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")
    receipt = {"phase": phase_name, "source_archive_sha256": acquired["archive_sha256"],
               "source_file_count": len(original_map), "source_map_sha256": sha_map(original_map),
               "native_binary_sha256": build["binary_sha256"], "build_receipt_sha256": sha256(build_path),
               "build_receipt_copy": build_copy.relative_to(ROOT).as_posix(),
               "source_mutation": mutation_row, "scenario": scenario,
               "duration_seconds": round(time.monotonic() - start, 3)}
    immutable_json(evidence / f"{phase_name}-receipt.json", receipt)
    return receipt


def sha_map(rows):
    import hashlib
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    parser.add_argument("--fault", choices=tuple(MUTATIONS), required=True)
    args = parser.parse_args()
    host = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    if host != args.host:
        raise RuntimeError(f"expected native {args.host}, got {platform.system()}")
    fault = MUTATIONS[args.fault]
    run_id = uuid.uuid4().hex
    evidence = RAW / "mg" / "fault-calibrations" / args.fault / host / run_id
    evidence.mkdir(parents=True, exist_ok=False)
    started = time.monotonic()
    deadline = started + MAX_CALIBRATION_SECONDS
    commands = []
    phase_cleanups = []
    fault_tree_open = False
    receipt = {"schema_version": 1, "project": "mg", "pin": PIN, "candidate": "v0.4.0-rc.6",
               "fault": args.fault, "host": host, "architecture": platform.machine(),
               "run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "phases": [], "status": "in_progress", "admission_credit": 0}
    immutable_json(evidence / "calibration-start.json", receipt)
    try:
        for phase_name in ("baseline", "fault", "recovery"):
            remove_owned_target()
            if phase_name == "fault":
                fault_tree_open = True
            receipt["phases"].append(phase(host, phase_name, fault, evidence, deadline, commands))
            phase_cleanups.append({"phase": phase_name, **remove_owned_target()})
            if phase_name == "recovery":
                fault_tree_open = False
        receipt["phase_cleanups"] = phase_cleanups
        if len(receipt["phases"]) != 3:
            raise RuntimeError("calibration did not complete all three phases")
        receipt["status"] = "calibration-passed"
    except Exception as error:
        receipt["status"] = "calibration-incomplete"
        receipt["error"] = f"{type(error).__name__}: {error}"[:2048]
        try:
            receipt["failure_cleanup"] = remove_owned_target()
        except Exception as cleanup_error:
            receipt["restoration_cleanup_error"] = f"{type(cleanup_error).__name__}: {cleanup_error}"[:1024]
        if fault_tree_open:
            try:
                run_command("failure source restoration acquisition",
                            [sys.executable, "-B", "scripts/acceptance/next20_acquire.py", "mg"],
                            evidence / "failure-source-restoration.log", deadline, commands)
                source = RAW / "active" / "mg" / "src"
                acquired = json.loads((RAW / "active" / "mg" / "acquisition.json").read_text(encoding="utf-8"))
                restored = source_map(source)
                expected = json.loads((DOC / "mg" / "source-provenance.json").read_text(encoding="utf-8"))["source_file_sha256"]
                if restored != expected or restored != acquired.get("source_files"):
                    raise RuntimeError("freshly reacquired source does not match the approved pin")
                receipt["failure_source_restoration"] = {"status": "exact pin source restored and hash-verified",
                                                          "archive_sha256": acquired["archive_sha256"],
                                                          "source_map_sha256": sha_map(restored),
                                                          "source_file_count": len(restored)}
                receipt["failure_restoration_cleanup"] = remove_owned_target()
            except Exception as restoration_error:
                receipt["failure_source_restoration_error"] = f"{type(restoration_error).__name__}: {restoration_error}"[:2048]
        raise
    finally:
        receipt["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        receipt["duration_seconds"] = round(time.monotonic() - started, 3)
        receipt["commands"] = commands
        immutable_json(evidence / "calibration-finished.json", receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
