"""Independently verify the two hosted JOE public-route artifacts."""
import argparse
import base64
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC, ROOT

PROJECT = "joe"
PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
RUNNER = {
    "linux": {"archive": "28ae9f37227bb0f6ba2df031420aa3d027b998e31eab523c4d13cd2816c4af7a",
              "binary": "e302a46eb090772d91aab7018b51eea0d1fb92247846f4a63375e1009e29309a"},
    "darwin": {"archive": "132152710ade2c01cac7558f75212121f01af8ab02c5735dc9c7de1c33dbe625",
               "binary": "609b184dac8664050643ec35036c4cffef2137ec778ae4d4678727b119e2fe0f"},
}
LABELS = [
    "joe-public-route-runner-version", "joe-first-public-record-review-replay-save",
    "joe-first-public-ordinary-test", "joe-public-seeded-screen-diagnosis",
    "joe-intended-change-before-file-state-update", "joe-selected-saved-file-state-maintenance",
    "joe-maintained-public-ordinary-test", "joe-public-unicode-path-relocation",
    "joe-public-delivered-workflow-preview",
]
EXIT_CODES = [0, 0, 0, 1, 1, 0, 0, 0, 0]
INITIAL = b"JOE_PUBLIC_ROUTE_START\n"
MARKER = "JOE_PUBLIC_ROUTE_RC6"
UPDATED = "JOE_PUBLIC_ROUTE_RC6_UPDATED"
MAX_MEMBER = 256 * 1024**2
MAX_TOTAL = 2 * 1024**3


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_zip(path, provider_size, provider_sha256):
    path = Path(path)
    raw_hash = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            raw_hash.update(block)
    require(path.stat().st_size == provider_size and raw_hash.hexdigest() == provider_sha256,
            "downloaded artifact differs from GitHub provider size/digest")
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        require(len(names) == len(set(names)), "artifact ZIP contains duplicate member paths")
        total = 0
        payloads = {}
        for info in infos:
            name = info.filename
            member = PurePosixPath(name)
            require(not member.is_absolute() and ".." not in member.parts and "\\" not in name and
                    not info.flag_bits & 1, "artifact ZIP contains an unsafe or encrypted member")
            require(info.file_size <= MAX_MEMBER, "artifact member exceeds independent size limit")
            total += info.file_size
            require(total <= MAX_TOTAL, "artifact expanded size exceeds independent limit")
            if not info.is_dir():
                data = archive.read(info)
                require(len(data) == info.file_size, "short ZIP member read")
                payloads[name] = data
        require(archive.testzip() is None, "artifact ZIP CRC verification failed")
    return payloads, len(infos), total


