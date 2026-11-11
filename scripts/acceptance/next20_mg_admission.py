"""Close mg's RC6 admission from retained provider, route and tamper evidence."""
import json
from pathlib import Path
import zipfile

from readiness_evidence import immutable_json, sha256

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/validation/runner-readiness-next-twenty-project-pass"
RAW = ROOT / "artifacts/runner-readiness-next-twenty-project-pass"
PROJECT = DOC / "mg"
PIN = "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66"
CANDIDATE = "v0.4.0-rc.6"


def require(value, message):
    if not value:
        raise ValueError(message)


def bind(subjects, path):
    path = Path(path)
    subjects[path.relative_to(ROOT).as_posix()] = sha256(path)
    return path


def main():
    ledger = json.loads((DOC / "projects.json").read_text(encoding="utf-8"))
    row = next((item for item in ledger["projects"] if item["id"] == "mg"), None)
    require(row is not None and row["repository"] == "troglobit/mg" and row["pin"] == PIN and
            row["admitted"] is False and ledger["qualification_candidate"] == CANDIDATE,
            "mg identity, candidate, or pre-admission status differs")
    selection = json.loads((DOC / "selection-declaration.json").read_text(encoding="utf-8"))
    require(any(item["id"] == "mg" and item["repository"] == "troglobit/mg" for item in selection["selected"]),
            "mg is not the selected canonical upstream")
    require(not (RAW / "active/mg").exists(), "owned mg source/runtime remains active")

    declaration_path = bind({}, PROJECT / "final-qualification-declaration-v2.json")
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    native_path = bind({}, PROJECT / "final-qualification-artifact-audit-run-42980303472-v1.json")
    native = json.loads(native_path.read_text(encoding="utf-8"))
    faults_path = bind({}, DOC / "mg-fault-calibration-audit-run-42811359525-v2.json")
    faults = json.loads(faults_path.read_text(encoding="utf-8"))
    require(declaration["source_pin"] == PIN and declaration["candidate"] == CANDIDATE and
            native["status"] == "native-matrix-audited" and native["run_id"] == 42980303472 and
            native["project_admission_credit"] == 0 and native["ordinary_executions"] == 480 and
            native["additional_e10_branch_executions"] == 24 and
            faults["status"] == "fault-calibration-audited" and faults["target_pin"] == PIN and
            faults["candidate"] == CANDIDATE and faults["distinct_real_source_faults"] == 4 and
            faults["calibration_phase_executions"] == 24 and faults["admission_credit"] == 0,
            "exact-candidate independent native/fault audit differs")
    require(len(declaration["scenarios"]) == 21 and declaration["canonical_scenario_count"] == 20 and
            declaration["expected_ordinary_executions"] == 480 and
            declaration["expected_additional_e10_branch_executions"] == 24,
            "declared canonical scenario matrix differs")

    controls_path = bind({}, PROJECT / "model-controls-v1.json")
    controls = json.loads(controls_path.read_text(encoding="utf-8"))
    require(controls["candidate"] == CANDIDATE and controls["pin"] == PIN and
            controls["semantic_corruptions_rejected"] == 42 and
            {cell["host"] for cell in controls["cells"]} == {"linux", "darwin"},
            "independent exact-model controls are incomplete")
    # Bind the exact provider ZIPs used to reconstruct the target binary identity.
    build_inputs = []
    for host in ("linux", "darwin"):
        path = RAW / f"mg/model-controls-input-v1/native-build-{host}-42815619413.zip"
        provider = next(item for item in native["provider_artifacts"]
                        if item.get("name") == f"next20-mg-build-{host}-42815619413")
        require(path.is_file() and sha256(path) == provider["sha256"] and path.stat().st_size == provider["size_bytes"],
                "retrieved target build ZIP differs from audited provider artifact")
        with zipfile.ZipFile(path) as archive:
            require(archive.testzip() is None, "target build ZIP CRC failed")
            build = json.loads(archive.read("active/mg/build.json"))
            acquisition = json.loads(archive.read("active/mg/acquisition.json"))
            binary = archive.read("active/mg/" + build["binary_relative_path"])
            require(build["project"] == "mg" and build["host"] == host and build["pin"] == PIN and
                    build["source_archive_sha256"] == acquisition["archive_sha256"] and
                    sha256_bytes(binary) == build["binary_sha256"] == provider["target_binary_sha256"] and
                    provider["source_pin"] == PIN and provider["crc"] == "passed",
                    "target build ZIP source or executable identity differs")
        build_inputs.append({"host": host, "provider_artifact_id": provider["artifact_id"],
                             "provider_name": provider["name"], "zip": path.relative_to(ROOT).as_posix(),
                             "zip_sha256": sha256(path), "target_binary_sha256": build["binary_sha256"],
                             "source_archive_sha256": build["source_archive_sha256"]})
        bind({}, path)

    route_path = bind({}, PROJECT / "public-route-audit-run-42995560305-v1.json")
    route = json.loads(route_path.read_text(encoding="utf-8"))
    require(route["status"] == "public-route-evidence-audited-not-admitted" and
            route["candidate"] == CANDIDATE and route["source_pin"] == PIN and
            route["project_admission_credit"] == 0 and route["attempt_count"] == 9 and
            route["repaired_window"] == {"controls": 15, "passed": True, "shell_invocations": 3},
            "hosted repaired first-use route is not positive")
    oracle = route["saved_state_oracle_calibration"]
    require(oracle["attempt_count"] == 6 and
            [case["exit_code"] for case in oracle["cases"]] == [0, 0, 1, 1, 1, 1],
            "saved-state oracle does not have two positives and four mutation rejections")
    technical = route["technical_authoring_route"]
    require(technical["attempt_count"] == 7 and
            technical["version_migration"] == "manual v2-to-v3 with exact saved-state assertion" and
            technical["reports"] == ["machine JSON", "offline HTML"] and technical["selected_suffix_rerecord"] and
            technical["target_copy_removed"],
            "technical public authoring route is incomplete")
    require("selected update passed" in route["selected_saved_state_maintenance"] and
            "ordinary run passed" in route["unicode_relocation"] and
            route["delivered_workflow"]["provider_run"] == "not-dispatched",
            "maintenance/relocation route or delivered-workflow accounting differs")

    subjects = {}
    for path in (PROJECT / "source-provenance.json", PROJECT / "preflight-review-v1.md",
                 PROJECT / "scenario-catalog-draft-v1.md", declaration_path, native_path, faults_path,
                 controls_path, route_path, PROJECT / "scenario-development-accounting-v31.json",
                 PROJECT / "pilot-attempt-accounting-v22.json", DOC / "replacement-candidate-freeze-native-exit-v1.json",
                 DOC / "storage-checkpoint-v48.json"):
        bind(subjects, path)
    for path in (RAW / controls["results"], RAW / controls["cells"][0]["model"], RAW / controls["cells"][1]["model"]):
        bind(subjects, path)
    for host in ("linux", "darwin"):
        bind(subjects, PROJECT / f"final-qualification-artifact-audit-run-42980303472-v1.json")
    admission = {
        "schema_version": 1, "project": "mg", "repository": "troglobit/mg", "pin": PIN,
        "admitted": True, "candidate": CANDIDATE, "canonical_scenarios": 20,
        "normal_scenarios": 8, "edge_scenarios": 12,
        "native_cells": [{"host": cell["host"], "architecture": cell["architecture"],
                          "candidate_archive_sha256": cell["archive_sha256"],
                          "runner_sha256": cell["binary_sha256"], "run": "42980303472",
                          "ordinary": 240, "calibrations": 12,
                          "actual_model": control_cell["model"],
                          "actual_model_sha256": control_cell["model_sha256"]}
                         for cell in declaration["native_cells"]
                         for control_cell in controls["cells"] if control_cell["host"] == cell["host"]],
        "ordinary": 480, "additional_e10_branch_executions": 24,
        "calibrations": 24, "real_source_faults": 4,
        "cell_model_negative_controls": 42, "build_inputs": build_inputs,
        "public_first_use_controls": 15, "public_first_use_commands": 3,
        "saved_state_oracle_cases": 6, "technical_authoring_operations": 7,
        "maintenance_and_unicode_relocation": True,
        "delivered_ci_observations": 0, "delivered_workflow_preview_only": True,
        "human_participants": 0, "human_usability": "unmeasured", "paid_admissions": 0,
        "local_target_absent": True, "subjects": subjects,
        "limitations": [
            "Private engineering qualification of exact v0.4.0-rc.6 cells; no stable-support or public-release claim.",
            "Human beginner usability remains unmeasured; the documented route was agent-operated.",
            "The delivered workflow was previewed but not dispatched; no delivered-CI triplet credit.",
            "Original-ten rc.6 requalification and campaign closure remain separate open gates.",
        ],
        "scope": "One independently reviewed current-candidate project admission from two exact native cells, twenty canonical scenarios, 480 passing ordinary executions, 24 calibration phases over four distinct source faults, 42 tampered-model rejections, repaired public first-use, saved-state oracle calibration, technical authoring, maintenance, relocation, and confirmed local target removal.",
    }
    immutable_json(PROJECT / "admission.json", admission)
    print("mg admission evidence prepared: 2 native cells, 20 scenarios, 480 ordinary, 24 calibrations, 4 faults, 42 model controls.")


def sha256_bytes(data):
    import hashlib
    return hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    main()
