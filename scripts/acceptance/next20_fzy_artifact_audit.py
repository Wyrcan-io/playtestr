"""Independently audit the exact provider ZIPs for fzy's native matrix."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = DOC / "fzy"
DECLARATION = PROJECT / "scenario-declaration-v1.json"
FREEZE = DOC / "replacement-candidate-freeze-native-exit-v3.json"


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load_object(data, label):
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid JSON in {label}") from error
    require(isinstance(value, dict), f"{label} must be a JSON object")
    return value


def inspect_zip(path, expected_bytes, expected_sha, host):
    raw = Path(path).read_bytes()
    require(len(raw) == expected_bytes and digest(raw) == expected_sha,
            f"{host}: provider ZIP bytes or SHA-256 differs")
    payload = {}
    expanded = 0
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [entry.filename for entry in infos]
        require(len(names) == len(set(names)) and archive.testzip() is None,
                f"{host}: duplicate member or failed ZIP CRC")
        for entry in infos:
            name = entry.filename
            member = PurePosixPath(name)
            mode = entry.external_attr >> 16
            require(not member.is_absolute() and ".." not in member.parts
                    and "\\" not in name and not entry.flag_bits & 1
                    and mode & 0o170000 != 0o120000,
                    f"{host}: unsafe ZIP member {name}")
            require(entry.file_size <= 8 * 1024**2,
                    f"{host}: member exceeds the reviewed bound: {name}")
            expanded += entry.file_size
            require(expanded <= 32 * 1024**2,
                    f"{host}: expanded artifact exceeds its bound")
            if not entry.is_dir():
                payload[name] = archive.read(entry)
    return payload, {"zip_bytes": len(raw), "zip_sha256": digest(raw),
                     "zip_entries": len(infos), "expanded_bytes": expanded}


def audit_host(host, path, receipt, declaration, freeze, run_id, phase, repetitions):
    row = receipt["hosts"][host]
    files, zip_stats = inspect_zip(path, row["provider_bytes"], row["provider_sha256"], host)

    def get(name):
        require(name in files, f"{host}: missing artifact member {name}")
        return files[name]

    def obj(name):
        return load_object(get(name), name)

    build = obj("fzy/retained-source/build.json")
    acquisition = obj("fzy/retained-source/acquisition.json")
    runtime = obj("fzy/retained-source/runtime.json")
    removed = obj("fzy/retained-source/removed.json")
    process = obj("fzy/process-proof.json")
    require(digest(get("fzy/retained-source/source.tar.gz")) == row["source_archive_sha256"]
            == acquisition.get("archive_sha256") == declaration["source_archive_sha256"],
            f"{host}: exact pinned source archive differs")
    require(acquisition.get("repository") == declaration["repository"]
            and acquisition.get("pin") == declaration["pin"]
            and acquisition.get("build_hooks_executed") is False,
            f"{host}: target acquisition identity or hook boundary differs")
    require(build.get("project") == "fzy" and build.get("pin") == declaration["pin"]
            and build.get("host") == host and build.get("upstream_tests") == "passed"
            and build.get("binary_sha256") == row["native_binary_sha256"]
            and runtime.get("native_sha256") == row["native_binary_sha256"]
            and runtime.get("kind") == "native",
            f"{host}: target build/runtime identity differs")
    require(removed.get("removed") is True and removed.get("source_restored_exact") is True
            and process.get("confirmed_no_matching_live_processes") is True
            and process.get("matching_live_processes") == [],
            f"{host}: source removal or descendant cleanup is not confirmed")
    require(row["native_binary_sha256"] == build.get("binary_sha256"),
            f"{host}: installed fzy binary differs from build receipt")

    installed = obj(f"candidate-native-exit-v3/{host}/installed.json")
    frozen = next(cell for cell in freeze["cells"] if cell["host"] == host)
    require(installed.get("version") == receipt["candidate"]
            and installed.get("series") == receipt["candidate_series"]
            and installed.get("archive_sha256") == frozen["archive_sha256"]
            == row["candidate_archive_sha256"]
            and installed.get("binary_sha256") == frozen["binary_sha256"],
            f"{host}: installed runner differs from frozen native candidate")

    attempts_doc = obj(f"fzy/{phase}-{host}-run-{run_id}.json")
    expected = {item["id"]: item for item in declaration["scenarios"]}
    expected_total = 20 * repetitions
    require(len(expected) == 20 and len(attempts_doc.get("attempts", [])) == expected_total
            and attempts_doc.get("attempt_count") == expected_total
            and attempts_doc.get("candidate") == receipt["candidate"]
            and attempts_doc.get("phase") == phase
            and attempts_doc.get("repetitions") == repetitions
            and attempts_doc.get("admission_credit") == 0,
            f"{host}: run receipt denominator/candidate/phase differs")
    require(len({item.get("attempt_id") for item in attempts_doc["attempts"]}) == expected_total
            and len({item.get("invocation_id") for item in attempts_doc["attempts"]}) == expected_total,
            f"{host}: attempt or invocation identifiers are not unique")
    audited = []
    for attempt in attempts_doc["attempts"]:
        sid = attempt.get("scenario")
        require(sid in expected, f"{host}: undeclared scenario {sid}")
        repetition = attempt.get("repetition")
        require(isinstance(repetition, int) and 1 <= repetition <= repetitions
                and attempt.get("phase") == phase,
                f"{host} {sid}: repetition or phase differs")
        contract = expected[sid]
        base = f"fzy/{phase}/{host}/r{repetition:02d}/{sid}"
        repo_spec_path = "docs/validation/runner-readiness-next-twenty-project-pass/" + contract["spec_path"]
        report_path = base + "/report.json"
        report_raw = get(report_path)
        report = load_object(report_raw, report_path)
        require(digest(report_raw) == attempt.get("report_sha256"),
                f"{host} {sid}: report hash differs from run receipt")
        require(report.get("runner_version") == receipt["candidate"]
                and report.get("os") == host
                and report.get("summary") == {"total": 1, "passed": 1, "failed": 0,
                                                "cancelled": 0, "not_run": 0}
                and len(report.get("results", [])) == 1,
                f"{host} {sid}: report candidate/host/status differs")
        result = report["results"][0]
        require(result.get("invocation_id") == attempt.get("invocation_id")
                and result.get("spec_path") == repo_spec_path
                and result.get("status") == "passed"
                and result.get("target", {}).get("exit_code") == contract["expected_target_exit"]
                and result.get("cleanup", {}).get("confirmed_exited") is True
                and result.get("workspace", {}).get("cleaned") is True
                and all(step.get("status") == "passed" for step in result.get("steps", [])),
                f"{host} {sid}: result, exact exit, step or cleanup differs")
        spec_path = ROOT / repo_spec_path
        require(sha256(spec_path) == contract["spec_sha256"],
                f"{host} {sid}: materialized scenario specification digest differs")
        identity_event = obj(f"events/{attempt['attempt_id']}-identified.json")
        require(identity_event.get("id") == attempt["attempt_id"]
                and identity_event.get("project") == "fzy"
                and identity_event.get("phase") == "development",
                f"{host} {sid}: identified event differs")
        manifest = identity_event.get("identity", {}).get("manifest")
        manifest_sha = identity_event.get("identity", {}).get("sha256")
        identity = obj(manifest)
        require(digest(get(manifest)) == manifest_sha,
                f"{host} {sid}: identity manifest digest differs")
        nested = {}
        for key in ("base", "target_catalog"):
            link = identity.get(key, {})
            child = load_object(get(link.get("manifest", "")), f"{host} {sid} {key} manifest")
            require(digest(get(link["manifest"])) == link.get("sha256"),
                    f"{host} {sid}: {key} manifest digest differs")
            nested[key] = child
        require(nested["base"].get("files", {}).get(repo_spec_path) == contract["spec_sha256"],
                f"{host} {sid}: base identity does not bind exact scenario spec")
        for event in ("started", "launched", "finished"):
            record = obj(f"events/{attempt['attempt_id']}-{event}.json")
            require(record.get("id") == attempt["attempt_id"]
                    and record.get("event") == event
                    and record.get("project") == "fzy"
                    and record.get("phase") == "development",
                    f"{host} {sid}: {event} event differs")
            if event == "finished":
                require(record.get("category") == "passed" and record.get("exit_code") == 0
                        and record.get("harness_cleanup") == "harness_process_reaped",
                        f"{host} {sid}: finished event is not a clean pass")
            if event == "launched":
                require(isinstance(record.get("pid"), int) and record["pid"] > 0,
                        f"{host} {sid}: positive launch evidence is missing")
            if event == "started":
                require(str(record.get("ci_run_id")) == str(run_id),
                        f"{host} {sid}: started event belongs to another provider run")
        audited.append({"scenario": sid, "repetition": repetition, "attempt_id": attempt["attempt_id"],
                        "invocation_id": attempt["invocation_id"],
                        "report_sha256": attempt["report_sha256"], "status": "passed"})
    require({(row["scenario"], row["repetition"]) for row in audited} ==
            {(sid, repetition) for sid in expected for repetition in range(1, repetitions + 1)},
            f"{host}: scenario/repetition set differs from frozen declaration")
    return {"host": host, **zip_stats, "ordinary_passes": len(audited),
            "scenarios": audited, "candidate_archive_sha256": installed["archive_sha256"],
            "runner_binary_sha256": installed["binary_sha256"],
            "target_binary_sha256": build["binary_sha256"],
            "source_restored": True, "descendants_confirmed_gone": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", default="43356291927")
    parser.add_argument("--phase", default="development")
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--receipt")
    parser.add_argument("--linux-zip", required=True)
    parser.add_argument("--darwin-zip", required=True)
    parser.add_argument("--output", default=str(PROJECT / "development-artifact-audit-v1.json"))
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 12:
        parser.error("--repetitions must be between 1 and 12")
    receipt_path = Path(args.receipt) if args.receipt else PROJECT / f"{args.phase}-run{args.run_id}-v1.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    require(receipt.get("run_id") == int(args.run_id)
            and declaration.get("project") == "fzy"
            and declaration.get("distinct_scenarios") == 20,
            "fzy development receipt or declaration differs")
    results = [audit_host(host, path, receipt, declaration, freeze, args.run_id,
                          args.phase, args.repetitions) for host, path in
               (("linux", args.linux_zip), ("darwin", args.darwin_zip))]
    audit = {"schema_version": 1, "project": "fzy", "run_id": int(args.run_id),
             "phase": args.phase, "repetitions_per_host": args.repetitions,
             "candidate": receipt["candidate"], "declaration_sha256": sha256(DECLARATION),
             "results": results, "ordinary_passes": sum(x["ordinary_passes"] for x in results),
             "new_project_admission_credit": 0,
             "scope": "Independent ZIP digest, safe member, candidate, source, event, identity, report, exact exit, scenario and cleanup readback."}
    immutable_json(Path(args.output), audit)
    print(json.dumps({"project": "fzy", "run_id": args.run_id,
                      "ordinary_passes": audit["ordinary_passes"],
                      "hosts": [row["host"] for row in results],
                      "audit_sha256": sha256(Path(args.output))}, sort_keys=True))


if __name__ == "__main__":
    main()
