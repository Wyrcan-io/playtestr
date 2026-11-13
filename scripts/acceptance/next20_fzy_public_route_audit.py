"""Independently audit fzy's native public-route provider packets."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC
from next20_fzy_public_route import DECLARATION, PACKAGE
from readiness_evidence import immutable_json, sha256


ROOT_MEMBER = "artifacts/runner-readiness-next-twenty-project-pass/"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def obj(data, label):
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON in {label}") from error
    require(isinstance(value, dict), f"{label} must contain an object")
    return value


def inspect_zip(path, expected_bytes, expected_sha, host):
    raw = Path(path).read_bytes()
    require(len(raw) == expected_bytes and digest(raw) == expected_sha,
            f"{host}: provider artifact byte count or SHA-256 differs")
    files = {}
    expanded = 0
    with zipfile.ZipFile(path) as archive:
        entries = archive.infolist()
        names = [item.filename for item in entries]
        require(len(names) == len(set(names)) and archive.testzip() is None,
                f"{host}: ZIP duplicate member or CRC failure")
        for entry in entries:
            path_value = PurePosixPath(entry.filename)
            mode = entry.external_attr >> 16
            require(not path_value.is_absolute() and ".." not in path_value.parts
                    and "\\" not in entry.filename and not entry.flag_bits & 1
                    and mode & 0o170000 != 0o120000,
                    f"{host}: unsafe ZIP member {entry.filename}")
            require(entry.file_size <= 8 * 1024**2,
                    f"{host}: ZIP member exceeds the reviewed bound")
            expanded += entry.file_size
            require(expanded <= 32 * 1024**2,
                    f"{host}: expanded ZIP exceeds the reviewed bound")
            if not entry.is_dir():
                files[entry.filename] = archive.read(entry)
    return files, {"zip_bytes": len(raw), "zip_sha256": digest(raw),
                   "zip_entries": len(entries), "expanded_bytes": expanded}


def repo_member(path):
    value = Path(path).as_posix()
    require(value.startswith(ROOT_MEMBER), "report path escapes campaign raw root")
    return value[len(ROOT_MEMBER):]


def audit_host(host, zip_path, provider, run_id, attempt):
    files, zip_stats = inspect_zip(zip_path, provider["artifact_bytes"],
                                   provider["artifact_sha256"], host)

    def get(name):
        require(name in files, f"{host}: missing ZIP member {name}")
        return files[name]

    def json_member(name):
        return obj(get(name), name)

    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v3.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    scenario_path = PACKAGE / "scenario-declaration-v1.json"
    cell = next(row for row in freeze["cells"] if row["host"] == host)
    route_root = f"fzy/public-route-v1/{host}"
    receipt = json_member(route_root + "/receipt-v1.json")
    require(receipt.get("project") == "fzy" and receipt.get("host") == host
            and receipt.get("source_pin") == declaration["source_pin"]
            and receipt.get("source_archive_sha256") == declaration["source_archive_sha256"]
            and receipt.get("candidate") == declaration["candidate"] == freeze["version"]
            and receipt.get("candidate_series") == declaration["candidate_series"] == freeze["series"]
            and receipt.get("candidate_archive_sha256") == cell["archive_sha256"]
            and receipt.get("candidate_binary_sha256") == cell["binary_sha256"]
            and receipt.get("route_declaration_sha256") == sha256(DECLARATION)
            and receipt.get("scenario_declaration_sha256") == sha256(scenario_path)
            and receipt.get("human_participants") == 0
            and receipt.get("usability") == "unmeasured"
            and receipt.get("admission_credit") == 0
            and receipt.get("saved_state_coverage_credit") == 0,
            f"{host}: route receipt source/candidate/declaration/credit differs")
    installed = json_member(f"candidate-native-exit-v3/{host}/installed.json")
    require(installed.get("archive_sha256") == cell["archive_sha256"]
            and installed.get("binary_sha256") == cell["binary_sha256"],
            f"{host}: installed runner differs from frozen candidate")
    retained = "fzy/retained-source"
    acquisition = json_member(retained + "/acquisition.json")
    build = json_member(retained + "/build.json")
    runtime = json_member(retained + "/runtime.json")
    inventory = json_member(retained + "/cleanup-inventory.json")
    removed = json_member(retained + "/removed.json")
    process = json_member("fzy/process-proof.json")
    require(digest(get(retained + "/source.tar.gz")) == declaration["source_archive_sha256"]
            and acquisition.get("repository") == declaration["repository"]
            and acquisition.get("pin") == declaration["source_pin"]
            and build.get("host") == host and build.get("pin") == declaration["source_pin"]
            and build.get("upstream_tests") == "passed"
            and build.get("binary_sha256") == receipt.get("target_binary_sha256")
            and runtime.get("native_sha256") == build.get("binary_sha256")
            and inventory.get("source_restored_exact") is True
            and removed.get("removed") is True and removed.get("source_restored_exact") is True
            and process.get("confirmed_no_matching_live_processes") is True
            and process.get("matching_live_processes") == []
            and digest(get("fzy/process-proof.json")) == inventory.get("process_proof_sha256"),
            f"{host}: exact source/build/runtime/cleanup evidence differs")

    project = json_member(route_root + "/project/fzy-select.json")
    fixture = get(route_root + "/project/fixtures/choices.txt")
    maintenance = json_member(route_root + "/maintenance/fzy-select.json")
    maintenance_fixture = get(route_root + "/maintenance/fixtures/choices.txt")
    relocated = json_member(route_root + "/relocated space café 雪/fzy-select.json")
    relocated_fixture = get(route_root + "/relocated space café 雪/fixtures/choices.txt")
    diagnosis = json_member(route_root + "/diagnosis/fzy-select.json")
    require(digest(fixture) == digest(__import__("base64").b64decode(
                declaration["first_use_fixture_base64"], validate=True))
            and digest(maintenance_fixture) == digest(__import__("base64").b64decode(
                declaration["maintenance_fixture_base64"], validate=True))
            and fixture == __import__("base64").b64decode(declaration["first_use_fixture_base64"], validate=True)
            and maintenance_fixture == __import__("base64").b64decode(
                declaration["maintenance_fixture_base64"], validate=True)
            and relocated_fixture == maintenance_fixture and relocated == maintenance
            and project["steps"][-1]["state"].get("bytes_base64") == declaration["first_use_output_base64"]
            and maintenance["steps"][-1]["state"].get("bytes_base64") == declaration["maintenance_output_base64"]
            and diagnosis["steps"][-1]["state"].get("bytes_base64") == "AQ==",
            f"{host}: recorded, maintained, relocated or seeded diagnosis contract differs")

    expected_reports = {
        "first-use-report.json": ("passed", None),
        "maintenance-report.json": ("passed", None),
        "relocation-report.json": ("passed", None),
        "diagnosis-report.json": ("failed", "state_assertion_failure"),
    }
    reports = {}
    for name, (expected_status, expected_failure) in expected_reports.items():
        path = route_root + "/" + name
        report = json_member(path)
        require(report.get("report_version") == 3 and report.get("runner_version") == "v0.4.0-rc.8"
                and report.get("summary", {}).get("total") == 1
                and len(report.get("results", [])) == 1,
                f"{host} {name}: report schema/candidate/denominator differs")
        result = report["results"][0]
        require(result.get("status") == expected_status
                and result.get("cleanup", {}).get("confirmed_exited") is True
                and result.get("workspace", {}).get("cleaned") is True,
                f"{host} {name}: status or target/workspace cleanup differs")
        states = [step for step in result.get("steps", []) if step.get("action") == "state"]
        require(len(states) == 1 and states[0].get("state", {}).get("path") == "result.txt"
                and states[0].get("state", {}).get("kind") == "file",
                f"{host} {name}: exact output state checkpoint missing")
        if expected_failure:
            failed = [step for step in result.get("steps", []) if step.get("status") == "failed"]
            require(result.get("failure", {}).get("category") == expected_failure
                    and len(failed) == 1 and failed[0].get("number") == 4
                    and states[0].get("status") == "failed"
                    and states[0].get("state", {}).get("outcome") == "rejected",
                    f"{host}: seeded diagnosis did not fail at exact state boundary")
        else:
            require(result.get("failure") is None
                    and all(step.get("status") == "passed" for step in result.get("steps", []))
                    and states[0].get("status") == "passed"
                    and states[0].get("state", {}).get("outcome") == "matched",
                    f"{host} {name}: exact state bytes did not pass")
        reports[name] = {"sha256": digest(get(path)), "status": result["status"],
                         "failure_category": result.get("failure", {}).get("category")}

    workflow = get(route_root + "/workflow-preview.yml").decode("utf-8")
    require(receipt.get("workflow_preview") == "reviewed-only-not-dispatched"
            and receipt.get("preview_sha256") == digest(get(route_root + "/workflow-preview.yml"))
            and declaration["source_pin"] in workflow and "pull_request:" in workflow,
            f"{host}: generated workflow preview identity or non-dispatch boundary differs")
    attempts = receipt.get("attempts", [])
    require(len(attempts) == 8 and len({item["attempt_id"] for item in attempts}) == 8,
            f"{host}: route attempt denominator differs")
    audited_events = []
    for item in attempts:
        attempt_id = item["attempt_id"]
        started = json_member(f"events/{attempt_id}-started.json")
        identified = json_member(f"events/{attempt_id}-identified.json")
        launched = json_member(f"events/{attempt_id}-launched.json")
        finished = json_member(f"events/{attempt_id}-finished.json")
        expected_exit = 1 if item["label"] == "fzy-seeded-saved-output-diagnosis" else 0
        require(started.get("project") == "fzy" and started.get("phase") == "public-authoring"
                and str(started.get("ci_run_id")) == str(run_id)
                and str(started.get("ci_run_attempt")) == str(attempt)
                and started.get("expected_exit") == expected_exit
                and identified.get("project") == "fzy" and identified.get("phase") == "public-authoring"
                and launched.get("project") == "fzy" and launched.get("phase") == "public-authoring"
                and isinstance(launched.get("pid"), int) and launched["pid"] > 0
                and finished.get("project") == "fzy" and finished.get("phase") == "public-authoring"
                and finished.get("category") == "passed" and finished.get("exit_code") == expected_exit
                and finished.get("harness_cleanup") == "harness_process_reaped",
                f"{host} {item['label']}: launch/exit/cleanup event sequence differs")
        identity_link = identified.get("identity", {})
        identity_path = identity_link.get("manifest", "")
        identity_member = identity_path if identity_path.startswith("identities/") else "identities/" + identity_path
        identity_bytes = get(identity_member)
        require(digest(identity_bytes) == identity_link.get("sha256"),
                f"{host} {item['label']}: identity manifest digest differs")
        identity = obj(identity_bytes, identity_path)
        for child in identity.values():
            if isinstance(child, dict) and "manifest" in child and "sha256" in child:
                nested = child["manifest"]
                nested_member = nested if nested.startswith("identities/") else "identities/" + nested
                require(digest(get(nested_member)) == child["sha256"],
                        f"{host} {item['label']}: nested identity digest differs")
        audited_events.append(attempt_id)
    require(receipt.get("target_cleanup_confirmed") is True
            and receipt.get("first_use") == "passed"
            and receipt.get("maintenance") == "passed-selected-state-update"
            and receipt.get("relocation") == "passed-unicode-and-spaces"
            and receipt.get("diagnosis") == "state_assertion_failure at step 4",
            f"{host}: route gate receipt claims are incomplete")
    return {"host": host, **zip_stats, "provider_artifact_id": provider["artifact_id"],
            "candidate_archive_sha256": cell["archive_sha256"],
            "candidate_binary_sha256": cell["binary_sha256"],
            "attempts": len(audited_events), "reports": reports,
            "first_use": "passed", "diagnosis": "state_assertion_failure at step 4",
            "maintenance": "passed", "relocation": "passed",
            "workflow_preview": "reviewed-only-not-dispatched",
            "target_cleanup_confirmed": True, "saved_state_coverage_credit": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--run-attempt", type=int, default=1)
    for host in ("linux", "darwin"):
        parser.add_argument(f"--{host}-zip", required=True)
        parser.add_argument(f"--{host}-artifact-id", type=int, required=True)
        parser.add_argument(f"--{host}-bytes", type=int, required=True)
        parser.add_argument(f"--{host}-sha256", required=True)
    parser.add_argument("--output", default=str(PACKAGE / "public-route-artifact-audit-v1.json"))
    args = parser.parse_args()
    require(1 <= args.run_attempt <= 99 and 1 <= args.run_id <= 10**12,
            "provider run identity is outside the reviewed bound")
    results = []
    for host in ("linux", "darwin"):
        provider = {"artifact_id": getattr(args, host + "_artifact_id"),
                    "artifact_bytes": getattr(args, host + "_bytes"),
                    "artifact_sha256": getattr(args, host + "_sha256")}
        results.append(audit_host(host, getattr(args, host + "_zip"), provider,
                                  args.run_id, args.run_attempt))
    audit = {"schema_version": 1, "project": "fzy", "run_id": args.run_id,
             "run_attempt": args.run_attempt, "candidate": "v0.4.0-rc.8",
             "candidate_series": "native-exit-v3", "results": results,
             "public_route_host_passes": len(results), "saved_state_coverage_credit": 0,
             "human_participants": 0, "usability": "unmeasured",
             "admission_credit": 0,
             "scope": "Independent bounded ZIP/provider, source/build/candidate, recorder spec/fixture, diagnosis/maintenance/relocation reports, workflow preview, event/identity, and process/source cleanup readback."}
    immutable_json(Path(args.output), audit)
    print(json.dumps({"project": "fzy", "run_id": args.run_id,
                      "public_route_hosts": audit["public_route_host_passes"],
                      "audit_sha256": sha256(Path(args.output))}, sort_keys=True))


if __name__ == "__main__":
    main()
