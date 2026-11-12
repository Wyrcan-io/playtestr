"""Build pinned Pick with owned tool/temp paths and run its upstream suite."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import time

from next20_check import RAW, ROOT
from next20_mg_build import MAX_OUTPUT, run_bounded
from readiness_evidence import immutable_json, sha256

PIN = "caae95938359b2e814b3e7406f396f486c9d99fb"
ARCHIVE_SHA256 = "e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653"
HOSTS = {"linux": "Linux", "darwin": "Darwin"}
MAX_BUILD_SECONDS = 1200
MAX_TREE_FILES = 10000
MAX_TREE_BYTES = 256 * 1024**2


def require(value, message):
    if not value:
        raise ValueError(message)


def file_map(root):
    rows = {}
    total = 0
    for path in sorted(root.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError("linked path in pinned Pick source tree: " + path.relative_to(root).as_posix())
        if path.is_file():
            relative = path.relative_to(root).as_posix()
            size = path.stat().st_size
            total += size
            if len(rows) >= MAX_TREE_FILES or size > 8 * 1024**2 or total > MAX_TREE_BYTES:
                raise ValueError("Pick source/build tree exceeded the reviewed file/byte bound")
            rows[relative] = sha256(path)
    return rows, total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-host", choices=tuple(HOSTS), required=True)
    args = parser.parse_args()
    host = "linux" if platform.system() == "Linux" else "darwin" if platform.system() == "Darwin" else "other"
    require(host == args.expected_host, "actual native host differs from the declared Pick build host")
    target = RAW / "active" / "pick"
    source = target / "src"
    owner = json.loads((target / "task-owned.json").read_text(encoding="utf-8"))
    acquisition = json.loads((target / "acquisition.json").read_text(encoding="utf-8"))
    require(owner.get("workspace") == str(ROOT) and owner.get("slug") == "pick" and owner.get("pin") == PIN and
            acquisition.get("repository") == "mptre/pick" and acquisition.get("pin") == PIN and
            acquisition.get("archive_sha256") == ARCHIVE_SHA256 and sha256(target / "source.tar.gz") == ARCHIVE_SHA256,
            "Pick source archive/owner does not match the reviewed canonical pin")
    pristine = acquisition.get("source_files")
    source_now, source_bytes = file_map(source)
    # ``entries`` counts all archive members, including the three directories
    # in Pick's archive.  ``source_files`` intentionally hashes regular files.
    require(isinstance(pristine, dict) and source_now == pristine and len(source_now) <= acquisition.get("entries", 0),
            "Pick extracted primary source differs from its immutable acquisition manifest")
    require(host in {"linux", "darwin"}, "Pick is declared only for native Linux/macOS hosts")

    tools = target / "tools"
    temp = target / "tmp"
    install = target / "install"
    output_paths = [tools, temp, install, target / "build-logs"]
    for path in output_paths:
        if path.exists():
            raise ValueError("preserve existing Pick build output: " + path.name)
        path.mkdir(parents=True)
    gmake = shutil.which("gmake")
    make_system = shutil.which("make")
    make_executable = gmake or make_system
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    require(make_executable is not None and compiler is not None,
            "native GNU make/C compiler prerequisite is missing; refuse before build launch")

    env = {key: os.environ[key] for key in ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT")
           if key in os.environ}
    env.update({"TMPDIR": str(temp), "TMP": str(temp), "TEMP": str(temp), "CC": compiler,
                "LC_ALL": "C", "LANG": "C", "MAKEFLAGS": "", "MFLAGS": ""})
    make_path = tools / "make"
    make_path.symlink_to(Path(make_executable).resolve(strict=True))
    env["PATH"] = str(tools) + os.pathsep + str(install / "bin") + os.pathsep + env.get("PATH", "")
    deadline = time.monotonic() + MAX_BUILD_SECONDS
    commands = []
    started_at = datetime.now(timezone.utc).isoformat()

    def command(name, argv, cwd):
        if time.monotonic() >= deadline:
            raise TimeoutError("Pick native build exceeded its shared twenty-minute deadline")
        log = target / "build-logs" / (f"{len(commands) + 1:02d}-" + name + ".log")
        return run_bounded(list(map(str, argv)), cwd, env, log, deadline, commands,
                           operation="Pick " + name)

    version = command("make-version", [make_path, "--version"], source)
    make_log = (ROOT / version["log"]).read_text(encoding="utf-8", errors="replace")
    require("GNU Make" in make_log, "Pick configure requires GNU make; do not substitute another implementation")
    command("compiler-version", [compiler, "--version"], source)
    command("configure", ["/bin/sh", "./configure"], source)
    command("build", [make_path, "-j2"], source)
    command("upstream-tests", [make_path, "test"], source)
    command("install", [make_path, "install", "BINDIR=" + str(install / "bin"),
                         "MANDIR=" + str(install / "man")], source)
    require((source / "config.h").is_file() and (source / "config.mk").is_file() and
            (source / "config.log").is_file(), "Pick configure did not retain its local probe output")
    # Preserve the immutable source identity after producing the installed
    # binary. Pick's upstream cleandir target removes configure outputs and
    # compiled test/application files from the source checkout.
    command("source-clean", [make_path, "cleandir"], source)

    binary = install / "bin" / "pick"
    require(binary.is_file() and not binary.is_symlink(), "Pick install did not create its owned native executable")
    build_sha = sha256(binary)
    source_after_cleanup, _ = file_map(source)
    require(source_after_cleanup == pristine,
            "Pick source cleanup did not restore every pinned file byte exactly")
    require(make_path.is_symlink() and make_path.resolve(strict=True) == Path(make_executable).resolve(strict=True),
            "owned GNU make alias changed; refusing removal")
    make_path.unlink()
    inventory, tree_bytes = file_map(target)
    require(len(inventory) <= MAX_TREE_FILES and tree_bytes <= MAX_TREE_BYTES,
            "Pick owned source/build/install tree exceeds its limit")
    receipt = {
        "schema_version": 1, "project": "pick", "repository": "mptre/pick", "pin": PIN,
        "source_archive_sha256": ARCHIVE_SHA256, "host": host, "architecture": platform.machine(),
        "runtime_kind": "native", "binary_relative_path": "install/bin/pick",
        "binary_sha256": build_sha, "binary_bytes": binary.stat().st_size,
        "source_file_count": len(pristine), "source_tree_sha256": hashlib.sha256(
            json.dumps(pristine, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        "commands": commands, "started_at_utc": started_at,
        "build_tree_file_count": len(inventory), "build_tree_bytes": tree_bytes,
        "upstream_tests": "passed", "install_prefix_relative": "install",
        "network_hooks": False, "build_hooks_reviewed": True,
    }
    immutable_json(target / "build.json", receipt)
    immutable_json(target / "runtime.json", {"schema_version": 1, "kind": "native",
                    "native": str(binary.resolve()), "native_sha256": build_sha,
                    "host": host, "pin": PIN})
    print(json.dumps({"project": "pick", "host": host, "source_archive_sha256": ARCHIVE_SHA256,
                      "binary_sha256": build_sha, "upstream_tests": "passed",
                      "commands": len(commands), "build_tree_bytes": tree_bytes}, sort_keys=True))


if __name__ == "__main__":
    main()
