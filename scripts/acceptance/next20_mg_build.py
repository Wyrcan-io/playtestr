"""Build the reviewed pinned mg source inside its one owned active target."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import uuid

from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256


PIN = "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66"
MAX_SECONDS = 20 * 60
MAX_OUTPUT = 4 * 1024 * 1024


def stop_group(process):
    stop_process_group(process.pid)
    if process.poll() is None:
        process.wait(timeout=5)


def process_group_exists(process_group):
    try:
        os.killpg(process_group, 0)
        return True
    except ProcessLookupError:
        return False


def stop_process_group(process_group):
    try:
        os.killpg(process_group, signal.SIGTERM)
    except ProcessLookupError:
        return
    try:
        deadline = time.monotonic() + 5
        while process_group_exists(process_group) and time.monotonic() < deadline:
            time.sleep(0.05)
        if process_group_exists(process_group):
            os.killpg(process_group, signal.SIGKILL)
            deadline = time.monotonic() + 5
            while process_group_exists(process_group) and time.monotonic() < deadline:
                time.sleep(0.05)
        if process_group_exists(process_group):
            raise RuntimeError(f"owned build process group {process_group} survived termination")
    except ProcessLookupError:
        pass


def command_group_cleanup(process_group):
    if process_group_exists(process_group):
        stop_process_group(process_group)
        return "remaining owned process group terminated and absence confirmed"
    return "no owned descendants remained after command exit"


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
                   "installed_files": installed, "commands": commands,
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