def verify_host(host, archive_path, provider_size, provider_sha256, run_id, freeze):
    payloads, zip_members, expanded_bytes = load_zip(archive_path, provider_size, provider_sha256)
    prefix = f"joe/public-route-v1/{host}/"

    def bytes_at(name):
        path = prefix + name
        require(path in payloads, "artifact is missing " + path)
        return payloads[path]

    def obj(name):
        try:
            value = json.loads(bytes_at(name).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("invalid JSON evidence " + name) from error
        require(isinstance(value, dict), "JSON evidence is not an object: " + name)
        return value

    def root_obj(name):
        try:
            value = json.loads(payloads[name].decode("utf-8"))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError("invalid root JSON evidence " + name) from error
        require(isinstance(value, dict), "root JSON evidence is not an object: " + name)
        return value

    receipt = obj("receipt.json")
    plan = obj("planned.json")
    build = root_obj("joe/retained-source/build.json")
    runtime = root_obj("joe/retained-source/runtime.json")
    acquisition = root_obj("joe/retained-source/acquisition.json")
    removed = root_obj("joe/retained-source/removed.json")
    process = root_obj("joe/process-proof.json")
    installed = root_obj(f"candidate-native-exit-v1/{host}/installed.json")
    host_runner = RUNNER[host]
    candidate_cells = [row for row in freeze["cells"] if row.get("host") == host]
    require(len(candidate_cells) == 1, "candidate freeze does not define exactly one host cell")
    candidate_cell = candidate_cells[0]
    require(receipt.get("project") == PROJECT and receipt.get("host") == host and
            receipt.get("candidate") == "v0.4.0-rc.6" and receipt.get("source_pin") == PIN and
            receipt.get("project_admission_credit") == 0, "public-route receipt project identity differs")
    require(receipt.get("target_build_run") == str(run_id), "route receipt points at another workflow run")
    require(receipt.get("runner_sha256") == host_runner["binary"] and
            plan.get("runner_sha256") == host_runner["binary"] and
            plan.get("candidate_archive_sha256") == host_runner["archive"],
            "route is not bound to the frozen rc.6 host executable/archive")
    require(installed.get("archive_sha256") == host_runner["archive"] and
            installed.get("binary_sha256") == host_runner["binary"] and
            installed.get("version") == "v0.4.0-rc.6", "installed runner differs from the candidate freeze")
    candidate_archive = payloads.get(installed.get("archive", ""))
    if candidate_archive is None:
        retained = ROOT / candidate_cell.get("archive_local_only", "")
        if retained.is_file():
            candidate_archive = retained.read_bytes()
    require(candidate_archive is not None and digest(candidate_archive) == host_runner["archive"],
            "candidate archive bytes are absent or differ from the freeze")
    require(build.get("project") == PROJECT and build.get("pin") == PIN and build.get("host") == host and
            build.get("runtime_kind") == "native" and build.get("binary_sha256") == receipt.get("target_binary_sha256") and
            build.get("binary_sha256") == runtime.get("native_sha256") and runtime.get("runtime_kind") == "native",
            "native target build/runtime identity does not match the route receipt")
    require(build.get("binary_relative_path") == "install/bin/joe" and
            receipt.get("architecture") == build.get("architecture") and runtime.get("architecture") == build.get("architecture"),
            "target architecture or installed path differs")
    source = payloads.get("joe/retained-source/source.tar.gz")
    require(source is not None and digest(source) == "5e00e2621225a304061c70903ef6490a700a4bbf1fa600c096b5bbb6746f2312",
            "retained pinned JOE source archive differs")
    require(removed.get("removed") is True and removed.get("source_restored_exact") is True and
            removed.get("owned_relative_path") == "active/joe", "owned JOE target cleanup did not verify")
    require(process.get("confirmed_no_matching_live_processes") is True and
            process.get("matching_live_processes") == [], "owned JOE process cleanup remains unverified")
    commands = build.get("commands", [])
    require(len(commands) == 7, "native build receipt does not contain the seven declared commands")
    build_log_ids = set()
    build_logs_raw = bytes_at("build-logs.json")
    require(digest(build_logs_raw) == receipt.get("build_command_logs_sha256"),
            "retained native build log manifest hash differs from route receipt")
    build_logs = json.loads(build_logs_raw.decode("utf-8"))
    require(build_logs.get("project") == PROJECT and build_logs.get("host") == host and
            build_logs.get("pin") == PIN and len(build_logs.get("commands", [])) == len(commands),
            "retained native build log manifest identity/count differs")
    for command, retained_log in zip(commands, build_logs["commands"]):
        log_name = "build-logs/" + retained_log.get("log", "")
        log = bytes_at(log_name)
        require(command.get("exit_code") == 0 and command.get("process_tree_cleanup") ==
                "process group absent; no owned descendants remain" and
                retained_log.get("command_id") == command.get("id") and
                retained_log.get("exit_code") == command.get("exit_code") and
                retained_log.get("process_tree_cleanup") == command.get("process_tree_cleanup") and
                len(log) == command.get("output_bytes") and digest(log) == command.get("output_sha256"),
                "native build command/log/cleanup identity failed readback")
        build_log_ids.add(command.get("id"))
    require(len(build_log_ids) == 7, "native build command IDs are not unique")

    require(plan.get("project") == PROJECT and plan.get("phase") == "public-authoring" and
            plan.get("no_handwritten_first_use_spec") is True and
            plan.get("first_use_control_count") == 12 and len(plan.get("first_use_controls", [])) == 12 and
            plan.get("first_use_shell_invocations_expected") == 3 and plan.get("architecture") == build.get("architecture"),
            "first-use plan violates the frozen public-route declaration")
    require(digest(bytes_at("planned.json")) == receipt.get("planned_sha256"), "planned route identity hash differs")
    spec_bytes = bytes_at("project/create-note.json")
    require(digest(spec_bytes) == receipt.get("first_use", {}).get("spec_sha256"), "first-use spec hash differs")
    spec = json.loads(spec_bytes.decode("utf-8"))
    expected_state = INITIAL[:-1] + MARKER.encode() + INITIAL[-1:]
    state_steps = [step.get("state") for step in spec.get("steps", []) if step.get("state", {}).get("path") == "public-note.txt"]
    snapshot_steps = [step.get("snapshot") for step in spec.get("steps", []) if step.get("snapshot")]
    require(spec.get("version") == 3 and spec.get("command") == ["joe", "-nobackups", "public-note.txt"] and
            spec.get("workspace", {}).get("fixture") == "fixtures" and len(state_steps) == 1 and
            state_steps[0].get("bytes_base64") == base64.b64encode(expected_state).decode("ascii") and
            snapshot_steps == ["initial-note.txt"], "recorded first-use spec is not the exact reviewed JOE interaction/state")
    snapshot_path = prefix + "project/snapshots/initial-note.txt"
    require(snapshot_path in payloads, "recorded initial screen snapshot was not retained")
    actual_text = payloads[snapshot_path].decode("utf-8")
    require("JOE_PUBLIC_ROUTE_START" in actual_text and "public-note.txt" in actual_text,
            "initial screen snapshot lacks positive file/readiness evidence")
    require(receipt.get("first_use", {}).get("status") == "passed" and
            receipt.get("first_use", {}).get("handwritten_spec") is False and
            receipt.get("first_use", {}).get("controls") == 12 and
            receipt.get("first_use", {}).get("shell_invocations") == 3 and
            receipt.get("first_use", {}).get("saved_state_bytes_verified") is True,
            "first-use result does not meet the declared command/control window")

    expected_status = {
        "first-use-report.json": "passed", "diagnosis-report.json": "failed",
        "maintenance-before-report.json": "failed", "maintenance-report.json": "passed",
        "relocation-report.json": "passed",
    }
    reports = {}
    receipt_digests = {
        "first-use-report.json": receipt["first_use"]["report_sha256"],
        "diagnosis-report.json": receipt["seeded_diagnosis"]["report_sha256"],
        "maintenance-before-report.json": receipt["maintenance"]["stale_state_failure_report_sha256"],
        "maintenance-report.json": receipt["maintenance"]["updated_report_sha256"],
        "relocation-report.json": receipt["relocation"]["report_sha256"],
    }
    for name, status in expected_status.items():
        raw = bytes_at(name)
        require(digest(raw) == receipt_digests[name], "report hash differs from route receipt: " + name)
        report = json.loads(raw.decode("utf-8"))
        require(report.get("report_version") == 3 and report.get("runner_version") == "v0.4.0-rc.6" and
                report.get("summary", {}).get("total") == 1 and len(report.get("results", [])) == 1,
                "candidate report denominator/version differs: " + name)
        result = report["results"][0]
        require(result.get("status") == status and result.get("cleanup", {}).get("confirmed_exited") is True and
                result.get("workspace", {}).get("cleaned") is True, "report result/cleanup differs: " + name)
        reports[name] = result
    for name in ("first-use-report.json", "maintenance-report.json", "relocation-report.json"):
        require(all(step.get("status") == "passed" for step in reports[name].get("steps", [])),
                "passing public route report contains a failed step: " + name)
    diagnosis = reports["diagnosis-report.json"]
    diagnosis_failure = diagnosis.get("failure", {})
    diagnosis_steps = diagnosis.get("steps", [])
    require(receipt.get("seeded_diagnosis", {}).get("status") == "failed-as-seeded" and
            diagnosis_steps and diagnosis_steps[0].get("status") == "passed" and
            diagnosis_failure.get("category") == receipt["seeded_diagnosis"].get("category") == "assertion_timeout" and
            diagnosis_steps[-1].get("status") == "not_run", "seeded wrong-screen diagnosis evidence differs")
    diagnosis_spec = json.loads(bytes_at("diagnosis/create-note.json").decode("utf-8"))
    require(any(step.get("expect") == "WRONG_JOE_SCREEN_EXPECTATION" for step in diagnosis_spec.get("steps", [])),
            "seeded diagnosis did not alter the intended rendered-screen expectation")
    stale = reports["maintenance-before-report.json"]
    stale_failure = stale.get("failure", {})
    require(stale_failure.get("category") == "state_assertion_failure" and
            any(step.get("status") == "passed" for step in stale.get("steps", [])),
            "stale saved-state maintenance probe did not fail at the intended saved-state check")
    require(receipt.get("maintenance", {}).get("selected_state_only") is True and
            receipt.get("maintenance", {}).get("updated_bytes_sha256") == digest(INITIAL[:-1] + UPDATED.encode() + INITIAL[-1:]),
            "selected-state maintenance receipt or resulting byte hash differs")
    maintenance_bytes = bytes_at("maintenance/create-note.json")
    maintenance = json.loads(maintenance_bytes.decode("utf-8"))
    expected_maintenance = json.loads(json.dumps(spec))
    for step in expected_maintenance["steps"]:
        if step.get("text") == MARKER:
            step["text"] = UPDATED
        if step.get("expect") == MARKER:
            step["expect"] = UPDATED
        if step.get("state", {}).get("path") == "public-note.txt":
            step["state"]["bytes_base64"] = base64.b64encode(INITIAL[:-1] + UPDATED.encode() + INITIAL[-1:]).decode("ascii")
    require(maintenance == expected_maintenance, "selected-state maintenance changed unrelated spec fields")
    maintenance_snapshot = prefix + "maintenance/snapshots/initial-note.txt"
    require(payloads.get(maintenance_snapshot) == payloads[snapshot_path], "maintenance changed the approved initial screen snapshot")
    relocated = json.loads(bytes_at("relocated space café 雪/create-note.json").decode("utf-8"))
    require(relocated == maintenance and receipt.get("relocation", {}).get("passed") is True and
            receipt.get("relocation", {}).get("path") == "relocated space café 雪",
            "spaced Unicode relocation did not preserve the exact maintained project")
    workflow = bytes_at("delivered-workflow-preview.yml")
    route_workflow = receipt["delivered_workflow_preview"]
    require(digest(workflow) == route_workflow.get("sha256") and
            route_workflow.get("dispatched") is False and route_workflow.get("provider_run") is None,
            "workflow preview hash or non-dispatch boundary differs")
    workflow_text = workflow.decode("utf-8")
    for value in (route_workflow.get("revision"), route_workflow.get("suite"), PIN,
                  route_workflow.get("setup"), route_workflow.get("build"), "pull_request:"):
        require(value and value in workflow_text, "delivered workflow preview omits a pinned command/revision/suite/trigger")

    attempts = receipt.get("attempts", [])
    require([item.get("label") for item in attempts] == LABELS and len(attempts) == len(set(item.get("id") for item in attempts)),
            "attempt receipt is incomplete, out of order, or reuses an ID")
    audited_attempts = []
    identity_paths = set()
    for item, expected_exit in zip(attempts, EXIT_CODES):
        ident, label = item["id"], item["label"]
        lifecycle = {}
        for kind in ("started", "identified", "launched", "finished"):
            event = root_obj(f"events/{ident}-{kind}.json")
            require(event.get("id") == ident and event.get("event") == kind and
                    event.get("project") == PROJECT and event.get("phase") == "public-authoring" and
                    event.get("label") == label, f"attempt lifecycle identity mismatch: {ident}/{kind}")
            lifecycle[kind] = event
        finished = lifecycle["finished"]
        require(isinstance(lifecycle["launched"].get("pid"), int) and lifecycle["launched"]["pid"] > 0 and
                finished.get("exit_code") == expected_exit == item.get("returncode") and
                finished.get("category") == "passed" and not finished.get("cleanup_errors") and
                finished.get("harness_cleanup") == "harness_process_reaped",
                "attempt launch, expected exit or cleanup differs: " + label)
        console_path = f"joe/{ident}/console.log"
        console = payloads.get(console_path)
        require(console is not None and len(console) == finished.get("output_bytes") and
                digest(console) == finished.get("console_sha256"), "attempt console hash/length differs: " + label)
        identity = lifecycle["identified"].get("identity", {})
        envelope_name = identity.get("manifest", "")
        envelope_path = PurePosixPath(envelope_name)
        require(not envelope_path.is_absolute() and ".." not in envelope_path.parts,
                "unsafe attempt identity envelope path")
        envelope_raw = payloads.get(envelope_name)
        require(envelope_raw is not None and digest(envelope_raw) == identity.get("sha256"),
                "attempt identity envelope hash differs: " + label)
        envelope = json.loads(envelope_raw.decode("utf-8"))
        nested = {}
        for ref_name in ("base", "target_catalog"):
            ref = envelope.get(ref_name, {})
            nested_name = ref.get("manifest", "")
            nested_path = PurePosixPath(nested_name)
            require(not nested_path.is_absolute() and ".." not in nested_path.parts,
                    "unsafe nested identity manifest path")
            nested_raw = payloads.get(nested_name)
            require(nested_raw is not None and digest(nested_raw) == ref.get("sha256"),
                    "nested attempt identity manifest hash differs: " + label)
            nested[ref_name] = json.loads(nested_raw.decode("utf-8"))
            identity_paths.add(nested_name)
        base_files = nested["base"].get("files", {})
        target_files = nested["target_catalog"].get("files", {})
        target_binary = [value for name, value in target_files.items()
                         if name.endswith("/active/joe/install/bin/joe")]
        candidate_binary = [value for name, value in base_files.items()
                            if name.endswith(f"/candidate-native-exit-v1/{host}/playtestr")]
        build_receipt_hashes = [value for name, value in base_files.items()
                                if name.endswith("/active/joe/build.json")]
        runtime_receipt_hashes = [value for name, value in base_files.items()
                                  if name.endswith("/active/joe/runtime.json")]
        acquisition_hashes = [value for name, value in base_files.items()
                              if name.endswith("/active/joe/acquisition.json")]
        require(nested["base"].get("project") == PROJECT and nested["target_catalog"].get("project") == PROJECT and
                host_runner["binary"] in candidate_binary and build.get("binary_sha256") in target_binary and
                digest(payloads["joe/retained-source/build.json"]) in build_receipt_hashes and
                digest(payloads["joe/retained-source/runtime.json"]) in runtime_receipt_hashes and
                digest(payloads["joe/retained-source/acquisition.json"]) in acquisition_hashes and
                acquisition.get("pin") == PIN,
                "nested attempt identity does not bind the candidate, target, build, runtime, and pin: " + label)
        audited_attempts.append({"id": ident, "label": label, "exit_code": expected_exit,
                                 "console_sha256": finished["console_sha256"],
                                 "identity_envelope": envelope_name, "identity_sha256": identity["sha256"],
                                 "base_manifest": envelope["base"]["manifest"],
                                 "target_catalog_manifest": envelope["target_catalog"]["manifest"],
                                 "launch_pid": lifecycle["launched"]["pid"],
                                 "harness_cleanup": finished["harness_cleanup"]})
    require(identity_paths, "attempts do not retain any source-bound identity manifests")
    return {
        "host": host, "architecture": build["architecture"], "target_binary_sha256": build["binary_sha256"],
        "native_build_commands": len(commands), "candidate_archive_sha256": host_runner["archive"],
        "runner_binary_sha256": host_runner["binary"], "zip_members": zip_members,
        "zip_expanded_bytes": expanded_bytes, "attempts": audited_attempts,
        "first_use_controls": receipt["first_use"]["controls"],
        "first_use_shell_invocations": receipt["first_use"]["shell_invocations"],
        "first_use_report_sha256": receipt["first_use"]["report_sha256"],
        "maintenance_report_sha256": receipt["maintenance"]["updated_report_sha256"],
        "diagnosis_category": diagnosis_failure["category"],
        "relocation_path": receipt["relocation"]["path"],
        "workflow_preview_sha256": route_workflow["sha256"], "target_removed": removed["removed"],
        "processes_confirmed_absent": process["confirmed_no_matching_live_processes"],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--linux-zip", type=Path, required=True)
    parser.add_argument("--linux-size", type=int, required=True)
    parser.add_argument("--linux-sha256", required=True)
    parser.add_argument("--darwin-zip", type=Path, required=True)
    parser.add_argument("--darwin-size", type=int, required=True)
    parser.add_argument("--darwin-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v1.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    results = {
        "linux": verify_host("linux", args.linux_zip, args.linux_size, args.linux_sha256, args.run_id, freeze),
        "darwin": verify_host("darwin", args.darwin_zip, args.darwin_size, args.darwin_sha256, args.run_id, freeze),
    }
    output = {
        "schema_version": 1, "project": PROJECT, "workflow_run": args.run_id,
        "workflow_head_sha": args.head_sha, "candidate": "v0.4.0-rc.6",
        "project_admission_credit": 0,
        "provider_packets": {
            "linux": {"bytes": args.linux_size, "sha256": args.linux_sha256},
            "darwin": {"bytes": args.darwin_size, "sha256": args.darwin_sha256},
        },
        "status": "public-route-readback-passed-not-project-admitted",
        "hosts": results,
        "scope": "Independent provider ZIP digest/CRC, candidate and target identity, all nine attempt lifecycles and console identities, first-use spec and exact state, seeded diagnosis, stale-state rejection, selected maintenance preservation, relocation, generated workflow preview, and cleanup. Twenty-scenario, fault, oracle-model, and admission evidence remain separate.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = (json.dumps(output, sort_keys=True, indent=2) + "\n").encode("utf-8")
    if args.output.exists():
        if args.output.read_bytes() != encoded:
            raise FileExistsError("refusing to overwrite a different immutable route readback")
    else:
        with args.output.open("xb") as stream:
            stream.write(encoded)
    print(json.dumps({"status": output["status"], "project": PROJECT,
                      "workflow_run": args.run_id, "readback": str(args.output)}, sort_keys=True))


if __name__ == "__main__":
    main()
