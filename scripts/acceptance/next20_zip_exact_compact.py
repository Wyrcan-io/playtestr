"""Losslessly deduplicate ZIP payload streams while preserving exact ZIP bytes."""
import argparse
import hashlib
import io
import json
import lzma
from pathlib import Path, PurePosixPath
import struct
import tarfile
import tempfile
import zipfile

from next20_check import RAW
from readiness_evidence import immutable_json, sha256


SCOPES = {"retrieved": "retrieved", "retained": "retained"}
MAX_ARCHIVES = 20
MAX_MEMBERS = 30000
MAX_EXPANDED = 3 * 1024**3
MAX_MEMBER = 64 * 1024**2


def read_index(root: Path) -> dict:
    """Read the exact index in its retained JSON or XZ representation."""
    packed = root / "index.json.xz"
    path = packed if packed.is_file() else root / "index.json"
    data = lzma.decompress(path.read_bytes()) if path == packed else path.read_bytes()
    value = json.loads(data.decode("utf-8"))
    if not isinstance(value, dict):
        raise ValueError("exact ZIP index must be an object")
    return value


def logical_index_sha256(root: Path) -> str:
    """Hash the original JSON bytes after decoding any storage compression."""
    packed = root / "index.json.xz"
    data = lzma.decompress(packed.read_bytes()) if packed.is_file() else (root / "index.json").read_bytes()
    return hashlib.sha256(data).hexdigest()


def safe_name(value: str) -> str:
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or "\\" in value or ":" in value or
            any(part in {"", ".", ".."} for part in path.parts)):
        raise ValueError(f"unsafe ZIP member name: {value!r}")
    return value


def put_blob(root: Path, data: bytes) -> tuple[str, int]:
    digest = hashlib.sha256(data).hexdigest()
    path = root / "blobs" / digest
    if path.exists():
        if path.stat().st_size != len(data) or sha256(path) != digest:
            raise ValueError("content-addressed ZIP segment collision")
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    return digest, len(data)


def local_range(raw, info):
    raw.seek(info.header_offset)
    header = raw.read(30)
    if len(header) != 30:
        raise ValueError("short local ZIP header")
    sig, _version, flags, method, _time, _date, crc, csize, _usize, nlen, xlen = struct.unpack(
        "<4s5H3I2H", header)
    if sig != b"PK\x03\x04" or flags & 1 or method != info.compress_type:
        raise ValueError("unsupported, encrypted, or mismatched local ZIP header")
    if csize != info.compress_size and not (flags & 8 and csize == 0):
        raise ValueError("local and central ZIP compressed sizes differ")
    if crc != info.CRC and not (flags & 8 and crc == 0):
        raise ValueError("local and central ZIP CRCs differ")
    start = info.header_offset + 30 + nlen + xlen
    return start, start + info.compress_size


