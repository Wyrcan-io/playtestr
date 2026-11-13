"""Independent admission review of fzy's complete exact-rc.8 project packet."""
import hashlib
import json
from pathlib import Path

from next20_check import DOC

PROJECT = DOC / "fzy"
INPUT_HASHES = {
    "source-provenance.json": "93c1514b25104f7f148d9888e79e6e0482b34d87d0c201d950068040f31fc9ef",
    "scenario-declaration-v1.json": "cfd0328f0766373d08352368a16c319857cba198bc396bd329798a245e971484",
    "development-artifact-audit-v2.json": "2ff117c829f3db5c8e97b1a6e5e2e52770357ecb8cc07104000edb9fd40645a7",
    "final-archive-artifact-audit-v1.json": "832d8bb154e76b399d581ec5cd4b2d6170eef0c3bee514f58ac5b5c3f1dec5e3",
    "fault-calibration-artifact-audit-v1.json": "fa4b8e891bb04bed64c6f5928c2a30cf0af747e0c0a2ba3d816506cfd5f0dbc9",
    "public-route-artifact-audit-v1.json": "503ca2151d5626749ec5dc1df20c11c754e2bbb8f60f58433b2c1f044482d218",
    "technical-route-audit-run43366281787-v1.json": "9c9ee645f5f9fd2f04b955a6ecc68d4035b6a1d88b69b7690baa6e05d1d423ae",
    "model-controls-v1.json": "df30297c56f0c57d71fb4a9cbcf52d014d921eaa215a93ce7b941f761642bcea",
    "source-review-v1.md": "ee9a176bb7ce191c5cb47c5fc75000014ea2aaae64d6096ab1201e20c9f1bd0b",
}
PIN = "34b88869d022e861da4846c4463aea3ddfb3ff30"
CANDIDATE = "v0.4.0-rc.8"
OUTPUT = PROJECT / "admission.json"
FAILED_ATTEMPTS = [
    "development-attempt-run43354015363-v1.json",
    "development-attempt-run43354855944-v1.json",
    "development-attempt-run43355127321-v1.json",
    "development-attempt-run43355826474-v1.json",
    "final-archive-attempt-run43358141466-v1.json",
    "fault-calibration-attempt-run43360846815-v1.json",
    "technical-route-attempt-run43365829863-v1.json",
]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def need(ok, message):
    if not ok:
        raise ValueError(message)


def load(name):
    return json.loads((PROJECT / name).read_text(encoding="utf-8"))


