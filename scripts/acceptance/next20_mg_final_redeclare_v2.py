"""Declare the corrected mg series after a workflow setup-only failure."""
import json

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def main():
    previous_path = DOC / "mg/final-qualification-declaration-v1.json"
    destination = DOC / "mg/final-qualification-declaration-v2.json"
    previous = json.loads(previous_path.read_text(encoding="utf-8"))
    if previous.get("status") != "declared-not-yet-qualified":
        raise ValueError("source declaration is not an unused qualification plan")
    if previous.get("expected_total_contract_executions") != 504:
        raise ValueError("source declaration does not match the frozen 504 contract denominator")
    declaration = json.loads(json.dumps(previous))
    declaration["series_id"] = "mg-final-series-v2"
    declaration["status"] = "declared-not-yet-qualified"
    declaration["supersedes"] = previous_path.relative_to(ROOT).as_posix()
    declaration["supersedes_sha256"] = sha256(previous_path)
    declaration["supersession_reason"] = {
        "failed_preflight_run": 42819643394,
        "failed_native_cells": 12,
        "scenario_contract_attempts": 0,
        "reason": "GitHub could not resolve the download-artifact commit and the matrix omitted the explicit host dimension; every observed Darwin job failed during Set up job before checkout or target execution.",
        "correction": "Use the repository-validated d3f86a106a0bac45b974a628896c90dbdf5c8093 action pin and explicit linux/darwin crossed with batch 0..11.",
    }
    declaration["run_policy"] = "Replacement series v2; the setup-only v1 failure remains preserved and receives no scenario or qualification credit. No scenario attempt from v1 is retried because none began."
    immutable_json(destination, declaration)
    print(json.dumps({"path": destination.relative_to(ROOT).as_posix(),
                      "sha256": sha256(destination), "series_id": declaration["series_id"],
                      "supersedes": declaration["supersedes"],
                      "scenario_attempts_in_prior_run": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
