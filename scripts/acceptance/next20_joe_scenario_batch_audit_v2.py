"""Independently audit retained JOE 20-scenario development artifacts."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC, ROOT

PROJECT = DOC / "joe"
RUN_ID = 43028795974
HEAD = "8d69a504fb5d062cb894bb33c34d30ca00fbd3ea"
PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
SOURCE_SHA256 = "5e00e2621225a304061c70903ef6490a700a4bbf1fa600c096b5bbb6746f2312"
DEFAULT_PROVIDER = {
    "linux": {"id": 13860620938, "bytes": 8854955,
              "sha256": "31a6ddbf13ff46505f230ee939a90773ed2dd3a057404eb22efc2fcad883ef21",
              "binary_sha256": "a87146372bab2f50dda3b65f060b2eac4a1c45603f1ef8bb0976f8505d9096f9"},
    "darwin": {"id": 13859392255, "bytes": 8038884,
               "sha256": "c75f2b271e0361868e3e8b20c314a0d43a7857223a257047fdbefad324ace33d",
               "binary_sha256": None},
}
PROCESS_CLEAN = "process group absent; no owned descendants remain"
DECLARATION_PATH = PROJECT / "scenario-declaration-v2.json"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def read_json(payloads, path, label):
    require(path in payloads, f"missing {label}: {path}")
    try:
        value = json.loads(payloads[path].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON for {label}: {path}") from error
    require(isinstance(value, dict), f"{label} is not an object: {path}")
    return value


def read_packet(path, host):
    expected = PROVIDER[host]
    raw = Path(path).read_bytes()
    require(len(raw) == expected["bytes"] and digest(raw) == expected["sha256"],
            f"{host} artifact differs from GitHub provider byte count or SHA-256")
    payloads = {}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        require(len(names) == len(set(names)), f"{host} ZIP contains duplicate paths")
        expanded = 0
        for info in infos:
            name = info.filename
            parts = PurePosixPath(name)
            require(not parts.is_absolute() and ".." not in parts.parts and
                    "\\" not in name and not info.flag_bits & 1,
                    f"{host} ZIP contains an unsafe or encrypted path: {name}")
            require(info.file_size <= 256 * 1024**2, f"{host} ZIP member exceeds the size bound")
            expanded += info.file_size
            require(expanded <= 512 * 1024**2, f"{host} ZIP expansion exceeds the size bound")
            if not info.is_dir():
                data = archive.read(info)
                require(len(data) == info.file_size, f"{host} truncated ZIP member: {name}")
                payloads[name] = data
        require(archive.testzip() is None, f"{host} ZIP CRC validation failed")
    return payloads, len(infos), expanded


def verify_host(host, path, scenario_ids, freeze, declaration_sha256):
    provider = PROVIDER[host]
    payloads, member_count, expanded = read_packet(path, host)
    prefix = f"joe/scenario-development/build-readback/{host}/{RUN_ID}/"

    def member(relative):
        name = prefix + relative
        require(name in payloads, f"{host} missing retained build evidence {name}")
        return payloads[name]

    def obj(relative, label):
        return json.loads(member(relative).decode("utf-8"))

    acquisition = obj("acquisition.json", "source acquisition")
    build_raw = member("build.json")
    build = json.loads(build_raw.decode("utf-8"))
    runtime_raw = member("runtime.json")
    runtime = json.loads(runtime_raw.decode("utf-8"))
    retained = obj("retained-build-evidence.json", "retained build manifest")
    binary = member("target-joe")
    source = member("source.tar.gz")
    require(digest(source) == SOURCE_SHA256 and acquisition.get("pin") == PIN and
            acquisition.get("archive_sha256") == SOURCE_SHA256,
            f"{host} source acquisition/archive does not match the reviewed pin")
    require(build.get("project") == "joe" and build.get("pin") == PIN and
            build.get("host") == host and build.get("runtime_kind") == "native" and
            build.get("binary_relative_path") == "install/bin/joe" and
            build.get("binary_sha256") == digest(binary) and
            (provider["binary_sha256"] is None or digest(binary) == provider["binary_sha256"]) and
            runtime.get("native_sha256") == digest(binary) and runtime.get("runtime_kind") == "native",
            f"{host} native build/runtime receipt does not bind the retained JOE executable")
    require(retained.get("project") == "joe" and retained.get("pin") == PIN and
            retained.get("host") == host and retained.get("binary_sha256") == digest(binary) and
            retained.get("build_receipt_sha256") == digest(build_raw) and
            retained.get("runtime_receipt_sha256") == digest(runtime_raw) and
            retained.get("command_count") == 7 and len(retained.get("build_logs", [])) == 7,
            f"{host} retained build manifest identity differs")
    logs = {Path(row["path"]).name: row for row in retained["build_logs"]}
    commands = build.get("commands", [])
    require(len(commands) == 7, f"{host} native build does not record seven commands")
    for command in commands:
        name = Path(command.get("log", "")).name
        data = member("build-logs/" + name)
        row = logs.get(name)
        require(row is not None and command.get("exit_code") == 0 and
                command.get("process_tree_cleanup") == PROCESS_CLEAN and
                len(data) == command.get("output_bytes") == row.get("bytes") and
                digest(data) == command.get("output_sha256") == row.get("sha256"),
                f"{host} native command log/exit/process evidence differs for {name}")

    installed_path = f"candidate-native-exit-v1/{host}/installed.json"
    installed = read_json(payloads, installed_path, "frozen candidate installation")
    frozen = next(row for row in freeze["cells"] if row["host"] == host)
    require(installed.get("version") == freeze.get("version") == "v0.4.0-rc.6" and
            installed.get("archive_sha256") == frozen["archive_sha256"] and
            installed.get("binary_sha256") == frozen["binary_sha256"],
            f"{host} installed candidate differs from the frozen rc.6 native artifact")

    batch_path = f"joe/scenario-development-batches/{host}/{RUN_ID}.json"
    batch = read_json(payloads, batch_path, "scenario batch manifest")
    require(batch.get("host") == host and batch.get("candidate") == "v0.4.0-rc.6" and
            batch.get("workflow_run") == RUN_ID and
            batch.get("scenario_declaration_sha256") == declaration_sha256 and
            batch.get("selected_scenarios") == len(scenario_ids) == 20 and
            batch.get("repetitions") == 1 and
            len(batch.get("outcomes", [])) == len(scenario_ids) == 20 and
            batch.get("passed") == sum(row.get("status") == "passed" for row in batch["outcomes"]) and
            batch.get("failed") == sum(row.get("status") == "failed" for row in batch["outcomes"]),
            f"{host} batch manifest is incomplete or its failure total differs")
    outcomes = []
    for declared, row in zip(scenario_ids, batch["outcomes"]):
        scenario_id = declared["id"]
        require(row.get("scenario_id") == scenario_id and row.get("repetition") == 0,
                f"{host} batch scenario order/repetition differs at {scenario_id}")
        declared_base = f"joe/scenario-development/{host}/{scenario_id}/"
        attempt_paths = [name for name in payloads
                         if name.startswith(declared_base) and name.endswith("/attempt.json")]
        require(len(attempt_paths) == 1,
                f"{host} {scenario_id} must have exactly one retained immutable attempt")
        attempt_id = Path(attempt_paths[0]).parent.name.removeprefix("r00-")
        require(isinstance(attempt_id, str) and len(attempt_id) == 32 and
                (row.get("attempt_id") is None or row.get("attempt_id") == attempt_id),
                f"{host} {scenario_id} attempt identity differs from batch journal")
        base = f"joe/scenario-development/{host}/{scenario_id}/r00-{attempt_id}/"
        attempt = read_json(payloads, base + "attempt.json", f"{scenario_id} attempt")
        started = read_json(payloads, base + "started.json", f"{scenario_id} started event")
        identified = read_json(payloads, base + "identified.json", f"{scenario_id} identified event")
        launched = read_json(payloads, base + "launched.json", f"{scenario_id} launched event")
        finished = read_json(payloads, base + "finished.json", f"{scenario_id} finished event")
        report_raw = payloads.get(base + "report.json")
        runner_log = payloads.get(base + "runner.log")
        require(report_raw is not None and runner_log is not None and
                all(event.get("attempt_id") == attempt_id for event in (attempt, started, identified, launched, finished)) and
                attempt.get("project") == "joe" and attempt.get("host") == host and
                attempt.get("target_pin") == PIN and attempt.get("target_binary_sha256") == digest(binary) and
                attempt.get("target_build_receipt_sha256") == digest(build_raw) and
                attempt.get("candidate") == "v0.4.0-rc.6" and
                attempt.get("candidate_archive_sha256") == frozen["archive_sha256"] and
                attempt.get("candidate_binary_sha256") == frozen["binary_sha256"] and
                attempt.get("scenario_id") == scenario_id and attempt.get("phase") == "scenario-development" and
                identified.get("target_sha256") == digest(binary) and
                identified.get("candidate_sha256") == frozen["binary_sha256"] and
                launched.get("candidate_sha256") == frozen["binary_sha256"] and
                finished.get("report_sha256") == digest(report_raw) and
                (row.get("report_sha256") is None or row.get("report_sha256") == digest(report_raw)) and
                finished.get("runner_log_sha256") == digest(runner_log) and
                finished.get("runner_command", {}).get("process_tree_cleanup") == PROCESS_CLEAN,
                f"{host} {scenario_id} lifecycle/source/candidate/report identity differs")
        contract = ROOT / declared["spec"]
        require(contract.is_file() and attempt.get("contract") == declared["spec"] and
                digest(contract.read_bytes()) == attempt.get("contract_sha256") == declared["spec_sha256"],
                f"{host} {scenario_id} attempt does not bind the frozen v2 scenario")
        report = json.loads(report_raw.decode("utf-8"))
        results = report.get("results", [])
        require(len(results) == 1 and results[0].get("spec_path") == attempt.get("contract"),
                f"{host} {scenario_id} report does not identify its exact contract")
        case = results[0]
        require(case.get("cleanup", {}).get("confirmed_exited") is True and
                case.get("workspace", {}).get("cleaned") is True and
                case.get("workspace", {}).get("prepared") is True,
                f"{host} {scenario_id} target or managed workspace cleanup is unconfirmed")
        screen = case.get("evidence", {}).get("screen_path")
        screen_names = [name for name in payloads if name.startswith(base) and name.endswith(".actual.txt")]
        if screen:
            require(screen_names and len(screen_names) == 1,
                    f"{host} {scenario_id} screen evidence is missing or ambiguous")
        if row["status"] == "passed":
            receipt = read_json(payloads, base + "receipt.json", f"{scenario_id} pass receipt")
            require(case.get("status") == "passed" and report.get("summary", {}).get("failed") == 0 and
                    receipt.get("status") == "passed" and
                    receipt.get("target_binary_sha256") == digest(binary) and
                    receipt.get("report_sha256") == digest(report_raw) and
                    receipt.get("target_cleanup", {}).get("confirmed_exited") is True and
                    receipt.get("workspace_cleanup", {}).get("cleaned") is True and
                    finished.get("runner_command", {}).get("exit_code") == 0,
                    f"{host} {scenario_id} pass receipt is not positive or exact")
        else:
            require(row["status"] == "failed" and base + "receipt.json" not in payloads and
                    case.get("status") == "failed" and report.get("summary", {}).get("failed") == 1 and
                    finished.get("runner_command", {}).get("exit_code") == 1 and
                    finished.get("failure") is not None,
                    f"{host} {scenario_id} failure was erased, misclassified, or credited")
        outcomes.append({"scenario_id": scenario_id, "attempt_id": attempt_id,
                         "status": row["status"], "report_sha256": digest(report_raw),
                         "failure_category": case.get("failure", {}).get("category") if row["status"] == "failed" else None,
                         "cleanup_confirmed": True, "workspace_cleaned": True,
                         "runner_process_group_absent": True})

    removed = read_json(payloads, "joe/retained-source/removed.json", "source cleanup receipt")
    process = read_json(payloads, "joe/process-proof.json", "owned process proof")
    require(removed.get("removed") is True and removed.get("source_restored_exact") is True and
            removed.get("owned_relative_path") == "active/joe" and
            process.get("confirmed_no_matching_live_processes") is True and
            not any(name.startswith("active/joe/") for name in payloads),
            f"{host} source restoration, target cleanup, or owned process proof is incomplete")
    passed = sum(item["status"] == "passed" for item in outcomes)
    failed = len(outcomes) - passed
    require(batch["failed"] == failed, f"{host} batch failure total differs from independently audited reports")
    return {"host": host, "provider_artifact_id": provider["id"],
            "provider_bytes": provider["bytes"], "provider_sha256": provider["sha256"],
            "zip_members": member_count, "zip_expanded_bytes": expanded,
            "source_pin": PIN, "source_archive_sha256": SOURCE_SHA256,
            "architecture": build["architecture"], "target_binary_sha256": digest(binary),
            "candidate_archive_sha256": frozen["archive_sha256"],
            "candidate_binary_sha256": frozen["binary_sha256"],
            "build_commands_audited": 7, "scenario_attempts": len(outcomes),
            "scenario_passes": passed, "scenario_failures": failed,
            "outcomes": outcomes, "source_tree_removal_confirmed": True,
            "owned_processes_absent": True}


def main():
    global RUN_ID, HEAD, PROVIDER, DECLARATION_PATH
    parser = argparse.ArgumentParser()
    parser.add_argument("--linux-zip", type=Path, required=True)
    parser.add_argument("--darwin-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", type=int, default=RUN_ID)
    parser.add_argument("--head", default=HEAD)
    parser.add_argument("--declaration", type=Path, default=DECLARATION_PATH)
    for host in ("linux", "darwin"):
        parser.add_argument(f"--{host}-artifact-id", type=int, default=DEFAULT_PROVIDER[host]["id"])
        parser.add_argument(f"--{host}-artifact-bytes", type=int, default=DEFAULT_PROVIDER[host]["bytes"])
        parser.add_argument(f"--{host}-artifact-sha256", default=DEFAULT_PROVIDER[host]["sha256"])
        parser.add_argument(f"--{host}-binary-sha256", default=DEFAULT_PROVIDER[host]["binary_sha256"])
    args = parser.parse_args()
    RUN_ID, HEAD, DECLARATION_PATH = args.run_id, args.head, args.declaration.resolve()
    PROVIDER = {host: {"id": getattr(args, f"{host}_artifact_id"),
                       "bytes": getattr(args, f"{host}_artifact_bytes"),
                       "sha256": getattr(args, f"{host}_artifact_sha256"),
                       "binary_sha256": getattr(args, f"{host}_binary_sha256")}
                for host in ("linux", "darwin")}
    declaration_path = DECLARATION_PATH
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    require(declaration.get("project") == "joe" and declaration.get("pin") == PIN and
            declaration.get("candidate") == "v0.4.0-rc.6" and len(declaration.get("scenarios", [])) == 20,
            "frozen JOE v2 declaration identity/count differs")
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v1.json").read_text(encoding="utf-8"))
    declaration_hash = digest(declaration_path.read_bytes())
    hosts = {host: verify_host(host, getattr(args, host + "_zip"), declaration["scenarios"], freeze,
                               declaration_hash)
             for host in ("linux", "darwin")}
    require(hosts["linux"]["scenario_attempts"] == hosts["darwin"]["scenario_attempts"] == 20,
            "both native hosts must have all 20 development attempts")
    output = {"schema_version": 1, "project": "joe", "workflow_run": RUN_ID,
              "workflow_head_sha": HEAD, "candidate": "v0.4.0-rc.6",
              "scenario_declaration": declaration_path.relative_to(DOC).as_posix(),
              "scenario_declaration_sha256": declaration_hash,
              "project_admission_credit": 0,
              "status": "development-attempts-independently-audited-not-qualified",
              "provider_artifacts": hosts,
              "attempts_per_host": 20,
              "scope": "Exact provider ZIP metadata/SHA/CRC/path checks; exact pinned native source/build/runtime/binary and seven build logs; frozen rc.6 installation; all 20 launched lifecycle attempts on each native host with report/spec/source/candidate identities, outcome, target/workspace/process cleanup; exact source restoration and removal.",
              "qualification_scenarios": 0, "real_faults": 0, "calibrations": 0,
              "admission_credit": 0}
    encoded = (json.dumps(output, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode()
    if args.output.exists():
        if args.output.read_bytes() != encoded:
            raise FileExistsError("refusing to overwrite JOE scenario batch readback")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(encoded)
    print(json.dumps({"status": output["status"], "project": "joe", "workflow_run": RUN_ID,
                      "readback": str(args.output),
                      "outcomes": {host: {key: value for key, value in data.items()
                                          if key in {"scenario_passes", "scenario_failures"}}
                                   for host, data in hosts.items()}}, sort_keys=True))


if __name__ == "__main__":
    main()
