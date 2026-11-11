"""Independently read back the first retained JOE scenario development artifacts."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC, ROOT
from next20_target_cleanup import workspace_setup_failure_before_launch

PROJECT = DOC / "joe"
PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
SOURCE_ARCHIVE_SHA256 = "5e00e2621225a304061c70903ef6490a700a4bbf1fa600c096b5bbb6746f2312"
RUN_ID = 43024880243
HEAD = "edef3003258bf10d9055cb7f9ec8730b28e9f134"
EXPECTED = {
    "linux": {"artifact_id": 13856667616, "size": 26644089,
              "sha256": "9eb4238a67c363e84fa72ab796ebe633fa7a26316e04831a5d7034d4f03149c9",
              "binary": "a87146372bab2f50dda3b65f060b2eac4a1c45603f1ef8bb0976f8505d9096f9"},
    "darwin": {"artifact_id": 13857012039, "size": 20772405,
               "sha256": "5ddf1c3f0d67260c4511d2f3a033d7468b6e335eb29aba5561aa9483b0991ea3",
               "binary": None},
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def read_packet(path, host):
    packet = EXPECTED[host]
    path = Path(path)
    raw = path.read_bytes()
    require(len(raw) == packet["size"] and digest(raw) == packet["sha256"],
            f"{host} archive differs from the exact GitHub provider size/digest")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [row.filename for row in infos]
        require(len(names) == len(set(names)), f"{host} artifact has duplicate ZIP paths")
        expanded = 0
        payloads = {}
        for info in infos:
            name = info.filename
            path_parts = PurePosixPath(name)
            require(not path_parts.is_absolute() and ".." not in path_parts.parts and
                    "\\" not in name and not info.flag_bits & 1,
                    f"{host} artifact has unsafe/encrypted member {name}")
            require(info.file_size <= 256 * 1024**2, f"{host} member exceeds the independent size bound")
            expanded += info.file_size
            require(expanded <= 512 * 1024**2, f"{host} expanded artifact exceeds the independent size bound")
            if not info.is_dir():
                data = archive.read(info)
                require(len(data) == info.file_size, f"{host} member is truncated: {name}")
                payloads[name] = data
        require(archive.testzip() is None, f"{host} ZIP CRC validation failed")
    return payloads, len(infos), expanded


def verify_host(host, path):
    packet = EXPECTED[host]
    payloads, member_count, expanded = read_packet(path, host)
    build_root = f"joe/scenario-development/build-readback/{host}/{RUN_ID}/"

    def get(name):
        full = build_root + name
        require(full in payloads, f"{host} missing retained build evidence {full}")
        return payloads[full]

    def obj(data, name):
        try:
            value = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"{host} invalid {name}") from error
        require(isinstance(value, dict), f"{host} {name} is not a JSON object")
        return value

    acquisition = obj(get("acquisition.json"), "acquisition")
    build_raw = get("build.json")
    build = obj(build_raw, "build")
    runtime_raw = get("runtime.json")
    runtime = obj(runtime_raw, "runtime")
    retained = obj(get("retained-build-evidence.json"), "build evidence manifest")
    binary = get("target-joe")
    source = get("source.tar.gz")
    require(digest(source) == SOURCE_ARCHIVE_SHA256 and acquisition.get("pin") == PIN and
            acquisition.get("archive_sha256") == SOURCE_ARCHIVE_SHA256,
            f"{host} retained source archive is not the reviewed JOE pin")
    require(build.get("project") == "joe" and build.get("pin") == PIN and
            build.get("host") == host and build.get("runtime_kind") == "native" and
            build.get("binary_relative_path") == "install/bin/joe" and
            build.get("binary_sha256") == digest(binary) and
            runtime.get("native_sha256") == digest(binary) and runtime.get("runtime_kind") == "native",
            f"{host} native source build/runtime receipt does not bind the retained target executable")
    require(retained.get("project") == "joe" and retained.get("pin") == PIN and
            retained.get("host") == host and retained.get("binary_sha256") == digest(binary) and
            retained.get("build_receipt_sha256") == digest(build_raw) and
            retained.get("runtime_receipt_sha256") == digest(runtime_raw) and
            retained.get("command_count") == 7 and len(retained.get("build_logs", [])) == 7,
            f"{host} retained build evidence manifest differs")
    log_digests = {Path(row["path"]).name: row for row in retained["build_logs"]}
    commands = build.get("commands", [])
    require(len(commands) == 7, f"{host} source build did not retain seven bounded commands")
    for command in commands:
        name = Path(command.get("log", "")).name
        log = get("build-logs/" + name)
        manifest_row = log_digests.get(name)
        require(command.get("exit_code") == 0 and
                command.get("process_tree_cleanup") == "process group absent; no owned descendants remain" and
                manifest_row is not None and len(log) == command.get("output_bytes") and
                digest(log) == command.get("output_sha256") == manifest_row.get("sha256") and
                manifest_row.get("bytes") == len(log),
                f"{host} native build log/exit/process cleanup differs for {name}")

    candidate_path = f"candidate-native-exit-v1/{host}/installed.json"
    require(candidate_path in payloads, f"{host} frozen candidate installation receipt is missing")
    installed = obj(payloads[candidate_path], "candidate installed receipt")
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v1.json").read_text(encoding="utf-8"))
    frozen = next(row for row in freeze["cells"] if row["host"] == host)
    require(installed.get("version") == freeze.get("version") == "v0.4.0-rc.6" and
            installed.get("archive_sha256") == frozen["archive_sha256"] and
            installed.get("binary_sha256") == frozen["binary_sha256"],
            f"{host} scenario candidate installation differs from the exact frozen native archive")

    outcomes = []
    for scenario_id in ("N01", "N02"):
        base = f"joe/scenario-development/{host}/{scenario_id}/"
        members = [name for name in payloads if name.startswith(base)]
        attempt_files = [name for name in members if name.endswith("/attempt.json")]
        require(len(attempt_files) == 1, f"{host} {scenario_id} must have exactly one predeclared attempt")
        attempt_prefix = attempt_files[0][:-len("attempt.json")]

        def attempt_obj(name):
            return obj(payloads.get(attempt_prefix + name, b""), name)

        attempt = attempt_obj("attempt.json")
        started = attempt_obj("started.json")
        identified = attempt_obj("identified.json")
        launched = attempt_obj("launched.json")
        finished = attempt_obj("finished.json")
        report_raw = payloads.get(attempt_prefix + "report.json")
        runner_log = payloads.get(attempt_prefix + "runner.log")
        require(report_raw is not None and runner_log is not None and
                started.get("attempt_id") == identified.get("attempt_id") ==
                launched.get("attempt_id") == finished.get("attempt_id") == attempt.get("attempt_id") and
                attempt.get("scenario_id") == scenario_id and attempt.get("host") == host and
                attempt.get("target_pin") == PIN and attempt.get("target_binary_sha256") == digest(binary) and
                attempt.get("target_build_receipt_sha256") == digest(build_raw) and
                attempt.get("candidate") == "v0.4.0-rc.6" and
                attempt.get("candidate_archive_sha256") == frozen["archive_sha256"] and
                attempt.get("candidate_binary_sha256") == frozen["binary_sha256"] and
                identified.get("target_sha256") == digest(binary) and
                identified.get("candidate_sha256") == frozen["binary_sha256"] and
                launched.get("candidate_sha256") == frozen["binary_sha256"] and
                finished.get("report_sha256") == digest(report_raw) and
                finished.get("runner_log_sha256") == digest(runner_log) and
                finished.get("runner_command", {}).get("process_tree_cleanup") ==
                    "process group absent; no owned descendants remain",
                f"{host} {scenario_id} attempt lifecycle or source/candidate/report identity differs")
        report = obj(report_raw, scenario_id + " report")
        case = report.get("results", [{}])[0]
        spec_path = PROJECT / "scenarios" / scenario_id / "scenario.json"
        require(spec_path.is_file() and digest(spec_path.read_bytes()) == attempt.get("contract_sha256") and
                attempt.get("contract") == spec_path.relative_to(ROOT).as_posix(),
                f"{host} {scenario_id} attempt does not bind its frozen spec")
        if scenario_id == "N01":
            receipt = attempt_obj("receipt.json")
            require(report.get("summary") == {"total": 1, "passed": 1, "failed": 0, "cancelled": 0, "not_run": 0} and
                    case.get("status") == "passed" and case.get("cleanup", {}).get("confirmed_exited") is True and
                    case.get("workspace", {}).get("cleaned") is True and
                    receipt.get("status") == "passed" and receipt.get("target_binary_sha256") == digest(binary) and
                    receipt.get("report_sha256") == digest(report_raw),
                    f"{host} N01 ordinary first scenario lacks exact positive outcome and cleanup")
            outcomes.append({"scenario_id": scenario_id, "status": "passed", "target_cleanup": True,
                             "workspace_cleanup": True, "report_sha256": digest(report_raw),
                             "attempt_id": attempt["attempt_id"]})
        else:
            require(attempt_prefix + "receipt.json" not in payloads and
                    report.get("summary", {}).get("failed") == 1 and
                    workspace_setup_failure_before_launch(report, case) and
                    not case.get("invocation_id") and
                    finished.get("runner_command", {}).get("exit_code") == 1,
                    f"{host} N02 is not the retained pre-target fixture setup refusal")
            outcomes.append({"scenario_id": scenario_id, "status": "failed-before-target-launch",
                             "failure_category": "workspace_setup_failure", "target_launched": False,
                             "workspace_prepared": False, "cleanup_credit": 0,
                             "report_sha256": digest(report_raw), "attempt_id": attempt["attempt_id"]})

    source_root = f"active/joe/"
    retained_active = any(name.startswith(source_root) for name in payloads)
    removed = f"joe/retained-provenance/removed.json"
    cleanup_complete = removed in payloads
    require(retained_active and not cleanup_complete,
            f"{host} expected the revision-1 cleanup refusal to preserve the target tree and omit removal proof")
    return {"host": host, "provider_artifact_id": packet["artifact_id"],
            "provider_bytes": packet["size"], "provider_sha256": packet["sha256"],
            "zip_members": member_count, "zip_expanded_bytes": expanded,
            "source_pin": PIN, "source_archive_sha256": SOURCE_ARCHIVE_SHA256,
            "architecture": build["architecture"], "target_binary_sha256": digest(binary),
            "candidate_archive_sha256": frozen["archive_sha256"],
            "candidate_binary_sha256": frozen["binary_sha256"],
            "native_build_commands": 7, "attempted_scenarios": 2,
            "declared_scenarios": 20, "attempts": outcomes,
            "target_tree_retained_after_checked_cleanup_refusal": retained_active,
            "source_runtime_deletion_confirmed": False,
            "classification": "attempt outcomes independently audited; project scenario qualification incomplete; no admission credit"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--linux-zip", type=Path, required=True)
    parser.add_argument("--darwin-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {host: verify_host(host, getattr(args, host + "_zip")) for host in ("linux", "darwin")}
    output = {"schema_version": 1, "project": "joe", "workflow_run": RUN_ID,
              "workflow_head_sha": HEAD, "candidate": "v0.4.0-rc.6",
              "project_admission_credit": 0, "status": "first-scenario-development-attempt-audited-not-qualified",
              "hosts": result,
              "scope": "Exact provider ZIP size/SHA/CRC, pinned native source/build/binary and all seven build logs, frozen candidate installation receipt, the two actually attempted scenario lifecycles per native host, N01 exact pass, N02 explicit pre-target fixture setup refusal, and withheld cleanup/admission credit.",
              "unattempted_scenarios": 18, "qualification_scenarios": 0,
              "real_faults": 0, "calibrations": 0}
    encoded = (json.dumps(output, ensure_ascii=True, indent=2, sort_keys=True) + "\n").encode()
    if args.output.exists():
        if args.output.read_bytes() != encoded:
            raise FileExistsError("refusing to overwrite JOE development readback")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as stream:
            stream.write(encoded)
    print(json.dumps({"status": output["status"], "project": "joe", "workflow_run": RUN_ID,
                      "readback": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
