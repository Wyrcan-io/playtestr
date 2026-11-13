"""Build and test the exact screened fzy source inside its owned native target."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import time

from next20_check import RAW, ROOT
from next20_mg_build import run_bounded
from readiness_evidence import immutable_json, sha256


PIN = "34b88869d022e861da4846c4463aea3ddfb3ff30"
ARCHIVE_SHA256 = "d55d4d0dcbced2daa0dd16b42ee0fc31654bd038ff6a147b38580c233d62c967"
HOSTS = {"linux": "Linux", "darwin": "Darwin"}
MAX_TREE_FILES = 10000
MAX_TREE_BYTES = 256 * 1024**2
MAX_BUILD_SECONDS = 20 * 60
GENERATED_DEPFILES = {
    "deps/theft/theft.d", "deps/theft/theft_bloom.d", "deps/theft/theft_hash.d",
    "deps/theft/theft_mt.d", "test/fzytest.d",
}


def require(value, message):
    if not value:
        raise ValueError(message)


def file_map(root):
    rows = {}
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("linked path in pinned fzy source tree: " + path.relative_to(root).as_posix())
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            size = path.stat().st_size
            total += size
            if len(rows) >= MAX_TREE_FILES or size > 8 * 1024**2 or total > MAX_TREE_BYTES:
                raise ValueError("fzy source/build tree exceeded its reviewed bound")
            rows[relative] = sha256(path)
    return rows, total


def remove_generated_outputs(build_source, pristine):
    """Remove only observed compiler outputs left outside upstream veryclean."""
    actual, _ = file_map(build_source)
    extras = set(actual) - set(pristine)
    allowed = set(GENERATED_DEPFILES)
    dsym = build_source / "test/fzytest.dSYM"
    if dsym.exists():
        for path in dsym.rglob("*"):
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                raise ValueError("linked path in compiler-generated fzy dSYM output")
        allowed.update(path.relative_to(build_source).as_posix()
                       for path in dsym.rglob("*") if path.is_file())
    require(extras <= allowed, "fzy build left unexpected files outside upstream clean target")
    removed = []
    for relative in sorted(extras):
        path = build_source / relative
        path.resolve(strict=True).relative_to(build_source.resolve(strict=True))
        if path.is_symlink() or not path.is_file():
            raise ValueError("compiler-generated fzy artifact is not a regular owned file")
        removed.append({"path": relative, "sha256": sha256(path), "bytes": path.stat().st_size})
        path.unlink()
    if dsym.exists():
        size = sum(path.stat().st_size for path in dsym.rglob("*") if path.is_file())
        if size > 64 * 1024**2:
            raise ValueError("compiler-generated fzy dSYM output exceeds its removal bound")
        shutil.rmtree(dsym)
        removed.append({"path": "test/fzytest.dSYM", "removed_directory": True,
                        "bytes": size})
    require(file_map(build_source)[0] == pristine,
            "fzy build source did not return byte-exact after reviewed output cleanup")
    return removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-host", choices=tuple(HOSTS), required=True)
    args = parser.parse_args()
    host = "linux" if platform.system() == "Linux" else "darwin" if platform.system() == "Darwin" else "other"
    require(host == args.expected_host, "actual native host differs from declared fzy host")
    target = RAW / "active" / "fzy"
    source = target / "src"
    owner = json.loads((target / "task-owned.json").read_text(encoding="utf-8"))
    acquisition = json.loads((target / "acquisition.json").read_text(encoding="utf-8"))
    require(owner.get("workspace") == str(ROOT) and owner.get("slug") == "fzy" and owner.get("pin") == PIN
            and acquisition.get("repository") == "jhawthorn/fzy" and acquisition.get("pin") == PIN
            and acquisition.get("archive_sha256") == ARCHIVE_SHA256
            and sha256(target / "source.tar.gz") == ARCHIVE_SHA256,
            "fzy source archive/owner differs from its selected pin")
    pristine, _ = file_map(source)
    provenance = json.loads((DOC / "fzy/source-provenance.json").read_text(encoding="utf-8"))
    source_tree_sha = hashlib.sha256(json.dumps(pristine, sort_keys=True,
                                                 separators=(",", ":")).encode()).hexdigest()
    require(provenance.get("project") == "fzy" and provenance.get("pin") == PIN
            and provenance.get("source_archive_sha256") == ARCHIVE_SHA256
            and provenance.get("source_file_count") == len(pristine)
            and provenance.get("source_tree_sha256") == source_tree_sha
            and provenance.get("license_file_sha256") == pristine.get("LICENSE"),
            "fzy source differs from its committed provenance binding")
    require("LICENSE" in pristine and (source / "LICENSE").read_bytes().startswith(b"The MIT License"),
            "pinned fzy license is missing or differs from reviewed MIT license")
    make = shutil.which("make")
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    require(make and compiler, "native make/C compiler prerequisite missing; refuse before build")
    tools, temp, install, logs = (target / name for name in ("tools", "tmp", "install", "build-logs"))
    for path in (tools, temp, install, logs):
        if path.exists():
            raise ValueError("preserve existing fzy build output: " + path.name)
        path.mkdir(parents=True)
    build_source = target / "build-source"
    if build_source.exists():
        raise ValueError("preserve existing fzy isolated build source")
    shutil.copytree(source, build_source)
    copied, _ = file_map(build_source)
    require(copied == pristine, "fzy isolated build copy differs from pinned source")
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env.update({"CC": compiler, "TMPDIR": str(temp), "TMP": str(temp), "TEMP": str(temp),
                "LC_ALL": "C", "LANG": "C", "MAKEFLAGS": "", "MFLAGS": ""})
    env["PATH"] = str(install / "bin") + os.pathsep + env.get("PATH", "")
    deadline = time.monotonic() + MAX_BUILD_SECONDS
    commands = []
    started = datetime.now(timezone.utc).isoformat()

    def command(name, argv):
        if time.monotonic() >= deadline:
            raise TimeoutError("fzy build exceeded its shared twenty-minute deadline")
        log = logs / f"{len(commands) + 1:02d}-{name}.log"
        return run_bounded(list(map(str, argv)), build_source, env, log, deadline, commands,
                           operation="fzy " + name)

    command("make-version", [make, "--version"])
    command("compiler-version", [compiler, "--version"])
    command("build", [make, "-j2"])
    command("upstream-tests", [make, "test"])
    command("install", [make, "PREFIX=" + str(install), "BINDIR=" + str(install / "bin"),
                         "MANDIR=" + str(install / "share/man"), "install"])
    command("source-clean", [make, "veryclean"])
    binary = install / "bin" / "fzy"
    require(binary.is_file() and not binary.is_symlink(), "fzy install did not produce an owned executable")
    removed_outputs = remove_generated_outputs(build_source, pristine)
    require(file_map(source)[0] == pristine,
            "upstream fzy build/test/clean changed the pristine acquired source")
    build_source.resolve(strict=True).relative_to(target.resolve(strict=True))
    shutil.rmtree(build_source)
    inventory, tree_bytes = file_map(target)
    require(len(inventory) <= MAX_TREE_FILES and tree_bytes <= MAX_TREE_BYTES,
            "fzy owned source/build/install tree exceeds bounds")
    receipt = {
        "schema_version": 1, "project": "fzy", "repository": "jhawthorn/fzy", "pin": PIN,
        "source_archive_sha256": acquisition["archive_sha256"], "host": host,
        "architecture": platform.machine(), "runtime_kind": "native",
        "binary_relative_path": "install/bin/fzy", "binary_sha256": sha256(binary),
        "binary_bytes": binary.stat().st_size,
        "source_file_count": len(pristine),
        "source_tree_sha256": source_tree_sha,
        "commands": commands, "started_at_utc": started,
        "compiler_generated_outputs_removed": removed_outputs,
        "build_tree_file_count": len(inventory), "build_tree_bytes": tree_bytes,
        "upstream_tests": "passed", "source_restored_exact": True,
        "network_hooks": False, "build_hooks_reviewed": True,
    }
    immutable_json(target / "build.json", receipt)
    immutable_json(target / "runtime.json", {"schema_version": 1, "kind": "native",
                    "native": str(binary.resolve()), "native_sha256": sha256(binary),
                    "host": host, "pin": PIN})
    print(json.dumps({"project": "fzy", "host": host, "pin": PIN,
                      "source_archive_sha256": acquisition["archive_sha256"],
                      "binary_sha256": sha256(binary), "upstream_tests": "passed",
                      "build_tree_bytes": tree_bytes}, sort_keys=True))


if __name__ == "__main__":
    main()
