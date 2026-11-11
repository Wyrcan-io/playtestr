"""Verify and materialize JOE's hosted source-only acquisition without running hooks."""
import hashlib
import json
from pathlib import Path
import tarfile

from next20_check import RAW, ROOT
from readiness_acquire_plop import extract_source
from readiness_evidence import immutable_json, sha256

PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
RUN = "43002605616"
ARTIFACT_ID = 13846562710
ARTIFACT_SHA256 = "2729b84ef892a233438da3b309fefa951b3e4cc81658692ef46bd854940ced11"
ARTIFACT_BYTES = 3773903
PACKET = RAW / "joe/source-provider-run-43002605616/artifacts/runner-readiness-next-twenty-project-pass/active/joe"
ACTIVE = RAW / "active"
TARGET = ACTIVE / "joe"


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    acquisition = json.loads((PACKET / "acquisition.json").read_text(encoding="utf-8"))
    source_archive = PACKET / "source.tar.gz"
    archive_hash = sha256(source_archive)
    require(acquisition["repository"] == "joe-editor/joe" and acquisition["pin"] == PIN and
            acquisition["url"].endswith("/tarball/" + PIN) and
            acquisition["archive_sha256"] == archive_hash and
            acquisition["compressed_bytes"] == source_archive.stat().st_size and
            acquisition["entries"] == 388 and acquisition["expanded_bytes"] == 20544969 and
            acquisition["build_hooks_executed"] is False,
            "hosted JOE acquisition record or source archive digest differs")
    with tarfile.open(source_archive, "r:gz") as archive:
        members = archive.getmembers()
        require(len(members) == acquisition["entries"] + 1 and
                all(member.isfile() or member.isdir() for member in members),
                "pinned source tar contains unsupported special entries")
    require(not TARGET.exists(), "active JOE source tree already exists")
    require(not ACTIVE.exists() or not any(ACTIVE.iterdir()), "another selected target is active")
    ACTIVE.mkdir(parents=True, exist_ok=True)
    TARGET.mkdir()
    (TARGET / "source.tar.gz").write_bytes(source_archive.read_bytes())
    (TARGET / "acquisition.json").write_bytes((PACKET / "acquisition.json").read_bytes())
    immutable_json(TARGET / "task-owned.json", {
        "workspace": str(ROOT), "campaign": "runner-readiness-next-twenty-project-pass",
        "project": "joe-editor/joe", "slug": "joe", "pin": PIN, "source_only": True,
        "provider_run": RUN, "provider_artifact_id": ARTIFACT_ID,
        "source_archive_sha256": archive_hash,
    })
    count, size = extract_source(source_archive.read_bytes(), TARGET / "src",
                                 expanded_limit=64 * 1024**2, entry_limit=10000, member_limit=8 * 1024**2)
    actual = {path.relative_to(TARGET / "src").as_posix(): sha256(path)
              for path in sorted((TARGET / "src").rglob("*")) if path.is_file()}
    expected = acquisition["source_files"]
    require(count == acquisition["entries"] and size == acquisition["expanded_bytes"] and actual == expected,
            "actual extracted JOE source map differs from provider acquisition receipt")
    receipt = {
        "schema_version": 1, "project": "joe", "repository": "joe-editor/joe", "pin": PIN,
        "provider_run": RUN, "provider_artifact_id": ARTIFACT_ID,
        "provider_artifact_name": "next20-joe-source-" + RUN,
        "provider_artifact_sha256": ARTIFACT_SHA256, "provider_artifact_bytes": ARTIFACT_BYTES,
        "source_archive_sha256": archive_hash, "source_archive_bytes": source_archive.stat().st_size,
        "source_file_count": count, "expanded_bytes": size,
        "source_map_sha256": hashlib.sha256(json.dumps(actual, sort_keys=True,
            ensure_ascii=True, separators=(",", ":")).encode()).hexdigest(),
        "source_tree": "artifacts/runner-readiness-next-twenty-project-pass/active/joe/src",
        "build_hooks_executed": False, "project_admission_credit": 0,
        "scope": "Provider-returned source packet digest and embedded archive identity checked; source safely extracted and each file hash matched the hosted acquisition map. No configure, build, test, install or target execution occurred.",
    }
    immutable_json(ROOT / "docs/validation/runner-readiness-next-twenty-project-pass/joe/source-acquisition-v1.json", receipt)
    print("Verified JOE pinned source-only packet:", count, "files,", size, "expanded bytes; no build hooks ran.")


if __name__ == "__main__":
    main()
