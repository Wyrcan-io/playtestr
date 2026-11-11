"""Independently audit exact native JOE source-fault calibration artifacts."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile
import zipfile

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256

PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
SOURCE_ARCHIVE_SHA256 = "5e00e2621225a304061c70903ef6490a700a4bbf1fa600c096b5bbb6746f2312"
FREEZE = DOC / "replacement-candidate-freeze-native-exit-v1.json"
DECLARATION = DOC / "joe" / "fault-declaration-v2.json"
SERIES = "native-exit-v1"
CANDIDATE = "v0.4.0-rc.6"
MAX_ARCHIVE_BYTES = 64 * 1024**2
MAX_MEMBER_BYTES = 256 * 1024**2
MAX_EXPANDED_BYTES = 512 * 1024**2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def scenario_contract_hash(fault):
    return sha256(DOC / "joe" / "scenarios-v3" / fault["scenario_id"] / "scenario.json")


def fault_manifest_hash(fault):
    return sha256(DOC / "joe" / fault["manifest"])


def unique_suffix(names, suffix):
    matches = [name for name in names if name.endswith(suffix)]
    require(len(matches) == 1, f"expected one ZIP member ending {suffix!r}; found {len(matches)}")
    return matches[0]


def json_member(archive, names, suffix):
    name = unique_suffix(names, suffix)
    raw = archive.read(name)
    value = json.loads(raw.decode("utf-8"))
    require(isinstance(value, dict), f"ZIP JSON member is not an object: {name}")
    return name, raw, value


def source_map_from_tar(raw, acquisition):
    require(digest(raw) == SOURCE_ARCHIVE_SHA256, "embedded pristine source archive digest differs")
    result = {}
    expanded = 0
    entries = 0
    prefix = None
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as source:
        for member in source:
            entries += 1
            path = PurePosixPath(member.name)
            require(not path.is_absolute() and ".." not in path.parts and "\\" not in member.name,
                    "unsafe pinned source tar path")
            if prefix is None:
                require(len(path.parts) >= 1, "pinned source archive has an empty root")
                prefix = path.parts[0]
            require(path.parts[0] == prefix and (member.isfile() or member.isdir()),
                    "pinned source archive contains an unsupported entry")
            if member.isdir():
                continue
            relative = PurePosixPath(*path.parts[1:]).as_posix()
            require(relative and relative not in result and member.size <= 8 * 1024**2,
                    "duplicate, empty or oversized source member")
            stream = source.extractfile(member)
            require(stream is not None, "pinned source file cannot be read")
            content = stream.read(member.size + 1)
            require(len(content) == member.size, "pinned source member is truncated")
            expanded += len(content)
            result[relative] = digest(content)
    require(entries == acquisition.get("entries") + 1 and
            expanded == acquisition.get("expanded_bytes") and
            result == acquisition.get("source_files"),
            "pinned source tree does not match hosted acquisition source map")
    return result


def verify_archive(path, provider, fault_rows, candidate_cells, declaration_hash):
    raw = path.read_bytes()
    require(len(raw) == provider["size_in_bytes"] and digest(raw) == provider["digest"],
            "local artifact bytes differ from GitHub provider metadata")
    require(not provider.get("expired", False), "provider artifact has expired")
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        require(len(names) == len(set(names)), "duplicate ZIP member paths")
        expanded = 0
        for item in infos:
            name = item.filename
            member_path = PurePosixPath(name)
            require(not member_path.is_absolute() and ".." not in member_path.parts and
                    "\\" not in name and not item.flag_bits & 1,
                    f"unsafe or encrypted ZIP member: {name}")
            require(item.file_size <= MAX_MEMBER_BYTES, f"oversized ZIP member: {name}")
            expanded += item.file_size
            require(expanded <= MAX_EXPANDED_BYTES, "expanded ZIP exceeds audit bound")
        require(archive.testzip() is None, "ZIP CRC validation failed")
        start_name, _, started = json_member(archive, names, "/calibration-start.json")
        finish_name, finish_raw, finished = json_member(archive, names, "/calibration-finished.json")
        require(finished.get("status") == "three-phase-source-fault-calibration-passed" and
                started.get("project") == "joe" and finished.get("project") == "joe" and
                started.get("candidate") == CANDIDATE and finished.get("candidate") == CANDIDATE and
                started.get("pin") == PIN and finished.get("pin") == PIN and
                started.get("fault_declaration_sha256") == declaration_hash and
                finished.get("fault_declaration_sha256") == declaration_hash and
                started.get("fault") == provider["fault"] and finished.get("fault") == provider["fault"] and
                started.get("host") == provider["host"] and finished.get("host") == provider["host"] and
                started.get("expected_phase_count") == 3 and
                started.get("expected_phases") == ["baseline", "fault", "recovery"] and
                [p.get("phase") for p in finished.get("phases", [])] == ["baseline", "fault", "recovery"],
                "calibration start/finish identity or three-phase status differs")
        fault = fault_rows[provider["fault"]]
        require(started.get("scenario_id") == fault["scenario_id"] and
                started.get("scenario_contract_sha256") == scenario_contract_hash(fault) and
                started.get("target_source_archive_sha256") == SOURCE_ARCHIVE_SHA256 and
                started.get("mutation_manifest_sha256") == fault_manifest_hash(fault),
                "calibration does not bind its frozen scenario/source/mutation declaration")
        cell = candidate_cells[provider["host"]]
        require(cell["archive_sha256"] and cell["binary_sha256"], "candidate freeze lacks exact host hashes")
        cleanups = {row.get("phase"): row for row in finished.get("cleanup", [])}
        require(set(cleanups) == {"baseline", "fault", "recovery"} and
                all(row.get("active_target_absent") is True and row.get("status") == "owned target tree removed"
                    for row in cleanups.values()), "one or more native source-tree cleanups are unconfirmed")
        command_rows = finished.get("commands", [])
        require(command_rows and all(row.get("exit_code") == 0 and
                                     "no owned descendants remain" in row.get("process_tree_cleanup", "")
                                     for row in command_rows),
                "bounded build/acquire/cleanup command or descendant cleanup failed")

        source_maps = {}
        source_bytes = None
        phase_results = []
        for phase in ("baseline", "fault", "recovery"):
            phase_receipt_name, phase_receipt_raw, phase_receipt = json_member(
                archive, names, f"/{phase}/phase-receipt.json")
            build_name, build_raw, build = json_member(archive, names, f"/{phase}/build.json")
            runtime_name, runtime_raw, runtime = json_member(archive, names, f"/{phase}/runtime.json")
            acquisition_name, _, acquisition = json_member(archive, names, f"/{phase}/acquisition.json")
            tar_name = unique_suffix(names, f"/{phase}/source.tar.gz")
            if source_bytes is None:
                source_bytes = archive.read(tar_name)
            require(digest(archive.read(tar_name)) == SOURCE_ARCHIVE_SHA256 and
                    acquisition.get("repository") == "joe-editor/joe" and acquisition.get("pin") == PIN and
                    acquisition.get("archive_sha256") == SOURCE_ARCHIVE_SHA256 and
                    acquisition.get("build_hooks_executed") is False,
                    f"{phase} acquisition/source identity differs")
            pristine_map = source_map_from_tar(source_bytes, acquisition)
            expected_map = dict(pristine_map)
            mutation = build.get("source_mutation")
            if phase == "fault":
                expected_map[fault["source_file"]] = fault["mutated_source_sha256"]
                require(mutation and mutation.get("id") == provider["fault"] and
                        mutation.get("baseline_source_sha256") == fault["baseline_source_sha256"] and
                        mutation.get("actual_mutated_source_sha256") == fault["mutated_source_sha256"] and
                        mutation.get("mutated_source_sha256") == fault["mutated_source_sha256"] and
                        mutation.get("manifest_sha256") == fault_manifest_hash(fault),
                        "fault build receipt does not bind the frozen source mutation")
                source_member = unique_suffix(names, "/mutated-source/" + fault["source_file"])
                mutated = archive.read(source_member)
                old = __import__("base64").b64decode(fault["mutation_old_base64"], validate=True)
                new = __import__("base64").b64decode(fault["mutation_new_base64"], validate=True)
                pristine_member = source_bytes
                with tarfile.open(fileobj=io.BytesIO(pristine_member), mode="r:gz") as tar:
                    original = None
                    for member in tar:
                        path = PurePosixPath(member.name)
                        if path.parts[1:] == PurePosixPath(fault["source_file"]).parts:
                            handle = tar.extractfile(member)
                            original = handle.read(member.size + 1) if handle else None
                            break
                require(original is not None and digest(original) == fault["baseline_source_sha256"] and
                        original.count(old) == 1 and original.replace(old, new, 1) == mutated and
                        digest(mutated) == fault["mutated_source_sha256"],
                        "mutated target source bytes do not equal the unique frozen patch on pinned source")
            else:
                require(mutation is None, f"{phase} unexpectedly contains a source mutation")
            source_map_hash = hashlib.sha256(json.dumps(expected_map, sort_keys=True, ensure_ascii=True,
                separators=(",", ":")).encode()).hexdigest()
            build_hash = digest(build_raw)
            runtime_hash = digest(runtime_raw)
            binary_name = unique_suffix(names, f"/{phase}/install/bin/joe")
            binary = archive.read(binary_name)
            binary_hash = digest(binary)
            require(build.get("project") == "joe" and build.get("pin") == PIN and
                    build.get("host") == provider["host"] and build.get("runtime_kind") == "native" and
                    build.get("source_archive_sha256") == SOURCE_ARCHIVE_SHA256 and
                    build.get("source_file_count") == len(expected_map) and
                    build.get("source_map_sha256") == source_map_hash and
                    build.get("binary_relative_path") == "install/bin/joe" and
                    build.get("binary_sha256") == binary_hash and build.get("binary_bytes") == len(binary) and
                    runtime.get("native_sha256") == binary_hash and runtime.get("host") == provider["host"] and
                    phase_receipt.get("phase") == phase and
                    phase_receipt.get("build_receipt_sha256") == build_hash and
                    phase_receipt.get("runtime_receipt_sha256") == runtime_hash and
                    phase_receipt.get("native_binary_sha256") == binary_hash and
                    phase_receipt.get("source_archive_sha256") == SOURCE_ARCHIVE_SHA256 and
                    phase_receipt.get("source_map_sha256") == source_map_hash,
                    f"{phase} build/runtime/phase receipt digest or source map differs")
            source_maps[phase] = source_map_hash

            scenario = phase_receipt.get("scenario", {})
            attempt_id = scenario.get("attempt_id")
            attempt_name = unique_suffix(names, "/r00-" + attempt_id + "/attempt.json")
            attempt_root = str(PurePosixPath(attempt_name).parent)
            attempt_raw = archive.read(attempt_name)
            attempt = json.loads(attempt_raw.decode("utf-8"))
            report_name = attempt_root + "/report.json"
            log_name = attempt_root + "/runner.log"
            finished_attempt_name = attempt_root + "/finished.json"
            report_raw = archive.read(report_name)
            log_raw = archive.read(log_name)
            attempt_finished = json.loads(archive.read(finished_attempt_name).decode("utf-8"))
            report = json.loads(report_raw.decode("utf-8"))
            result = report.get("results", [{}])[0]
            if phase == "fault":
                expected_status = "failed"
                expected_run_status = "expected-target-fault-rejection"
                expected_category = fault["expected_failure_categories"][0]
                failure = result.get("failure", {})
                failed_steps = [step.get("number") for step in result.get("steps", []) if step.get("status") == "failed"]
                require(report.get("summary", {}).get("failed") == 1 and result.get("status") == "failed" and
                        failure.get("category") == expected_category and
                        failed_steps == [fault["expected_failure_step"]] and
                        attempt.get("target_fault_id") == provider["fault"] and
                        attempt.get("target_fault_source_sha256") == fault["mutated_source_sha256"] and
                        attempt_finished.get("expected_target_fault_rejection") is True,
                        "unchanged scenario did not reject the exact target fault at the declared step/category")
            else:
                expected_status = "passed"
                expected_run_status = "passed"
                expected_category = None
                require(report.get("summary", {}).get("passed") == 1 and result.get("status") == "passed" and
                        not result.get("failure") and attempt.get("target_fault_id") is None and
                        attempt_finished.get("expected_target_fault_rejection") is False,
                        f"{phase} pristine scenario lacks a positive pass")
            require(attempt.get("attempt_id") == attempt_id and attempt.get("project") == "joe" and
                    attempt.get("scenario_id") == fault["scenario_id"] and
                    attempt.get("contract_sha256") == scenario_contract_hash(fault) and
                    attempt.get("candidate") == CANDIDATE and
                    attempt.get("candidate_archive_sha256") == cell["archive_sha256"] and
                    attempt.get("candidate_binary_sha256") == cell["binary_sha256"] and
                    attempt.get("target_pin") == PIN and attempt.get("target_binary_sha256") == binary_hash and
                    attempt.get("target_build_receipt_sha256") == build_hash and
                    attempt_finished.get("report_sha256") == digest(report_raw) and
                    attempt_finished.get("runner_log_sha256") == digest(log_raw) and
                    scenario.get("report_sha256") == digest(report_raw) and
                    scenario.get("status") == expected_run_status and
                    scenario.get("failure_category") == expected_category and
                    attempt_finished.get("process_tree_cleanup") == "process group absent; no owned descendants remain" and
                    result.get("cleanup", {}).get("confirmed_exited") is True and
                    result.get("workspace", {}).get("cleaned") is True,
                    f"{phase} scenario identity, result hashes, process or target/workspace cleanup differs")
            phase_results.append({"phase": phase, "scenario_attempt_id": attempt_id,
                                  "scenario_status": expected_run_status,
                                  "failure_category": expected_category,
                                  "failed_step": fault["expected_failure_step"] if phase == "fault" else None,
                                  "target_binary_sha256": binary_hash,
                                  "report_sha256": digest(report_raw),
                                  "runner_process_tree_confirmed": True,
                                  "target_and_workspace_cleanup_confirmed": True,
                                  "owned_source_tree_removed": cleanups[phase]["active_target_absent"]})

        require(source_maps["baseline"] == source_maps["recovery"] and
                source_maps["baseline"] != source_maps["fault"] and
                finished.get("project_admission_credit") == 0,
                "fault recovery source map was not restored exactly or admission credit was invented")
        return {"artifact_id": provider["id"], "artifact_name": provider["name"],
                "bytes": len(raw), "sha256": digest(raw), "provider_digest": "sha256:" + digest(raw),
                "zip_entries": len(names), "expanded_bytes": expanded, "zip_crc": "passed",
                "host": provider["host"], "fault": provider["fault"],
                "target_pin": PIN, "candidate": CANDIDATE,
                "status": "baseline-detected-restored", "phases": phase_results,
                "source_map_restored": True, "owned_source_phase_trees_removed": 3}


def main():
    global FREEZE, DECLARATION, SERIES, CANDIDATE
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--series", choices=("native-exit-v1", "native-exit-v2"), default="native-exit-v1")
    parser.add_argument("--run-id", type=int, default=43054584381)
    parser.add_argument("--head", default="df7fd54375e411542ce899c0e05b19db643ba64b")
    args = parser.parse_args()
    SERIES = args.series
    FREEZE = DOC / f"replacement-candidate-freeze-{SERIES}.json"
    DECLARATION = DOC / "joe" / ("fault-declaration-v3.json" if SERIES == "native-exit-v2" else "fault-declaration-v2.json")
    CANDIDATE = json.loads(FREEZE.read_text(encoding="utf-8"))["version"]
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    require(manifest.get("workflow_run_id") == args.run_id and
            manifest.get("workflow_conclusion") == "success" and
            manifest.get("workflow_revision") == args.head,
            "provider manifest does not identify the completed JOE v2 workflow")
    declaration_hash = sha256(DECLARATION)
    require(manifest.get("fault_declaration_sha256") == declaration_hash and
            declaration.get("candidate") == CANDIDATE and declaration.get("pin") == PIN,
            "frozen JOE declaration/pin differs from provider manifest")
    scenario_declaration = DOC / "joe" / ("scenario-declaration-v4.json" if SERIES == "native-exit-v2" else "scenario-declaration-v3.json")
    require(sha256(scenario_declaration) == declaration.get("scenario_declaration_sha256"),
            "frozen JOE scenario declaration changed")
    readback_path = DOC / "joe" / ("fault-declaration-source-readback-v3.json" if SERIES == "native-exit-v2" else "fault-declaration-source-readback-v2.json")
    readback = json.loads(readback_path.read_text(encoding="utf-8"))
    require(readback.get("fault_declaration_sha256") == declaration_hash,
            "static exact-source fault readback differs from declaration")
    fault_rows = {row["id"]: row for row in declaration["faults"]}
    for fault_id, fault in fault_rows.items():
        scenario = DOC / "joe" / "scenarios-v3" / fault["scenario_id"] / "scenario.json"
        patch = DOC / "joe" / fault["patch"]
        require(scenario_contract_hash(fault) and
                sha256(patch) == fault["patch_sha256"], f"frozen JOE contract/patch changed: {fault_id}")
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    candidate_cells = {row["host"]: row for row in freeze["cells"]}
    expected = {(fault_id, host) for fault_id in fault_rows for host in ("linux", "darwin")}
    providers = manifest.get("artifacts", [])
    actual = {(row.get("fault"), row.get("host")) for row in providers}
    require(len(providers) == 6 and actual == expected and len(actual) == 6,
            "provider manifest is not the complete six-cell native fault matrix")
    audited = []
    for provider in providers:
        require(provider.get("expired") is False and provider.get("digest", "").startswith("sha256:"),
                "provider artifact is expired or lacks its SHA-256 digest")
        local_path = args.artifact_root / provider["local_filename"]
        provider_row = dict(provider, digest=provider["digest"].removeprefix("sha256:"))
        audited.append(verify_archive(local_path, provider_row, fault_rows, candidate_cells, declaration_hash))
    require(len(audited) == 6, "not all six JOE v2 native artifacts were audited")
    output = {"schema_version": 1, "project": "joe", "status": "source-fault-calibration-audited",
              "workflow_run_id": manifest["workflow_run_id"], "workflow_revision": manifest["workflow_revision"],
              "workflow_conclusion": manifest["workflow_conclusion"],
              "candidate": CANDIDATE, "candidate_series": SERIES,
              "current_candidate_transfer": SERIES == "native-exit-v2",
              "fault_declaration": DECLARATION.relative_to(DOC).as_posix(),
              "fault_declaration_sha256": declaration_hash,
              "source_readback": readback_path.relative_to(DOC).as_posix(),
              "target_pin": PIN, "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
              "distinct_detected_source_faults": 3, "native_cells": 2,
              "calibration_phase_executions": 18,
              "baseline_passes": 6, "fault_contract_rejections": 6,
              "restored_recovery_passes": 6, "owned_target_trees_removed": 18,
              "runner_process_groups_reaped": 18,
              "provider_artifacts": audited,
              "admission_credit": 0,
              "audited_at_utc": datetime.now(timezone.utc).isoformat(),
              "limitation": ("Fault calibrations bind exact current rc.7 archives; scenario admission, oracle/model controls and final audit remain open." if SERIES == "native-exit-v2" else "These successful calibrations used exact v0.4.0-rc.6 host archives. They do not transfer to native-exit-v2/rc.7; repeat on the rebuilt candidate before JOE admission.")}
    immutable_json(args.output, output)
    print(json.dumps({"status": output["status"], "faults": 3, "native_cells": 2,
                      "calibration_phase_executions": 18, "admission_credit": 0,
                      "audit": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
