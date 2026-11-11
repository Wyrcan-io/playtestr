"""Reconstruct mg's exact-candidate cells and reject semantic model tampering."""
import copy
import hashlib
import json
import lzma
from pathlib import Path
import zipfile
import uuid

from readiness_evidence import immutable_json, sha256


ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "artifacts/runner-readiness-next-twenty-project-pass"
DOC = ROOT / "docs/validation/runner-readiness-next-twenty-project-pass"
PROJECT = DOC / "mg"
NATIVE_AUDIT = PROJECT / "final-qualification-artifact-audit-run-42980303472-v1.json"
FAULT_AUDIT = DOC / "mg-fault-calibration-audit-run-42811359525-v2.json"
DECLARATION = PROJECT / "final-qualification-declaration-v2.json"
FREEZE = DOC / "replacement-candidate-freeze-native-exit-v1.json"
BUILD_INPUT = RAW / "mg/model-controls-input-v1"
PIN = "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66"
CANDIDATE = "v0.4.0-rc.6"
HOSTS = ("linux", "darwin")


def load_build(host, native):
    filename = BUILD_INPUT / f"native-build-{host}-42815619413.zip"
    provider_name = f"next20-mg-build-{host}-42815619413"
    provider = next((row for row in native["provider_artifacts"] if row.get("name") == provider_name), None)
    require(provider is not None, "host build is absent from the native audit provider inventory")
    raw = filename.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(len(raw) == provider["size_bytes"] and digest == provider["sha256"] == provider["provider_digest"].removeprefix("sha256:"),
            "retrieved native build ZIP differs from the audited provider artifact")
    with zipfile.ZipFile(filename) as archive:
        require(archive.testzip() is None, "native build ZIP CRC validation failed")
        build = json.loads(archive.read("active/mg/build.json"))
        acquisition = json.loads(archive.read("active/mg/acquisition.json"))
        binary = archive.read("active/mg/" + build["binary_relative_path"])
        require(hashlib.sha256(binary).hexdigest() == build["binary_sha256"] and
                len(binary) == build["binary_bytes"], "native target binary digest or size differs from its receipt")
    require(build["project"] == "mg" and build["host"] == host and build["pin"] == PIN and
            build["source_archive_sha256"] == acquisition["archive_sha256"] and
            provider["source_pin"] == PIN and provider["target_binary_sha256"] == build["binary_sha256"] and
            provider["crc"] == "passed" and provider["artifact_id"] > 0,
            "native target build identity differs from its audited provider record")
    return {"binary_sha256": build["binary_sha256"], "source_archive_sha256": build["source_archive_sha256"],
            "source_file_count": build["source_map_count"], "provider_artifact_id": provider["artifact_id"],
            "provider_name": provider_name, "zip_sha256": digest, "zip_bytes": len(raw)}


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical_case(scenario_id):
    value = scenario_id.upper().replace("PILOT-", "").split("-", 1)[0]
    if value in {"E10A", "E10B"}:
        return "E10"
    return value


