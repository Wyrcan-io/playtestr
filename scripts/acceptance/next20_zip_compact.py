"""Create a self-contained content-deduplicated packet for retained ZIPs."""
import argparse
from collections import defaultdict
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import tempfile
import tarfile
import zipfile

from next20_check import RAW
from readiness_evidence import immutable_json, sha256


SOURCE = RAW / "retrieved"
FINAL = SOURCE / "retained-content-dedup-v1"
ARCHIVE_NAME = "blobs.tar.xz"
MAX_ARCHIVES = 20
MAX_MEMBERS = 30000
MAX_EXPANDED = 3 * 1024**3
MAX_MEMBER = 64 * 1024**2


def safe_name(value: str) -> str:
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or "\\" in value or ":" in value or
            any(part in {"", ".", ".."} for part in path.parts)):
        raise ValueError(f"unsafe ZIP member name: {value!r}")
    return value


def verify_packet(root: Path) -> dict:
    index_path = root / "index.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    archive = root / ARCHIVE_NAME
    if index.get("archive_sha256") != sha256(archive):
        raise ValueError("deduplicated archive hash differs")
    members = index.get("members")
    if not isinstance(members, list) or not 0 < len(members) <= MAX_MEMBERS:
        raise ValueError("deduplicated member count outside bound")
    unique = {}
    for row in members:
        digest = row["sha256"]
        if (len(digest) != 64 or row["bytes"] < 0 or row["bytes"] > MAX_MEMBER or
                row["bytes"] != int(row["bytes"])):
            raise ValueError("invalid member hash/size")
        if digest in unique and unique[digest] != row["bytes"]:
            raise ValueError("same hash declared with different lengths")
        unique[digest] = row["bytes"]
    blobs = {}
    with tarfile.open(archive, "r:xz") as packet:
        for item in packet:
            name = safe_name(item.name)
            if (not item.isfile() or name in blobs or not name.startswith("blobs/") or
                    name[6:] not in unique or name[6:] != name[6:].lower()):
                raise ValueError("invalid content-addressed packet member")
            stream = packet.extractfile(item)
            digest = hashlib.sha256()
            size = 0
            while block := stream.read(1024 * 1024):
                size += len(block)
                digest.update(block)
            hexdigest = digest.hexdigest()
            if hexdigest != name[6:] or size != unique[hexdigest]:
                raise ValueError("blob path/content hash or size differs")
            blobs[hexdigest] = size
    if blobs != unique:
        raise ValueError("deduplicated packet omits or adds content blobs")
    if len(members) != index["member_count"]:
        raise ValueError("member count differs from index")
    return index


def prepare() -> None:
    if FINAL.exists():
        raise ValueError("preserve existing retained ZIP packet")
    staging = Path(tempfile.gettempdir()) / "playtestr-next20-retrieved-zip-dedup-v1"
    if staging.exists():
        raise ValueError("preserve existing staged ZIP compaction attempt")
    zips = sorted(SOURCE.glob("*.zip"))
    if not 0 < len(zips) <= MAX_ARCHIVES:
        raise ValueError("retained ZIP count outside bound")
    archives = []
    members = []
    seen = {}
    expanded = 0
    for zip_path in zips:
        if zip_path.is_symlink() or getattr(zip_path, "is_junction", lambda: False)():
            raise ValueError("linked retained ZIP")
        before = sha256(zip_path)
        record = {"name": zip_path.name, "bytes": zip_path.stat().st_size,
                  "sha256": before, "members": []}
        with zipfile.ZipFile(zip_path) as source:
            infos = source.infolist()
            if len(members) + len(infos) > MAX_MEMBERS:
                raise ValueError("retained ZIP member count outside bound")
            names = set()
            for info in infos:
                name = safe_name(info.filename)
                mode = (info.external_attr >> 16) & 0xFFFF
                if info.is_dir() or (mode & 0o170000) == 0o120000:
                    raise ValueError("directory or symlink member requires separate review")
                if name in names or info.file_size > MAX_MEMBER:
                    raise ValueError("duplicate ZIP member or member size outside bound")
                names.add(name)
                expanded += info.file_size
                if expanded > MAX_EXPANDED:
                    raise ValueError("retained ZIP expansion exceeds bound")
                data = source.read(info)
                if (len(data) != info.file_size or
                        (zipfile.crc32(data) & 0xFFFFFFFF) != info.CRC):
                    raise ValueError("ZIP member length or CRC differs")
                digest = hashlib.sha256(data).hexdigest()
                if digest in seen and seen[digest] != len(data):
                    raise ValueError("same SHA-256 has conflicting lengths")
                seen[digest] = len(data)
                entry = {"name": name, "bytes": len(data), "sha256": digest,
                         "crc32": f"{info.CRC:08x}", "compression": info.compress_type}
                record["members"].append(entry)
                members.append({"archive": zip_path.name, **entry})
        if sha256(zip_path) != before:
            raise ValueError("retained ZIP changed during compaction")
        archives.append(record)
    staging.mkdir()
    with tarfile.open(staging / ARCHIVE_NAME, "w:xz", preset=3) as packet:
        written = set()
        for zip_path in zips:
            with zipfile.ZipFile(zip_path) as source:
                for info in source.infolist():
                    data = source.read(info)
                    digest = hashlib.sha256(data).hexdigest()
                    if digest in written:
                        continue
                    written.add(digest)
                    item = tarfile.TarInfo(f"blobs/{digest}")
                    item.size = len(data)
                    item.mode = 0o644
                    packet.addfile(item, io.BytesIO(data))
    index = {
        "schema_version": 1,
        "compression": "tar.xz content-addressed by SHA-256",
        "archives": archives,
        "members": members,
        "archive_sha256": sha256(staging / ARCHIVE_NAME),
        "member_count": len(members),
        "unique_blob_count": len(seen),
        "expanded_member_bytes": expanded,
        "unique_blob_bytes": sum(seen.values()),
        "scope": "Exact full member payloads of the listed retrieved ZIP files, with repeated byte-identical payloads stored once. Each original ZIP hash, per-archive member path, size, CRC and SHA-256 is bound. ZIP container metadata is not preserved.",
    }
    immutable_json(staging / "index.json", index)
    verify_packet(staging)
    immutable_json(staging / "prepared.json", {
        "schema_version": 1,
        "index_sha256": sha256(staging / "index.json"),
        "archive_sha256": sha256(staging / ARCHIVE_NAME),
        "source_archive_count": len(archives),
        "member_count": len(members),
        "unique_blob_count": len(seen),
        "all_zip_payloads_readback": True,
        "source_removal_confirmed": False,
        "staging_path": str(staging),
    })
    print("Prepared verified ZIP payload packet:", len(archives), "archives,",
          len(members), "members,", expanded, "expanded bytes,",
          len(seen), "unique blobs /", sum(seen.values()), "bytes ->",
          (staging / ARCHIVE_NAME).stat().st_size, "bytes. Source ZIP removal pending.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "readback"))
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    root = (Path(tempfile.gettempdir()) / "playtestr-next20-retrieved-zip-dedup-v1"
            if args.staged else FINAL)
    if args.mode == "prepare":
        prepare()
    else:
        index = verify_packet(root)
        print("Verified ZIP payload packet:", index["member_count"], "members,",
              index["unique_blob_count"], "unique blobs")


if __name__ == "__main__":
    main()
