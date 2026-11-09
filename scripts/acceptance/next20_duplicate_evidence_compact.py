"""Content-address duplicate campaign evidence with exact path metadata."""
import argparse
import hashlib
import json
import lzma
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile
import tempfile

from next20_check import RAW
from readiness_evidence import immutable_json, sha256


STAGE = Path(tempfile.gettempdir()) / "playtestr-next20-duplicate-evidence-v1"
FINAL = RAW / "duplicate-evidence-v1"
EXCLUDED = {"active", "toolchain", "go-cache", "gopath", "gh-cache", "tmp"}
MAX_FILES = 100_000
MAX_BYTES = 4 * 1024**3


def read_index(root: Path) -> dict:
    """Read the duplicate evidence index in JSON or compact XZ form."""
    packed = root / "index.json.xz"
    path = packed if packed.is_file() else root / "index.json"
    data = lzma.decompress(path.read_bytes()) if path == packed else path.read_bytes()
    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("duplicate evidence index must be an object")
    return value


def logical_index_sha256(root: Path) -> str:
    packed = root / "index.json.xz"
    data = lzma.decompress(packed.read_bytes()) if packed.is_file() else (root / "index.json").read_bytes()
    return hashlib.sha256(data).hexdigest()


def safe_name(value: str) -> str:
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or "\\" in value or ":" in value or
            any(part in {"", ".", ".."} for part in path.parts) or
            path.parts[0] in EXCLUDED):
        raise ValueError(f"unsafe duplicate evidence path: {value!r}")
    return value


def verify(root: Path) -> dict:
    archive_path = root / "payload.tar.xz"
    index = read_index(root)
    groups = index.get("groups")
    if (index.get("schema_version") != 1 or index.get("archive_sha256") != sha256(archive_path) or
            not isinstance(groups, list) or not groups):
        raise ValueError("duplicate evidence packet identity/schema differs")
    expected = {}
    seen_paths = set()
    source_bytes = 0
    for group in groups:
        digest = group.get("sha256")
        size = group.get("bytes")
        aliases = group.get("paths")
        if (not isinstance(digest, str) or len(digest) != 64 or
                not isinstance(size, int) or size < 0 or not isinstance(aliases, list) or len(aliases) < 2 or
                digest in expected):
            raise ValueError("duplicate evidence group schema differs")
        expected[digest] = size
        for row in aliases:
            name = safe_name(row["path"])
            if name in seen_paths or row["sha256"] != digest or row["bytes"] != size:
                raise ValueError("duplicate evidence alias path or identity differs")
            seen_paths.add(name)
            source_bytes += size
    if len(seen_paths) > MAX_FILES or source_bytes > MAX_BYTES:
        raise ValueError("duplicate evidence packet exceeds declared inventory bounds")
    observed = {}
    with tempfile.TemporaryDirectory(prefix="next20-duplicate-evidence-") as td:
        with tarfile.open(archive_path, "r:xz") as archive:
            for member in archive:
                name = member.name
                if (not member.isfile() or not name.startswith("blobs/") or
                        name[6:] not in expected or name[6:] in observed or
                        member.size != expected[name[6:]]):
                    raise ValueError("duplicate evidence archive coverage/type differs")
                stream = archive.extractfile(member)
                digest = hashlib.sha256()
                size = 0
                while block := stream.read(1024 * 1024):
                    digest.update(block)
                    size += len(block)
                if size != member.size or digest.hexdigest() != name[6:]:
                    raise ValueError("duplicate evidence blob hash/size differs")
                observed[name[6:]] = size
    if observed != expected:
        raise ValueError("duplicate evidence archive omitted/added blobs")
    return index


