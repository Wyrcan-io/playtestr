"""Independently audit fzy's native source-fault calibration ZIP packets."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC, RAW, ROOT
from next20_fzy_fault_calibration import DECLARATION, PHASES, load_contract
from readiness_evidence import immutable_json, sha256


PROJECT = DOC / "fzy"
FREEZE = DOC / "replacement-candidate-freeze-native-exit-v3.json"
ROOT_MEMBER = "artifacts/runner-readiness-next-twenty-project-pass/"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def object_bytes(data, label):
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON object in {label}") from error
    require(isinstance(value, dict), f"{label} must contain an object")
    return value


def inspect_zip(path, byte_count, expected_sha, host):
    raw = Path(path).read_bytes()
    require(len(raw) == byte_count and digest(raw) == expected_sha,
            f"{host}: provider artifact byte count or SHA-256 differs")
    files = {}
    expanded = 0
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [entry.filename for entry in infos]
        require(len(names) == len(set(names)) and archive.testzip() is None,
                f"{host}: ZIP duplicate member or CRC failure")
        for info in infos:
            member = PurePosixPath(info.filename)
            mode = info.external_attr >> 16
            require(not member.is_absolute() and ".." not in member.parts
                    and "\\" not in info.filename and not info.flag_bits & 1
                    and mode & 0o170000 != 0o120000,
                    f"{host}: unsafe ZIP member {info.filename}")
            require(info.file_size <= 8 * 1024**2,
                    f"{host}: ZIP member exceeds the reviewed bound")
            expanded += info.file_size
            require(expanded <= 64 * 1024**2,
                    f"{host}: expanded ZIP exceeds the reviewed bound")
            if not info.is_dir():
                files[info.filename] = archive.read(info)
    return files, {"zip_bytes": len(raw), "zip_sha256": digest(raw),
                   "zip_entries": len(infos), "expanded_bytes": expanded}


def repo_member(path):
    value = Path(path).as_posix()
    require(value.startswith(ROOT_MEMBER), "evidence path is outside this campaign root")
    return value[len(ROOT_MEMBER):]


def audit_host(host, zip_path, provider, run_id, run_attempt):
    files, zip_stats = inspect_zip(zip_path, provider["artifact_bytes"],
                                   provider["artifact_sha256"], host)

    def get(name):
        require(name in files, f"{host}: missing ZIP member {name}")
        return files[name]

    def obj(name):
        return object_bytes(get(name), name)

    declaration, scenario, freeze, fault_rows = load_contract()
    host_cell = next(row for row in freeze["cells"] if row["host"] == host)
    installed = obj(f"candidate-native-exit-v3/{host}/installed.json")
    require(installed.get("archive_sha256") == host_cell["archive_sha256"]
            and installed.get("binary_sha256") == host_cell["binary_sha256"],
            f"{host}: candidate installation differs from frozen rc.8 cell")

    summary_path = f"fzy/fault-calibration-v1/run-{run_id}-{host}.json"
    summary = obj(summary_path)
    require(summary.get("project") == "fzy" and summary.get("host") == host
            and summary.get("pin") == declaration["pin"]
            and summary.get("candidate") == "v0.4.0-rc.8"
            and summary.get("fault_declaration_sha256") == sha256(DECLARATION)
            and summary.get("scenario_declaration_sha256") == sha256(PROJECT / "scenario-declaration-v1.json")
            and summary.get("phase_execution_count") == 9
            and summary.get("admission_credit") == 0,
            f"{host}: fault run summary identity differs")

    scenarios = {row[1]["id"]: row for row in fault_rows}
    require(len(summary.get("results", [])) == 9,
            f"{host}: phase result denominator differs")
    seen = set()
    audited = []
    for phase_receipt in summary["results"]:
        fault_id = phase_receipt.get("fault_id")
        phase_name = phase_receipt.get("phase")
        key = (fault_id, phase_name)
        require(fault_id in {row[0]["id"] for row in fault_rows}
                and phase_name in {"baseline", "fault", "restored"}
                and key not in seen,
                f"{host}: duplicate or undeclared fault phase")
        seen.add(key)
        fault, case, spec_path = next(row for row in fault_rows if row[0]["id"] == fault_id)
        require(phase_receipt.get("scenario_id") == case["id"]
                and phase_receipt.get("scenario_sha256") == sha256(spec_path)
                and phase_receipt.get("source_archive_sha256") == declaration["source_archive_sha256"]
                and phase_receipt.get("candidate_archive_sha256") == host_cell["archive_sha256"]
                and phase_receipt.get("candidate_binary_sha256") == host_cell["binary_sha256"]
                and phase_receipt.get("host") == host,
                f"{host} {fault_id} {phase_name}: source/scenario/candidate binding differs")
        evidence = (f"fzy/fault-calibration-v1/{fault_id}/{phase_name}/{host}")
        def local(name):
            return get(evidence + "/" + name)

        require(digest(local("source.tar.gz")) == declaration["source_archive_sha256"],
                f"{host} {fault_id} {phase_name}: pinned source archive differs")
        acquisition = object_bytes(local("acquisition.json"), "acquisition.json")
        build = object_bytes(local("pristine-build.json"), "pristine-build.json")
        runtime = object_bytes(local("pristine-runtime.json"), "pristine-runtime.json")
        require(acquisition.get("repository") == declaration["repository"]
                and acquisition.get("pin") == declaration["pin"]
                and acquisition.get("archive_sha256") == declaration["source_archive_sha256"]
                and build.get("pin") == declaration["pin"]
                and build.get("host") == host
                and build.get("source_archive_sha256") == declaration["source_archive_sha256"]
                and build.get("upstream_tests") == "passed"
                and runtime.get("kind") == "native"
                and runtime.get("native_sha256") == build.get("binary_sha256"),
                f"{host} {fault_id} {phase_name}: pristine upstream build/runtime evidence differs")
        verify_logs(files, evidence + "/pristine-build-logs", build.get("commands", []),
                    host, fault_id, phase_name, "pristine")

        target_binary_sha = build["binary_sha256"]
        if phase_name == "fault":
            fault_build = object_bytes(local("fault-build-v1.json"), "fault-build-v1.json")
            mutation = phase_receipt.get("source_mutation")
            require(isinstance(mutation, dict)
                    and mutation.get("id") == fault_id
                    and mutation.get("baseline_source_sha256") == fault["baseline_source_sha256"]
                    and mutation.get("mutated_source_sha256") == fault["mutated_source_sha256"]
                    and fault_build.get("mutated_source_sha256") == fault["mutated_source_sha256"]
                    and fault_build.get("pristine_acquired_source_unchanged") is True
                    and fault_build.get("upstream_tests") == "passed on pristine source before source mutation"
                    and digest(local("mutated-source.c")) == fault["mutated_source_sha256"]
                    and digest(local("mutated-fzy")) == fault_build.get("mutated_binary_sha256")
                    and mutation.get("mutated_binary_sha256") == fault_build.get("mutated_binary_sha256"),
                    f"{host} {fault_id}: isolated source mutation/build identity differs")
            target_binary_sha = fault_build["mutated_binary_sha256"]
            verify_logs(files, evidence + "/fault-build-logs", fault_build.get("commands", []),
                        host, fault_id, phase_name, "fault")
            require(digest(local("mutated-fzy")) == phase_receipt.get("target_binary_sha256"),
                    f"{host} {fault_id}: actual fault target binary differs from the report phase")
        require(phase_receipt.get("target_binary_sha256") == target_binary_sha,
                f"{host} {fault_id} {phase_name}: target binary hash differs")

        report_member = repo_member(phase_receipt["report"])
        report_data = get(report_member)
        require(digest(report_data) == phase_receipt["report_sha256"],
                f"{host} {fault_id} {phase_name}: report digest differs")
        report = object_bytes(report_data, report_member)
        require(report.get("report_version") == 3 and report.get("runner_version") == "v0.4.0-rc.8"
                and report.get("summary", {}).get("total") == 1
                and len(report.get("results", [])) == 1,
                f"{host} {fault_id} {phase_name}: report schema/candidate/denominator differs")
        result = report["results"][0]
        attempt = phase_receipt["runner_attempt_id"]
        expected_phase = PHASES[phase_name]
        expected_exit = 1 if phase_name == "fault" else 0
        started = obj(f"events/{attempt}-started.json")
        identified = obj(f"events/{attempt}-identified.json")
        launched = obj(f"events/{attempt}-launched.json")
        finished = obj(f"events/{attempt}-finished.json")
        require(started.get("project") == "fzy" and started.get("phase") == expected_phase
                and str(started.get("ci_run_id")) == str(run_id)
                and str(started.get("ci_run_attempt")) == str(run_attempt)
                and started.get("expected_exit") == expected_exit
                and identified.get("project") == "fzy" and identified.get("phase") == expected_phase
                and launched.get("project") == "fzy" and launched.get("phase") == expected_phase
                and isinstance(launched.get("pid"), int) and launched["pid"] > 0
                and finished.get("project") == "fzy" and finished.get("phase") == expected_phase
                and finished.get("category") == "passed" and finished.get("exit_code") == expected_exit
                and finished.get("harness_cleanup") == "harness_process_reaped",
                f"{host} {fault_id} {phase_name}: runner event sequence/launch/exit/cleanup differs")
        identity_link = identified.get("identity", {})
        identity_path = identity_link.get("manifest", "")
        identity_data = get("identities/" + identity_path)
        require(digest(identity_data) == identity_link.get("sha256"),
                f"{host} {fault_id} {phase_name}: identity manifest hash differs")
        identity = object_bytes(identity_data, identity_path)
        for entry in identity.values():
            if isinstance(entry, dict) and "manifest" in entry and "sha256" in entry:
                nested_data = get("identities/" + entry["manifest"])
                require(digest(nested_data) == entry["sha256"],
                        f"{host} {fault_id} {phase_name}: nested identity digest differs")

        require(result.get("target", {}).get("exited") is True
                and result.get("cleanup", {}).get("confirmed_exited") is True
                and result.get("workspace", {}).get("cleaned") is True
                and result.get("invocation_id") == phase_receipt.get("invocation_id"),
                f"{host} {fault_id} {phase_name}: process/workspace cleanup or invocation differs")
        failed = [step for step in result.get("steps", []) if step.get("status") == "failed"]
        if phase_name == "fault":
            require(result.get("status") == "failed"
                    and result.get("failure", {}).get("category") == fault["expected_failure_category"]
                    and len(failed) == 1 and failed[0].get("number") == fault["expected_failure_step"]
                    and report.get("summary", {}).get("failed") == 1
                    and phase_receipt.get("classification") == "expected-target-fault-rejection",
                    f"{host} {fault_id}: source fault escaped its exact public detection boundary")
        else:
            require(result.get("status") == "passed" and result.get("failure") is None and not failed
                    and result.get("target", {}).get("exit_code") == case["expected_target_exit"]
                    and phase_receipt.get("classification") == "passed",
                    f"{host} {fault_id} {phase_name}: pristine/restored scenario failed")

        window = f"rebuild-fault-{fault_id.lower()}-{phase_name}-{host}"
        cleanup_root = evidence + "/cleanup-proof"
        process = object_bytes(get(cleanup_root + "/process-proof-" + window + ".json"), "process proof")
        inventory = object_bytes(get(cleanup_root + "/cleanup-inventory.json"), "cleanup inventory")
        removed = object_bytes(get(cleanup_root + "/removed.json"), "source removal proof")
        require(process.get("confirmed_no_matching_live_processes") is True
                and process.get("matching_live_processes") == []
                and digest(get(cleanup_root + "/process-proof-" + window + ".json"))
                == inventory.get("process_proof_sha256")
                and inventory.get("source_restored_exact") is True
                and removed.get("removed") is True and removed.get("source_restored_exact") is True,
                f"{host} {fault_id} {phase_name}: actual source/process cleanup receipt differs")
        seen.add(key)
        audited.append({"fault_id": fault_id, "phase": phase_name,
                        "scenario_id": case["id"], "runner_attempt_id": attempt,
                        "report_sha256": phase_receipt["report_sha256"],
                        "classification": phase_receipt["classification"]})

    require(seen == {(fault["id"], phase) for fault, _, _ in fault_rows
                     for phase in ("baseline", "fault", "restored")},
            f"{host}: fault/phase matrix differs")
    require(sum(row["phase"] == "fault" and row["classification"] == "expected-target-fault-rejection"
                for row in audited) == 3,
            f"{host}: distinct detected source fault count differs")
    return {"host": host, **zip_stats, "provider_artifact_id": provider["artifact_id"],
            "candidate_archive_sha256": host_cell["archive_sha256"],
            "candidate_binary_sha256": host_cell["binary_sha256"],
            "audited_phases": audited, "phase_execution_count": len(audited),
            "distinct_detected_source_faults": 3}


def verify_logs(files, root, commands, host, fault, phase, label):
    require(isinstance(commands, list) and commands,
            f"{host} {fault} {phase}: {label} build commands are missing")
    for command in commands:
        name = PurePosixPath(command.get("log", "")).name
        member = root + "/" + name
        require(name and member in files and digest(files[member]) == command.get("output_sha256")
                and len(files[member]) == command.get("output_bytes"),
                f"{host} {fault} {phase}: {label} build log differs: {name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--run-attempt", type=int, default=1)
    parser.add_argument("--linux-zip", required=True)
    parser.add_argument("--linux-artifact-id", type=int, required=True)
    parser.add_argument("--linux-bytes", type=int, required=True)
    parser.add_argument("--linux-sha256", required=True)
    parser.add_argument("--darwin-zip", required=True)
    parser.add_argument("--darwin-artifact-id", type=int, required=True)
    parser.add_argument("--darwin-bytes", type=int, required=True)
    parser.add_argument("--darwin-sha256", required=True)
    parser.add_argument("--output", default=str(PROJECT / "fault-calibration-artifact-audit-v1.json"))
    args = parser.parse_args()
    require(1 <= args.run_attempt <= 99 and 1 <= args.run_id <= 10**12,
            "provider run identity is outside the reviewed bound")
    providers = {"linux": {"artifact_id": args.linux_artifact_id,
                           "artifact_bytes": args.linux_bytes,
                           "artifact_sha256": args.linux_sha256},
                 "darwin": {"artifact_id": args.darwin_artifact_id,
                            "artifact_bytes": args.darwin_bytes,
                            "artifact_sha256": args.darwin_sha256}}
    results = [audit_host(host, path, providers[host], args.run_id, args.run_attempt)
               for host, path in (("linux", args.linux_zip), ("darwin", args.darwin_zip))]
    audit = {"schema_version": 1, "project": "fzy", "run_id": args.run_id,
             "run_attempt": args.run_attempt, "candidate": "v0.4.0-rc.8",
             "candidate_series": "native-exit-v3",
             "fault_declaration_sha256": sha256(DECLARATION),
             "results": results, "audited_phases": sum(row["phase_execution_count"] for row in results),
             "distinct_detected_source_faults": min(row["distinct_detected_source_faults"] for row in results),
             "calibration_admission_credit": 0,
             "scope": "Independent bounded ZIP, exact provider digests, source/build/logs, candidate, event/identity, report oracle, and source/process cleanup readback."}
    immutable_json(Path(args.output), audit)
    print(json.dumps({"project": "fzy", "run_id": args.run_id,
                      "audited_phases": audit["audited_phases"],
                      "distinct_detected_source_faults": audit["distinct_detected_source_faults"],
                      "audit_sha256": sha256(Path(args.output))}, sort_keys=True))


if __name__ == "__main__":
    main()
