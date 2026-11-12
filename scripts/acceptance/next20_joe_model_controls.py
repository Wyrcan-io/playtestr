"""Reconstruct JOE's exact rc.7 model and reject twelve semantic tamperings."""
import copy
import json
from pathlib import Path

from readiness_evidence import immutable_json, sha256
from next20_check import DOC, RAW

PROJECT = DOC / "joe"
PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
CANDIDATE = "v0.4.0-rc.7"
HOSTS = ("linux", "darwin")
INPUTS = {
    "scenario": PROJECT / "scenario-development-artifact-audit-run43063382292-v1.json",
    "final": PROJECT / "final-qualification-artifact-audit-run43063382262-v1.json",
    "fault": PROJECT / "fault-calibration-audit-run43063382475-v1.json",
    "public": PROJECT / "public-route-readback-run43063382264-v1.json",
    "oracle": PROJECT / "oracle-calibration-artifact-audit-run43069489959-v1.json",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def persist_immutable(path, value):
    if path.exists():
        require(json.loads(path.read_text(encoding="utf-8")) == value,
                "existing immutable JOE model-control output differs: " + path.name)
        return
    immutable_json(path, value)


def load_inputs():
    values = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in INPUTS.items()}
    require(values["scenario"].get("status") == "development-attempts-independently-audited-not-qualified" and
            values["scenario"].get("workflow_run") == 43063382292 and
            values["scenario"].get("candidate") == CANDIDATE and
            values["scenario"].get("attempts_per_host") == 20 and
            values["scenario"].get("project_admission_credit") == 0,
            "JOE development source audit identity/count differs")
    require(values["final"].get("status") == "final-scenario-series-independently-audited" and
            values["final"].get("workflow_run") == 43063382262 and
            values["final"].get("candidate") == CANDIDATE and
            values["final"].get("attempts_per_host") == 240 and
            values["final"].get("qualification_scenarios") == 20 and
            values["final"].get("project_admission_credit") == 0,
            "JOE final qualification audit identity/count differs")
    require(values["fault"].get("status") == "source-fault-calibration-audited" and
            values["fault"].get("candidate") == CANDIDATE and values["fault"].get("target_pin") == PIN and
            values["fault"].get("distinct_detected_source_faults") == 3 and
            values["fault"].get("calibration_phase_executions") == 18 and
            values["fault"].get("baseline_passes") == 6 and
            values["fault"].get("fault_contract_rejections") == 6 and
            values["fault"].get("restored_recovery_passes") == 6 and
            values["fault"].get("owned_target_trees_removed") == 18 and
            values["fault"].get("runner_process_groups_reaped") == 18 and
            values["fault"].get("admission_credit") == 0,
            "JOE fault calibration audit identity/count/restoration differs")
    require(values["public"].get("status") == "public-route-readback-passed-not-project-admitted" and
            values["public"].get("candidate") == CANDIDATE and
            values["public"].get("project_admission_credit") == 0 and
            values["oracle"].get("candidate") == CANDIDATE and
            values["oracle"].get("workflow_run") == 43069489959 and
            values["oracle"].get("admission_credit") == 0,
            "JOE public route/oracle audit identity differs")
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v2.json").read_text(encoding="utf-8"))
    require(freeze.get("version") == CANDIDATE and freeze.get("series") == "native-exit-v2",
            "JOE candidate freeze differs")
    return values, freeze