def prepare() -> None:
    if STAGE.exists() or FINAL.exists():
        raise ValueError("preserve existing duplicate evidence compaction attempt")
    by_size = {}
    file_count = 0
    entries_seen = 0
    pending = [RAW]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as children:
            for entry in children:
                entries_seen += 1
                if entries_seen > 500_000:
                    raise ValueError("campaign duplicate scan exceeds directory entry bound")
                relative = Path(entry.path).relative_to(RAW)
                if len(relative.parts) == 1 and relative.parts[0] in EXCLUDED | {FINAL.name}:
                    continue
                info = entry.stat(follow_symlinks=False)
                linked = (stat.S_ISLNK(info.st_mode) or getattr(info, "st_reparse_tag", 0) ==
                          getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003))
                if linked:
                    raise ValueError(f"linked campaign evidence path: {relative}")
                if stat.S_ISDIR(info.st_mode):
                    pending.append(Path(entry.path))
                elif stat.S_ISREG(info.st_mode) and info.st_size:
                    file_count += 1
                    if file_count > MAX_FILES * 4:
                        raise ValueError("campaign duplicate scan exceeds bounded file count")
                    by_size.setdefault(info.st_size, []).append(Path(entry.path))
                elif not stat.S_ISREG(info.st_mode):
                    raise ValueError(f"special campaign evidence path: {relative}")
    groups = {}
    candidates = [path for paths in by_size.values() if len(paths) > 1 for path in paths]
    if len(candidates) > MAX_FILES:
        raise ValueError("duplicate-size candidate inventory exceeds bound")
    for path in candidates:
        size = path.stat().st_size
        digest = sha256(path)
        groups.setdefault((digest, size), []).append(path)
    duplicates = [(digest, size, paths) for (digest, size), paths in groups.items() if len(paths) > 1]
    if not duplicates:
        raise ValueError("no exact duplicate campaign evidence found")
    duplicates.sort(key=lambda item: item[0])
    rows = []
    unique_bytes = 0
    expanded_bytes = 0
    blobs = {}
    for digest, size, paths in duplicates:
        paths.sort(key=lambda path: path.relative_to(RAW).as_posix())
        rows.append({
            "sha256": digest,
            "bytes": size,
            "paths": [{
                "path": path.relative_to(RAW).as_posix(),
                "sha256": digest,
                "bytes": size,
                "mode": stat.S_IMODE(path.stat().st_mode),
                "mtime_ns": path.stat().st_mtime_ns,
            } for path in paths],
        })
        unique_bytes += size
        expanded_bytes += size * len(paths)
        blobs[digest] = (paths[0], size)
    if len(rows) > MAX_FILES or expanded_bytes > MAX_BYTES:
        raise ValueError("duplicate campaign evidence exceeds declared bounds")
    STAGE.mkdir()
    archive_path = STAGE / "payload.tar.xz"
    with tarfile.open(archive_path, "w:xz", preset=6) as archive:
        for digest, (path, size) in blobs.items():
            observed = sha256(path)
            if path.stat().st_size != size or observed != digest:
                raise ValueError(f"duplicate source changed while staging: {path}; expected {digest}, observed {observed}")
            info = tarfile.TarInfo(f"blobs/{digest}")
            info.size = path.stat().st_size
            info.mode = stat.S_IMODE(path.stat().st_mode)
            info.mtime = path.stat().st_mtime
            with path.open("rb") as source:
                archive.addfile(info, source)
    immutable_json(STAGE / "index.json", {
        "schema_version": 1,
        "compression": "tar.xz preset 6; one blob per exact SHA-256; all original paths remain explicit aliases",
        "groups": rows,
        "duplicate_group_count": len(rows),
        "alias_path_count": sum(len(row["paths"]) for row in rows),
        "unique_payload_bytes": unique_bytes,
        "expanded_alias_bytes": expanded_bytes,
        "archive_sha256": sha256(archive_path),
        "scope": "Every exact duplicate non-cache campaign file is indexed with original path, byte count, SHA-256, mode and nanosecond mtime. One byte-identical payload per hash is retained; aliases do not chain.",
    })
    index = verify(STAGE)
    immutable_json(STAGE / "prepared.json", {
        "schema_version": 1,
        "index_sha256": sha256(STAGE / "index.json"),
        "archive_sha256": sha256(archive_path),
        "duplicate_group_count": len(index["groups"]),
        "alias_path_count": index["alias_path_count"],
        "all_unique_payloads_readback": True,
        "all_alias_identities_indexed": True,
        "source_removal_confirmed": False,
        "staging_path": str(STAGE),
    })
    print("Prepared exact duplicate evidence packet:", len(index["groups"]), "hash groups,",
          index["alias_path_count"], "paths;", expanded_bytes, "original bytes ->",
          unique_bytes, "unique bytes and", archive_path.stat().st_size,
          "archive bytes; removal pending")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "readback", "removal-plan"))
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    root = STAGE if args.mode == "prepare" or args.staged else FINAL
    if args.mode == "prepare":
        prepare()
    elif args.mode == "removal-plan":
        index = read_index(root)
        prepared = json.loads((root / "prepared.json").read_text(encoding="utf-8"))
        if (prepared.get("all_unique_payloads_readback") is not True or
                prepared.get("all_alias_identities_indexed") is not True or
                prepared.get("index_sha256") != logical_index_sha256(root) or
                prepared.get("archive_sha256") != sha256(root / "payload.tar.xz")):
            raise ValueError("complete duplicate evidence readback receipt does not bind packet")
        for group in index["groups"]:
            for row in group["paths"]:
                path = RAW / Path(*PurePosixPath(safe_name(row["path"])).parts)
                if (not path.is_file() or path.is_symlink() or path.stat().st_size != row["bytes"] or
                        sha256(path) != row["sha256"]):
                    raise ValueError(f"duplicate evidence source differs before removal: {row['path']}")
        immutable_json(root / "removal-plan.json", {
            "schema_version": 1,
            "index_sha256": logical_index_sha256(root),
            "archive_sha256": sha256(root / "payload.tar.xz"),
            "prepared_sha256": sha256(root / "prepared.json"),
            "alias_path_count": index["alias_path_count"],
            "expanded_alias_bytes": index["expanded_alias_bytes"],
            "scope": "All exact source aliases were rehashed against the fully read-back unique payload packet.",
        })
        print("Verified duplicate evidence removal plan:", index["alias_path_count"], "paths,",
              index["expanded_alias_bytes"], "bytes")
    else:
        index = verify(root)
        if not (root / "removal-plan.json").is_file():
            raise ValueError("duplicate evidence post-removal plan is absent")
        for group in index["groups"]:
            for row in group["paths"]:
                path = RAW / Path(*PurePosixPath(safe_name(row["path"])).parts)
                if path.exists():
                    raise ValueError(f"duplicate evidence alias source reappeared after removal: {row['path']}")
        immutable_json(root / "removal-receipt.json", {
            "schema_version": 1,
            "index_sha256": logical_index_sha256(root),
            "archive_sha256": sha256(root / "payload.tar.xz"),
            "removal_plan_sha256": sha256(root / "removal-plan.json"),
            "alias_path_count": index["alias_path_count"],
            "expanded_alias_bytes": index["expanded_alias_bytes"],
            "all_original_alias_paths_absent": True,
            "all_unique_payloads_readback": True,
        })
        print("Verified duplicate evidence packet:", len(index["groups"]), "groups,",
              index["alias_path_count"], "indexed paths")


if __name__ == "__main__":
    main()
