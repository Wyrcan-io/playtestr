"""Reconstruct fzy's exact rc.8 evidence model and reject semantic corruption."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from next20_check import DOC


PROJECT = DOC / "fzy"
INPUTS = {
    "development": PROJECT / "development-artifact-audit-v2.json",
    "final": PROJECT / "final-archive-artifact-audit-v1.json",
    "fault": PROJECT / "fault-calibration-artifact-audit-v1.json",
    "public": PROJECT / "public-route-artifact-audit-v1.json",
    "technical": PROJECT / "technical-route-audit-run43366281787-v1.json",
}
EXPECTED_HASHES = {
    "development": "2ff117c829f3db5c8e97b1a6e5e2e52770357ecb8cc07104000edb9fd40645a7",
    "final": "832d8bb154e76b399d581ec5cd4b2d6170eef0c3bee514f58ac5b5c3f1dec5e3",
    "fault": "fa4b8e891bb04bed64c6f5928c2a30cf0af747e0c0a2ba3d816506cfd5f0dbc9",
    "public": "503ca2151d5626749ec5dc1df20c11c754e2bbb8f60f58433b2c1f044482d218",
    "technical": "9c9ee645f5f9fd2f04b955a6ecc68d4035b6a1d88b69b7690baa6e05d1d423ae",
}
HOSTS = ("linux", "darwin")
PIN = "34b88869d022e861da4846c4463aea3ddfb3ff30"
CANDIDATE = "v0.4.0-rc.8"
SERIES = "native-exit-v3"
FREEZE_PATH = DOC / "replacement-candidate-freeze-native-exit-v3.json"
SCENARIO_PATH = PROJECT / "scenario-declaration-v1.json"
FAULT_PATH = PROJECT / "fault-declaration-v1.json"
SOURCE_SHA = "d55d4d0dcbced2daa0dd16b42ee0fc31654bd038ff6a147b38580c233d62c967"
OUTPUT = PROJECT / "model-controls-v1.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def need(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def read_inputs():
    values = {}
    for name, path in INPUTS.items():
        raw = path.read_bytes()
        need(digest(raw) == EXPECTED_HASHES[name], f"{name} audit receipt digest changed")
        values[name] = json.loads(raw.decode("utf-8"))
    freeze_raw = FREEZE_PATH.read_bytes()
    scenario_raw = SCENARIO_PATH.read_bytes()
    fault_raw = FAULT_PATH.read_bytes()
    need(digest(freeze_raw) == "29668abbb0518073a6b53d2d23dc2d6904e76046eea26d917003013a16ddd4d8",
         "exact rc.8 candidate freeze changed")
    need(digest(scenario_raw) == "cfd0328f0766373d08352368a16c319857cba198bc396bd329798a245e971484",
         "fzy scenario contract changed")
    need(digest(fault_raw) == "ccb1a967b16bd99a0a2b2fdf3a52e8a82e6ded5637cc937824c039fbf39d7f05",
         "fzy source-fault declaration changed")
    return values, json.loads(freeze_raw.decode("utf-8")), {
        "freeze": digest(freeze_raw), "scenario": digest(scenario_raw), "fault": digest(fault_raw)}


def build_model() -> dict:
    values, freeze, declarations = read_inputs()
    development, final = values["development"], values["final"]
    fault, public, technical = values["fault"], values["public"], values["technical"]
    scenario = json.loads(SCENARIO_PATH.read_text(encoding="utf-8"))
    need(freeze.get("version") == CANDIDATE and freeze.get("series") == SERIES
         and freeze.get("publication") is False and freeze.get("project_credits") == 0,
         "freeze is not the unpublished exact rc.8 candidate")
    need(scenario.get("project") == "fzy" and scenario.get("pin") == PIN
         and scenario.get("candidate") == CANDIDATE and scenario.get("candidate_series") == SERIES
         and scenario.get("source_archive_sha256") == SOURCE_SHA
         and scenario.get("distinct_scenarios") == 20 and scenario.get("normal_scenarios") == 8
         and scenario.get("edge_scenarios") == 12 and scenario.get("project_admission_credit") == 0
         and scenario.get("saved_state_coverage_credit") == 0,
         "scenario declaration identity, denominator, or credit boundary differs")
    need(development.get("project") == "fzy" and development.get("run_id") == 43356291927
         and development.get("ordinary_passes") == 40 and development.get("new_project_admission_credit") == 0
         and final.get("project") == "fzy" and final.get("run_id") == 43358562580
         and final.get("ordinary_passes") == 480 and final.get("new_project_admission_credit") == 0,
         "development/final archive audit identity or denominator differs")
    need(fault.get("project") == "fzy" and fault.get("run_id") == 43363053728
         and fault.get("candidate") == CANDIDATE and fault.get("candidate_series") == SERIES
         and fault.get("distinct_detected_source_faults") == 3 and fault.get("audited_phases") == 18
         and fault.get("calibration_admission_credit") == 0,
         "fault audit identity, denominator, or admission boundary differs")
    need(public.get("project") == "fzy" and public.get("run_id") == 43364417379
         and public.get("public_route_host_passes") == 2 and public.get("human_participants") == 0
         and public.get("usability") == "unmeasured" and public.get("saved_state_coverage_credit") == 0
         and public.get("admission_credit") == 0,
         "public route audit identity or human/saved-state/admission boundary differs")
    need(technical.get("status") == "technical-route-evidence-audited-not-admitted"
         and technical.get("project") == "fzy" and technical.get("run_id") == 43366281787
         and technical.get("human_participants") == 0 and technical.get("usability") == "unmeasured"
         and technical.get("admission_credit") == 0,
         "technical route audit identity or credit boundary differs")

    rows = {}
    for host in HOSTS:
        dev = next(row for row in development["results"] if row["host"] == host)
        fin = next(row for row in final["results"] if row["host"] == host)
        fa = next(row for row in fault["results"] if row["host"] == host)
        pu = next(row for row in public["results"] if row["host"] == host)
        te = next(row for row in technical["hosts"] if row["host"] == host)
        cell = next(row for row in freeze["cells"] if row["host"] == host)
        need(dev["ordinary_passes"] == 20 and dev["candidate_archive_sha256"] == cell["archive_sha256"]
             and dev["runner_binary_sha256"] == cell["binary_sha256"]
             and dev["source_restored"] and dev["descendants_confirmed_gone"],
             f"{host}: development cases or cleanup differ")
        need(fin["ordinary_passes"] == 240 and fin["candidate_archive_sha256"] == cell["archive_sha256"]
             and fin["runner_binary_sha256"] == cell["binary_sha256"]
             and fin["source_restored"] and fin["descendants_confirmed_gone"],
             f"{host}: final archive cases or cleanup differ")
        phases = fa["audited_phases"]
        need(fa["phase_execution_count"] == 9 and fa["distinct_detected_source_faults"] == 3
             and {row["fault_id"] for row in phases} == {"F01", "F02", "F03"}
             and len(phases) == 9 and all(row["classification"] in ("passed", "expected-target-fault-rejection")
                                          for row in phases)
             and fa["candidate_archive_sha256"] == cell["archive_sha256"]
             and fa["candidate_binary_sha256"] == cell["binary_sha256"],
             f"{host}: fault phases or exact candidate identity differ")
        need(pu["first_use"] == pu["maintenance"] == pu["relocation"] == "passed"
             and pu["diagnosis"] == "state_assertion_failure at step 4"
             and pu["workflow_preview"] == "reviewed-only-not-dispatched"
             and pu["target_cleanup_confirmed"] and pu["saved_state_coverage_credit"] == 0
             and pu["candidate_archive_sha256"] == cell["archive_sha256"]
             and pu["candidate_binary_sha256"] == cell["binary_sha256"],
             f"{host}: public route, diagnosis, preview, or cleanup differs")
        need(te["suite_selection"] == "passed-two-specs" and len(te["technical_attempts"]) == 8
             and all(row["returncode"] == 0 for row in te["technical_attempts"])
             and all(te[key] for key in ("manual_report_sha256", "html_sha256", "v2_report_sha256",
                                         "migrated_report_sha256", "suffix_report_sha256"))
             and te["source_restored_exact"] and te["target_removed"] and te["no_matching_processes"]
             and te["candidate_archive_sha256"] == cell["archive_sha256"]
             and te["candidate_binary_sha256"] == cell["binary_sha256"],
             f"{host}: technical authoring or cleanup differs")
        rows[host] = {"development_passes": dev["ordinary_passes"], "final_passes": fin["ordinary_passes"],
                      "fault_phases": fa["phase_execution_count"], "faults": ["F01", "F02", "F03"],
                      "candidate_archive_sha256": cell["archive_sha256"],
                      "candidate_binary_sha256": cell["binary_sha256"], "public_route_attempts": pu["attempts"],
                      "technical_route_attempts": len(te["technical_attempts"]),
                      "cleanup_confirmed": True}
    return {
        "schema_version": 1, "status": "model-controls-passed-not-project-admitted",
        "project": "fzy", "repository": "jhawthorn/fzy", "source_pin": PIN,
        "candidate": CANDIDATE, "candidate_series": SERIES, "declarations": declarations,
        "audit_receipt_sha256": EXPECTED_HASHES, "hosts": rows,
        "totals": {"distinct_scenarios": 20, "normal_scenarios": 8, "edge_scenarios": 12,
                   "development_attempts": 40, "ordinary_attempts": 480, "native_cells": 2,
                   "faults": 3, "fault_phases": 18, "public_route_attempts": 16,
                   "technical_route_attempts": 16},
        "false_greens": 0, "saved_state_coverage_credit": 0, "human_participants": 0,
        "usability": "unmeasured", "delivered_ci": "not-run", "admission_credit": 0,
    }


def validate(model: dict) -> None:
    need(model.get("status") == "model-controls-passed-not-project-admitted"
         and model.get("project") == "fzy" and model.get("repository") == "jhawthorn/fzy"
         and model.get("source_pin") == PIN and model.get("candidate") == CANDIDATE
         and model.get("candidate_series") == SERIES, "model identity or admission boundary changed")
    need(model.get("audit_receipt_sha256") == EXPECTED_HASHES, "audit receipt bindings changed")
    need(model.get("hosts", {}).keys() == set(HOSTS), "native host matrix differs")
    expected_totals = {"distinct_scenarios": 20, "normal_scenarios": 8, "edge_scenarios": 12,
                       "development_attempts": 40, "ordinary_attempts": 480, "native_cells": 2,
                       "faults": 3, "fault_phases": 18, "public_route_attempts": 16,
                       "technical_route_attempts": 16}
    need(model.get("totals") == expected_totals, "scenario, cell, attempt, or fault denominator differs")
    for host in HOSTS:
        row = model["hosts"][host]
        need(row["development_passes"] == 20 and row["final_passes"] == 240
             and row["fault_phases"] == 9 and row["faults"] == ["F01", "F02", "F03"]
             and row["public_route_attempts"] == 8 and row["technical_route_attempts"] == 8
             and row["cleanup_confirmed"], f"{host}: incomplete native matrix or route evidence")
        need(len(row["candidate_archive_sha256"]) == len(row["candidate_binary_sha256"]) == 64,
             f"{host}: candidate digest missing")
    need(model.get("false_greens") == 0 and model.get("saved_state_coverage_credit") == 0,
         "false-green or saved-state coverage overclaim")
    need(model.get("human_participants") == 0 and model.get("usability") == "unmeasured",
         "human usability evidence invented")
    need(model.get("delivered_ci") == "not-run", "local workflow preview misreported as delivered CI")
    need(model.get("admission_credit") == 0, "model controls cannot grant admission")


def corruption_controls(model: dict) -> list[str]:
    corruptions = [
        ("candidate", lambda m: m.update(candidate="v0.4.0-rc.7")),
        ("source", lambda m: m.update(source_pin="0" * 40)),
        ("receipt_binding", lambda m: m["audit_receipt_sha256"].update(final="0" * 64)),
        ("host_omission", lambda m: m["hosts"].pop("darwin")),
        ("scenario_total", lambda m: m["totals"].update(distinct_scenarios=19)),
        ("ordinary_denominator", lambda m: m["totals"].update(ordinary_attempts=479)),
        ("calibration_denominator", lambda m: m["totals"].update(fault_phases=17)),
        ("fault_identity", lambda m: m["hosts"]["linux"].update(faults=["F01", "F02", "F04"])),
        ("cleanup", lambda m: m["hosts"]["darwin"].update(cleanup_confirmed=False)),
        ("development", lambda m: m["hosts"]["linux"].update(development_passes=19)),
        ("final", lambda m: m["hosts"]["linux"].update(final_passes=239)),
        ("public_route", lambda m: m["hosts"]["linux"].update(public_route_attempts=7)),
        ("technical_route", lambda m: m["hosts"]["darwin"].update(technical_route_attempts=7)),
        ("saved_state_overclaim", lambda m: m.update(saved_state_coverage_credit=1)),
        ("human_claim", lambda m: m.update(human_participants=1, usability="measured")),
        ("preview_as_ci", lambda m: m.update(delivered_ci="passed")),
        ("self_admission", lambda m: m.update(admission_credit=1)),
    ]
    rejected = []
    for name, mutate in corruptions:
        candidate = copy.deepcopy(model)
        mutate(candidate)
        try:
            validate(candidate)
        except (ValueError, KeyError, TypeError):
            rejected.append(name)
        else:
            raise ValueError(f"model controls accepted semantic corruption: {name}")
    return rejected


def main() -> None:
    model = build_model()
    validate(model)
    rejected = corruption_controls(model)
    result = {**model, "semantic_corruptions_rejected": rejected,
              "semantic_corruptions_rejected_count": len(rejected)}
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if OUTPUT.exists():
        need(OUTPUT.read_text(encoding="utf-8") == encoded,
             "immutable fzy model-control receipt already exists with different content")
    else:
        OUTPUT.write_text(encoded, encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "project": "fzy",
                      "semantic_corruptions_rejected": len(rejected), "admission_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
