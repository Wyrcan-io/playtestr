"""Independently audit the two-host Pick source-fault calibration artifacts."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "docs/validation/runner-readiness-next-twenty-project-pass"
RAW = "pick/fault-calibration/v1"
PIN = "caae95938359b2e814b3e7406f396f486c9d99fb"
SOURCE_SHA256 = "e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653"
BASELINE_SOURCE_SHA256 = "b2a9252d7c684da668b5d306b8e41ed5fcb169a60fd3bb29e0897031a70c890a"
PHASES = {"baseline": "passed", "fault": "expected-target-fault-rejection", "restored": "passed"}


def need(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def audit_host(host, directory, run_id, declaration, freeze, faults):
    directory = Path(directory).resolve(strict=True)
    base = directory / RAW
    summary_path = base / host / "summary.json"
    summary = read_json(summary_path)
    need(summary.get("schema_version") == 1 and summary.get("project") == "pick"
         and summary.get("host") == host and str(summary.get("run_id")) == str(run_id)
         and summary.get("pin") == PIN and summary.get("phase") == "fault-calibration"
         and summary.get("phase_count") == 9 and summary.get("passed_pristine_and_restored") == 6
         and summary.get("rejected_corrupted") == 3 and summary.get("false_greens") == 0
         and summary.get("admission_credit") == 0,
         f"{host}: summary identity/counts/status differ")
    need(summary.get("fault_declaration_sha256") == digest(DOC / "pick/fault-declaration-v1.json"),
         f"{host}: fault declaration digest differs")
    need(summary.get("scenario_declaration_sha256") == digest(DOC / "pick/scenario-declaration-v10.json"),
         f"{host}: frozen scenario declaration digest differs")

    candidate = next(row for row in freeze["cells"] if row["host"] == host)
    installed_path = directory / "candidate-native-exit-v3" / host / "installed.json"
    installed = read_json(installed_path)
    need(installed.get("archive_sha256") == candidate["archive_sha256"]
         and installed.get("binary_sha256") == candidate["binary_sha256"],
         f"{host}: installed candidate differs from frozen archive/binary")

    outputs = []
    for fault_index, (fault, manifest, scenario) in enumerate(faults, 1):
        triplet_path = base / fault["id"] / host / "triplet.json"
        triplet = read_json(triplet_path)
        need(triplet.get("schema_version") == 1 and triplet.get("fault_id") == fault["id"]
             and triplet.get("host") == host and triplet.get("scenario_id") == scenario["id"]
             and triplet.get("pin") == PIN and triplet.get("admission_credit") == 0,
             f"{host}/{fault['id']}: triplet identity differs")
        need(triplet.get("fault_manifest_sha256") == digest(manifest),
             f"{host}/{fault['id']}: fault manifest hash differs")
        phases = {}
        for phase_index, (phase, expected_status) in enumerate(PHASES.items(), 1):
            folder = base / fault["id"] / phase / host
            receipt_path, report_path = folder / "phase-receipt.json", folder / "report.json"
            receipt, report = read_json(receipt_path), read_json(report_path)
            phase_result = receipt.get("phase_result") or {}
            case_rows = report.get("results") or []
            need(receipt.get("schema_version") == 1 and receipt.get("project") == "pick"
                 and str(receipt.get("run_id")) == str(run_id)
                 and receipt.get("fault_id") == fault["id"] and receipt.get("host") == host
                 and receipt.get("phase") == phase, f"{host}/{fault['id']}/{phase}: receipt identity differs")
            expected_cleanup_log = ("Verified exact source restoration and "
                                    f"{(fault_index - 1) * 3 + phase_index} target/workspace cleanups; "
                                    "retained provenance; owned source/runtime removed")
            need(receipt.get("cleanup", {}).get("active_target_absent") is True
                 and receipt.get("cleanup", {}).get("source_restored_exact") is True
                 and digest(folder / "cleanup.log") == receipt["cleanup"].get("log_sha256")
                 and expected_cleanup_log == (folder / "cleanup.log").read_text(encoding="utf-8").strip(),
                 f"{host}/{fault['id']}/{phase}: cleanup/restoration receipt differs")
            need(report.get("report_version") == 3 and len(case_rows) == 1,
                 f"{host}/{fault['id']}/{phase}: report schema/denominator differs")
            case = case_rows[0]
            receipt_report_path = (Path("artifacts/runner-readiness-next-twenty-project-pass") /
                                   report_path.relative_to(directory)).as_posix()
            need(digest(report_path) == phase_result.get("report_sha256")
                 and phase_result.get("report") == receipt_report_path
                 and phase_result.get("scenario_id") == scenario["id"]
                 and phase_result.get("scenario_sha256") == digest(DOC / scenario["spec_path"])
                 and phase_result.get("source_archive_sha256") == SOURCE_SHA256
                 and phase_result.get("candidate_archive_sha256") == candidate["archive_sha256"]
                 and phase_result.get("candidate_binary_sha256") == candidate["binary_sha256"]
                 and phase_result.get("target_cleanup_confirmed") is True
                 and phase_result.get("workspace_cleaned") is True
                 and case.get("cleanup", {}).get("confirmed_exited") is True
                 and case.get("workspace", {}).get("cleaned") is True
                 and case.get("target", {}).get("exited") is True,
                 f"{host}/{fault['id']}/{phase}: report and phase receipt disagree")

            if phase == "fault":
                failures = [step for step in case.get("steps", []) if step.get("status") == "failed"]
                need(phase_result.get("status") == expected_status and case.get("status") == "failed"
                     and case.get("failure", {}).get("category") in fault["expected_failure_categories"]
                     and len(failures) == 1
                     and failures[0].get("number") == fault["expected_failure_step"]
                     and phase_result.get("failure_category") == case["failure"]["category"]
                     and phase_result.get("failed_step") == fault["expected_failure_step"],
                     f"{host}/{fault['id']}: corrupted target was not rejected at the held contract oracle")
                mutation_path = folder / "mutated-source" / fault["source_file"]
                need(digest(mutation_path) == fault["mutated_source_sha256"]
                     and phase_result.get("source_mutation", {}).get("mutated_source_sha256") ==
                         fault["mutated_source_sha256"],
                     f"{host}/{fault['id']}: mutated source bytes differ")
            else:
                need(phase_result.get("status") == "passed" and case.get("status") == "passed"
                     and case.get("failure") is None
                     and not [step for step in case.get("steps", []) if step.get("status") == "failed"]
                     and phase_result.get("source_mutation") is None
                     and phase_result.get("upstream_tests") == "passed",
                     f"{host}/{fault['id']}/{phase}: pristine or restored target did not pass")

            event_path = directory / "events" / (phase_result["runner_command_id"] + "-finished.json")
            event = read_json(event_path)
            expected_runner_exit = 1 if phase == "fault" else 0
            need(event.get("category") == "passed" and event.get("exit_code") == expected_runner_exit,
                 f"{host}/{fault['id']}/{phase}: native runner command event differs")
            phases[phase] = phase_result

        need(phases["baseline"]["source_binary_sha256"] == phases["restored"]["source_binary_sha256"]
             and phases["baseline"]["source_binary_sha256"] != phases["fault"]["source_binary_sha256"],
             f"{host}/{fault['id']}: pristine/mutated/restored binary identity differs")
        for phase, result in phases.items():
            triplet_key = "corrupted" if phase == "fault" else phase
            need(triplet.get(triplet_key) == result,
                 f"{host}/{fault['id']}: triplet copy differs from phase receipt")
        outputs.append({"fault_id": fault["id"], "scenario_id": scenario["id"],
                        "baseline": "passed", "corrupted": "expected-target-fault-rejection",
                        "restored": "passed",
                        "baseline_binary_sha256": phases["baseline"]["source_binary_sha256"],
                        "mutated_binary_sha256": phases["fault"]["source_binary_sha256"],
                        "restored_binary_sha256": phases["restored"]["source_binary_sha256"]})

    need(summary.get("faults") == outputs, f"{host}: summary rows differ from independently audited triplets")
    report_count = len(list(base.rglob("report.json")))
    receipt_count = len(list(base.rglob("phase-receipt.json")))
    need(report_count == receipt_count == 9, f"{host}: expected exactly nine reports and phase receipts")
    return {"host": host, "summary_sha256": digest(summary_path), "phase_count": 9,
            "reports": report_count, "receipts": receipt_count, "candidate_archive_sha256": candidate["archive_sha256"],
            "candidate_binary_sha256": candidate["binary_sha256"], "faults": outputs}


def audit(args):
    provider_path = args.provider_manifest.resolve(strict=True)
    declaration_path = DOC / "pick/fault-declaration-v1.json"
    declaration = read_json(declaration_path)
    freeze_path = ROOT / declaration["candidate_freeze"]
    scenarios_path = ROOT / declaration["scenario_declaration"]
    freeze, scenarios = read_json(freeze_path), read_json(scenarios_path)
    need(declaration.get("project") == "pick" and declaration.get("pin") == PIN
         and declaration.get("source_archive_sha256") == SOURCE_SHA256
         and declaration.get("candidate_freeze_sha256") == digest(freeze_path)
         and declaration.get("scenario_declaration_sha256") == digest(scenarios_path)
         and declaration.get("candidate") == freeze.get("version") == "v0.4.0-rc.8"
         and declaration.get("series") == freeze.get("series") == "native-exit-v3",
         "campaign declaration/freeze identity differs")
    faults = []
    for row in declaration["faults"]:
        manifest = (DOC / row["manifest"]).resolve(strict=True)
        manifest.relative_to((DOC / "pick").resolve(strict=True))
        fault = read_json(manifest)
        need(fault.get("id") == row["id"] and fault.get("scenario_id") == row["scenario_id"]
             and fault.get("project") == "pick" and fault.get("pin") == PIN
             and fault.get("source_archive_sha256") == SOURCE_SHA256
             and fault.get("baseline_source_sha256") == BASELINE_SOURCE_SHA256,
             f"{row['id']}: reviewed source-fault manifest identity differs")
        patch = (DOC / fault["patch"]).resolve(strict=True)
        patch.relative_to((DOC / "pick").resolve(strict=True))
        need(digest(patch) == fault.get("patch_sha256"), f"{row['id']}: patch digest differs")
        scenario = next(item for item in scenarios["scenarios"] if item["id"] == row["scenario_id"])
        faults.append((fault, manifest, scenario))

    provider = read_json(provider_path)
    need(provider.get("run_id") == args.run_id and provider.get("head_sha") == args.head_sha
         and len(provider.get("artifacts", [])) == 2, "provider manifest run/host denominator differs")
    rows = {}
    for artifact in provider["artifacts"]:
        host = artifact["host"]
        need(host in {"linux", "darwin"} and host not in rows, "duplicate/unknown provider host")
        rows[host] = artifact
    need(set(rows) == {"linux", "darwin"}, "provider manifest must bind both native hosts")
    linux = audit_host("linux", args.linux, args.run_id, declaration, freeze, faults)
    darwin = audit_host("darwin", args.darwin, args.run_id, declaration, freeze, faults)
    for report in (linux, darwin):
        artifact = rows[report["host"]]
        need(artifact.get("artifact_id") and artifact.get("artifact_sha256")
             and artifact.get("name", "").endswith(f"-{report['host']}-{args.run_id}"),
             f"{report['host']}: provider artifact identity is incomplete")
    result = {"schema_version": 1, "project": "pick", "run_id": args.run_id,
              "head_sha": args.head_sha, "phase": "fault-calibration-independent-audit",
              "candidate": "v0.4.0-rc.8", "candidate_series": "native-exit-v3",
              "fault_declaration": declaration_path.relative_to(ROOT).as_posix(),
              "fault_declaration_sha256": digest(declaration_path),
              "scenario_declaration_sha256": digest(scenarios_path),
              "hosts": [linux, darwin], "reports": 18, "phase_receipts": 18,
              "pristine_and_restored_passes": 12, "mutated_targets_rejected": 6,
              "false_greens": 0, "source_restoration_confirmed": True,
              "process_and_workspace_cleanup_confirmed": True,
              "provider_manifest": provider_path.relative_to(ROOT).as_posix(),
              "provider_manifest_sha256": digest(provider_path),
              "admission_credit": 0,
              "audited_at_utc": datetime.now(timezone.utc).isoformat()}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"project": "pick", "hosts": 2, "reports": 18,
                      "false_greens": 0, "admission_credit": 0}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--provider-manifest", type=Path, required=True)
    parser.add_argument("--linux", type=Path, required=True)
    parser.add_argument("--darwin", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    audit(args)


if __name__ == "__main__":
    main()
