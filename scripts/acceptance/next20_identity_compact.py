"""Losslessly compact/read back the campaign identity JSON corpus."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import tarfile

from next20_check import RAW
from readiness_evidence import immutable_json, sha256


ROOT = RAW / "identities"
PACKET = ROOT / "retained-identities-v1"
ARCHIVE = PACKET / "payload.tar.xz"
INDEX = PACKET / "index.json"
MAX_FILES = 6000
MAX_EXPANDED = 300 * 1024**2


def safe_name(name: str) -> str:
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or "\\" in name or ":" in name or
            any(part in {"", ".", ".."} for part in path.parts)):
        raise ValueError(f"unsafe identity archive member: {name!r}")
    return name


def verify() -> dict:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    if (index.get("schema_version") != 1 or index.get("format") != "tar.xz" or
            index.get("archive_sha256") != sha256(ARCHIVE)):
        raise ValueError("identity packet index/archive identity differs")
    entries = index.get("files")
    if not isinstance(entries, dict) or not 0 < len(entries) <= MAX_FILES:
        raise ValueError("identity packet member count outside bound")
    if index.get("expanded_bytes", MAX_EXPANDED + 1) > MAX_EXPANDED:
        raise ValueError("identity packet expansion exceeds bound")
    observed = {}
    total = 0
    with tarfile.open(ARCHIVE, "r:xz") as archive:
        for member in archive:
            name = safe_name(member.name)
            if (not member.isfile() or name in observed or name not in entries or
                    member.size > MAX_EXPANDED):
                raise ValueError("identity packet member coverage/type/size differs")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("identity packet member is unreadable")
            digest = hashlib.sha256()
            size = 0
            while block := stream.read(1024 * 1024):
                size += len(block)
                total += len(block)
                if total > MAX_EXPANDED:
                    raise ValueError("identity packet expansion exceeds bound")
                digest.update(block)
            row = {"bytes": size, "sha256": digest.hexdigest()}
            if row != entries[name]:
                raise ValueError(f"identity packet member hash/size differs: {name}")
            observed[name] = row
    if observed != entries or total != index["expanded_bytes"]:
        raise ValueError("identity packet is incomplete or total differs")
    return index


def compact() -> None:
    recovering = PACKET.exists()
    if recovering:
        existing = list(PACKET.iterdir())
        if existing != [ARCHIVE] or not ARCHIVE.is_file() or ARCHIVE.is_symlink():
            raise ValueError("preserve prior identity packet attempt")
        immutable_json(PACKET / "interrupted-attempt.json", {
            "schema_version": 1,
            "archive_sha256": sha256(ARCHIVE),
            "index_present": False,
            "disposition": "Initial process produced a complete tar stream but ended before writing its index. Originals remain intact; recovery rebinds every archived member to current original bytes.",
        })
    files = {}
    total = 0
    for path in sorted(ROOT.rglob("*.json")):
        if PACKET in path.parents:
            continue
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("linked identity evidence path")
        name = path.relative_to(ROOT).as_posix()
        safe_name(name)
        size = path.stat().st_size
        total += size
        if len(files) >= MAX_FILES or total > MAX_EXPANDED:
            raise ValueError("identity evidence inventory exceeds declared bound")
        files[name] = {"bytes": size, "sha256": sha256(path)}
    if not files:
        raise ValueError("no identity records to compact")
    if not recovering:
        PACKET.mkdir()
        with tarfile.open(ARCHIVE, "w:xz", preset=6) as archive:
            for name, row in files.items():
                path = ROOT / Path(*PurePosixPath(name).parts)
                if sha256(path) != row["sha256"]:
                    raise ValueError("identity changed while compacting")
                info = tarfile.TarInfo(name)
                info.size = row["bytes"]
                info.mode = 0o644
                with path.open("rb") as stream:
                    archive.addfile(info, stream)
    immutable_json(INDEX, {
        "schema_version": 1,
        "format": "tar.xz",
        "files": files,
        "expanded_bytes": total,
        "archive_sha256": sha256(ARCHIVE),
        "scope": "Exact lossless packet of expanded campaign identity JSON records. No source, scenario, or admission credit.",
    })
    index = verify()
    immutable_json(PACKET / "prepared.json", {
        "schema_version": 1,
        "index_sha256": sha256(INDEX),
        "archive_sha256": sha256(ARCHIVE),
        "verified_members": len(index["files"]),
        "verified_expanded_bytes": index["expanded_bytes"],
        "expanded_removal_confirmed": False,
    })
    print("Verified identity packet:", len(files), "records,", total,
          "expanded bytes ->", ARCHIVE.stat().st_size,
          "archive bytes; expanded removal remains pending")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("compact", "readback", "remove-plan", "finalize-removal"))
    args = parser.parse_args()
    if ROOT.is_symlink() or getattr(ROOT, "is_junction", lambda: False)():
        raise ValueError("identity root is linked")
    if args.mode == "compact":
        compact()
    elif args.mode == "remove-plan":
        index = verify()
        candidates = []
        for name, row in index["files"].items():
            path = ROOT / Path(*PurePosixPath(safe_name(name)).parts)
            if not path.is_file() or path.is_symlink() or sha256(path) != row["sha256"]:
                raise ValueError(f"original identity bytes differ before removal: {name}")
            candidates.append({"path": name, **row})
        observed = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*.json")
                          if PACKET not in p.parents)
        if observed != sorted(index["files"]):
            raise ValueError("expanded identities include unindexed JSON files")
        immutable_json(PACKET / "removal-plan.json", {
            "schema_version": 1,
            "index_sha256": sha256(INDEX),
            "archive_sha256": sha256(ARCHIVE),
            "files": candidates,
            "scope": "Native checked deletion candidates after complete indexed packet readback and original byte/hash comparison.",
        })
        print("Removal plan verified:", len(candidates), "files;", index["expanded_bytes"], "bytes")
    elif args.mode == "finalize-removal":
        index = verify()
        plan = json.loads((PACKET / "removal-plan.json").read_text(encoding="utf-8"))
        if plan.get("index_sha256") != sha256(INDEX) or plan.get("archive_sha256") != sha256(ARCHIVE):
            raise ValueError("identity removal plan no longer matches packet")
        present = [name for name in index["files"] if
                   (ROOT / Path(*PurePosixPath(name).parts)).exists()]
        if present:
            raise ValueError(f"expanded identity files remain: {len(present)}")
        immutable_json(PACKET / "removal-receipt.json", {
            "schema_version": 1,
            "index_sha256": sha256(INDEX),
            "archive_sha256": sha256(ARCHIVE),
            "removed_files": len(index["files"]),
            "removed_expanded_bytes": index["expanded_bytes"],
            "expanded_absence_verified": True,
        })
        print("Verified native checked removal:", len(index["files"]), "files; packet readback passes")
    else:
        index = verify()
        print("Verified exact identity packet:", len(index["files"]),
              "records,", index["expanded_bytes"], "expanded bytes")


if __name__ == "__main__":
    main()