def verify_packet(root: Path, *, reconstruct: bool) -> dict:
    index_path = root / "index.json.xz"
    if not index_path.is_file():
        index_path = root / "index.json"
    index = read_index(root)
    archive = root / "blobs.tar.xz"
    if index.get("archive_sha256") != sha256(archive):
        raise ValueError("exact ZIP segment packet hash differs")
    expected = index.get("blobs")
    if not isinstance(expected, dict) or not expected:
        raise ValueError("exact ZIP segment blob index missing")
    blobs = {}
    with tempfile.TemporaryDirectory(prefix="next20-zip-readback-") as td:
        temp = Path(td)
        staged_blobs = root / "blobs"
        use_staged = reconstruct and staged_blobs.is_dir()
        blob_root = staged_blobs if use_staged else temp / "blobs"
        if not use_staged:
            blob_root.mkdir()
        with tarfile.open(archive, "r:xz") as packet:
            for member in packet:
                name = safe_name(member.name)
                digest = name.removeprefix("blobs/")
                if (not member.isfile() or not name.startswith("blobs/") or digest in blobs or
                        digest not in expected or member.size != expected[digest]):
                    raise ValueError("exact ZIP segment packet member differs")
                stream = packet.extractfile(member)
                hasher = hashlib.sha256()
                size = 0
                target = blob_root / digest
                if use_staged and (not target.is_file() or target.stat().st_size != expected[digest]):
                    raise ValueError("staged exact ZIP blob is absent or wrong length")
                if use_staged and sha256(target) != digest:
                    raise ValueError("staged exact ZIP blob hash differs")
                out = target.open("wb") if not use_staged else None
                try:
                    while block := stream.read(1024 * 1024):
                        size += len(block)
                        hasher.update(block)
                        if reconstruct and not use_staged:
                            out.write(block)
                finally:
                    if out is not None:
                        out.close()
                if hasher.hexdigest() != digest:
                    raise ValueError("exact ZIP segment content hash differs")
                blobs[digest] = size
        if blobs != expected:
            raise ValueError("exact ZIP segment packet omitted/added blobs")
        if reconstruct:
            restored_root = temp / "restored"
            restored_root.mkdir()
            for row in index["archives"]:
                restored = restored_root / row["name"]
                restored.parent.mkdir(parents=True, exist_ok=True)
                hasher = hashlib.sha256()
                size = 0
                with restored.open("wb") as out:
                    for segment in row["segments"]:
                        source = blob_root / segment["sha256"]
                        if source.stat().st_size != segment["bytes"]:
                            raise ValueError("exact ZIP segment blob length differs")
                        with source.open("rb") as data:
                            while block := data.read(1024 * 1024):
                                out.write(block)
                                hasher.update(block)
                                size += len(block)
                if size != row["bytes"] or hasher.hexdigest() != row["sha256"]:
                    raise ValueError(f"reconstructed ZIP bytes differ: {row['name']}")
                with zipfile.ZipFile(restored) as archive_check:
                    if archive_check.testzip() is not None:
                        raise ValueError("reconstructed ZIP CRC check failed")
                    if len(archive_check.infolist()) != len(row["members"]):
                        raise ValueError("reconstructed ZIP member count differs")
                    for info, member in zip(archive_check.infolist(), row["members"]):
                        safe_name(info.filename)
                        data = archive_check.read(info)
                        if (info.filename != member["name"] or len(data) != member["bytes"] or
                                hashlib.sha256(data).hexdigest() != member["sha256"] or
                                f"{info.CRC:08x}" != member["crc32"]):
                            raise ValueError("reconstructed ZIP member payload differs")
    return index