def expected_cell(host, native, faults, declaration, freeze, build):
    candidate_cell = next(row for row in declaration["native_cells"] if row["host"] == host)
    batches = sorted((row for row in native["batches"] if row["host"] == host), key=lambda row: row["batch"])
    require(len(batches) == 12 and [row["batch"] for row in batches] == list(range(12)),
            "native batch coverage is incomplete")
    declared = {canonical_case(row["id"]): row for row in declaration["scenarios"]}
    ordinary, extra = [], []
    seen_invocations = set()
    for batch in batches:
        require(batch["contract_executions"] == 21 and batch["canonical_scenarios"] == 20,
                "native batch branch/canonical counts differ")
        rows = batch["attempts"]
        require(len(rows) == 21, "native batch attempt inventory is incomplete")
        counts = {}
        for row in rows:
            scenario = canonical_case(row["scenario_id"])
            counts[scenario] = counts.get(scenario, 0) + 1
            require(scenario in declared, "native attempt is outside the reviewed declaration")
            require(row["attempt_id"] not in seen_invocations, "duplicate native attempt ID")
            seen_invocations.add(row["attempt_id"])
            record = {"batch": batch["batch"], "scenario": scenario,
                      "source_scenario": row["scenario_id"], "attempt_id": row["attempt_id"],
                      "contract_sha256": row["executed_contract_sha256"],
                      "report_sha256": row["report_sha256"],
                      "runner_log_sha256": row["runner_log_sha256"],
                      "passed": True, "target_exit_confirmed": row["target_exit_confirmed"],
                      "process_tree_confirmed": row["runner_process_tree_confirmed"],
                      "phase": "final-archive", "variation": batch["variation"]}
            if row["scenario_id"] == "e10b-accept-overwrite":
                extra.append(record)
            else:
                ordinary.append(record)
        require(counts == {case: 1 for case in declared} | {"E10": 2},
                "native batch has missing/duplicate scenario or E10 branch")
    require(len(ordinary) == 240 and len(extra) == 12, "ordinary/E10 branch accounting differs")

    host_faults = [row for row in faults["cells"] if row["host"] == host]
    require(len(host_faults) == 4 and len({row["fault"] for row in host_faults}) == 4,
            "four distinct native source faults are required per host")
    fault_rows = []
    seen_fault_attempts = set()
    for fault in sorted(host_faults, key=lambda row: row["fault"]):
        require(fault["owned_source_phase_trees_removed"] == 3,
                "source fault phase target cleanup is incomplete")
        require([phase["phase"] for phase in fault["phases"]] == ["baseline", "fault", "recovery"],
                "source fault lacks baseline/fault/recovery phases")
        for phase in fault["phases"]:
            attempt = phase["attempt_id"]
            require(attempt not in seen_fault_attempts and attempt not in seen_invocations,
                    "source fault attempt identity is duplicated")
            seen_fault_attempts.add(attempt)
            expected = "failed" if phase["phase"] == "fault" else "passed"
            require(phase["result"] == expected and phase["runner_process_tree_confirmed"] and
                    phase["target_cleanup_confirmed"], "source fault outcome or process cleanup differs")
            fault_rows.append({"fault": fault["fault"], "phase": phase["phase"],
                               "attempt_id": attempt, "result": expected,
                               "report_sha256": phase["report_sha256"],
                               "runner_log_sha256": phase["runner_log_sha256"],
                               "build_receipt_sha256": phase["build_receipt_sha256"],
                               "target_binary_sha256": phase["target_binary_sha256"],
                               "target_cleanup_confirmed": True,
                               "process_tree_confirmed": True})
    require(len(fault_rows) == 12, "native fault phase count differs")
    return {
        "schema_version": 1, "project": "mg", "repository": "troglobit/mg", "pin": PIN,
        "candidate": CANDIDATE, "host": host,
        "native_run": str(native["run_id"]), "native_audit_sha256": sha256(NATIVE_AUDIT),
        "fault_run": str(faults["run_id"]), "fault_audit_sha256": sha256(FAULT_AUDIT),
        "candidate_archive_sha256": candidate_cell["archive_sha256"],
        "runner_sha256": candidate_cell["binary_sha256"],
        "target_binary_sha256": build["binary_sha256"],
        "source_archive_sha256": build["source_archive_sha256"],
        "source_file_count": build["source_file_count"],
        "restored_source_map_sha256": faults["restored_source_map_sha256"],
        "normal_scenarios": declaration["normal_scenarios"],
        "edge_scenarios": declaration["edge_scenarios"],
        "ordinary": ordinary, "additional_e10_branch": extra, "faults": fault_rows,
        "project_admission_credit": 0,
    }


def validate(model, host, native, faults, declaration, freeze, build):
    expected = expected_cell(host, native, faults, declaration, freeze, build)
    require(model == expected, "actual cell model differs from the independently audited native/fault records")
    require(model["host"] == host and len(model["ordinary"]) == 240 and
            len(model["additional_e10_branch"]) == 12 and len(model["faults"]) == 12,
            "model host or execution counts differ")
    require(len({row["attempt_id"] for row in model["ordinary"] + model["additional_e10_branch"] + model["faults"]}) == 264,
            "duplicate attempt identity across ordinary, branch or fault rows")
    return {"host": host, "ordinary": 240, "additional_e10_branch": 12,
            "calibrations": 12, "distinct_real_faults": 4}


