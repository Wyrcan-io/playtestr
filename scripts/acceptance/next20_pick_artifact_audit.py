"""Independently audit the retained rc.8 Pick development artifacts."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC, ROOT


def digest(data):
    return hashlib.sha256(data).hexdigest()


def require(value, message):
    if not value:
        raise ValueError(message)


def audit_host(row, archive_path, declaration, freeze, phase="development", repetitions=1):
    host = row["host"]
    raw = Path(archive_path).read_bytes()
    require(len(raw) == row["artifact_bytes"] and digest(raw) == row["artifact_sha256"],
            f"{host}: provider artifact size/digest differs")
    with zipfile.ZipFile(archive_path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        require(len(names) == len(set(names)) and archive.testzip() is None,
                f"{host}: duplicate ZIP path or CRC failure")
        payload = {}
        expanded = 0
        for item in infos:
            path = PurePosixPath(item.filename)
            mode = item.external_attr >> 16
            require(not path.is_absolute() and ".." not in path.parts and "\\" not in item.filename
                    and not item.flag_bits & 1 and not (mode & 0o170000) == 0o120000
                    and item.file_size <= 64 * 1024**2,
                    f"{host}: unsafe or oversized ZIP member {item.filename}")
            expanded += item.file_size
            require(expanded <= 96 * 1024**2, f"{host}: expanded artifact exceeds bound")
            if not item.is_dir():
                payload[item.filename] = archive.read(item)

    def get(path):
        require(path in payload, f"{host}: missing {path}")
        return payload[path]

    def obj(path):
        try:
            value = json.loads(get(path).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ValueError(f"{host}: invalid JSON in {path}") from error
        require(isinstance(value, dict), f"{host}: {path} is not an object")
        return value

    source = obj("pick/retained-source/acquisition.json")
    build_raw = get("pick/retained-source/build.json")
    build = json.loads(build_raw)
    runtime = obj("pick/retained-source/runtime.json")
    removed = obj("pick/retained-source/removed.json")
    proof = obj("pick/process-proof.json")
    source_archive = get("pick/retained-source/source.tar.gz")
    require(digest(source_archive) == row["source_archive_sha256"] == source["archive_sha256"]
            and source.get("pin") == declaration["pin"]
            and source.get("repository") == declaration["repository"],
            f"{host}: reviewed source pin/archive identity differs")
    require(build.get("project") == "pick" and build.get("pin") == declaration["pin"]
            and build.get("host") == host and build.get("upstream_tests") == "passed"
            and build.get("binary_sha256") == row["target_binary_sha256"]
            and runtime.get("native_sha256") == row["target_binary_sha256"]
            and runtime.get("kind") == "native",
            f"{host}: native build/runtime identity differs")
    require(removed.get("removed") is True and removed.get("source_restored_exact") is True
            and proof.get("confirmed_no_matching_live_processes") is True
            and not proof.get("matching_live_processes"),
            f"{host}: source restoration or descendant cleanup is unconfirmed")

    installed = obj(f"candidate-native-exit-v3/{host}/installed.json")
    frozen = next(cell for cell in freeze["cells"] if cell["host"] == host)
    require(installed.get("series") == declaration["candidate_series"]
            and installed.get("version") == declaration["candidate"]
            and installed.get("archive_sha256") == frozen["archive_sha256"] == row["candidate_archive_sha256"]
            and installed.get("binary_sha256") == frozen["binary_sha256"] == row["candidate_binary_sha256"],
            f"{host}: installed runner is not the exact frozen rc.8 archive")

    expected = {scenario["id"]: scenario for scenario in declaration["scenarios"]}
    require(len(expected) == 20 and row["attempt_count"] == 20 * repetitions,
            f"{host}: scenario contract or attempt count differs")
    outcomes = []
    for repetition, (scenario_id, contract) in (
            (repetition, item) for repetition in range(1, repetitions + 1)
            for item in sorted(expected.items())):
        report_path = f"pick/{phase}/{host}/r{repetition:02d}/{scenario_id}/report.json"
        report_raw = get(report_path)
        report = json.loads(report_raw)
        require(report.get("runner_version") == declaration["candidate"]
                and report.get("os") == host and report.get("summary") ==
                {"total": 1, "passed": 1, "failed": 0, "cancelled": 0, "not_run": 0}
                and len(report.get("results", [])) == 1,
                f"{host} {scenario_id}: report summary/version differs")
        case = report["results"][0]
        require(case.get("status") == "passed" and case.get("target", {}).get("exited") is True
                and case.get("target", {}).get("exit_code") == contract["expected_target_exit"]
                and case.get("cleanup", {}).get("confirmed_exited") is True
                and case.get("workspace", {}).get("cleaned") is True
                and case.get("workspace", {}).get("id") == case.get("invocation_id")
                and all(step.get("status") == "passed" for step in case.get("steps", []))
                and case.get("steps", [])[-1].get("action") == "exit",
                f"{host} {scenario_id}: positive steps, exact exit, or same-invocation cleanup missing")
        spec_path = DOC / contract["spec_path"]
        fixture_path = DOC / contract["fixture_path"]
        spec_repo_path = spec_path.relative_to(ROOT).as_posix()
        fixture_repo_path = fixture_path.relative_to(ROOT).as_posix()
        require(digest(spec_path.read_bytes()) == contract["spec_sha256"]
                and len(fixture_path.read_bytes()) == contract["fixture_bytes"]
                and digest(fixture_path.read_bytes()) == contract["fixture_sha256"]
                and case.get("spec_path") == spec_repo_path,
                f"{host} {scenario_id}: executed contract or fixture differs from declaration")
        invocation = case["invocation_id"]
        label = f"pick-{phase}-{host}-r{repetition:02d}-{scenario_id}"
        started_rows = [json.loads(data) for name, data in payload.items()
                        if name.startswith("events/") and name.endswith("-started.json")
                        and json.loads(data).get("label") == label]
        require(len(started_rows) == 1, f"{host} {scenario_id}: expected exactly one started harness command")
        event_id = started_rows[0]["id"]
        base = f"events/{event_id}"
        started = obj(base + "-started.json")
        identified = obj(base + "-identified.json")
        launched = obj(base + "-launched.json")
        finished = obj(base + "-finished.json")
        require(all(event.get("id") == event_id and event.get("label") == label
                    and event.get("project") == "pick" and event.get("phase") == phase
                    for event in (started, identified, launched, finished))
                and started.get("ci_run_id") == row["run_id"]
                and identified.get("identity", {}).get("sha256")
                and launched.get("pid") and finished.get("category") == "passed"
                and finished.get("exit_code") == 0 and finished.get("cleanup_errors") == []
                and finished.get("harness_cleanup") == "harness_process_reaped",
                f"{host} {scenario_id}: run lifecycle/event evidence differs")
        identity_path = identified["identity"]["manifest"]
        identity_raw = get(identity_path)
        require(digest(identity_raw) == identified["identity"]["sha256"],
                f"{host} {scenario_id}: command identity manifest hash differs")
        identity = json.loads(identity_raw)
        base_ref = identity["base"]
        base_raw = get(base_ref["manifest"])
        require(digest(base_raw) == base_ref["sha256"],
                f"{host} {scenario_id}: base identity manifest hash differs")
        files = json.loads(base_raw)["files"]
        require(files.get(f"artifacts/runner-readiness-next-twenty-project-pass/candidate-native-exit-v3/{host}/playtestr") == row["candidate_binary_sha256"]
                and files.get(spec_repo_path) == contract["spec_sha256"]
                and files.get(fixture_repo_path) == contract["fixture_sha256"]
                and files.get("artifacts/runner-readiness-next-twenty-project-pass/active/pick/build.json") == digest(build_raw),
                f"{host} {scenario_id}: exact candidate/target/spec/fixture not bound to command")
        console_path = f"pick/{event_id}/console.log"
        console = get(console_path)
        require(digest(console) == finished.get("console_sha256")
                and len(console) == finished.get("output_bytes"),
                f"{host} {scenario_id}: retained runner console identity differs")
        outcomes.append({"id": scenario_id, "repetition": repetition, "invocation_id": invocation,
                         "report_sha256": digest(report_raw), "status": "passed",
                         "target_exit": case["target"]["exit_code"],
                         "step_count": len(case["steps"])})

    require(len(outcomes) == row["passed"] == 20 * repetitions and row["failed"] == 0,
            f"{host}: all-attempt reconciliation differs")
    return {"host": host, "provider_job_id": row["databaseId"],
            "provider_artifact_id": row["artifact_id"], "provider_bytes": len(raw),
            "provider_sha256": digest(raw), "zip_members": len(infos),
            "expanded_bytes": expanded, "source_archive_sha256": digest(source_archive),
            "target_binary_sha256": row["target_binary_sha256"],
            "candidate_archive_sha256": row["candidate_archive_sha256"],
            "candidate_binary_sha256": row["candidate_binary_sha256"],
            "upstream_tests": "passed", "source_restored_exact": True,
            "target_and_descendant_cleanup": "confirmed", "attempt_count": 20 * repetitions,
            "passed": 20 * repetitions, "failed": 0, "scenarios": outcomes}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--linux-zip", type=Path, required=True)
    parser.add_argument("--darwin-zip", type=Path, required=True)
    parser.add_argument("--phase", default="development")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(args.phase and 1 <= args.repetitions <= 12, "invalid audit phase/repetition bound")
    manifest_raw = args.manifest.read_bytes()
    manifest = json.loads(manifest_raw)
    declaration_path = ROOT / manifest["scenario_declaration"]
    declaration_raw = declaration_path.read_bytes()
    declaration = json.loads(declaration_raw)
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v3.json"
    freeze_raw = freeze_path.read_bytes()
    freeze = json.loads(freeze_raw)
    require(digest(declaration_raw) == manifest["scenario_declaration_sha256"]
            and digest(freeze_raw) == declaration["candidate_freeze_sha256"]
            and manifest["candidate_run_id"] == "43330369205"
            and declaration["candidate_series"] == freeze["series"] == "native-exit-v3"
            and declaration["candidate"] == freeze["version"] == "v0.4.0-rc.8"
            and declaration["distinct_scenarios"] == 20 and declaration["project"] == "pick",
            "scenario declaration/provider manifest/frozen candidate identity differs")
    rows = {row["host"]: row for row in manifest["jobs"]}
    for row in rows.values():
        row["run_id"] = manifest["run_id"]
    require(set(rows) == {"linux", "darwin"} and len(manifest["jobs"]) == 2
            and all(row["status"] == "completed" and row["conclusion"] == "success"
                    and row["attempt_count"] == 20 * args.repetitions
                    and row["passed"] == 20 * args.repetitions and row["failed"] == 0
                    for row in rows.values()), "provider native host matrix or outcomes are incomplete")
    cells = [audit_host(rows[host], path, declaration, freeze, args.phase, args.repetitions)
             for host, path in (("linux", args.linux_zip), ("darwin", args.darwin_zip))]
    receipt = {"schema_version": 1, "run_id": manifest["run_id"],
               "workflow_revision": manifest["head_sha"], "candidate_run_id": manifest["candidate_run_id"],
               "candidate_series": manifest["candidate_series"], "candidate_version": manifest["candidate_version"],
               "phase": args.phase, "repetitions": args.repetitions,
               "scenario_declaration": manifest["scenario_declaration"],
               "scenario_declaration_sha256": manifest["scenario_declaration_sha256"],
               "provider_manifest_sha256": digest(manifest_raw), "hosts": cells,
               "ordinary_invocations": 40 * args.repetitions, "distinct_scenarios": 20,
               "scenario_project_credit": 0, "admission_credit": 0,
               "audit": "Provider ZIP digests/paths, candidate installs, source pin/build identity, exact declarations/fixtures, per-invocation source/candidate/spec/fixture identity, positive rendered-screen/exit steps, same-invocation workspace cleanup, process cleanup, and all 40 report/event/console records independently verified."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("xb") as stream:
        stream.write((json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode())
    print(json.dumps({"status": "audited", "output": str(args.output),
                      "hosts": len(cells), "ordinary_invocations": 40 * args.repetitions,
                      "project_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
