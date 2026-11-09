"""Losslessly index and compact expanded text evidence under retained/."""
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


ROOT = RAW / "retained"
STAGE = Path(tempfile.gettempdir()) / "playtestr-next20-retained-text-v1"
FINAL = ROOT / "retained-text-v1"
TEXT_SUFFIXES = {
    ".json", ".jsonc", ".go", ".feature", ".md", ".markdown", ".s",
    ".log", ".svg", ".out", ".sh", ".yml", ".yaml", ".txt", ".ts",
    ".sample", ".sum", ".rev", ".work", ".wxs", ".bash", ".toml",
    ".ps1", ".jq", ".mod", ".nuspec", ".hbs", ".conf", ".razor", ".c",
    ".lock",
}
MAX_FILES = 40000
MAX_EXPANDED = 512 * 1024**2
MAX_MEMBER = 32 * 1024**2


def read_index(root: Path) -> dict:
    """Read the retained text index from its JSON or compact XZ file."""
    packed = root / "index.json.xz"
    path = packed if packed.is_file() else root / "index.json"
    data = lzma.decompress(path.read_bytes()) if path == packed else path.read_bytes()
    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("retained text index must be an object")
    return value


def logical_index_sha256(root: Path) -> str:
    """Hash the original JSON bytes after decoding any storage compression."""
    packed = root / "index.json.xz"
    data = lzma.decompress(packed.read_bytes()) if packed.is_file() else (root / "index.json").read_bytes()
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> str:
    path = PurePosixPath(name)
    if (not name.startswith("retained/") or path.is_absolute() or "\\" in name or
            ":" in name or any(p in {"", ".", ".."} for p in path.parts)):
        raise ValueError(f"unsafe retained text member: {name!r}")
    return name


def verify(root: Path, *, reconstruct: bool) -> dict:
    index_path = root / "index.json.xz"
    if not index_path.is_file():
        index_path = root / "index.json"
    archive_path = root / "payload.tar.xz"
    index = read_index(root)
    entries = index.get("files")
    if (index.get("schema_version") != 1 or index.get("archive_sha256") != sha256(archive_path) or
            not isinstance(entries, dict) or not 0 < len(entries) <= MAX_FILES):
        raise ValueError("retained text packet identity/schema differs")
    if index.get("expanded_bytes", MAX_EXPANDED + 1) > MAX_EXPANDED:
        raise ValueError("retained text packet exceeds expansion bound")
    observed = {}
    total = 0
    with tempfile.TemporaryDirectory(prefix="next20-retained-text-") as td:
        restore_root = Path(td) if reconstruct else None
        with tarfile.open(archive_path, "r:xz") as archive:
            for member in archive:
                name = safe_name(member.name)
                if (not member.isfile() or name in observed or name not in entries or
                        member.size > MAX_MEMBER):
                    raise ValueError("retained text archive member type/coverage/size differs")
                source = archive.extractfile(member)
                digest = hashlib.sha256()
                size = 0
                restored = None
                if reconstruct:
                    relative = PurePosixPath(name).relative_to("retained")
                    restored = restore_root.joinpath(*relative.parts)
                    restored.parent.mkdir(parents=True, exist_ok=True)
                    output = restored.open("wb")
                else:
                    output = None
                try:
                    while block := source.read(1024 * 1024):
                        size += len(block)
                        total += len(block)
                        if total > MAX_EXPANDED:
                            raise ValueError("retained text packet expansion exceeds bound")
                        digest.update(block)
                        if output is not None:
                            output.write(block)
                finally:
                    if output is not None:
                        output.close()
                row = entries[name]
                if size != row["bytes"] or digest.hexdigest() != row["sha256"]:
                    raise ValueError(f"retained text member hash/size differs: {name}")
                if reconstruct:
                    os_mode = row.get("mode")
                    if isinstance(os_mode, int):
                        restored.chmod(os_mode & 0o777)
                    mtime_ns = row.get("mtime_ns")
                    if isinstance(mtime_ns, int):
                        os.utime(restored, ns=(mtime_ns, mtime_ns))
                    st = restored.stat()
                    if (stat.S_IMODE(st.st_mode) != row.get("mode") or
                            st.st_mtime_ns != row.get("mtime_ns")):
                        raise ValueError(f"retained text mode/mtime differs: {name}")
                observed[name] = {"bytes": size, "sha256": digest.hexdigest()}
    if set(observed) != set(entries) or total != index["expanded_bytes"]:
        raise ValueError("retained text packet omitted members or total differs")
    return index


