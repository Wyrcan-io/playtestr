"""Audit and freeze the exact rc.8 native packet artifacts without rebuilding."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
import zipfile

from next20_check import DOC, NAME, RAW, ROOT
from next20_replacement_audit import audit, hashes
from readiness_evidence import immutable_json, sha256

RUN = "43330369205"
QUALIFICATION_REVISION = "78252c770635ec429e63e4b618e9c319af89c343"
SOURCE_REVISION = "78252c770635ec429e63e4b618e9c319af89c343"
SERIES = "native-exit-v3"
VERSION = "v0.4.0-rc.8"
HOST_LABEL = {"linux": "Linux", "darwin": "macOS", "windows": "Windows"}
HOST_RUNNER = {"linux": "ubuntu-24.04", "darwin": "macos-15", "windows": "windows-2025"}


def require(value, message):
    if not value:
        raise ValueError(message)


def immutable_or_match(path, value):
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
        require(existing == value, "existing immutable output differs: " + path.name)
        return
    immutable_json(path, value)


def source_readback(packet, host, provider, output_path):
    source_archive = subprocess.check_output(
        ["git", "archive", QUALIFICATION_REVISION, "scripts/acceptance", "scripts/ci", "schema", "go.mod", "go.sum"],
        cwd=ROOT, timeout=60)
    require(len(source_archive) <= 64 * 1024**2, "qualification source archive bound")
    expected = {}
    with tarfile.open(fileobj=io.BytesIO(source_archive)) as stream:
        for member in stream:
            if member.isfile() and (member.name.endswith(".py") or
                    member.name.startswith("schema/") and member.name.endswith(".json") or
                    member.name in {"go.mod", "go.sum"}):
                expected[member.name] = hashes(stream.extractfile(member).read())
    observed = []
    events = packet / "events"
    identified = sorted(events.glob("*-identified.json"))
    require(len(identified) == 12, f"expected twelve command identity receipts; found {len(identified)}")
    for event_path in identified:
        event = json.loads(event_path.read_text(encoding="utf-8"))
        reference = event["identity"]
        manifest_path = (packet / reference["manifest"]).resolve(strict=True)
        manifest_path.relative_to(packet.resolve(strict=True))
        require(manifest_path.is_file() and not manifest_path.is_symlink() and
                sha256(manifest_path) == reference["sha256"], "command identity manifest hash/path differs")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = manifest["files"]
        missing = [name for name, allowed in expected.items() if name not in files or files[name] not in allowed]
        require(not missing, "command does not bind the exact qualification helper/module source" +
                (": " + missing[0] if missing else ""))
        require(event.get("campaign") == NAME and event.get("event") == "identified" and
                event.get("project") == "core", "unexpected command identity event")
        observed.append({"attempt": event["id"], "label": event["label"],
                         "manifest_sha256": reference["sha256"],
                         "matched_qualification_inputs": len(expected)})
    workflow_path = ".github/workflows/runner-readiness-next20-replacement-candidate.yml"
    workflow_bytes = subprocess.check_output(["git", "show", f"{QUALIFICATION_REVISION}:{workflow_path}"],
                                             cwd=ROOT, timeout=30)
    workflow_sha = hashlib.sha256(workflow_bytes).hexdigest()
    result = {"schema_version": 1, "host": host, "run": RUN,
              "qualification_revision": QUALIFICATION_REVISION,
              "source_revision": SOURCE_REVISION, "candidate_series": SERIES,
              "candidate_version": VERSION, "provider_job_id": provider["databaseId"],
              "retained_packet_artifact": provider["artifact_name"],
              "qualification_workflow": workflow_path,
              "qualification_workflow_sha256": workflow_sha,
              "qualification_inputs": len(expected), "commands": observed,
              "comparison": "Every captured Python helper under scripts/acceptance and scripts/ci, root module files, and root JSON schemas matches the exact qualification Git blobs; LF/CRLF spelling is accepted. The native production-source map is separately checked against SOURCE_REVISION by the native packet auditor.",
              "project_credits": 0}
    immutable_or_match(output_path, result)
    return result


def compare_packet_zip(packet, zip_path):
    with zipfile.ZipFile(zip_path) as archive:
        infos = archive.infolist()
        require(len(infos) == 70 and archive.testzip() is None,
                "provider packet ZIP member count or CRC differs")
        seen = set()
        expanded = 0
        for info in infos:
            name = info.filename
            path = PurePosixPath(name)
            require(not path.is_absolute() and ".." not in path.parts and "\\" not in name and
                    not info.flag_bits & 1 and info.file_size <= 16 * 1024**2 and name not in seen,
                    "unsafe, duplicate, encrypted or oversized host packet member")
            seen.add(name)
            expanded += info.file_size
            require(expanded <= 32 * 1024**2, "host packet expanded-size bound")
            if info.is_dir():
                continue
            local = (packet / Path(*path.parts)).resolve(strict=True)
            local.relative_to(packet.resolve(strict=True))
            data = archive.read(info)
            require(local.is_file() and not local.is_symlink() and local.stat().st_size == len(data) and
                    local.read_bytes() == data, "extracted host packet differs from exact provider ZIP member")
        local_names = {p.relative_to(packet).as_posix() for p in packet.rglob("*") if p.is_file()}
        require(local_names == {name for name in seen if not name.endswith("/")},
                "extracted host packet has missing or extra files")
        return {"zip_entries": len(infos), "expanded_bytes": expanded,
                "zip_sha256": sha256(zip_path), "zip_bytes": zip_path.stat().st_size}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--packet-root", type=Path, required=True)
    parser.add_argument("--zip-root", type=Path, required=True)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    declaration_path = DOC / "replacement-candidate-declaration-native-exit-v3.json"
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    require(manifest.get("run_id") == RUN and manifest.get("run_status") == "completed" and
            manifest.get("run_conclusion") == "success" and
            manifest.get("workflow_revision") == QUALIFICATION_REVISION and
            declaration.get("production_source_revision") == SOURCE_REVISION and
            declaration.get("version") == VERSION and declaration.get("series") == SERIES,
            "provider run/declaration identity differs from frozen rc.8 qualification")
    provider = {"headSha": manifest["workflow_revision"], "status": manifest["run_status"],
                "conclusion": manifest["run_conclusion"], "jobs": manifest["jobs"]}
    artifacts = {row["host"]: row for row in manifest["artifacts"]}
    require(set(artifacts) == {"linux", "darwin", "windows"} and len(artifacts) == 3,
            "provider artifact manifest is not the three-host native matrix")
    archive_root = RAW / "replacement-archives" / SERIES
    archive_root.mkdir(parents=True, exist_ok=True)
    cells = []
    source_maps = {}
    for host in ("linux", "darwin", "windows"):
        packet = args.packet_root / HOST_LABEL[host]
        artifact = artifacts[host]
        zip_path = args.zip_root / artifact["local_filename"]
        raw_hash = sha256(zip_path)
        require(zip_path.stat().st_size == artifact["size_in_bytes"] and
                "sha256:" + raw_hash == artifact["digest"] and not artifact["expired"],
                "downloaded provider ZIP does not match size/digest/expiry metadata")
        extraction = compare_packet_zip(packet, zip_path)
        job_rows = [row for row in manifest["jobs"] if HOST_RUNNER[host] in row["name"]]
        require(len(job_rows) == 1 and job_rows[0]["conclusion"] == "success" and
                job_rows[0]["status"] == "completed", "native provider job is not uniquely successful")
        receipt, built_archive = audit(packet, provider, host, QUALIFICATION_REVISION,
                                      SOURCE_REVISION, RUN, SERIES, VERSION)
        destination = archive_root / built_archive.name
        if not destination.exists():
            with destination.open("xb") as stream:
                stream.write(built_archive.read_bytes())
        require(sha256(destination) == receipt["archive_sha256"], "preserved exact archive digest differs")
        receipt.update({"archive_local_only": destination.relative_to(ROOT).as_posix(),
                        "provider_artifact_id": artifact["id"],
                        "provider_artifact_name": artifact["provider_name"],
                        "provider_artifact_sha256": artifact["digest"],
                        "provider_artifact_bytes": artifact["size_in_bytes"],
                        "provider_packet_readback": extraction,
                        "provider_job_id": job_rows[0]["databaseId"],
                        "candidate_declaration": declaration_path.relative_to(ROOT).as_posix(),
                        "candidate_declaration_sha256": sha256(declaration_path)})
        audit_path = DOC / f"replacement-native-{SERIES}-{host}-{RUN}.json"
        immutable_or_match(audit_path, receipt)
        readback_path = DOC / f"replacement-source-readback-{SERIES}-{host}-{RUN}.json"
        readback = source_readback(packet, host,
                                   dict(job_rows[0], artifact_name=artifact["provider_name"]),
                                   readback_path)
        candidate_path = packet / "replacement-candidate" / SERIES / (
            host + ("-arm64" if host == "darwin" else "-amd64")) / "candidate.json"
        candidate = json.loads(candidate_path.read_text(encoding="utf-8"))
        source_maps[host] = candidate["source_inputs"]
        cells.append(dict(receipt, audit=audit_path.relative_to(ROOT).as_posix(),
                          audit_sha256=sha256(audit_path),
                          qualification_source_readback=readback_path.relative_to(ROOT).as_posix(),
                          qualification_source_readback_sha256=sha256(readback_path)))
    require(set(source_maps["linux"]) == set(source_maps["darwin"]) == set(source_maps["windows"]),
            "native hosts did not select the same production source input paths")
    canonical_inputs = {}
    for name in sorted(source_maps["linux"]):
        git_blob = subprocess.check_output(["git", "show", f"{SOURCE_REVISION}:{name}"],
                                           cwd=ROOT, timeout=30)
        normalized = git_blob.replace(b"\r\n", b"\n")
        canonical = hashlib.sha256(normalized).hexdigest()
        require(all(source_maps[host][name] in hashes(git_blob)
                    for host in ("linux", "darwin", "windows")),
                "native source input differs from its pinned Git blob: " + name)
        canonical_inputs[name] = canonical
    freeze = {"schema_version": 1, "series": SERIES, "version": VERSION,
              "source_revision": SOURCE_REVISION, "qualification_revision": QUALIFICATION_REVISION,
              "candidate_declaration": declaration_path.relative_to(ROOT).as_posix(),
              "candidate_declaration_sha256": sha256(declaration_path),
              "provider_manifest": args.manifest.resolve(strict=True).relative_to(ROOT).as_posix(),
              "provider_manifest_sha256": sha256(args.manifest),
              "source_input_map_sha256": hashlib.sha256(json.dumps(canonical_inputs, sort_keys=True,
                  ensure_ascii=True, separators=(",", ":")).encode()).hexdigest(),
              "cells": cells, "project_credits": 0, "publication": False,
              "qualification": "Three native Linux amd64, macOS arm64 and Windows amd64 source/test/vet/race and single-build private archive packets independently passed provider digest, complete command identity, source-input, package member, checksum-sidecar, extracted executable, version and help audits. This freeze transfers no project/scenario/fault admission from earlier candidate bytes.",
              "requalification_required": declaration["requalification_required"]}
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v3.json"
    immutable_or_match(freeze_path, freeze)
    print(json.dumps({"status": "three-host rc.8 candidate independently audited and frozen",
                      "freeze": freeze_path.relative_to(ROOT).as_posix(),
                      "hosts": len(cells), "project_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