def main():
    native = json.loads(NATIVE_AUDIT.read_text(encoding="utf-8"))
    faults = json.loads(FAULT_AUDIT.read_text(encoding="utf-8"))
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    require(native["status"] == "native-matrix-audited" and
            native["run_id"] == 42980303472 and native["project_admission_credit"] == 0 and
            native["ordinary_executions"] == 480 and native["additional_e10_branch_executions"] == 24,
            "native source audit identity/counts differ")
    require(faults["status"] == "fault-calibration-audited" and faults["project"] == "mg" and
            faults["target_pin"] == PIN and faults["candidate"] == CANDIDATE and
            faults["distinct_real_source_faults"] == 4 and faults["calibration_phase_executions"] == 24 and
            faults["admission_credit"] == 0, "fault source audit identity/counts differ")
    require(declaration["source_pin"] == PIN and declaration["expected_ordinary_executions"] == 480 and
            declaration["expected_additional_e10_branch_executions"] == 24 and
            declaration["canonical_scenario_count"] == 20, "qualification declaration differs")
    directory = RAW / "mg/audit-controls" / ("exact-rc6-models-" + uuid.uuid4().hex)
    directory.mkdir(parents=True, exist_ok=False)
    results = []
    controls = []
    for host in HOSTS:
        build = load_build(host, native)
        model = expected_cell(host, native, faults, declaration, freeze, build)
        baseline = validate(model, host, native, faults, declaration, freeze, build)
        patches = [
            ("wrong-project", ["project"], "other"),
            ("wrong-repository", ["repository"], "troglobit/fork"),
            ("wrong-pin", ["pin"], "0" * 40),
            ("wrong-candidate", ["candidate"], "v0.4.0-rc.5"),
            ("wrong-host", ["host"], "windows"),
            ("mixed-archive", ["candidate_archive_sha256"], "0" * 64),
            ("mixed-runner", ["runner_sha256"], "0" * 64),
            ("wrong-target-binary", ["target_binary_sha256"], "0" * 64),
            ("missing-ordinary", ["ordinary"], model["ordinary"][:-1]),
            ("duplicate-ordinary-attempt", ["ordinary", 1, "attempt_id"], model["ordinary"][0]["attempt_id"]),
            ("false-green-ordinary", ["ordinary", 0, "passed"], False),
            ("unconfirmed-target-exit", ["ordinary", 0, "target_exit_confirmed"], False),
            ("wrong-phase", ["ordinary", 0, "phase"], "development"),
            ("corrupt-contract-hash", ["ordinary", 0, "contract_sha256"], "0" * 64),
            ("missing-e10-branch", ["additional_e10_branch"], []),
            ("extra-e10-branch-as-ordinary", ["ordinary", 0, "scenario"], "E10"),
            ("missing-fault-phase", ["faults"], model["faults"][:-1]),
            ("false-green-mutated-source", ["faults", 1, "result"], "passed"),
            ("unconfirmed-source-cleanup", ["faults", 0, "target_cleanup_confirmed"], False),
            ("source-not-restored", ["restored_source_map_sha256"], "0" * 64),
            ("false-admission", ["project_admission_credit"], 1),
        ]
        for name, path, value in patches:
            changed = copy.deepcopy(model)
            parent = changed
            for key in path[:-1]:
                parent = parent[key]
            parent[path[-1]] = value
            try:
                validate(changed, host, native, faults, declaration, freeze, build)
            except (ValueError, KeyError, TypeError, IndexError) as error:
                controls.append({"host": host, "control": name, "rejected": True,
                                 "reason": str(error), "path": path})
            else:
                raise ValueError("tampered mg actual cell model accepted: " + host + "/" + name)
        encoded = json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
        packed = lzma.compress(encoded, preset=6)
        path = directory / (host + "-actual-model.json.xz")
        path.write_bytes(packed)
        restored = json.loads(lzma.decompress(packed, memlimit=64 * 1024 * 1024))
        require(restored == model and validate(restored, host, native, faults, declaration, freeze, build) == baseline,
                "positive exact-candidate model did not survive roundtrip")
        results.append({"host": host, "counts": baseline,
                        "model": path.relative_to(RAW).as_posix(), "model_sha256": sha256(path),
                        "decoded_model_sha256": hashlib.sha256(encoded).hexdigest(),
                        "model_bytes": len(encoded)})
    immutable_json(directory / "results.json", {
        "schema_version": 1, "project": "mg", "candidate": CANDIDATE,
        "native_audit": NATIVE_AUDIT.relative_to(DOC).as_posix(),
        "native_audit_sha256": sha256(NATIVE_AUDIT),
        "fault_audit": "../mg-fault-calibration-audit-run-42811359525-v2.json",
        "fault_audit_sha256": sha256(FAULT_AUDIT), "cells": results, "controls": controls,
        "semantic_corruptions_rejected": len(controls), "project_admission_credit": 0,
        "scope": "Two exact-rc.6 native cells reconstructed from independently audited provider records; 21 semantic model corruptions rejected per host. No project admission or new scenario/fault credit.",
    })
    print("mg exact-candidate cell models roundtripped;", len(controls), "tampered models rejected; no admission.")


if __name__ == "__main__":
    main()
