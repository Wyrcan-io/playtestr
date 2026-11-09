"""Build the reviewed pinned mg source inside its one owned active target."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import signal
import subprocess
import sys
import time
import urllib.request
import uuid

from next20_check import DOC, RAW, ROOT
from readiness_acquire_plop import extract_source
from readiness_evidence import immutable_json, sha256


PIN = "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66"
MAX_SECONDS = 20 * 60
MAX_OUTPUT = 4 * 1024 * 1024
TOOLCHAIN_SOURCES = (
    {"name": "m4", "version": "1.4.21",
     "url": "https://ftp.gnu.org/gnu/m4/m4-1.4.21.tar.xz",
     "sha256": "f25c6ab51548a73a75558742fb031e0625d6485fe5f9155949d6486a2408ab66"},
    {"name": "autoconf", "version": "2.73",
     "url": "https://ftp.gnu.org/gnu/autoconf/autoconf-2.73.tar.xz",
     "sha256": "9fd672b1c8425fac2fa67fa0477b990987268b90ff36d5f016dae57be0d6b52e"},
    {"name": "automake", "version": "1.18.1",
     "url": "https://ftp.gnu.org/gnu/automake/automake-1.18.1.tar.xz",
     "sha256": "168aa363278351b89af56684448f525a5bce5079d0b6842bd910fdd3f1646887"},
)


def stop_group(process):
    stop_process_group(process.pid)
    if process.poll() is None:
        process.wait(timeout=5)


def process_group_members(process_group):
    """Return the exact POSIX process records still in an owned process group."""
    probe = subprocess.run(["ps", "-axo", "pid=,pgid=,stat=,uid="],
                           stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE, timeout=5, check=True)
    if len(probe.stdout) > MAX_OUTPUT:
        raise RuntimeError("process-group inspection exceeded its output bound")
    members = []
    for line in probe.stdout.decode("ascii", errors="replace").splitlines():
        fields = line.split()
        if len(fields) != 4:
            continue
        try:
            pid, pgid, uid = int(fields[0]), int(fields[1]), int(fields[3])
        except ValueError:
            continue
        if pgid == process_group:
            members.append({"pid": pid, "process_group": pgid,
                            "state": fields[2], "uid": uid})
    return members


def process_group_has_live_members(process_group):
    return any(not member["state"].startswith("Z")
               for member in process_group_members(process_group))


def stop_process_group(process_group):
    members = process_group_members(process_group)
    if any(member["uid"] != os.getuid() for member in members):
        raise RuntimeError(f"owned process group {process_group} contains another uid")
    if not any(not member["state"].startswith("Z") for member in members):
        return
    os.killpg(process_group, signal.SIGTERM)
    try:
        deadline = time.monotonic() + 5
        while process_group_has_live_members(process_group) and time.monotonic() < deadline:
            time.sleep(0.05)
        if process_group_has_live_members(process_group):
            os.killpg(process_group, signal.SIGKILL)
            deadline = time.monotonic() + 5
            while process_group_has_live_members(process_group) and time.monotonic() < deadline:
                time.sleep(0.05)
        if process_group_has_live_members(process_group):
            raise RuntimeError(f"owned build process group {process_group} has live processes after termination")
    except ProcessLookupError:
        if process_group_has_live_members(process_group):
            raise


def command_group_cleanup(process_group):
    members = process_group_members(process_group)
    if any(member["uid"] != os.getuid() for member in members):
        raise RuntimeError(f"owned process group {process_group} contains another uid")
    live = [member for member in members if not member["state"].startswith("Z")]
    if live:
        stop_process_group(process_group)
        members = process_group_members(process_group)
        live = [member for member in members if not member["state"].startswith("Z")]
        if live:
            raise RuntimeError(f"owned build process group {process_group} has live processes after cleanup")
    zombies = sum(member["state"].startswith("Z") for member in members)
    if zombies:
        return f"no live processes remain; {zombies} terminated zombie record(s) await OS reaping"
    return "process group absent; no owned descendants remain"


def owned_autotools(target, evidence, env, deadline, commands):
    """Build pinned GNU bootstrap tools under the active target when absent."""
    required = ("autoreconf", "autoconf", "automake", "aclocal", "autoheader", "m4")
    missing = [name for name in required if shutil.which(name, path=env.get("PATH")) is None]
    if not missing:
        return env, {"kind": "runner-image", "missing_before_build": [],
                     "source_archives": []}

    root = target / "toolchain"
    downloads = root / "downloads"
    sources = root / "sources"
    builds = root / "build"
    prefix = root / "install"
    if root.exists() and (root.is_symlink() or getattr(root, "is_junction", lambda: False)()):
        raise ValueError("linked owned toolchain root")
    root.mkdir(exist_ok=True)
    for path in (downloads, sources, builds, prefix):
        if path.exists() and (path.is_symlink() or getattr(path, "is_junction", lambda: False)()):
            raise ValueError(f"linked owned toolchain root: {path}")
        path.mkdir(parents=True, exist_ok=True)
    local_env = dict(env)
    local_env["PATH"] = str(prefix / "bin") + os.pathsep + env.get("PATH", "")
    local_env["M4"] = str(prefix / "bin" / "m4")
    archive_receipts = []
    for item in TOOLCHAIN_SOURCES:
        archive = downloads / f"{item['name']}-{item['version']}.tar.xz"
        with urllib.request.urlopen(item["url"], timeout=30) as response:
            data = response.read(8 * 1024**2 + 1)
        if len(data) > 8 * 1024**2:
            raise ValueError(f"{item['name']} source archive exceeds 8 MiB")
        with archive.open("xb") as stream:
            stream.write(data)
        actual_hash = sha256(archive)
        if actual_hash != item["sha256"]:
            raise ValueError(f"{item['name']} source archive SHA-256 mismatch")
        source = sources / item["name"]
        count, expanded = extract_source(data, source, expanded_limit=64 * 1024**2,
                                         entry_limit=10000, member_limit=8 * 1024**2,
                                         archive_mode="r:xz")
        if sum(row["expanded_bytes"] for row in archive_receipts) + expanded > 48 * 1024**2:
            raise ValueError("pinned bootstrap sources exceed the 48 MiB combined expansion limit")
        archive_receipts.append({"name": item["name"], "version": item["version"],
                                 "url": item["url"], "sha256": actual_hash,
                                 "archive_bytes": len(data), "expanded_bytes": expanded,
                                 "entries": count})
        immutable_json(downloads / f"{item['name']}.json", archive_receipts[-1])
        build_dir = builds / item["name"]
        build_dir.mkdir(parents=True, exist_ok=False)
        configure = source / "configure"
        flags = [f"--prefix={prefix}"]
        if item["name"] == "m4":
            flags.append("--disable-nls")
        run_bounded([str(configure), *flags], build_dir, local_env,
                    evidence / f"toolchain-{item['name']}-configure.log", deadline, commands)
        if item["name"] == "automake":
            # Automake's out-of-tree bootstrap writes a temporary fragment under
            # build_dir/t before atomically replacing the source-tree target.
            # Its release archive does not require that build-side directory.
            (build_dir / "t").mkdir(exist_ok=True)
        run_bounded(["make", "-j2"], build_dir, local_env,
                    evidence / f"toolchain-{item['name']}-make.log", deadline, commands)
        run_bounded(["make", "install"], build_dir, local_env,
                    evidence / f"toolchain-{item['name']}-install.log", deadline, commands)

    receipt = {"schema_version": 1, "kind": "owned-source-built-autotools",
               "missing_before_build": missing, "prefix_relative": prefix.relative_to(target).as_posix(),
               "source_archives": archive_receipts,
               "build_command_ids": [row["id"] for row in commands
                                     if "toolchain-" in row["log"]]}
    immutable_json(root / "provenance.json", receipt)
    return local_env, receipt


def run_bounded(argv, cwd, env, log_path, deadline, commands):
    started = time.monotonic()
    started_utc = datetime.now(timezone.utc).isoformat()
    command_id = uuid.uuid4().hex
    with log_path.open("xb") as log:
        process = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        process_group = process.pid
        try:
            while process.poll() is None:
                if time.monotonic() >= deadline:
                    stop_group(process)
                    raise TimeoutError(f"mg build exceeded the shared {MAX_SECONDS}s wall limit")
                if log_path.stat().st_size > MAX_OUTPUT:
                    stop_group(process)
                    raise ValueError(f"mg build output exceeded {MAX_OUTPUT} bytes")
                time.sleep(0.1)
        finally:
            if process.poll() is None:
                stop_group(process)
    group_cleanup = command_group_cleanup(process_group)
    duration = time.monotonic() - started
    size = log_path.stat().st_size
    if size > MAX_OUTPUT:
        raise ValueError(f"mg build output exceeded {MAX_OUTPUT} bytes")
    row = {"id": command_id, "argv": argv, "cwd": str(cwd),
           "pid": process.pid, "process_group": process_group,
           "started_at_utc": started_utc,
           "exit_code": process.returncode, "duration_seconds": round(duration, 4),
           "process_tree_cleanup": group_cleanup,
           "output_bytes": size, "output_sha256": sha256(log_path),
           "log": log_path.relative_to(ROOT).as_posix()}
    commands.append(row)
    if process.returncode != 0:
        raise RuntimeError(f"mg build command failed ({process.returncode}); see {row['log']}")
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-host", choices=("linux", "darwin"), required=True)
    parser.add_argument("--operation-started-epoch", type=float)
    args = parser.parse_args()
    host = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    if host != args.expected_host:
        raise ValueError(f"expected native {args.expected_host}, got {platform.system()}")
    target = RAW / "active" / "mg"
    source = target / "src"
    source.resolve(strict=True).relative_to((RAW / "active").resolve(strict=True))
    owner = json.loads((target / "task-owned.json").read_text(encoding="utf-8"))
    acquired = json.loads((target / "acquisition.json").read_text(encoding="utf-8"))
    provenance = json.loads((DOC / "mg" / "source-provenance.json").read_text(encoding="utf-8"))
    if (owner.get("pin") != PIN or acquired.get("pin") != PIN or
            acquired.get("archive_sha256") != provenance.get("archive_sha256") or
            acquired.get("source_files") != provenance.get("source_file_sha256") or
            acquired.get("build_hooks_executed") is not False):
        raise ValueError("mg source, owner, or prebuild provenance differs from its frozen pin")
    observed = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError(f"linked pinned source path: {path.relative_to(source)}")
        if path.is_file():
            observed[path.relative_to(source).as_posix()] = sha256(path)
    if observed != acquired["source_files"]:
        raise ValueError("pinned source files changed before the first build")

    run_id = uuid.uuid4().hex
    evidence = RAW / "mg" / "build-development" / run_id
    evidence.mkdir(parents=True, exist_ok=False)
    build = target / "build"
    install = target / "install"
    home = target / "home"
    temp = target / "tmp"
    for path in (build, install, home, temp):
        path.mkdir(parents=True, exist_ok=True)
    for path in (build, install, home, temp):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError(f"linked owned build root: {path}")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "HOME": str(home), "USERPROFILE": str(home), "TMPDIR": str(temp),
           "TMP": str(temp), "TEMP": str(temp), "LC_ALL": "C.UTF-8",
           "LANG": "C.UTF-8", "TERM": "xterm-256color", "MAKEFLAGS": "-j2",
           "SOURCE_DATE_EPOCH": "0"}
    if host == "darwin":
        env["LC_ALL"] = "C"
        env["LANG"] = "C"
    prefix = install.resolve()
    commands = []
    toolchain = []
    started_at = datetime.now(timezone.utc).isoformat()
    immutable_json(evidence / "build-start.json", {
        "schema_version": 1, "run_id": run_id, "project": "mg", "pin": PIN,
        "host": host, "architecture": platform.machine(),
        "started_at_utc": started_at, "source_archive_sha256": acquired["archive_sha256"],
        "source_map_sha256": sha256(DOC / "mg" / "source-provenance.json"),
        "wall_limit_seconds": MAX_SECONDS, "output_limit_bytes_per_command": MAX_OUTPUT,
        "build_root": str(build), "install_prefix": str(prefix),
        "scope": "Native source build of the exact pinned mg source. No system package install, default-prefix install, user startup file, or real target file."})
    operation_started_epoch = args.operation_started_epoch or time.time()
    operation_started_utc = datetime.fromtimestamp(operation_started_epoch, timezone.utc).isoformat()
    deadline = time.monotonic() + max(0, MAX_SECONDS - (time.time() - operation_started_epoch))
    try:
        env, toolchain_build = owned_autotools(target, evidence, env, deadline, commands)
        for name, argv in (("compiler", ["cc", "--version"]),
                           ("make", ["make", "--version"]),
                           ("autoreconf", ["autoreconf", "--version"]),
                           ("autoconf", ["autoconf", "--version"]),
                           ("automake", ["automake", "--version"]),
                           ("m4", ["m4", "--version"])):
            row = run_bounded(argv, build, env, evidence / f"toolchain-{name}.log",
                              deadline, commands)
            toolchain.append({"name": name, "argv": argv,
                              "log": row["log"], "output_bytes": row["output_bytes"],
                              "output_sha256": row["output_sha256"]})
        run_bounded(["./autogen.sh"], source, env, evidence / "autogen.log", deadline, commands)
        configure = str(source / "configure")
        run_bounded([configure, f"--prefix={prefix}", f"--sysconfdir={prefix / 'etc'}",
                     f"--datadir={prefix / 'share'}", f"--docdir={prefix / 'share/doc/mg'}"],
                    build, env, evidence / "configure.log", deadline, commands)
        run_bounded(["make", "-j2"], build, env, evidence / "make.log", deadline, commands)
        run_bounded(["make", "install-strip"], build, env,
                    evidence / "install.log", deadline, commands)
        binary = prefix / "bin" / "mg"
        binary.resolve(strict=True).relative_to(target.resolve(strict=True))
        digest = sha256(binary)
        run_bounded([str(binary), "-h"], build, env, evidence / "help-smoke.log", deadline, commands)
        installed = {}
        for path in sorted(install.rglob("*")):
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                raise ValueError(f"linked install output: {path.relative_to(install)}")
            if path.is_file():
                path.resolve(strict=True).relative_to(target.resolve(strict=True))
                installed[path.relative_to(install).as_posix()] = {
                    "bytes": path.stat().st_size, "sha256": sha256(path)}
        if installed.get("bin/mg", {}).get("sha256") != digest:
            raise ValueError("installed mg binary differs from smoke-tested executable")
        completed = datetime.now(timezone.utc).isoformat()
        receipt = {"schema_version": 1, "project": "mg", "pin": PIN,
                   "host": host, "architecture": platform.machine(),
                   "source_archive_sha256": acquired["archive_sha256"],
                   "source_map_count": len(observed),
                   "binary_relative_path": binary.relative_to(target).as_posix(),
                   "binary_sha256": digest, "binary_bytes": binary.stat().st_size,
                   "install_prefix_relative": install.relative_to(target).as_posix(),
                   "installed_files": installed, "toolchain": toolchain,
                   "toolchain_build": toolchain_build,
                   "commands": commands,
                   "duration_seconds": round(time.time() - operation_started_epoch, 4),
                   "build_started_at_utc": started_at,
                   "operation_started_at_utc": operation_started_utc,
                   "finished_at_utc": completed,
                   "process_tree_timeout_cleanup": "not needed; every command exited naturally",
                   "upstream_tests": "none declared in the reviewed source; native build, install-strip and -h smoke only",
                   "evidence_root": evidence.relative_to(ROOT).as_posix()}
        immutable_json(target / "build.json", receipt)
        immutable_json(target / "runtime.json", {"kind": "native", "native": str(binary.resolve()),
                                                  "native_sha256": digest,
                                                  "source_pin": PIN, "build_sha256": sha256(target / "build.json")})
        immutable_json(evidence / "build-finished.json", receipt)
        print(f"Built mg {PIN} on {host} ({platform.machine()}): {digest}; {receipt['duration_seconds']}s")
    except Exception as error:
        immutable_json(evidence / "build-failed.json", {
            "schema_version": 1, "run_id": run_id, "project": "mg", "pin": PIN,
            "host": host, "commands": commands, "error_type": type(error).__name__,
            "error": str(error)[:2048], "finished_at_utc": datetime.now(timezone.utc).isoformat(),
            "target_source_retained": True, "scope": "Failed build attempt retained; no admission credit."})
        raise


if __name__ == "__main__":
    main()