def build_review():
    evidence = {}
    for name, expected in INPUT_HASHES.items():
        actual = sha(PROJECT / name)
        need(actual == expected, f"fzy package evidence changed: {name}")
        evidence[name] = actual
    provenance = load("source-provenance.json")
    scenario = load("scenario-declaration-v1.json")
    development = load("development-artifact-audit-v2.json")
    final = load("final-archive-artifact-audit-v1.json")
    fault = load("fault-calibration-artifact-audit-v1.json")
    public = load("public-route-artifact-audit-v1.json")
    technical = load("technical-route-audit-run43366281787-v1.json")
    model = load("model-controls-v1.json")
    freeze_path = PROJECT.parent / "replacement-candidate-freeze-native-exit-v3.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    need(provenance.get("project") == "fzy" and provenance.get("pin") == PIN
         and provenance.get("source_archive_sha256") == "d55d4d0dcbced2daa0dd16b42ee0fc31654bd038ff6a147b38580c233d62c967"
         and provenance.get("license") == "MIT" and provenance.get("build_hooks_reviewed") is True,
         "source provenance or license review differs")
    need(scenario.get("distinct_scenarios") == 20 and scenario.get("normal_scenarios") == 8
         and scenario.get("edge_scenarios") == 12 and scenario.get("stateful") is False
         and scenario.get("saved_state_coverage_credit") == 0,
         "canonical case matrix or output-capture boundary differs")
    need(development.get("ordinary_passes") == 40 and final.get("ordinary_passes") == 480
         and development.get("run_id") == 43356291927 and final.get("run_id") == 43358562580,
         "development or final archive scenarios differ")
    need(fault.get("audited_phases") == 18 and fault.get("distinct_detected_source_faults") == 3
         and fault.get("run_id") == 43363053728,
         "three-source-fault calibration is incomplete")
    need(public.get("public_route_host_passes") == 2 and public.get("admission_credit") == 0
         and technical.get("status") == "technical-route-evidence-audited-not-admitted"
         and technical.get("run_id") == 43366281787 and technical.get("admission_credit") == 0,
         "public/technical route audit is missing or grants credit early")
    need(model.get("status") == "model-controls-passed-not-project-admitted"
         and model.get("semantic_corruptions_rejected_count") == 17
         and len(model.get("semantic_corruptions_rejected", [])) == 17
         and model.get("admission_credit") == 0,
         "independent model controls are incomplete or self-admitting")
    need(freeze.get("version") == CANDIDATE and freeze.get("series") == "native-exit-v3"
         and freeze.get("publication") is False and freeze.get("project_credits") == 0,
         "candidate is not the frozen unpublished exact rc.8 build")
    for host in ("linux", "darwin"):
        dev = next(row for row in development["results"] if row["host"] == host)
        fin = next(row for row in final["results"] if row["host"] == host)
        fa = next(row for row in fault["results"] if row["host"] == host)
        pu = next(row for row in public["results"] if row["host"] == host)
        te = next(row for row in technical["hosts"] if row["host"] == host)
        model_host = model["hosts"][host]
        cell = next(row for row in freeze["cells"] if row["host"] == host)
        need(dev["ordinary_passes"] == 20 and fin["ordinary_passes"] == 240
             and dev["candidate_archive_sha256"] == fin["candidate_archive_sha256"] == cell["archive_sha256"]
             and dev["runner_binary_sha256"] == fin["runner_binary_sha256"] == cell["binary_sha256"]
             and dev["source_restored"] and fin["source_restored"]
             and dev["descendants_confirmed_gone"] and fin["descendants_confirmed_gone"],
             f"{host}: ordinary native evidence/candidate/cleanup differs")
        need(fa["phase_execution_count"] == 9 and fa["distinct_detected_source_faults"] == 3
             and fa["candidate_archive_sha256"] == cell["archive_sha256"]
             and fa["candidate_binary_sha256"] == cell["binary_sha256"],
             f"{host}: fault packet/candidate differs")
        need(pu["first_use"] == pu["maintenance"] == pu["relocation"] == "passed"
             and pu["target_cleanup_confirmed"] and pu["workflow_preview"] == "reviewed-only-not-dispatched"
             and te["suite_selection"] == "passed-two-specs" and len(te["technical_attempts"]) == 8
             and te["source_restored_exact"] and te["target_removed"] and te["no_matching_processes"]
             and model_host["cleanup_confirmed"], f"{host}: authoring route or cleanup differs")
    for name in FAILED_ATTEMPTS:
        need((PROJECT / name).is_file(), f"failed/partial attempt record missing: {name}")
    return {
        "schema_version": 1, "status": "project-admitted-exact-candidate",
        "project": "fzy", "repository": "jhawthorn/fzy", "source_pin": PIN,
        "candidate": CANDIDATE, "candidate_series": "native-exit-v3",
        "evidence_sha256": evidence,
        "hosts": ["linux-amd64", "macos-arm64"],
        "canonical_scenarios": {"normal": 8, "edge": 12, "total": 20},
        "development_passes": 40, "final_ordinary_passes": 480,
        "fault_calibration_phases": 18, "distinct_detected_source_faults": 3,
        "public_route_hosts": 2, "technical_route_attempts": 16,
        "semantic_corruptions_rejected": 17,
        "failed_or_partial_run_receipts": FAILED_ATTEMPTS,
        "failed_attempts_retained_zero_credit": 11,
        "false_greens": 0, "source_restoration_and_cleanup": "passed-both-hosts",
        "saved_state_coverage_credit": 0, "human_participants": 0,
        "usability": "unmeasured", "delivered_ci": "not-run",
        "campaign_final_gate_credit": 0,
        "project_admission_credit": 1,
        "scope": "Independent project-specific review passes for the exact rc.8 candidate. This records one fzy project admission; it does not close the campaign-wide same-candidate original-ten, twenty-project, delivered-CI, storage, or final-reconciliation gates.",
    }


def validate(receipt):
    need(receipt.get("status") == "project-admitted-exact-candidate"
         and receipt.get("candidate") == CANDIDATE and receipt.get("source_pin") == PIN,
         "admission identity changed")
    need(receipt.get("canonical_scenarios") == {"normal": 8, "edge": 12, "total": 20}
         and receipt.get("final_ordinary_passes") == 480
         and receipt.get("fault_calibration_phases") == 18
         and receipt.get("distinct_detected_source_faults") == 3,
         "required project test matrix incomplete")
    need(receipt.get("semantic_corruptions_rejected") == 17
         and receipt.get("campaign_final_gate_credit") == 0
         and receipt.get("project_admission_credit") == 1,
         "model-control/admission accounting differs")
    need(receipt.get("saved_state_coverage_credit") == 0
         and receipt.get("human_participants") == 0 and receipt.get("usability") == "unmeasured"
         and receipt.get("delivered_ci") == "not-run" and receipt.get("false_greens") == 0,
         "coverage, human, CI, or false-green claim exceeds evidence")


def main():
    receipt = build_review()
    validate(receipt)
    encoded = json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    if OUTPUT.exists():
        need(OUTPUT.read_text(encoding="utf-8") == encoded, "immutable fzy admission receipt changed")
    else:
        OUTPUT.write_text(encoded, encoding="utf-8", newline="\n")
    print(json.dumps({"project": "fzy", "status": receipt["status"],
                      "project_admission_credit": 1, "campaign_final_gate_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