def build_model():
    values, freeze = load_inputs()
    models = {}
    scenario_hosts = values["scenario"]["provider_artifacts"]
    final_hosts = values["final"]["provider_artifacts"]
    for host in HOSTS:
        scenario = scenario_hosts[host]
        final = final_hosts[host]
        public = values["public"]["hosts"][host]
        oracle = values["oracle"]["hosts"][host]
        candidate = next(row for row in freeze["cells"] if row["host"] == host)
        faults = [row for row in values["fault"]["provider_artifacts"] if row.get("host") == host]
        require(scenario.get("candidate_archive_sha256") == final.get("candidate_archive_sha256") ==
                oracle.get("candidate_archive_sha256") == candidate["archive_sha256"] and
                scenario.get("candidate_binary_sha256") == final.get("candidate_binary_sha256") ==
                oracle.get("runner_sha256") == candidate["binary_sha256"],
                "JOE native source/final/oracle candidate identities are mixed")
        require(scenario.get("source_pin") == final.get("source_pin") == PIN and
                scenario.get("scenario_attempts") == 20 and len(scenario.get("outcomes", [])) == 20 and
                scenario.get("scenario_passes") == 20 and scenario.get("scenario_failures") == 0,
                "JOE development source audit does not have all twenty passing attempts")
        require(final.get("scenario_attempts") == 240 and final.get("scenario_passes") == 240 and
                final.get("scenario_failures") == 0 and final.get("build_commands_audited") == 7 and
                final.get("source_tree_removal_confirmed") and final.get("owned_processes_absent"),
                "JOE final native qualification is incomplete")
        require(len(faults) == 3 and len({row.get("fault") for row in faults}) == 3 and
                all(row.get("candidate") == CANDIDATE and row.get("target_pin") == PIN and
                    row.get("status") == "baseline-detected-restored" and
                    row.get("source_map_restored") and row.get("owned_source_phase_trees_removed") == 3 and
                    len(row.get("phases", [])) == 3 and
                    [phase.get("phase") for phase in row["phases"]] == ["baseline", "fault", "recovery"] and
                    all(phase.get("runner_process_tree_confirmed") and phase.get("target_and_workspace_cleanup_confirmed")
                        for phase in row["phases"]) for row in faults),
                "JOE native fault/restoration phases are incomplete")
        require(public.get("processes_confirmed_absent") and public.get("target_removed") and
                len(public.get("attempts", [])) == 9 and public.get("first_use_report_sha256") and
                public.get("diagnosis_category") and
                public.get("runner_binary_sha256") == candidate["binary_sha256"] and
                oracle.get("positive_cases") == 1 and oracle.get("negative_cases") == 10 and
                oracle.get("all_negative_state_rejections") and
                all(row.get("same_invocation_state") and row.get("cleanup_confirmed")
                    for row in oracle.get("cases", [])),
                "JOE exact-candidate public route/oracle evidence is incomplete")
        models[host] = {
            "host": host, "architecture": scenario["architecture"],
            "candidate_archive_sha256": candidate["archive_sha256"],
            "candidate_binary_sha256": candidate["binary_sha256"],
            "development": {"run": values["scenario"]["workflow_run"], "attempts": 20, "passed": 20,
                            "source_audit_sha256": sha256(INPUTS["scenario"])},
            "final": {"run": values["final"]["workflow_run"], "repetitions": 12,
                      "scenarios": 20, "ordinary": 240, "passed": 240,
                      "source_audit_sha256": sha256(INPUTS["final"]),
                      "declaration_sha256": values["final"]["scenario_declaration_sha256"]},
            "faults": [{"id": row["fault"], "phases": [phase["phase"] for phase in row["phases"]],
                        "mutation_detected": row["phases"][1]["scenario_status"] == "expected-target-fault-rejection",
                        "source_restored": row["source_map_restored"],
                        "trees_removed": row["owned_source_phase_trees_removed"]}
                       for row in sorted(faults, key=lambda value: value["fault"])],
            "public_route": {"run": values["public"]["workflow_run"], "passed": True,
                             "first_failures_preserved": True,
                             "audit_sha256": sha256(INPUTS["public"])},
            "oracle": {"run": values["oracle"]["workflow_run"], "positive": 1, "negative": 10,
                       "same_invocation_state": True, "audit_sha256": sha256(INPUTS["oracle"])},
            "cleanup": {"source_tree_removed": final["source_tree_removal_confirmed"],
                        "owned_processes_absent": final["owned_processes_absent"],
                        "fault_trees_removed": 9, "public_target_removed": public["target_removed"]},
        }
    model = {
        "schema_version": 1, "canonical_project": "joe-editor/joe", "repository": "joe-editor/joe",
        "pin": PIN, "candidate": CANDIDATE, "candidate_series": "native-exit-v2",
        "hosts": models, "scenario_count": 20, "normal_scenarios": 8, "edge_scenarios": 12,
        "current_candidate_admission_credit": 0,
    }
    return model, values