def prepare() -> None:
    if STAGE.exists() or FINAL.exists():
        raise ValueError("preserve existing retained text compaction attempt")
    files = {}
    total = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if FINAL in path.parents:
            continue
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("linked retained text evidence path")
        name = path.relative_to(RAW).as_posix()
        safe_name(name)
        size = path.stat().st_size
        if size > MAX_MEMBER:
            raise ValueError("retained text member exceeds bound")
        total += size
        if len(files) >= MAX_FILES or total > MAX_EXPANDED:
            raise ValueError("retained text inventory exceeds declared bounds")
        mode = stat.S_IMODE(path.stat().st_mode)
        files[name] = {"bytes": size, "sha256": sha256(path), "mode": mode,
                       "mtime_ns": path.stat().st_mtime_ns}
    if not files:
        raise ValueError("no expanded retained text evidence found")
    STAGE.mkdir()
    archive_path = STAGE / "payload.tar.xz"
    with tarfile.open(archive_path, "w:xz", preset=3) as archive:
        for name, row in files.items():
            path = RAW / Path(*PurePosixPath(name).parts)
            if sha256(path) != row["sha256"] or path.stat().st_size != row["bytes"]:
                raise ValueError("retained text changed during packet creation")
            info = tarfile.TarInfo(name)
            info.size = row["bytes"]
            info.mode = row["mode"]
            info.mtime = path.stat().st_mtime
            with path.open("rb") as payload:
                archive.addfile(info, payload)
    immutable_json(STAGE / "index.json", {
        "schema_version": 1,
        "compression": "tar.xz",
        "files": files,
        "expanded_bytes": total,
        "archive_sha256": sha256(archive_path),
        "scope": "Exact path, byte, SHA-256, mode and modification-time inventory for expanded retained text evidence. Binary payloads and existing compact ZIP packets remain separate.",
    })
    index = verify(STAGE, reconstruct=True)
    immutable_json(STAGE / "prepared.json", {
        "schema_version": 1,
        "index_sha256": sha256(STAGE / "index.json"),
        "archive_sha256": sha256(archive_path),
        "members": len(index["files"]),
        "expanded_bytes": total,
        "all_paths_hashes_modes_and_times_readback": True,
        "source_removal_confirmed": False,
        "staging_path": str(STAGE),
    })
    print("Prepared exact retained text packet:", len(files), "files,", total,
          "expanded bytes ->", archive_path.stat().st_size, "bytes plus index; removal pending")


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
        if (prepared.get("all_paths_hashes_modes_and_times_readback") is not True or
                prepared.get("index_sha256") != logical_index_sha256(root) or
                prepared.get("archive_sha256") != sha256(root / "payload.tar.xz")):
            raise ValueError("complete retained text readback receipt does not bind packet")
        entries = index["files"]
        for name, row in entries.items():
            path = RAW / Path(*PurePosixPath(safe_name(name)).parts)
            if not path.is_file() or path.is_symlink() or path.stat().st_size != row["bytes"] or sha256(path) != row["sha256"]:
                raise ValueError(f"retained text source differs before removal: {name}")
        immutable_json(root / "removal-plan.json", {
            "schema_version": 1,
            "index_sha256": logical_index_sha256(root),
            "archive_sha256": sha256(root / "payload.tar.xz"),
            "prepared_sha256": sha256(root / "prepared.json"),
            "members": len(entries),
            "expanded_bytes": index["expanded_bytes"],
            "scope": "Native checked deletion candidates after complete indexed text archive readback and original SHA-256 comparison.",
        })
        print("Verified retained text removal plan:", len(entries), "files,", index["expanded_bytes"], "bytes")
    else:
        index = verify(root, reconstruct=False)
        if not (root / "removal-plan.json").is_file():
            raise ValueError("retained text post-removal plan is absent")
        for name in index["files"]:
            path = RAW / Path(*PurePosixPath(safe_name(name)).parts)
            if path.exists():
                raise ValueError(f"retained text source reappeared after removal: {name}")
        immutable_json(root / "removal-receipt.json", {
            "schema_version": 1,
            "index_sha256": logical_index_sha256(root),
            "archive_sha256": sha256(root / "payload.tar.xz"),
            "removal_plan_sha256": sha256(root / "removal-plan.json"),
            "members": len(index["files"]),
            "expanded_bytes": index["expanded_bytes"],
            "all_original_paths_absent": True,
            "all_payload_hashes_readback": True,
        })
        print("Verified retained text packet:", len(index["files"]), "members,", index["expanded_bytes"], "bytes")


if __name__ == "__main__":
    main()
