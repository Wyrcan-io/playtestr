"""Index, compress, and selectively restore expanded campaign text evidence."""
import argparse
import hashlib
import json
import lzma
from pathlib import Path, PurePosixPath
import os
import stat
import tarfile

from next20_check import RAW


PACKET = RAW / "text-evidence-v1"
STAGE = RAW / "text-evidence-v1-stage"
EXCLUDED = {"active", "toolchain", "go-cache", "gopath", "gh-cache", "tmp",
            "retained", "duplicate-evidence-v1", "duplicate-evidence-v2",
            PACKET.name, STAGE.name}
SUFFIXES = {".json", ".jsonc", ".go", ".feature", ".md", ".markdown", ".s",
            ".log", ".svg", ".out", ".sh", ".yml", ".yaml", ".txt", ".ts",
            ".sample", ".sum", ".rev", ".work", ".wxs", ".bash", ".toml",
            ".ps1", ".jq", ".mod", ".nuspec", ".hbs", ".conf", ".razor", ".c",
            ".lock"}
MAX_FILES = 50000
MAX_BYTES = 512 * 1024**2
MAX_MEMBER = 32 * 1024**2


def safe_name(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or "\\" in name or ":" in name or
            any(part in {"", ".", ".."} for part in path.parts) or path.parts[0] in EXCLUDED):
        raise ValueError(f"unsafe text evidence path: {name!r}")
    return name


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        while block := stream.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def index_data(root):
    raw = lzma.decompress((root / "index.json.xz").read_bytes())
    return raw, json.loads(raw.decode("utf-8"))