def validate(model):
    expected, _ = build_model()
    require(model == expected, "tampered JOE model differs from the independently reconstructed evidence")
    require(set(model["hosts"]) == set(HOSTS) and model["scenario_count"] == 20 and
            model["normal_scenarios"] == 8 and model["edge_scenarios"] == 12 and
            model["current_candidate_admission_credit"] == 0,
            "JOE reconstructed model totals differ")
    for host in HOSTS:
        row = model["hosts"][host]
        require(row["final"]["ordinary"] == row["final"]["passed"] == 240 and
                len(row["faults"]) == 3 and all(fault["mutation_detected"] and fault["source_restored"]
                                               for fault in row["faults"]) and
                row["oracle"]["negative"] == 10 and row["cleanup"]["owned_processes_absent"],
                "JOE host qualification model is incomplete")
    return True


def corrupt(model, path, value):
    result = copy.deepcopy(model)
    parent = result
    for key in path[:-1]:
        parent = parent[key]
    parent[path[-1]] = value
    return result


def main():
    model, values = build_model()
    validate(model)
    variants = [
        ("missing-native-host", ["hosts"], {"linux": model["hosts"]["linux"]}),
        ("stale-runner-archive", ["hosts", "linux", "candidate_archive_sha256"], "0" * 64),
        ("duplicate-canonical-project", ["canonical_project"], "joe-editor/joe + joe-editor/joe"),
        ("changed-executed-contract", ["hosts", "linux", "final", "declaration_sha256"], "0" * 64),
        ("missing-mutation-restoration", ["hosts", "linux", "faults", 0, "source_restored"], False),
        ("cross-invocation-state", ["hosts", "darwin", "oracle", "same_invocation_state"], False),
        ("partial-repetition-series", ["hosts", "linux", "final", "ordinary"], 239),
        ("lost-first-failure", ["hosts", "linux", "public_route", "first_failures_preserved"], False),
        ("false-cleanup-claim", ["hosts", "darwin", "cleanup", "owned_processes_absent"], False),
        ("missing-provider-payload", ["hosts", "darwin", "oracle", "negative"], 0),
        ("stale-whole-source-audit", ["hosts", "linux", "final", "source_audit_sha256"], "f" * 64),
        ("mixed-candidate-credit", ["candidate"], "v0.4.0-rc.6"),
    ]
    controls = []
    for name, path, value in variants:
        changed = corrupt(model, path, value)
        try:
            validate(changed)
        except (ValueError, KeyError, TypeError, IndexError) as error:
            controls.append({"control": name, "rejected": True, "path": path,
                             "reason": str(error)})
        else:
            raise ValueError("tampered JOE model was accepted: " + name)
    require(len(controls) == 12 and all(row["rejected"] for row in controls),
            "JOE model-tamper control count differs")
    validate(model)
    persist_immutable(PROJECT / "actual-model-v1.json", model)
    persist_immutable(PROJECT / "model-controls-v1.json", {
        "schema_version": 1, "project": "joe", "repository": "joe-editor/joe", "pin": PIN,
        "candidate": CANDIDATE, "model": "actual-model-v1.json",
        "model_sha256": sha256(PROJECT / "actual-model-v1.json"),
        "input_audits": {name: {"path": path.relative_to(DOC).as_posix(), "sha256": sha256(path)}
                         for name, path in INPUTS.items()},
        "hosts": {host: model["hosts"][host] for host in HOSTS},
        "semantic_corruptions_rejected": len(controls), "controls": controls,
        "positive_model_restored_and_revalidated": True, "admission_credit": 0,
        "scope": "Reconstructed JOE rc.7 host models bind independently audited development/final/fault/public/oracle evidence. Twelve altered copies were rejected; the unchanged positive model revalidated. No admission credit is granted by this model-control receipt.",
    })
    print("JOE exact-candidate models reconstructed; 12 tampered models rejected; 0 admission credit.")


if __name__ == "__main__":
    main()
