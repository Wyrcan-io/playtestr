"""Losslessly retain exact duplicate control-test files as one indexed payload."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import tarfile

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


SOURCE = RAW / "control-tests"
STAGE = ROOT / ".runner-readiness-compaction-tmp" / "control-duplicates-v1"
FINAL = RAW / "duplicate-control-tests-v1"
MAX_FILES = 10_000
MAX_EXPANDED = 96 * 1024**2


def safe_path(name: str) -> Path:
    relative = PurePosixPath(name)
    if (not name.startswith("control-tests/") or relative.is_absolute() or "\\" in name or
            ":" in name or any(part in {"", ".", ".."} for part in relative.parts)):
        raise ValueError(f"unsafe control evidence path: {name!r}")
    return RAW.joinpath(*relative.parts)


def readback(root: Path, *, require_removed: bool = False) -> dict:
    index_path = root / "index.json"
    archive_path = root / "payload.tar.xz"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    groups = index.get("groups")
    if (index.get("schema_version") != 1 or index.get("archive_sha256") != sha256(archive_path) or
            not isinstance(groups, list) or not groups):
        raise ValueError("control duplicate packet identity/schema differs")
    expected = {}
    aliases = set()
    expanded = 0
    for group in groups:
        digest, size, paths = group.get("sha256"), group.get("bytes"), group.get("paths")
        if (not isinstance(digest, str) or len(digest) != 64 or not isinstance(size, int) or size <= 0 or
                not isinstance(paths, list) or len(paths) < 2 or digest in expected):
            raise ValueError("control duplicate group schema differs")
        expected[digest] = group
        for row in paths:
            name = row.get("path")
            if not isinstance(name, str):
                raise ValueError("control duplicate alias path is not text")
            safe_path(name)
            if (name in aliases or row.get("sha256") != digest or row.get("bytes") != size or
                    not isinstance(row.get("mode"), int) or not isinstance(row.get("mtime_ns"), int)):
                raise ValueError("control duplicate alias identity differs")
            aliases.add(name)
            expanded += size
    if len(aliases) > MAX_FILES or expanded != index.get("expanded_alias_bytes") or expanded > MAX_EXPANDED:
        raise ValueError("control duplicate inventory exceeds its frozen bounds")
    observed = {}
    with tarfile.open(archive_path, "r:xz") as archive:
        for member in archive:
            name = member.name
            group = expected.get(name[6:]) if name.startswith("blobs/") else None
            if (not member.isfile() or group is None or name[6:] in observed or
                    member.size != group["bytes"]):
                raise ValueError("control duplicate archive coverage/type differs")
            if (member.mode != group["paths"][0]["mode"] or
                    int(member.mtime) != group["paths"][0]["mtime_ns"] // 1_000_000_000):
                raise ValueError("control duplicate canonical payload metadata differs")
            stream = archive.extractfile(member)
            digest = hashlib.sha256()
            count = 0
            while block := stream.read(1024 * 1024):
                count += len(block)
                digest.update(block)
            if count != member.size or digest.hexdigest() != name[6:]:
                raise ValueError("control duplicate payload hash/size differs")
            observed[name[6:]] = count
    if observed != {digest: group["bytes"] for digest, group in expected.items()}:
        raise ValueError("control duplicate archive omitted or added payloads")
    for group in groups:
        for row in group["paths"]:
            name = row["path"]
            path = safe_path(name)
            if require_removed:
                if path.exists():
                    raise ValueError(f"compacted control alias reappeared: {name}")
            elif (not path.is_file() or path.is_symlink() or path.stat().st_size != row["bytes"] or
                  sha256(path) != row["sha256"] or stat.S_IMODE(path.stat().st_mode) != row["mode"] or
                  path.stat().st_mtime_ns != row["mtime_ns"]):
                raise ValueError(f"control alias source differs: {name}")
    return index


def prepare() -> None:
    if STAGE.exists() or FINAL.exists():
        raise ValueError("preserve existing control duplicate compaction attempt")
    by_size = {}
    file_count = 0
    entries = 0
    pending = [SOURCE]
    while pending:
        directory = pending.pop()
        if directory.is_symlink() or getattr(directory, "is_junction", lambda: False)():
            raise ValueError("linked control-test directory")
        with os.scandir(directory) as children:
            for entry in children:
                entries += 1
                if entries > 20_000:
                    raise ValueError("control-test directory entry bound")
                path = Path(entry.path)
                info = entry.stat(follow_symlinks=False)
                linked = (stat.S_ISLNK(info.st_mode) or getattr(info, "st_reparse_tag", 0) ==
                          getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003))
                if linked:
                    raise ValueError(f"linked control-test evidence path: {path.relative_to(RAW)}")
                if stat.S_ISDIR(info.st_mode):
                    pending.append(path)
                elif stat.S_ISREG(info.st_mode):
                    file_count += 1
                    if file_count > MAX_FILES:
                        raise ValueError("control-test file count bound")
                    if info.st_size:
                        by_size.setdefault(info.st_size, []).append(path)
                else:
                    raise ValueError(f"special control-test entry: {path.relative_to(RAW)}")
    groups = {}
    for paths in (values for values in by_size.values() if len(values) > 1):
        for path in paths:
            digest = sha256(path)
            groups.setdefault((digest, path.stat().st_size), []).append(path)
    duplicates = [(digest, size, paths) for (digest, size), paths in groups.items() if len(paths) > 1]
    duplicates.sort(key=lambda item: item[0])
    if not duplicates:
        raise ValueError("no exact duplicate control evidence found")
    rows = []
    expanded = 0
    unique_bytes = 0
    payloads = {}
    for digest, size, paths in duplicates:
        paths.sort(key=lambda path: path.relative_to(RAW).as_posix())
        path_rows = []
        for path in paths:
            name = path.relative_to(RAW).as_posix()
            row = {"path": name, "sha256": digest, "bytes": size,
                   "mode": stat.S_IMODE(path.stat().st_mode), "mtime_ns": path.stat().st_mtime_ns}
            path_rows.append(row)
            expanded += size
        rows.append({"sha256": digest, "bytes": size, "paths": path_rows})
        unique_bytes += size
        payloads[digest] = (paths[0], size)
    aliases = sum(len(group["paths"]) for group in rows)
    if aliases > MAX_FILES or expanded > MAX_EXPANDED:
        raise ValueError("control duplicate packet exceeds frozen bounds")
    STAGE.mkdir(parents=True)
    archive_path = STAGE / "payload.tar.xz"
    with tarfile.open(archive_path, "w:xz", preset=6) as archive:
        for digest, (path, size) in payloads.items():
            if path.stat().st_size != size or sha256(path) != digest:
                raise ValueError("control source changed during packet creation")
            info = tarfile.TarInfo(f"blobs/{digest}")
            info.size = size
            info.mode = stat.S_IMODE(path.stat().st_mode)
            info.mtime = path.stat().st_mtime
            with path.open("rb") as stream:
                archive.addfile(info, stream)
    immutable_json(STAGE / "index.json", {
        "schema_version": 1,
        "scope": "Only exact byte-identical files under control-tests are compacted. Each source path, SHA-256, byte count, mode and nanosecond modification time remains explicit; one directly addressed blob per content hash is retained.",
        "groups": rows,
        "duplicate_group_count": len(rows),
        "alias_path_count": aliases,
        "expanded_alias_bytes": expanded,
        "unique_payload_bytes": unique_bytes,
        "archive_sha256": sha256(archive_path),
    })
    index = readback(STAGE)
    immutable_json(STAGE / "prepared.json", {
        "schema_version": 1,
        "index_sha256": sha256(STAGE / "index.json"),
        "archive_sha256": sha256(archive_path),
        "groups": len(index["groups"]),
        "alias_paths": index["alias_path_count"],
        "expanded_alias_bytes": expanded,
        "unique_payload_bytes": unique_bytes,
        "payload_readback_passed": True,
        "source_removal_confirmed": False,
        "compactor_sha256": sha256(__file__),
    })
    print("Prepared control duplicate packet:", len(rows), "groups,", aliases,
          "paths;", expanded, "source bytes ->", archive_path.stat().st_size,
          "archive bytes plus index; removal pending")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "removal-plan", "finalize"))
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    root = STAGE if args.mode == "prepare" or args.staged else FINAL
    if args.mode == "prepare":
        prepare()
    elif args.mode == "removal-plan":
        index = readback(root)
        prepared = json.loads((root / "prepared.json").read_text(encoding="utf-8"))
        if (prepared.get("index_sha256") != sha256(root / "index.json") or
                prepared.get("archive_sha256") != sha256(root / "payload.tar.xz") or
                prepared.get("compactor_sha256") != sha256(__file__)):
            raise ValueError("prepared control duplicate packet identity differs")
        removal_helper = ROOT / "scripts/acceptance/next20_control_duplicate_remove.ps1"
        if not removal_helper.is_file():
            raise ValueError("native removal helper is missing")
        immutable_json(root / "removal-plan.json", {
            "schema_version": 1,
            "index_sha256": sha256(root / "index.json"),
            "archive_sha256": sha256(root / "payload.tar.xz"),
            "prepared_sha256": sha256(root / "prepared.json"),
            "compactor_sha256": sha256(__file__),
            "removal_helper_sha256": sha256(removal_helper),
            "alias_path_count": index["alias_path_count"],
            "expanded_alias_bytes": index["expanded_alias_bytes"],
            "removal_helper": removal_helper.relative_to(ROOT).as_posix(),
            "scope": "All duplicate source aliases rehashed against the fully read-back unique payload archive; deletion must use the separately reviewed native PowerShell helper.",
        })
        print("Verified removal plan:", index["alias_path_count"], "paths,",
              index["expanded_alias_bytes"], "bytes")
    else:
        index = readback(root, require_removed=True)
        plan = json.loads((root / "removal-plan.json").read_text(encoding="utf-8"))
        if plan.get("index_sha256") != sha256(root / "index.json"):
            raise ValueError("control duplicate removal plan differs from final index")
        immutable_json(root / "removal-receipt.json", {
            "schema_version": 1,
            "index_sha256": sha256(root / "index.json"),
            "archive_sha256": sha256(root / "payload.tar.xz"),
            "removal_plan_sha256": sha256(root / "removal-plan.json"),
            "alias_path_count": index["alias_path_count"],
            "expanded_alias_bytes": index["expanded_alias_bytes"],
            "all_source_aliases_absent": True,
            "all_unique_payloads_readback": True,
        })
        print("Verified compacted control packet:", len(index["groups"]), "groups,",
              index["alias_path_count"], "original paths")


if __name__ == "__main__":
    main()
