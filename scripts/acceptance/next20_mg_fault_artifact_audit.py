"""Independently recheck mg's native fault-calibration provider packets."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

from next20_check import DOC, ROOT
from next20_mg_final_artifact_audit import REPO, artifact_index, gh_json, github_env
from readiness_evidence import immutable_json, sha256


RUN_ID = 42811359525
PIN = "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66"
SOURCE_ARCHIVE_SHA256 = "bd8aff8ddbf55f7d37067a9f01e6bef887a2b0f2c0699aaa08a73d7dfd6069a8"
RESTORED_MAP_SHA256 = "36120c2c102dd27b33efab95af2af79d5287fa9b2c7affd9aa8c87fea2a3505c"
ALIASES = {"save-no-write": "save", "delete-byte-corruption": "delete",
           "readonly-edit-accepted": "readonly", "undo-delete-omitted": "undo"}
RECEIPT_PHASE = {"baseline": "baseline-receipt.json", "fault": "fault-receipt.json",
                 "recovery": "recovery-receipt.json"}


def digest(value):
    return hashlib.sha256(value).hexdigest()


def find_one(names, suffix):
    matches = [name for name in names if name.endswith(suffix)]
    if len(matches) != 1:
        raise ValueError(f"expected one ZIP entry ending {suffix}; found {len(matches)}")
    return matches[0]


def member_json(archive, names, suffix):
    path = find_one(names, suffix)
    return path, json.loads(archive.read(path).decode("utf-8"))


def phase_audit(archive, names, root, cell, phase, summary, source_fault, target_map, candidate_cell):
    phase_receipt_name = root + "/" + RECEIPT_PHASE[phase]
    receipt = json.loads(archive.read(phase_receipt_name).decode("utf-8"))
    build_name = root + "/" + phase + "-build-receipt.json"
    build_bytes = archive.read(build_name)
    build = json.loads(build_bytes.decode("utf-8"))
    scenario = receipt["scenario"]
    attempt_member = find_one(names, "/" + scenario["attempt_id"] + "/attempt.json")
    attempt_dir = str(PurePosixPath(attempt_member).parent)
    attempt_path = attempt_dir + "/attempt.json"
    report_path = attempt_dir + "/report.json"
    log_path = attempt_dir + "/runner.log"
    finished_path = attempt_dir + "/finished.json"
    attempt_bytes = archive.read(attempt_path)
    report_bytes = archive.read(report_path)
    log_bytes = archive.read(log_path)
    attempt = json.loads(attempt_bytes.decode("utf-8"))
    report = json.loads(report_bytes.decode("utf-8"))
    finished = json.loads(archive.read(finished_path).decode("utf-8"))
    expected_result = "failed" if phase == "fault" else "passed"
    expected_failed_steps = [cell["fault_scenario_failed_step"]] if phase == "fault" else []
    if (receipt.get("phase") != phase or receipt.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256 or
            receipt.get("source_file_count") != 126 or receipt.get("source_map_sha256") != RESTORED_MAP_SHA256 or
            receipt.get("native_binary_sha256") != build.get("binary_sha256") or
            build.get("project") != "mg" or build.get("pin") != PIN or build.get("host") != cell["host"] or
            build.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256 or
            build.get("source_map_sha256") != RESTORED_MAP_SHA256 or
            build.get("source_map_count") != 126 or build.get("binary_sha256") != scenario.get("target_binary_sha256") or
            build.get("binary_sha256") != target_map[phase] or
            attempt.get("attempt_id") != scenario.get("attempt_id") or
            attempt.get("candidate") != "v0.4.0-rc.6" or
            attempt.get("candidate_archive_sha256") != candidate_cell["archive_sha256"] or
            attempt.get("candidate_binary_sha256") != candidate_cell["binary_sha256"] or
            attempt.get("contract_sha256") != source_fault["contract_sha256"] or
            attempt.get("contract_sha256") != scenario.get("contract_sha256") or
            scenario.get("attempt_sha256") != digest(attempt_bytes) or
            scenario.get("report_sha256") != digest(report_bytes) or
            scenario.get("runner_log_sha256") != digest(log_bytes) or
            scenario.get("result") != expected_result or scenario.get("failed_steps") != expected_failed_steps or
            scenario.get("target_cleanup", {}).get("confirmed_exited") is not True or
            "no owned descendants remain" not in scenario.get("workflow_command", {}).get("process_tree_cleanup", "") or
            finished.get("failure") != (None if phase != "fault" else finished.get("failure"))):
        raise ValueError(f"phase identity/result/hash/cleanup mismatch: {root}/{phase}")
    if phase == "fault":
        mutation = receipt.get("source_mutation") or {}
        expected = source_fault
        build_mutation = build.get("source_mutation", {})
        if (mutation.get("id") != cell["fault"] or mutation.get("path") != expected["source"] or
                mutation.get("original_sha256") != expected["source_sha256"] or
                build_mutation.get("id") != cell["fault"] or
                build_mutation != mutation or
                not build.get("mutated_source_sha256") or
                build.get("mutated_source_sha256") == RESTORED_MAP_SHA256):
            raise ValueError(f"fault mutation differs from reviewed mutation: {cell['fault']} {cell['host']}")
        expected_summary = report.get("summary", {})
        if (len(report.get("results", [])) != 1 or report["results"][0].get("status") != "failed" or
                expected_summary.get("failed") != 1 or expected_summary.get("passed") != 0):
            raise ValueError(f"fault did not fail the public contract: {root}")
    else:
        if (len(report.get("results", [])) != 1 or report["results"][0].get("status") != "passed" or
                report.get("summary", {}).get("passed") != 1):
            raise ValueError(f"pristine or restored scenario lacks a positive public result: {root}")
    report_rows = report.get("results", [])
    cleanup = report_rows[0].get("cleanup", {}) if report_rows else {}
    if not cleanup.get("confirmed_exited") or not cleanup.get("attempted"):
        raise ValueError(f"target cleanup missing in {root}/{phase}")
    if (summary.get("phase") != phase or summary.get("result") != expected_result or
            summary.get("failed_steps") != expected_failed_steps or
            summary.get("attempt_id") != scenario.get("attempt_id") or
            summary.get("attempt_sha256") != digest(attempt_bytes) or
            summary.get("report_sha256") != digest(report_bytes) or
            summary.get("runner_log_sha256") != digest(log_bytes) or
            summary.get("target_binary_sha256") != build.get("binary_sha256") or
            summary.get("process_tree_cleanup") != scenario["workflow_command"]["process_tree_cleanup"]):
        raise ValueError(f"phase summary does not match raw packet: {root}/{phase}")
    return {"phase": phase, "result": expected_result, "attempt_id": scenario["attempt_id"],
            "target_binary_sha256": build["binary_sha256"],
            "report_sha256": digest(report_bytes), "runner_log_sha256": digest(log_bytes),
            "build_receipt_sha256": digest(build_bytes),
            "target_cleanup_confirmed": True, "runner_process_tree_confirmed": True}


def main():
    readback_path = DOC / "mg-fault-calibration-readback-v2.json"
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    source_review_path = DOC / "mg-fault-source-review-v1.json"
    source_review = json.loads(source_review_path.read_text(encoding="utf-8"))
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v1.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if (readback.get("workflow_run_id") != RUN_ID or readback.get("workflow_conclusion") != "success" or
            readback.get("target_pin") != PIN or readback.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256 or
            readback.get("restored_source_map_sha256") != RESTORED_MAP_SHA256 or
            source_review.get("pin") != PIN or source_review.get("source_archive_sha256") != SOURCE_ARCHIVE_SHA256):
        raise ValueError("calibration/readback/source review identity mismatch")
    for fault in source_review["faults"]:
        contract_path = DOC / "mg" / fault["contract"]
        if sha256(contract_path) != fault["contract_sha256"]:
            raise ValueError(f"reviewed fault contract changed: {fault['contract']}")
    source_by_fault = {"save-no-write": source_review["faults"][0],
                       "delete-byte-corruption": source_review["faults"][1],
                       "readonly-edit-accepted": source_review["faults"][2],
                       "undo-delete-omitted": source_review["faults"][3]}
    env = github_env()
    run = gh_json(["run", "view", str(RUN_ID), "--json", "headSha,status,conclusion"], env)
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ValueError("fault calibration provider run is incomplete or failed")
    artifacts = artifact_index(RUN_ID, env)
    if len(artifacts) != 8:
        raise ValueError(f"expected eight native fault artifacts; found {len(artifacts)}")
    expected_artifacts = {item["artifact_id"]: item for item in readback["artifact_readback"]}
    actual_artifacts = {item["id"]: item for item in artifacts}
    if set(expected_artifacts) != set(actual_artifacts):
        raise ValueError("provider artifact IDs differ from retained calibration readback")
    artifact_root = ROOT / "artifacts/runner-readiness-next-twenty-project-pass/mg/fault-calibrations/retrieved/run-42811359525"
    audited_artifacts, audited_cells = [], []
    for cell in readback["matrix_cells"]:
        key = ALIASES[cell["fault"]] + "-" + cell["host"]
        item = next(value for value in readback["artifact_readback"] if value["key"] == key)
        provider = actual_artifacts[item["artifact_id"]]
        path = ROOT / item["retained_path"]
        blob = path.read_bytes()
        expected_digest = provider.get("digest", "").removeprefix("sha256:")
        if (provider.get("expired") or provider.get("size_in_bytes") != len(blob) or
                expected_digest != digest(blob) or item["bytes"] != len(blob) or
                item["provider_sha256"] != provider.get("digest") or
                item["retained_sha256"] != digest(blob)):
            raise ValueError(f"provider artifact size/digest mismatch: {key}")
        archive = zipfile.ZipFile(io.BytesIO(blob))
        if archive.testzip() is not None or len(archive.namelist()) != item["member_count"]:
            raise ValueError(f"provider ZIP CRC/member mismatch: {key}")
        names = archive.namelist()
        roots = [name.rsplit("/", 1)[0] for name in names
                 if name.endswith("/calibration-finished.json")]
        if len(roots) != 1:
            raise ValueError(f"expected one calibration root: {key}")
        root = roots[0]
        finished_name, finished = member_json(archive, names, "/calibration-finished.json")
        start_name, started = member_json(archive, names, "/calibration-start.json")
        if (finished.get("status") != "calibration-passed" or
                started.get("fault") != cell["fault"] or started.get("host") != cell["host"]):
            raise ValueError(f"calibration completion identity mismatch: {key}")
        source_fault = source_by_fault[cell["fault"]]
        candidate_cell = next(candidate for candidate in freeze["cells"] if candidate["host"] == cell["host"])
        if len(cell["phases"]) != 3 or len(cell["phase_cleanups"]) != 3:
            raise ValueError(f"calibration phases/cleanup missing: {key}")
        if any(not entry.get("present") or not entry.get("removed")
               for entry in cell["phase_cleanups"]):
            raise ValueError(f"owned source tree cleanup unconfirmed: {key}")
        build_hashes = {phase["phase"]: phase["target_binary_sha256"] for phase in cell["phases"]}
        phase_rows = [phase_audit(archive, names, root, cell, phase["phase"], phase,
                                  source_fault, build_hashes, candidate_cell) for phase in cell["phases"]]
        source_maps = {phase["phase"]: phase["source_map_sha256"] for phase in cell["phases"]}
        if (build_hashes["fault"] == build_hashes["baseline"] or
                any(source_map != RESTORED_MAP_SHA256 for source_map in source_maps.values())):
            raise ValueError(f"fault binary was not distinct or restored source maps mismatch: {key}")
        audited_artifacts.append({"key": key, "artifact_id": provider["id"],
                                  "bytes": len(blob), "sha256": digest(blob),
                                  "provider_digest": provider["digest"],
                                  "zip_entries": len(names), "crc": "passed"})
        audited_cells.append({"host": cell["host"], "architecture": cell["architecture"],
                              "fault": cell["fault"], "contract": cell["contract"],
                              "status": "baseline-detected-restored", "phases": phase_rows,
                              "owned_source_phase_trees_removed": 3})
    if len(audited_cells) != 8 or len(audited_artifacts) != 8:
        raise ValueError("incomplete eight-cell fault matrix audit")
    for path_text in ("scripts/acceptance/next20_mg_build.py",
                      ".github/workflows/runner-readiness-next20-mg-fault-calibration.yml"):
        blob = subprocess.run(["git", "show", f"{run['headSha']}:{path_text}"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=20, check=False)
        if blob.returncode:
            raise ValueError(f"fault workflow revision lacks {path_text}")
    source_revision = run["headSha"]
    tooling = {}
    for path_text in ("scripts/acceptance/next20_mg_build.py",
                      "scripts/acceptance/next20_mg_scenario.py",
                      ".github/workflows/runner-readiness-next20-mg-fault-calibration.yml"):
        blob = subprocess.run(["git", "show", f"{source_revision}:{path_text}"],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=20, check=False)
        if blob.returncode:
            raise ValueError(f"fault workflow revision lacks {path_text}")
        tooling[path_text] = digest(blob.stdout)
    output = {
        "schema_version": 1, "project": "mg", "status": "fault-calibration-audited",
        "admission_credit": 0, "run_id": RUN_ID, "workflow_revision": run["headSha"],
        "qualification_tooling_git_tree": tooling,
        "workflow_conclusion": run["conclusion"], "candidate": readback["candidate"],
        "target_pin": PIN, "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
        "restored_source_map_sha256": RESTORED_MAP_SHA256,
        "distinct_real_source_faults": 4, "native_cells": 8,
        "calibration_phase_executions": 24,
        "baseline_phases_passed": 8, "mutated_contract_failures_expected": 8,
        "restored_source_recoveries_passed": 8,
        "confirmed_owned_source_tree_removals": 24,
        "provider_artifacts": audited_artifacts, "cells": audited_cells,
        "retained_false_negative_attempts": readback["summary"]["false_negative_attempts_preserved_separately"],
        "provider_audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "readback": readback_path.relative_to(ROOT).as_posix(),
        "source_review": source_review_path.relative_to(ROOT).as_posix(),
    }
    destination = DOC / "mg-fault-calibration-audit-run-42811359525-v2.json"
    immutable_json(destination, output)
    print(json.dumps({"audit": destination.relative_to(ROOT).as_posix(),
                      "status": output["status"], "calibration_phases": 24,
                      "distinct_faults": 4, "provider_artifacts": 8,
                      "admission_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
