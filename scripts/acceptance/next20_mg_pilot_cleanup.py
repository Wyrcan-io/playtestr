"""Inventory and remove only the two exact rc.6/mg pilot input roots."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import uuid

from next20_candidate import contract
from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


def inventory(path):
    count = total = 0
    for directory, names, files in os.walk(path, followlinks=False):
        base = Path(directory)
        for name in names + files:
            item = base / name
            mode = item.lstat().st_mode
            if not stat.S_ISDIR(mode) and not stat.S_ISREG(mode):
                raise ValueError(f"unexpected linked or special pilot input: {item}")
            if stat.S_ISREG(mode):
                count += 1
                total += item.stat().st_size
                if count > 100 or total > 32 * 1024**2:
                    raise ValueError("pilot input inventory exceeded cleanup bound")
    return count, total


def remove_exact(path, expected):
    path = Path(path)
    expected = Path(expected)
    if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
        raise ValueError("refusing linked cleanup root")
    if path.resolve() != expected.resolve():
        raise ValueError(f"cleanup path did not match its owned root: {path}")
    if not path.exists():
        return {"path": path.relative_to(ROOT).as_posix(), "present": False,
                "removed": True, "files": 0, "bytes": 0}
    count, total = inventory(path)
    shutil.rmtree(path)
    if path.exists():
        raise RuntimeError(f"owned cleanup root remains: {path}")
    return {"path": path.relative_to(ROOT).as_posix(), "present": True,
            "removed": True, "files": count, "bytes": total}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    parser.add_argument("--pilot-input", required=True)
    args = parser.parse_args()
    host = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    if host != args.host:
        raise RuntimeError(f"native host mismatch: expected {args.host}, got {host}")
    input_root = ROOT / args.pilot_input
    if input_root.is_symlink() or getattr(input_root, "is_junction", lambda: False)():
        raise ValueError("pilot input root is linked")
    input_root.resolve().relative_to(RAW.resolve())
    if input_root.resolve() != (RAW / "pilot-input").resolve():
        raise ValueError("pilot input cleanup must name the exact declared root")
    _, _, candidate_root = contract("native-exit-v1", host)
    candidate_install = candidate_root
    if candidate_install.exists():
        _, candidate, _ = contract("native-exit-v1", host)
        if candidate_install.is_symlink() or getattr(candidate_install, "is_junction", lambda: False)():
            raise ValueError("refusing linked candidate install")
        names = set()
        for item in candidate_install.iterdir():
            if item.is_symlink() or not item.is_file():
                raise ValueError("unexpected candidate install entry")
            names.add(item.name)
        allowed = {"playtestr", "LICENSE", "README.md", "THIRD_PARTY_NOTICES.md", "installed.json"}
        if not names <= allowed:
            raise ValueError("candidate install contains an unexpected file")
        manifest_path = candidate_install / "installed.json"
        if manifest_path.is_file():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            binary = candidate_install / "playtestr"
            if (manifest.get("host") != host or
                    manifest.get("archive_sha256") != candidate["archive_sha256"] or
                    manifest.get("binary_sha256") != candidate["binary_sha256"] or
                    binary.is_symlink() or sha256(binary) != candidate["binary_sha256"]):
                raise ValueError("refusing to remove an unbound candidate install")
    rows = [remove_exact(candidate_install, candidate_root),
            remove_exact(input_root, RAW / "pilot-input")]
    cleanup_parent = RAW / "mg/pilot-development" / host
    cleanup_parent.mkdir(parents=True, exist_ok=True)
    receipt = {"schema_version": 1, "host": host,
               "checked_at_utc": datetime.now(timezone.utc).isoformat(),
               "removals": rows, "all_owned_inputs_absent": all(
                   row["removed"] and not (ROOT / row["path"]).exists() for row in rows)}
    if not receipt["all_owned_inputs_absent"]:
        raise RuntimeError("pilot input cleanup was not confirmed")
    immutable_json(cleanup_parent / ("cleanup-" + uuid.uuid4().hex + ".json"), receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
