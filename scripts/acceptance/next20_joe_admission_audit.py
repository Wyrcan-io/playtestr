"""Close JOE's rc.7 project package from its independent native evidence audits."""
import json
from pathlib import Path

from next20_check import DOC
from readiness_evidence import immutable_json, sha256
import next20_joe_model_controls as model_controls

PROJECT = DOC / "joe"
PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
CANDIDATE = "v0.4.0-rc.7"


def require(value, message):
    if not value:
        raise ValueError(message)


def update_campaign_ledger(admission):
    path = DOC / "projects.json"
    ledger = json.loads(path.read_text(encoding="utf-8"))
    row = next(item for item in ledger["projects"] if item.get("id") == "joe")
    subject = {"project": "joe", "candidate": CANDIDATE,
               "path": "joe/admission.json", "sha256": sha256(PROJECT / "admission.json")}
    existing_subjects = [item for item in ledger.get("admission_subjects", [])
                         if item.get("project") == "joe" and item.get("candidate") == CANDIDATE]
    if existing_subjects:
        require(len(existing_subjects) == 1 and existing_subjects[0] == subject,
                "existing JOE rc.7 admission ledger subject differs")
    else:
        ledger["admission_subjects"].append(subject)
    row.update({"status": "Admitted on exact v0.4.0-rc.7; 20 scenarios, two native cells, three faults, oracle and model controls audited.",
                "admitted": True, "current_candidate_qualified": True,
                "current_candidate": CANDIDATE, "qualified_scenarios": 20,
                "qualified_native_cells": 2, "admission": "joe/admission.json"})
    row.setdefault("candidate_admissions", []).append(subject)
    ledger["qualification_candidate"] = CANDIDATE
    ledger["admission_counters_candidate"] = CANDIDATE
    ledger["current_candidate_new_project_admissions"] = 1
    ledger["current_candidate_ordinary_executions_qualified"] = 480
    ledger["current_candidate_calibration_executions_qualified"] = 18
    ledger["current_candidate_canonical_scenarios"] = 20
    ledger["current_candidate_native_cells"] = 2
    ledger["current_candidate_real_source_faults"] = 3
    ledger["candidate_counters"][CANDIDATE] = {
        "projects": 1, "ordinary": 480, "calibrations": 18,
        "canonical_scenarios": 20, "native_cells": 2, "real_source_faults": 3,
    }
    ledger["recorded_candidate_counters"][CANDIDATE] = dict(ledger["candidate_counters"][CANDIDATE])
    ledger["distinct_new_projects_with_any_candidate_admission"] = len({
        item["project"] for item in ledger["admission_subjects"]})
    ledger["candidate_scope"] = (
        "v0.4.0-rc.5 and rc.6 admissions remain historical and transfer no current-candidate credit. "
        "The exact v0.4.0-rc.7 projection currently admits only JOE; the original ten and the other "
        "new projects still require rc.7 carry-forward or requalification before the final campaign gate.")
    path.write_text(json.dumps(ledger, ensure_ascii=True, indent=2) + "\n",
                    encoding="utf-8", newline="\n")


