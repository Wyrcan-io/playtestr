"""Independent hash and counter readback for mg's prepared RC6 admission."""
import json
from pathlib import Path

from readiness_evidence import immutable_json, sha256

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/validation/runner-readiness-next-twenty-project-pass"
RAW = ROOT / "artifacts/runner-readiness-next-twenty-project-pass"


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    path = DOC / "mg/admission.json"
    admission = json.loads(path.read_text(encoding="utf-8"))
    require(admission["admitted"] and admission["candidate"] == "v0.4.0-rc.6" and
            admission["ordinary"] == 480 and admission["calibrations"] == 24 and
            admission["real_source_faults"] == 4 and admission["cell_model_negative_controls"] == 42 and
            len(admission["native_cells"]) == 2 and admission["delivered_ci_observations"] == 0 and
            admission["human_participants"] == 0 and admission["paid_admissions"] == 0,
            "mg admission counters or scope differ")
    checked = []
    for relative, expected in admission["subjects"].items():
        subject = ROOT / relative
        require(subject.is_file() and sha256(subject) == expected, "mg admission subject hash differs: " + relative)
        checked.append({"path": relative, "sha256": expected})
    cleanup_path = RAW / "mg/audit-controls/target-cleanup-v1.json"
    cleanup = json.loads(cleanup_path.read_text(encoding="utf-8"))
    require(cleanup["result"]["removed"] and cleanup["result"]["files"] == 129 and
            cleanup["active_mg_absent"] and not (RAW / "active/mg").exists(),
            "owned target cleanup evidence or current absence differs")
    ledger = json.loads((DOC / "projects.json").read_text(encoding="utf-8"))
    row = next(item for item in ledger["projects"] if item["id"] == "mg")
    require(row["current_candidate_qualified"] and len(row["candidate_admissions"]) == 1 and
            ledger["current_candidate_new_project_admissions"] == 6 and
            ledger["current_candidate_ordinary_executions_qualified"] == 2880 and
            ledger["current_candidate_calibration_executions_qualified"] == 114 and
            ledger["current_candidate_native_cells"] == 12 and
            ledger["current_candidate_canonical_scenarios"] == 120,
            "current candidate ledger counters do not include only the audited mg admission")
    receipt = {
        "schema_version": 1, "project": "mg", "candidate": admission["candidate"],
        "admission": path.relative_to(DOC).as_posix(), "admission_sha256": sha256(path),
        "ledger_candidate_projects": 6, "ledger_ordinary": 2880, "ledger_calibrations": 114,
        "ledger_scenarios": 120, "ledger_native_cells": 12,
        "admission_subjects_verified": len(checked), "subjects": checked,
        "cleanup_receipt": cleanup_path.relative_to(RAW).as_posix(),
        "cleanup_receipt_sha256": sha256(cleanup_path), "active_target_absent": True,
        "delivered_ci_credit": 0, "human_participants": 0, "paid_admissions": 0,
        "scope": "Independent admission subject hash readback and exact candidate ledger reconciliation; no CI, human, paid, original-ten or campaign-closure credit.",
    }
    immutable_json(DOC / "mg/admission-audit-v1.json", receipt)
    print("mg RC6 admission independently reconciled: 6/20 new projects, 2,880 ordinary, 114 calibrations, 12 cells.")


if __name__ == "__main__":
    main()
