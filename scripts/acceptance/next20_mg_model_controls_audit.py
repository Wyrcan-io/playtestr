"""Independently inspect mg's retained model-tamper evidence and curate its receipt."""
import hashlib
import json
import lzma
from pathlib import Path

from readiness_evidence import immutable_json, sha256

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/validation/runner-readiness-next-twenty-project-pass"
RAW = ROOT / "artifacts/runner-readiness-next-twenty-project-pass"
PROJECT = DOC / "mg"
NATIVE = PROJECT / "final-qualification-artifact-audit-run-42980303472-v1.json"
FAULTS = DOC / "mg-fault-calibration-audit-run-42811359525-v2.json"


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    dirs = sorted((RAW / "mg/audit-controls").glob("exact-rc6-models-*"),
                  key=lambda p: p.stat().st_mtime_ns, reverse=True)
    require(dirs, "no retained exact-candidate model controls")
    result_path = dirs[0] / "results.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    require(result["project"] == "mg" and result["candidate"] == "v0.4.0-rc.6" and
            result["project_admission_credit"] == 0 and
            result["native_audit_sha256"] == sha256(NATIVE) and result["fault_audit_sha256"] == sha256(FAULTS),
            "model controls are not bound to current independent native and fault audits")
    require(result["semantic_corruptions_rejected"] == 42 and len(result["controls"]) == 42 and
            all(row["rejected"] for row in result["controls"]), "semantic rejection set is incomplete")
    require({row["host"] for row in result["cells"]} == {"linux", "darwin"}, "native host model coverage differs")
    cells = []
    for row in result["cells"]:
        require(row["counts"] == {"host": row["host"], "ordinary": 240,
                                  "additional_e10_branch": 12, "calibrations": 12,
                                  "distinct_real_faults": 4}, "exact host-cell counts differ")
        model_path = RAW / row["model"]
        require(sha256(model_path) == row["model_sha256"], "compressed model digest differs")
        encoded = lzma.decompress(model_path.read_bytes(), memlimit=64 * 1024 * 1024)
        require(hashlib.sha256(encoded).hexdigest() == row["decoded_model_sha256"], "decoded model digest differs")
        model = json.loads(encoded)
        require(model["host"] == row["host"] and model["project"] == "mg" and
                model["candidate"] == "v0.4.0-rc.6" and model["project_admission_credit"] == 0 and
                len(model["ordinary"]) == 240 and len(model["additional_e10_branch"]) == 12 and
                len(model["faults"]) == 12 and len({x["attempt_id"] for x in
                model["ordinary"] + model["additional_e10_branch"] + model["faults"]}) == 264,
                "positive exact-cell model inventory differs")
        require(all(x["passed"] and x["target_exit_confirmed"] and x["process_tree_confirmed"]
                    for x in model["ordinary"] + model["additional_e10_branch"]),
                "ordinary/branch evidence lacks positive outcomes or process confirmation")
        require(sum(x["result"] == "failed" for x in model["faults"]) == 4 and
                sum(x["result"] == "passed" for x in model["faults"]) == 8 and
                all(x["target_cleanup_confirmed"] and x["process_tree_confirmed"] for x in model["faults"]),
                "fault calibration phase outcomes or cleanup differ")
        cells.append({**row, "model_sha256_verified": True,
                      "decoded_model_sha256_verified": True, "attempts": 264})
    controls_doc = {
        "schema_version": 1, "project": "mg", "repository": "troglobit/mg",
        "pin": "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66", "candidate": "v0.4.0-rc.6",
        "native_audit": NATIVE.relative_to(DOC).as_posix(), "native_audit_sha256": sha256(NATIVE),
        "fault_audit": FAULTS.relative_to(DOC).as_posix(), "fault_audit_sha256": sha256(FAULTS),
        "results": result_path.relative_to(RAW).as_posix(), "results_sha256": sha256(result_path),
        "cells": cells, "semantic_corruptions_rejected": 42,
        "corruptions_rejected_per_host": {"linux": 21, "darwin": 21},
        "project_admission_credit": 0,
        "scope": "Independent readback of two exact RC6 native cell models and their 42 semantic tampering challenges. This controls receipt grants no project-admission, scenario, execution, or fault credit.",
    }
    immutable_json(PROJECT / "model-controls-v1.json", controls_doc)
    print("Independently audited mg model controls: 2 hosts, 42 corruptions rejected; 0 admission credit.")


if __name__ == "__main__":
    main()