def main():
    model, inputs = model_controls.build_model()
    model_controls.validate(model)
    model_receipt = json.loads((PROJECT / "model-controls-v1.json").read_text(encoding="utf-8"))
    require(model_receipt.get("candidate") == CANDIDATE and
            model_receipt.get("model_sha256") == sha256(PROJECT / "actual-model-v1.json") and
            model_receipt.get("positive_model_restored_and_revalidated") is True and
            model_receipt.get("semantic_corruptions_rejected") == 12 and
            len(model_receipt.get("controls", [])) == 12 and
            all(row.get("rejected") for row in model_receipt["controls"]),
            "JOE positive/tampered evidence models are incomplete")
    scenario = inputs["scenario"]
    final = inputs["final"]
    faults = inputs["fault"]
    public = inputs["public"]
    oracle = inputs["oracle"]
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v2.json").read_text(encoding="utf-8"))
    require(scenario["scenario_declaration"] == "joe/scenario-declaration-v4.json" and
            final["scenario_declaration"] == scenario["scenario_declaration"] and
            final["scenario_declaration_sha256"] == scenario["scenario_declaration_sha256"],
            "JOE exact candidate audits do not share one frozen public scenario contract")
    declaration = json.loads((PROJECT / "scenario-declaration-v4.json").read_text(encoding="utf-8"))
    scenario_kinds = [row.get("kind") for row in declaration.get("scenarios", [])]
    require(declaration["candidate"] == CANDIDATE and declaration["pin"] == PIN and
            declaration.get("minimums") == {"normal": 8, "edge": 12, "distinct": 20,
                                               "native_cells": ["linux-amd64", "macos-arm64"]} and
            scenario_kinds.count("normal") == 8 and scenario_kinds.count("edge") == 12 and
            len(scenario_kinds) == 20,
            "JOE frozen 8/12 scenario boundary differs")
    require(faults["fault_declaration"] == "joe/fault-declaration-v3.json" and
            faults["fault_declaration_sha256"] == sha256(PROJECT / "fault-declaration-v3.json") and
            faults["distinct_detected_source_faults"] == 3 and faults["calibration_phase_executions"] == 18,
            "JOE exact-candidate fault declaration or calibration count differs")
    require(public["hosts"].keys() == oracle["hosts"].keys() == {"linux", "darwin"},
            "JOE public route/oracle native host allocation differs")
    require(scenario["provider_artifacts"].keys() == final["provider_artifacts"].keys() == {"linux", "darwin"},
            "JOE native scenario qualification is missing a host")
    for host in ("linux", "darwin"):
        cell = next(row for row in freeze["cells"] if row["host"] == host)
        require(host in model["hosts"] and
                model["hosts"][host]["candidate_archive_sha256"] == cell["archive_sha256"] and
                model["hosts"][host]["candidate_binary_sha256"] == cell["binary_sha256"] and
                model["hosts"][host]["final"]["ordinary"] == 240 and
                model["hosts"][host]["final"]["passed"] == 240 and
                len(model["hosts"][host]["faults"]) == 3 and
                model["hosts"][host]["oracle"]["negative"] == 10 and
                model["hosts"][host]["cleanup"]["source_tree_removed"] and
                model["hosts"][host]["cleanup"]["owned_processes_absent"],
                "JOE candidate-native host admission requirements differ: " + host)
    project_metadata = json.loads((DOC / "projects.json").read_text(encoding="utf-8"))
    project_row = next(row for row in project_metadata["projects"] if row.get("id") == "joe")
    require(project_row.get("repository") == "joe-editor/joe" and project_row.get("pin") == PIN and
            (not project_row.get("current_candidate_qualified") or
             project_row.get("current_candidate") == CANDIDATE),
            "JOE canonical ledger identity or prior-candidate disposition changed")
    evidence = {
        name: {"path": path.relative_to(DOC).as_posix(), "sha256": sha256(path)}
        for name, path in model_controls.INPUTS.items()
    }
    evidence["model_controls"] = {"path": "joe/model-controls-v1.json",
                                  "sha256": sha256(PROJECT / "model-controls-v1.json")}
    evidence["candidate_freeze"] = {"path": "replacement-candidate-freeze-native-exit-v2.json",
                                    "sha256": sha256(DOC / "replacement-candidate-freeze-native-exit-v2.json")}
    admission = {
        "schema_version": 1, "status": "admitted-on-exact-current-candidate",
        "project": "joe", "canonical_repository": "joe-editor/joe", "source_pin": PIN,
        "candidate": CANDIDATE, "candidate_series": "native-exit-v2",
        "candidate_freeze_sha256": sha256(DOC / "replacement-candidate-freeze-native-exit-v2.json"),
        "qualified_scenarios": 20, "normal_scenarios": 8, "edge_scenarios": 12,
        "qualified_native_cells": 2,
        "hosts": {host: {"architecture": model["hosts"][host]["architecture"],
                         "candidate_archive_sha256": model["hosts"][host]["candidate_archive_sha256"],
                         "candidate_binary_sha256": model["hosts"][host]["candidate_binary_sha256"],
                         "ordinary_executions": 240, "ordinary_passes": 240,
                         "target_binary_sha256": inputs["final"]["provider_artifacts"][host]["target_binary_sha256"],
                         "final_run": inputs["final"]["workflow_run"],
                         "development_run": inputs["scenario"]["workflow_run"],
                         "source_tree_removed": model["hosts"][host]["cleanup"]["source_tree_removed"],
                         "owned_processes_absent": model["hosts"][host]["cleanup"]["owned_processes_absent"]}
                  for host in ("linux", "darwin")},
        "real_source_faults": 3, "calibration_phase_executions": 18,
        "fault_phases": ["baseline", "fault", "recovery"],
        "public_authoring_route": {"status": public["status"], "run": public["workflow_run"],
                                   "hosts": 2, "first_use_diagnosis_maintenance_relocation": "passed",
                                   "human_participants": 0, "usability": "unmeasured"},
        "oracle_calibration": {"run": oracle["workflow_run"], "positive_cases": 2,
                               "negative_cases": 20, "same_invocation_state": True,
                               "model_tamper_controls_rejected": 12},
        "first_failures_retained": True, "candidate_mixing": False,
        "evidence": evidence,
        "paid_admissions": 0, "human_participants": 0,
        "scope": "JOE's 20 reviewed public v3 editor workflows passed twelve repetitions on exact rc.7 Linux amd64 and macOS arm64 archives. Three distinct source faults were detected and restored across both hosts; public authoring, independent saved-state oracle calibration, twelve tampered evidence models, and owned cleanup passed. Human usability remains unmeasured.",
    }
    admission_path = PROJECT / "admission.json"
    if admission_path.exists():
        require(json.loads(admission_path.read_text(encoding="utf-8")) == admission,
                "existing JOE admission receipt differs from the current independent audit")
    else:
        immutable_json(admission_path, admission)
    update_campaign_ledger(admission)
    print("JOE admitted on exact rc.7: 20 scenarios, 2 native cells, 480 ordinary runs, 3 source faults, 18 calibration phases.")


if __name__ == "__main__":
    main()