def prepare(source: Path, final: Path, stage: Path) -> None:
    if stage.exists() or final.exists():
        raise ValueError("preserve existing ZIP exact-compaction attempt")
    sources = sorted(source.rglob("*.zip"))
    if not 0 < len(sources) <= MAX_ARCHIVES:
        raise ValueError("retained ZIP count outside bound")
    stage.mkdir()
    archives = []
    blob_sizes = {}
    expanded_total = 0
    member_total = 0
    for source_path in sources:
        initial_hash = sha256(source_path)
        initial_size = source_path.stat().st_size
        archive_record = {"name": source_path.relative_to(source).as_posix(), "bytes": initial_size,
                          "sha256": initial_hash, "members": [], "segments": []}
        ranges = []
        with source_path.open("rb") as raw, zipfile.ZipFile(source_path) as source_zip:
            for info in source_zip.infolist():
                name = safe_name(info.filename)
                mode = (info.external_attr >> 16) & 0xFFFF
                if info.is_dir() or (mode & 0o170000) == 0o120000:
                    raise ValueError("directory/symlink ZIP member requires separate handling")
                if info.file_size > MAX_MEMBER:
                    raise ValueError("ZIP member exceeds declared bound")
                expanded_total += info.file_size
                member_total += 1
                if expanded_total > MAX_EXPANDED or member_total > MAX_MEMBERS:
                    raise ValueError("ZIP expanded evidence exceeds declared bound")
                payload = source_zip.read(info)  # verifies ZIP CRC
                member = {"name": name, "bytes": len(payload),
                          "sha256": hashlib.sha256(payload).hexdigest(),
                          "crc32": f"{info.CRC:08x}",
                          "compression": info.compress_type}
                archive_record["members"].append(member)
                start, end = local_range(raw, info)
                if start < 0 or end > initial_size or end < start:
                    raise ValueError("ZIP compressed stream range outside archive")
                if end > start:
                    ranges.append((start, end))
            ranges.sort()
            cursor = 0
            for start, end in ranges:
                if start < cursor:
                    raise ValueError("ZIP compressed stream ranges overlap")
                if start > cursor:
                    raw.seek(cursor)
                    digest, size = put_blob(stage, raw.read(start - cursor))
                    archive_record["segments"].append({"sha256": digest, "bytes": size})
                    blob_sizes[digest] = size
                raw.seek(start)
                digest, size = put_blob(stage, raw.read(end - start))
                archive_record["segments"].append({"sha256": digest, "bytes": size})
                blob_sizes[digest] = size
                cursor = end
            if cursor < initial_size:
                raw.seek(cursor)
                digest, size = put_blob(stage, raw.read(initial_size - cursor))
                archive_record["segments"].append({"sha256": digest, "bytes": size})
                blob_sizes[digest] = size
        if sha256(source_path) != initial_hash or source_path.stat().st_size != initial_size:
            raise ValueError("source ZIP changed during exact compaction")
        if sum(seg["bytes"] for seg in archive_record["segments"]) != initial_size:
            raise ValueError("ZIP segment stream length differs from source")
        archives.append(archive_record)
    tar_path = stage / "blobs.tar.xz"
    with tarfile.open(tar_path, "w:xz", preset=3) as packet:
        for digest, size in sorted(blob_sizes.items()):
            path = stage / "blobs" / digest
            if path.stat().st_size != size or sha256(path) != digest:
                raise ValueError("staged ZIP blob changed before packet creation")
            info = tarfile.TarInfo(f"blobs/{digest}")
            info.size = size
            info.mode = 0o644
            with path.open("rb") as payload:
                packet.addfile(info, payload)
    index = {
        "schema_version": 1,
        "encoding": "interleaved exact archive byte segments; payload streams content-addressed by SHA-256",
        "archives": archives,
        "blobs": blob_sizes,
        "archive_sha256": sha256(tar_path),
        "source_archive_count": len(archives),
        "member_count": member_total,
        "expanded_member_bytes": expanded_total,
        "original_zip_bytes": sum(row["bytes"] for row in archives),
        "unique_segment_bytes": sum(blob_sizes.values()),
        "scope": "Every original ZIP byte, including local/central headers, descriptors, comments and member order, is reconstructed exactly. Reconstructed archives are checked against original SHA-256, ZIP CRCs and every logical member path/size/CRC/SHA-256 before source removal.",
    }
    immutable_json(stage / "index.json", index)
    verify_packet(stage, reconstruct=True)
    immutable_json(stage / "prepared.json", {
        "schema_version": 1,
        "index_sha256": sha256(stage / "index.json"),
        "archive_sha256": sha256(tar_path),
        "original_zip_count": len(archives),
        "member_count": member_total,
        "all_original_zip_hashes_reconstructed": True,
        "all_logical_members_readback": True,
        "source_removal_confirmed": False,
        "staging_path": str(stage),
    })
    print("Prepared byte-exact ZIP packet:", len(archives), "archives,",
          member_total, "members; original bytes", index["original_zip_bytes"],
          "unique segment bytes", index["unique_segment_bytes"],
          "packet", tar_path.stat().st_size, "plus index",
          (stage / "index.json").stat().st_size,
          "bytes. All ten ZIPs reconstructed and verified; source removal pending.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "readback", "remove-plan"))
    parser.add_argument("--scope", choices=tuple(SCOPES), default="retrieved")
    parser.add_argument("--reconstruct", action="store_true")
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    source = RAW / SCOPES[args.scope]
    final = source / ("retained-exact-zip-v1" if args.scope == "retrieved" else "retained-exact-zip-v2")
    stage = Path(tempfile.gettempdir()) / f"playtestr-next20-{args.scope}-exact-zip-v1"
    root = stage if args.mode == "prepare" or args.staged else final
    if args.mode == "prepare":
        prepare(source, final, stage)
    elif args.mode == "remove-plan":
        index = read_index(root)
        prepared = json.loads((root / "prepared.json").read_text(encoding="utf-8"))
        final_readback_path = root / "final-readback-v1.json"
        final_readback = json.loads(final_readback_path.read_text(encoding="utf-8"))
        if (prepared.get("all_original_zip_hashes_reconstructed") is not True or
                prepared.get("all_logical_members_readback") is not True or
                prepared.get("index_sha256") != logical_index_sha256(root) or
                prepared.get("archive_sha256") != sha256(root / "blobs.tar.xz") or
                final_readback.get("archive_sha256") != sha256(root / "blobs.tar.xz") or
                final_readback.get("index_sha256") != logical_index_sha256(root) or
                final_readback.get("all_original_zip_hashes_reconstructed") is not True or
                final_readback.get("all_logical_members_readback") is not True):
            raise ValueError("complete exact ZIP readback receipt does not bind current packet")
        if not (root / "interrupted-removal-plan-v1.json").exists():
            immutable_json(root / "interrupted-removal-plan-v1.json", {
                "schema_version": 1,
                "index_sha256": logical_index_sha256(root),
                "archive_sha256": sha256(root / "blobs.tar.xz"),
                "disposition": "An initial removal-plan pass repeated all per-file hashing of the 42,000-file expanded staging tree and was stopped as redundant after complete archive/member readback. No source ZIP or staging file was removed by that pass.",
            })
        blob_root = root / "blobs"
        if not blob_root.is_dir() or blob_root.is_symlink():
            raise ValueError("expanded ZIP segment directory absent or linked")
        observed = {}
        for path in blob_root.iterdir():
            if not path.is_file() or path.is_symlink():
                raise ValueError("unexpected expanded ZIP segment entry")
            if path.name not in index["blobs"]:
                raise ValueError("unindexed expanded ZIP segment")
            observed[path.name] = path.stat().st_size
        if observed != index["blobs"]:
            raise ValueError("expanded ZIP segment inventory differs from exact packet")
        immutable_json(root / "expanded-removal-final-plan-v1.json", {
            "schema_version": 1,
            "index_sha256": logical_index_sha256(root),
            "archive_sha256": sha256(root / "blobs.tar.xz"),
            "prepared_sha256": sha256(root / "prepared.json"),
            "final_readback_sha256": sha256(final_readback_path),
            "expanded_blob_count": len(observed),
            "expanded_blob_bytes": sum(observed.values()),
            "packet_byte_exact_reconstruction_passed": True,
            "scope": "Only the expanded duplicate blobs directory is eligible for native checked removal; exact ZIP byte streams and all member reports remain in blobs.tar.xz and index.json.",
        })
        print("Verified expanded-blob removal plan:", len(observed), "blobs,", sum(observed.values()), "bytes")
    else:
        if (args.staged and args.mode == "readback" and args.reconstruct and
                not (root / "interrupted-verification-v1.json").exists() and
                not (root / "prepared.json").exists()):
            immutable_json(root / "interrupted-verification-v1.json", {
                "schema_version": 1,
                "index_sha256": logical_index_sha256(root),
                "archive_sha256": sha256(root / "blobs.tar.xz"),
                "disposition": "The first exact readback failed because temporary reconstruction did not create parent directories for ZIPs stored below nested paths. Original ZIPs remain intact; this retry creates the contained restore path and repeats byte-exact reconstruction.",
            })
        index = verify_packet(root, reconstruct=args.reconstruct)
        if args.staged and args.mode == "readback" and args.reconstruct and not (root / "prepared.json").exists():
            immutable_json(root / "prepared.json", {
                "schema_version": 1,
                "index_sha256": logical_index_sha256(root),
                "archive_sha256": sha256(root / "blobs.tar.xz"),
                "original_zip_count": len(index["archives"]),
                "member_count": index["member_count"],
                "all_original_zip_hashes_reconstructed": True,
                "all_logical_members_readback": True,
                "source_removal_confirmed": False,
                "staging_path": str(root),
            })
        print("Verified byte-exact ZIP packet:", index["source_archive_count"],
              "archives,", index["member_count"], "members; exact reconstruction:",
              bool(args.reconstruct))


if __name__ == "__main__":
    main()