def verify(root, restore=None):
    raw_index, index = index_data(root)
    archive = root / "payload.tar.xz"
    index_identity = dict(index)
    recorded_index_sha = index_identity.pop("index_sha256", None)
    canonical_index = (json.dumps(index_identity, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode()
    if (index.get("schema_version") != 1 or recorded_index_sha != hashlib.sha256(canonical_index).hexdigest() or
            index.get("archive_sha256") != sha(archive) or not isinstance(index.get("files"), dict)):
        raise ValueError("text evidence packet/index identity differs")
    entries = index["files"]
    if len(entries) > MAX_FILES or index.get("expanded_bytes", MAX_BYTES + 1) > MAX_BYTES:
        raise ValueError("text evidence packet exceeds declared bounds")
    wanted = {safe_name(name): row for name, row in entries.items()}
    observed = set()
    expanded = 0
    with tarfile.open(archive, "r:xz") as tar:
        for member in tar:
            name = safe_name(member.name)
            if not member.isfile() or name not in wanted or name in observed:
                raise ValueError("unexpected text evidence packet member")
            row = wanted[name]
            if member.size != row["bytes"]:
                raise ValueError("text evidence member length differs")
            digest = hashlib.sha256()
            size = 0
            selected = restore is not None and name == restore
            destination = None
            if selected:
                destination = root / "selected-restore" / Path(*PurePosixPath(name).parts)
                destination.parent.mkdir(parents=True, exist_ok=False)
                output = destination.open("xb")
            else:
                output = None
            source = tar.extractfile(member)
            try:
                while block := source.read(1024 * 1024):
                    digest.update(block)
                    size += len(block)
                    expanded += len(block)
                    if expanded > MAX_BYTES:
                        raise ValueError("text evidence expansion exceeds bound")
                    if output is not None:
                        output.write(block)
            finally:
                if output is not None:
                    output.close()
            if size != row["bytes"] or digest.hexdigest() != row["sha256"]:
                raise ValueError(f"text evidence content identity differs: {name}")
            observed.add(name)
            if selected:
                destination.chmod(row["mode"] & 0o777)
                os.utime(destination, ns=(row["mtime_ns"], row["mtime_ns"]))
                st = destination.stat()
                if (sha(destination) != row["sha256"] or st.st_size != row["bytes"] or
                        stat.S_IMODE(st.st_mode) != row["mode"] or st.st_mtime_ns != row["mtime_ns"]):
                    raise ValueError("selected text restoration metadata differs")
    if observed != set(wanted) or expanded != index["expanded_bytes"]:
        raise ValueError("text evidence packet has incomplete path coverage")
    return index


def prepare():
    if STAGE.exists() or PACKET.exists():
        raise ValueError("preserve existing text evidence compaction attempt")
    files = {}
    total = 0
    entries = 0
    pending = [RAW]
    while pending:
        directory = pending.pop()
        with os.scandir(directory) as children:
            for item in children:
                rel = Path(item.path).relative_to(RAW)
                if len(rel.parts) == 1 and rel.parts[0] in EXCLUDED:
                    continue
                info = item.stat(follow_symlinks=False)
                linked = stat.S_ISLNK(info.st_mode) or getattr(info, "st_reparse_tag", 0) == getattr(
                    stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)
                if linked:
                    raise ValueError(f"linked campaign evidence path: {rel}")
                if stat.S_ISDIR(info.st_mode):
                    pending.append(Path(item.path))
                elif stat.S_ISREG(info.st_mode) and Path(item.name).suffix.lower() in SUFFIXES:
                    if info.st_size > MAX_MEMBER:
                        raise ValueError(f"text evidence member exceeds size bound: {rel}")
                    name = safe_name(rel.as_posix())
                    files[name] = {"bytes": info.st_size, "sha256": sha(item.path),
                                   "mode": stat.S_IMODE(info.st_mode), "mtime_ns": info.st_mtime_ns}
                    total += info.st_size
                    if len(files) > MAX_FILES or total > MAX_BYTES:
                        raise ValueError("text evidence inventory exceeds declared bounds")
                elif not stat.S_ISREG(info.st_mode):
                    raise ValueError(f"special campaign evidence path: {rel}")
                entries += 1
                if entries > 500000:
                    raise ValueError("campaign text scan exceeds directory entry bound")
    if not files:
        raise ValueError("no expanded campaign text evidence found")
    STAGE.mkdir()
    archive = STAGE / "payload.tar.xz"
    with tarfile.open(archive, "w:xz", preset=3) as tar:
        for name, row in files.items():
            source = RAW / Path(*PurePosixPath(name).parts)
            if source.stat().st_size != row["bytes"] or sha(source) != row["sha256"]:
                raise ValueError(f"source changed during text packet creation: {name}")
            info = tarfile.TarInfo(name)
            info.size = row["bytes"]
            info.mode = row["mode"]
            info.mtime = source.stat().st_mtime
            with source.open("rb") as stream:
                tar.addfile(info, stream)
    index = {"schema_version": 1, "compression": "tar.xz preset 3",
             "files": files, "expanded_bytes": total,
             "archive_sha256": sha(archive),
             "scope": "Exact bytes, SHA-256, mode, and nanosecond mtime for expanded campaign text evidence; active roots, existing packets, and binary archives are excluded."}
    canonical = (json.dumps(index, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode()
    index["index_sha256"] = hashlib.sha256(canonical).hexdigest()
    encoded = (json.dumps(index, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode()
    (STAGE / "index.json.xz").write_bytes(lzma.compress(encoded, preset=6))
    (STAGE / "prepared.json").write_text(json.dumps({
        "schema_version": 1, "index_sha256": sha(STAGE / "index.json.xz"),
        "archive_sha256": sha(archive), "members": len(files), "expanded_bytes": total,
        "source_removal_confirmed": False}, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    checked = verify(STAGE)
    print(f"Prepared text packet: {len(checked['files'])} files, {total} bytes -> "
          f"{archive.stat().st_size + (STAGE/'index.json.xz').stat().st_size} bytes; removal pending")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "readback", "removal-plan", "removal-receipt"))
    parser.add_argument("--restore")
    args = parser.parse_args()
    root = STAGE if args.mode == "prepare" else PACKET
    if args.mode == "prepare":
        prepare()
    elif args.mode == "readback":
        index = verify(root, args.restore)
        print(f"Readback passed: {len(index['files'])} files, {index['expanded_bytes']} bytes")
    elif args.mode == "removal-plan":
        raw, index = index_data(root)
        prepared = json.loads((root / "prepared.json").read_text(encoding="utf-8"))
        if (prepared.get("archive_sha256") != sha(root / "payload.tar.xz") or
                prepared.get("index_sha256") != sha(root / "index.json.xz")):
            raise ValueError("prepared receipt does not bind text packet")
        verify(root)
        for name, row in index["files"].items():
            path = RAW / Path(*PurePosixPath(safe_name(name)).parts)
            if path.stat().st_size != row["bytes"] or sha(path) != row["sha256"]:
                raise ValueError(f"source differs before text removal: {name}")
        (root / "removal-plan.json").write_text(json.dumps({
            "schema_version": 1, "index_sha256": index["index_sha256"],
            "compressed_index_sha256": sha(root / "index.json.xz"),
            "archive_sha256": sha(root / "payload.tar.xz"),
            "members": len(index["files"]), "expanded_bytes": index["expanded_bytes"],
            "files": index["files"]},
            sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(f"Text evidence removal plan passed: {len(index['files'])} paths")
    else:
        _, index = index_data(root)
        plan = json.loads((root / "removal-plan.json").read_text(encoding="utf-8"))
        if (plan.get("index_sha256") != index["index_sha256"] or
                plan.get("compressed_index_sha256") != sha(root / "index.json.xz") or
                plan.get("archive_sha256") != sha(root / "payload.tar.xz") or
                plan.get("files") != index["files"]):
            raise ValueError("text removal plan does not bind current packet")
        verify(root)
        for name in index["files"]:
            path = RAW / Path(*PurePosixPath(safe_name(name)).parts)
            if path.exists():
                raise ValueError(f"text evidence source reappeared after removal: {name}")
        (root / "removal-receipt.json").write_text(json.dumps({
            "schema_version": 1, "index_sha256": index["index_sha256"],
            "archive_sha256": sha(root / "payload.tar.xz"),
            "removal_plan_sha256": sha(root / "removal-plan.json"),
            "members": len(index["files"]), "expanded_bytes": index["expanded_bytes"],
            "all_indexed_source_paths_absent": True, "packet_readback_passed": True},
            sort_keys=True, indent=2) + "\n", encoding="utf-8")
        print(f"Text evidence removal verified: {len(index['files'])} paths absent")


if __name__ == "__main__":
    main()
