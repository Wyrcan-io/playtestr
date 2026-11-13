"""Reconstruct Pick's exact rc.8 evidence model and reject semantic tampering."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from next20_check import DOC


PROJECT = DOC / "pick"
FREEZE_PATH = DOC / "replacement-candidate-freeze-native-exit-v3.json"
INPUTS = {
    "development": PROJECT / "development-audit-run43333839727-v1.json",
    "final": PROJECT / "final-archive-audit-run43336391685-v1.json",
    "fault": PROJECT / "fault-calibration-audit-run43341927666-v1.json",
    "public": PROJECT / "public-route-audit-run43347165865-v1.json",
    "technical": PROJECT / "technical-route-audit-run43350106198-v1.json",
}
EXPECTED_HASHES = {
    "development": "681a53fcba067bda7afdfb8e7bc654123ea8c9cf2031ece103a3615a81281cd2",
    "final": "a0f19e6924a4ab2fc264e43a4fa545ece2b3715ddbbe5cff408233bc220ad92c",
    "fault": "6ea5f51296edd18f904d2b49b79775f3f59dc321e2e9419b9f80312cf96036e7",
    "public": "f43b174f91d3c4ae9609e985cb64e25899264887bc0b000e84966bf2adabd20d",
    "technical": "849bbac4a2a984742aef579d451829b2238151fd938b1fc054afc7d8bdc62941",
}
HOSTS = ("linux", "darwin")
PIN = "caae95938359b2e814b3e7406f396f486c9d99fb"
CANDIDATE = "v0.4.0-rc.8"
SERIES = "native-exit-v3"
SCENARIO_SHA = "1f1b6b455e931b5ebde69cee820c3872abd8ffafd08d35e9452f25be5eeac65c"
FAULT_DECLARATION_SHA = "4ce4f034a842f73a09501122dca097f802f51e401ed277baffdbf3b4707a424a"
SOURCE_SHA = "e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653"
OUTPUT = PROJECT / "model-controls-v1.json"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def read_inputs() -> tuple[dict, dict, dict]:
    values = {}
    for name, path in INPUTS.items():
        raw = path.read_bytes()
        require(digest(raw) == EXPECTED_HASHES[name], f"{name} audit receipt hash changed")
        values[name] = json.loads(raw.decode("utf-8"))
    freeze_raw = FREEZE_PATH.read_bytes()
    require(digest(freeze_raw) == "29668abbb0518073a6b53d2d23dc2d6904e76046eea26d917003013a16ddd4d8",
            "candidate freeze hash changed")
    freeze = json.loads(freeze_raw.decode("utf-8"))
    scenario_raw = (PROJECT / "scenario-declaration-v10.json").read_bytes()
    require(digest(scenario_raw) == SCENARIO_SHA, "scenario declaration hash changed")
    fault_raw = (PROJECT / "fault-declaration-v1.json").read_bytes()
    require(digest(fault_raw) == FAULT_DECLARATION_SHA, "fault declaration hash changed")
    return values, freeze, {"scenario": digest(scenario_raw), "fault": digest(fault_raw),
                            "freeze": digest(freeze_raw)}


def build_model() -> dict:
    values, freeze, declarations = read_inputs()
    development, final = values["development"], values["final"]
    fault, public, technical = values["fault"], values["public"], values["technical"]
    require(development["candidate_version"] == final["candidate_version"] == CANDIDATE
            and development["candidate_series"] == final["candidate_series"] == SERIES
            and development["distinct_scenarios"] == final["distinct_scenarios"] == 20
            and development["scenario_declaration_sha256"] == final["scenario_declaration_sha256"] == SCENARIO_SHA
            and development["scenario_project_credit"] == final["scenario_project_credit"] == 0
            and development["admission_credit"] == final["admission_credit"] == 0,
            "development/final archive identity or no-credit boundary differs")
    require(fault["project"] == "pick" and fault["candidate"] == CANDIDATE
            and fault["candidate_series"] == SERIES and fault["run_id"] == 43341927666
            and fault["scenario_declaration_sha256"] == SCENARIO_SHA
            and fault["fault_declaration_sha256"] == FAULT_DECLARATION_SHA
            and fault["false_greens"] == 0 and fault["mutated_targets_rejected"] == 6
            and fault["phase_receipts"] == fault["reports"] == 18
            and fault["pristine_and_restored_passes"] == 12
            and fault["process_and_workspace_cleanup_confirmed"]
            and fault["source_restoration_confirmed"] and fault["admission_credit"] == 0,
            "fault audit identity, outcomes, restoration, cleanup, or credit differs")
    require(public["status"] == "public-route-evidence-audited-not-admitted"
            and public["project"] == "pick" and public["run_id"] == 43347165865
            and public["human_participants"] == 0 and public["usability"] == "unmeasured"
            and public["admission_credit"] == 0,
            "public route audit identity or human/admission boundary differs")
    require(technical["status"] == "technical-route-evidence-audited-not-admitted"
            and technical["project"] == "pick" and technical["run_id"] == 43350106198
            and technical["human_participants"] == 0 and technical["usability"] == "unmeasured"
            and technical["admission_credit"] == 0,
            "technical route audit identity or human/admission boundary differs")
    require(freeze.get("version") == CANDIDATE and freeze.get("series") == SERIES
            and freeze.get("publication") is False and freeze.get("project_credits") == 0,
            "candidate freeze is not the unpublished exact rc.8 candidate")

    rows = {}
    for host in HOSTS:
        dev = next(row for row in development["hosts"] if row["host"] == host)
        fin = next(row for row in final["hosts"] if row["host"] == host)
        fa = next(row for row in fault["hosts"] if row["host"] == host)
        pu = next(row for row in public["hosts"] if row["host"] == host)
        te = next(row for row in technical["hosts"] if row["host"] == host)
        cell = next(row for row in freeze["cells"] if row["host"] == host)
        require(dev["attempt_count"] == dev["passed"] == 20 and dev["failed"] == 0
                and dev["source_archive_sha256"] == SOURCE_SHA
                and dev["candidate_archive_sha256"] == cell["archive_sha256"]
                and dev["candidate_binary_sha256"] == cell["binary_sha256"]
                and dev["upstream_tests"] == "passed" and dev["source_restored_exact"]
                and dev["target_and_descendant_cleanup"] == "confirmed",
                f"{host}: development evidence incomplete or identity mismatch")
        require(fin["attempt_count"] == fin["passed"] == 240 and fin["failed"] == 0
                and fin["candidate_archive_sha256"] == cell["archive_sha256"]
                and fin["candidate_binary_sha256"] == cell["binary_sha256"]
                and fin["source_archive_sha256"] == SOURCE_SHA
                and fin["upstream_tests"] == "passed" and fin["source_restored_exact"]
                and fin["target_and_descendant_cleanup"] == "confirmed",
                f"{host}: final archive evidence incomplete or identity mismatch")
        faults = fa["faults"]
        require(fa["phase_count"] == 9 and len(faults) == 3
                and {item["fault_id"] for item in faults} == {"F01", "F02", "F03"},
                f"{host}: expected three complete fault triples")
        for item in faults:
            require(item["baseline"] == item["restored"] == "passed"
                    and item["corrupted"] == "expected-target-fault-rejection"
                    and item["baseline_binary_sha256"] == item["restored_binary_sha256"]
                    and item["mutated_binary_sha256"] != item["baseline_binary_sha256"],
                    f"{host}/{item['fault_id']}: fault detection or binary restoration differs")
        require(pu["candidate_archive_sha256"] == cell["archive_sha256"]
                and pu["candidate_binary_sha256"] == cell["binary_sha256"]
                and pu["first_use"] == pu["maintenance"] == pu["relocation"] == "passed"
                and pu["seeded_diagnosis"] == "assertion_timeout with cleanup"
                and pu["delivered_workflow_preview"] == "reviewed-not-dispatched"
                and pu["source_restored_exact"] and pu["target_removed"] and pu["no_matching_processes"]
                and pu["admission_credit"] == 0,
                f"{host}: public authoring evidence or cleanup differs")
        require(te["candidate_archive_sha256"] == cell["archive_sha256"]
                and te["candidate_binary_sha256"] == cell["binary_sha256"]
                and te["suite_selection"] == "passed-two-specs"
                and len(te["technical_attempts"]) == 8
                and all(attempt["returncode"] == 0 for attempt in te["technical_attempts"])
                and all(te[key] for key in ("manual_v3_report_sha256", "manual_html_sha256",
                                            "v2_report_sha256", "migrated_v3_report_sha256",
                                            "suffix_report_sha256"))
                and te["source_restored_exact"] and te["target_removed"]
                and te["no_matching_processes"] and te["admission_credit"] == 0,
                f"{host}: technical route evidence or cleanup differs")
        rows[host] = {
            "development_scenarios": dev["passed"], "final_scenarios": fin["passed"],
            "fault_phases": fa["phase_count"], "faults": sorted(item["fault_id"] for item in faults),
            "candidate_archive_sha256": cell["archive_sha256"],
            "candidate_binary_sha256": cell["binary_sha256"],
            "public_route": "passed-audited", "technical_route_attempts": 8,
            "cleanup_confirmed": True,
        }
    require(len(rows) == 2, "both native hosts must be present")
    return {
        "schema_version": 1,
        "status": "model-controls-passed-not-project-admitted",
        "project": "pick", "repository": "mptre/pick", "source_pin": PIN,
        "candidate": CANDIDATE, "candidate_series": SERIES,
        "declarations": declarations,
        "audit_receipt_sha256": EXPECTED_HASHES,
        "hosts": rows,
        "totals": {"distinct_scenarios": 20, "normal_scenarios": 8, "edge_scenarios": 12,
                   "development_attempts": 40, "ordinary_attempts": 480,
                   "native_cells": 2, "faults": 3, "fault_phases": 18,
                   "public_routes": 2, "technical_route_attempts": 16},
        "false_greens": 0,
        "historical_false_green_disclosed": True,
        "saved_state_coverage_credit": 0,
        "human_participants": 0, "usability": "unmeasured",
        "delivered_ci": "not-run", "admission_credit": 0,
    }


def validate(model: dict) -> None:
    require(model.get("status") == "model-controls-passed-not-project-admitted",
            "model status or admission boundary changed")
    require(model.get("project") == "pick" and model.get("repository") == "mptre/pick"
            and model.get("source_pin") == PIN and model.get("candidate") == CANDIDATE
            and model.get("candidate_series") == SERIES,
            "project/source/candidate identity differs")
    require(model.get("audit_receipt_sha256") == EXPECTED_HASHES,
            "audit receipt binding differs")
    require(model.get("hosts", {}).keys() == set(HOSTS), "missing or extra native host")
    require(model.get("totals") == {
        "distinct_scenarios": 20, "normal_scenarios": 8, "edge_scenarios": 12,
        "development_attempts": 40, "ordinary_attempts": 480, "native_cells": 2,
        "faults": 3, "fault_phases": 18, "public_routes": 2, "technical_route_attempts": 16,
    }, "scenario, execution, route, cell, or calibration denominator differs")
    for host in HOSTS:
        row = model["hosts"][host]
        require(row["development_scenarios"] == 20 and row["final_scenarios"] == 240
                and row["fault_phases"] == 9 and row["faults"] == ["F01", "F02", "F03"]
                and row["public_route"] == "passed-audited"
                and row["technical_route_attempts"] == 8 and row["cleanup_confirmed"],
                f"{host}: incomplete matrix, routes, or cleanup")
        require(len(row["candidate_archive_sha256"]) == len(row["candidate_binary_sha256"]) == 64,
                f"{host}: candidate digest missing")
    require(model.get("false_greens") == 0 and model.get("historical_false_green_disclosed") is True,
            "false-green history was hidden or miscounted")
    require(model.get("saved_state_coverage_credit") == 0,
            "Pick's scenario suite claims saved-state coverage it did not earn")
    require(model.get("human_participants") == 0 and model.get("usability") == "unmeasured",
            "human usability evidence is invented")
    require(model.get("delivered_ci") == "not-run", "preview was misrepresented as delivered CI")
    require(model.get("admission_credit") == 0, "model controls cannot self-grant admission")


def corruption_controls(model: dict) -> list[str]:
    corruptions = [
        ("candidate", lambda m: m.update(candidate="v0.4.0-rc.7")),
        ("source", lambda m: m.update(source_pin="0" * 40)),
        ("receipt_binding", lambda m: m["audit_receipt_sha256"].update(final="0" * 64)),
        ("host_omission", lambda m: m["hosts"].pop("darwin")),
        ("scenario_total", lambda m: m["totals"].update(distinct_scenarios=19)),
        ("ordinary_denominator", lambda m: m["totals"].update(ordinary_attempts=479)),
        ("calibration_denominator", lambda m: m["totals"].update(fault_phases=17)),
        ("false_green", lambda m: m.update(false_greens=1)),
        ("historical_false_green", lambda m: m.update(historical_false_green_disclosed=False)),
        ("fault_identity", lambda m: m["hosts"]["linux"].update(faults=["F01", "F02", "F04"])),
        ("cleanup", lambda m: m["hosts"]["darwin"].update(cleanup_confirmed=False)),
        ("public_route", lambda m: m["hosts"]["linux"].update(public_route="preview-only")),
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
            raise ValueError(f"model control accepted semantic corruption: {name}")
    return rejected


def main() -> None:
    model = build_model()
    validate(model)
    rejected = corruption_controls(model)
    result = {**model, "semantic_corruptions_rejected": rejected,
              "semantic_corruptions_rejected_count": len(rejected)}
    encoded = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if OUTPUT.exists():
        require(OUTPUT.read_text(encoding="utf-8") == encoded,
                "immutable Pick model-control receipt already exists with different content")
    else:
        OUTPUT.write_text(encoded, encoding="utf-8", newline="\n")
    print(json.dumps({"status": result["status"], "project": "pick",
                      "semantic_corruptions_rejected": len(rejected), "admission_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
