"""Run one immutable JOE baseline/fault/rebuilt-recovery calibration per host."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import uuid

from next20_check import DOC, RAW, ROOT
from next20_joe_build import PIN, source_map
from next20_mg_build import MAX_OUTPUT, run_bounded
from next20_joe_scenarios import cases, run_one
from readiness_evidence import immutable_json, sha256

MAX_CALIBRATION_SECONDS = 60 * 60
MAX_SOURCE_FILES = 10000
MAX_SOURCE_BYTES = 64 * 1024**2
FAULT_DECLARATION = DOC / "joe" / "fault-declaration-v1.json"


def require(value, message):
    if not value:
        raise ValueError(message)


def load_faults():
    declaration = json.loads(FAULT_DECLARATION.read_text(encoding="utf-8"))
    require(declaration.get("project") == "joe" and declaration.get("pin") == PIN and
            declaration.get("candidate") == "v0.4.0-rc.6" and
            declaration.get("scenario_declaration_sha256") == sha256(DOC / "joe" / "scenario-declaration-v3.json") and
            len(declaration.get("faults", [])) == 3,
            "frozen JOE fault declaration identity/count differs")
    rows = {row["id"]: row for row in declaration["faults"]}
    require(len(rows) == 3 and len(set(rows)) == 3, "JOE fault IDs must be unique")
    for fault in rows.values():
        path = (DOC / "joe" / fault["patch"]).resolve(strict=True)
        require(path.is_relative_to((DOC / "joe").resolve(strict=True)) and
                sha256(path) == fault.get("patch_sha256"), "JOE fault patch hash/path differs")
        source_path = (DOC / "joe" / "scenarios-v3" / fault["scenario_id"] / "scenario.json")
        spec = json.loads(source_path.read_text(encoding="utf-8"))
        require(1 <= fault.get("expected_failure_step", 0) <= len(spec.get("steps", [])) and
                fault.get("expected_failure_categories") and
                all(isinstance(category, str) for category in fault["expected_failure_categories"]),
                "JOE fault expected failure is not bound to a real frozen scenario step/category")
        old = base64.b64decode(fault["mutation_old_base64"], validate=True)
        new = base64.b64decode(fault["mutation_new_base64"], validate=True)
        require(old and new and old != new, "JOE source fault has an empty or no-op byte mutation")
    return declaration, rows


def bounded_command(argv, label, log, commands, deadline):
    return run_bounded(argv, ROOT, dict(os.environ), log, deadline, commands,
                       operation="JOE fault " + label)


def retain_phase_inputs(evidence, phase_name, target, acquisition, build):
    phase_root = evidence / phase_name
    phase_root.mkdir(parents=True, exist_ok=False)
    for name in ("acquisition.json", "source.tar.gz", "build.json", "runtime.json"):
        source = target / name
        require(source.is_file() and not source.is_symlink(), "missing regular JOE phase identity: " + name)
        shutil.copyfile(source, phase_root / name)
        require(sha256(source) == sha256(phase_root / name), "JOE phase receipt copy hash differs: " + name)
    for name in ("build-logs",):
        source = target / name
        require(source.is_dir() and not source.is_symlink(), "missing JOE build logs")
        shutil.copytree(source, phase_root / name)
    binary = target / "install" / "bin" / "joe"
    require(binary.is_file() and not binary.is_symlink() and sha256(binary) == build["binary_sha256"],
            "built JOE binary differs from its build receipt")
    (phase_root / "install").mkdir()
    (phase_root / "install" / "bin").mkdir()
    shutil.copyfile(binary, phase_root / "install" / "bin" / "joe")
    require(sha256(binary) == sha256(phase_root / "install" / "bin" / "joe"),
            "retained JOE executable hash differs")
    if build.get("source_mutation"):
        mutation = build["source_mutation"]
        mutant = target / "src" / Path(mutation["source_file"])
        dest = phase_root / "mutated-source" / Path(mutation["source_file"])
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(mutant, dest)
        require(sha256(mutant) == sha256(dest) == mutation["actual_mutated_source_sha256"],
                "retained JOE mutated source bytes differ")
    return phase_root


def cleanup_target(phase_name, evidence, commands, deadline):
    log = evidence / f"{phase_name}-cleanup.log"
    fault_id = evidence.parents[1].name
    window = f"rebuild-{fault_id}-{phase_name}"[:63]
    bounded_command([sys.executable, "-B", "scripts/acceptance/next20_target_cleanup.py",
                     "--project", "joe", "--window", window],
                    phase_name + " owned source cleanup", log, commands, deadline)
    active = RAW / "active" / "joe"
    require(not active.exists(), "owned JOE source/build tree remains after cleanup")
    return {"status": "owned target tree removed", "cleanup_window": window,
            "cleanup_command_id": commands[-1]["id"],
            "cleanup_log_sha256": sha256(log), "cleanup_log_bytes": log.stat().st_size,
            "active_target_absent": True}


def phase(host, fault, phase_name, evidence, commands, deadline):
    acquisition_log = evidence / f"{phase_name}-acquire.log"
    bounded_command([sys.executable, "-B", "scripts/acceptance/next20_acquire.py", "joe"],
                    phase_name + " source acquisition", acquisition_log, commands, deadline)
    target = RAW / "active" / "joe"
    source = target / "src"
    acquisition = json.loads((target / "acquisition.json").read_text(encoding="utf-8"))
    original_map = source_map(source)
    require(acquisition.get("pin") == PIN and
            acquisition.get("archive_sha256") == fault["source_archive_sha256"] and
            original_map == acquisition.get("source_files"),
            "fresh JOE source map/archive does not match the frozen pin")

    original_bytes = None
    mutation_applied = False
    mutation = None
    try:
        if phase_name == "fault":
            mutation = fault
            relative = Path(fault["source_file"])
            source_path = (source / relative).resolve(strict=True)
            source_path.relative_to(source.resolve(strict=True))
            original_bytes = source_path.read_bytes()
            require(hashlib.sha256(original_bytes).hexdigest() == fault["baseline_source_sha256"],
                    "JOE source file differs from frozen mutation baseline")
            old = base64.b64decode(fault["mutation_old_base64"], validate=True)
            new = base64.b64decode(fault["mutation_new_base64"], validate=True)
            require(original_bytes.count(old) == 1, "JOE mutation anchor is no longer unique")
            mutated_bytes = original_bytes.replace(old, new, 1)
            require(hashlib.sha256(mutated_bytes).hexdigest() == fault["mutated_source_sha256"],
                    "JOE declared mutation output hash differs")
            source_path.write_bytes(mutated_bytes)
            mutation_applied = True
            require(sha256(source_path) == fault["mutated_source_sha256"], "JOE source mutation write hash differs")
        build_log = evidence / f"{phase_name}-build.log"
        build_argv = [sys.executable, "-B", "scripts/acceptance/next20_joe_build.py",
                      "--expected-host", host]
        if phase_name == "fault":
            build_argv += ["--source-fault-manifest", (DOC / "joe" / "faults" / f"{fault['id']}.json").relative_to(ROOT).as_posix()]
        bounded_command(build_argv, phase_name + " native build", build_log, commands, deadline)
        build = json.loads((target / "build.json").read_text(encoding="utf-8"))
        build_source_map = source_map(target / "src")
        expected_source_map = dict(original_map)
        if phase_name == "fault":
            expected_source_map[fault["source_file"]] = fault["mutated_source_sha256"]
            mutation_receipt = build.get("source_mutation") or {}
            require(mutation_receipt.get("id") == fault["id"] and
                    mutation_receipt.get("actual_mutated_source_sha256") == fault["mutated_source_sha256"],
                    "JOE mutated build receipt does not bind the frozen fault")
        else:
            require(build.get("source_mutation") is None, "pristine JOE build has a source mutation receipt")
        require(build_source_map == expected_source_map and build.get("pin") == PIN and
                build.get("source_archive_sha256") == acquisition["archive_sha256"],
                "JOE build source/archive identity differs from its declared phase")
        phase_root = retain_phase_inputs(evidence, phase_name, target, acquisition, build)
        case = next(item for item in cases() if item["id"] == fault["scenario_id"])
        scenario = run_one(case, host, f"fault-{fault['id']}-{phase_name}",
                           target_fault=fault if phase_name == "fault" else None)
        if phase_name == "fault":
            require(scenario["status"] == "expected-target-fault-rejection" and
                    scenario["failure_category"] in fault["expected_failure_categories"],
                    "unchanged JOE contract did not reject the declared source fault as expected")
        else:
            require(scenario["status"] == "passed", "pristine JOE baseline/recovery scenario did not pass")
        retained = {"phase": phase_name, "source_archive_sha256": acquisition["archive_sha256"],
                    "source_file_count": len(original_map),
                    "source_map_sha256": hashlib.sha256(json.dumps(build_source_map, sort_keys=True,
                        ensure_ascii=True, separators=(",", ":")).encode()).hexdigest(),
                    "source_mutation": build.get("source_mutation"),
                    "native_binary_sha256": build["binary_sha256"],
                    "build_receipt_sha256": sha256(target / "build.json"),
                    "runtime_receipt_sha256": sha256(target / "runtime.json"),
                    "scenario": scenario, "retained_phase_inputs": phase_root.relative_to(ROOT).as_posix()}
        immutable_json(phase_root / "phase-receipt.json", retained)
        return retained
    finally:
        if mutation_applied and original_bytes is not None:
            source_path.write_bytes(original_bytes)
            require(sha256(source_path) == fault["baseline_source_sha256"],
                    "JOE fault source could not be restored byte-for-byte before target cleanup")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    parser.add_argument("--fault", required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    declaration, faults = load_faults()
    if args.verify_only:
        print(json.dumps({"project": "joe", "fault_count": len(faults),
                          "fault_declaration_sha256": sha256(FAULT_DECLARATION),
                          "status": "frozen JOE fault declaration verified"}, sort_keys=True))
        return
    actual_host = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    require(actual_host == args.host, f"native JOE host mismatch: expected {args.host}, got {platform.system()}")
    require(args.fault in faults, "undeclared JOE target fault")
    fault = faults[args.fault]
    run_id = uuid.uuid4().hex
    evidence = RAW / "joe" / "fault-calibrations" / args.fault / args.host / run_id
    evidence.mkdir(parents=True, exist_ok=False)
    commands = []
    started = time.monotonic()
    deadline = started + MAX_CALIBRATION_SECONDS
    receipt = {"schema_version": 1, "project": "joe", "pin": PIN,
               "candidate": "v0.4.0-rc.6", "fault_declaration_sha256": sha256(FAULT_DECLARATION),
               "attempt_id": run_id, "fault": args.fault, "host": args.host,
               "architecture": platform.machine(),
               "scenario_id": fault["scenario_id"],
               "scenario_contract_sha256": sha256(DOC / "joe" / "scenarios-v3" / fault["scenario_id"] / "scenario.json"),
               "target_source_archive_sha256": fault["source_archive_sha256"],
               "mutation_manifest_sha256": sha256(DOC / "joe" / "faults" / f"{fault['id']}.json"),
               "expected_phases": ["baseline", "fault", "recovery"],
               "expected_phase_count": 3,
               "run_id": run_id, "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "phases": [], "cleanup": [], "status": "in_progress", "project_admission_credit": 0}
    immutable_json(evidence / "calibration-start.json", receipt)
    fault_tree_open = False
    recovery_complete = False
    try:
        for phase_name in ("baseline", "fault", "recovery"):
            if phase_name == "fault":
                fault_tree_open = True
            row = phase(args.host, fault, phase_name, evidence, commands, deadline)
            receipt["phases"].append(row)
            cleanup = cleanup_target(phase_name, evidence, commands, deadline)
            receipt["cleanup"].append({"phase": phase_name, **cleanup})
            if phase_name == "fault":
                fault_tree_open = False
            if phase_name == "recovery":
                recovery_complete = True
        require(len(receipt["phases"]) == 3 and recovery_complete,
                "JOE source-fault calibration did not complete baseline, fault and recovery")
        receipt["status"] = "three-phase-source-fault-calibration-passed"
    except Exception as error:
        receipt["status"] = "source-fault-calibration-incomplete"
        receipt["error"] = f"{type(error).__name__}: {error}"[:2048]
        target = RAW / "active" / "joe"
        if target.exists():
            try:
                if fault_tree_open and not recovery_complete:
                    cleanup_target("failed-fault", evidence, commands, deadline)
                    recovery = phase(args.host, fault, "recovery", evidence, commands, deadline)
                    receipt["failure_recovery"] = recovery
                    receipt["cleanup"].append({"phase": "failure-recovery", **cleanup_target("failure-recovery", evidence, commands, deadline)})
                    receipt["failure_recovery_status"] = "exact source reacquired and normally rebuilt; unchanged contract passed"
                else:
                    receipt["failure_cleanup"] = cleanup_target("failed-attempt", evidence, commands, deadline)
            except Exception as cleanup_error:
                receipt["restoration_or_cleanup_error"] = f"{type(cleanup_error).__name__}: {cleanup_error}"[:2048]
        raise
    finally:
        receipt["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        receipt["duration_seconds"] = round(time.monotonic() - started, 3)
        receipt["commands"] = commands
        immutable_json(evidence / "calibration-finished.json", receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
