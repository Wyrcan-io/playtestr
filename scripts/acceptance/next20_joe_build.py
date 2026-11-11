"""Build the reviewed pinned JOE source in an owned native Linux/macOS tree."""
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
from next20_mg_build import MAX_OUTPUT, run_bounded
from readiness_evidence import immutable_json, sha256

PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
MAX_SECONDS = 20 * 60
MAX_FILES = 10000
MAX_BYTES = 64 * 1024**2


def require(value, message):
    if not value:
        raise ValueError(message)


def safe_tree(root, *, allow_install_aliases=False):
    count = total = 0
    for directory, names, files in os.walk(root, followlinks=False):
        base = Path(directory)
        for name in names + files:
            path = base / name
            if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
                allowed = (allow_install_aliases and path.parent == root / "install/bin" and
                           path.name in {"jmacs", "jstar", "rjoe", "jpico"} and
                           path.is_symlink() and os.readlink(path) == "joe")
                if not allowed:
                    raise ValueError("linked path under owned JOE tree: " + str(path))
            if path.is_file():
                count += 1
                total += path.stat().st_size
                if count > MAX_FILES or total > MAX_BYTES:
                    raise ValueError("owned JOE tree exceeds file/size bounds")
    return count, total


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--expected-host", choices=("linux", "darwin"), required=True)
    parser.add_argument("--operation-started-epoch", type=int)
    args = parser.parse_args()
    host = "darwin" if platform.system() == "Darwin" else "linux" if platform.system() == "Linux" else "other"
    arch = platform.machine().lower()
    require(host == args.expected_host and arch in {"x86_64", "amd64", "arm64", "aarch64"},
            "actual native host/architecture differs from declaration")
    target = RAW / "active/joe"
    source = target / "src"
    require(source.is_dir() and (target / "task-owned.json").is_file(), "pinned JOE source-only acquisition is absent")
    owner = json.loads((target / "task-owned.json").read_text(encoding="utf-8"))
    acquisition = json.loads((target / "acquisition.json").read_text(encoding="utf-8"))
    require(owner["slug"] == "joe" and owner["pin"] == PIN and acquisition["pin"] == PIN and
            acquisition["repository"] == "joe-editor/joe", "active JOE source owner or pin differs")
    prefix = target.resolve()
    build_source = target / "build-source"
    install_prefix = target / "install"
    logs = target / "build-logs"
    home = target / "home"
    temp = target / "tmp"
    for path in (build_source, install_prefix, logs, home, temp):
        if path.exists():
            raise ValueError("preserve an existing JOE build output: " + str(path))
    safe_tree(source)
    shutil.copytree(source, build_source, symlinks=False)
    for path in (logs, home, temp):
        path.mkdir()
    require(build_source.resolve().is_relative_to(prefix) and install_prefix.resolve().is_relative_to(prefix),
            "JOE build or install path escaped owned root")
    tools = {}
    for name in ("autoreconf", "make", "cc", "sed", "install"):
        resolved = shutil.which(name)
        require(resolved is not None, "required native build tool missing: " + name)
        tools[name] = str(Path(resolved).resolve(strict=True))
    env = {key: os.environ[key] for key in ("PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env.update({"HOME": str(home), "TMPDIR": str(temp), "TMP": str(temp), "TEMP": str(temp),
                "LC_ALL": "C", "LANG": "C", "MAKEFLAGS": "", "MFLAGS": ""})
    command_rows = []
    started = time.monotonic()
    started_utc = datetime.now(timezone.utc).isoformat()
    elapsed_before = max(0, int(time.time()) - args.operation_started_epoch) if args.operation_started_epoch is not None else 0
    remaining = MAX_SECONDS - elapsed_before
    require(remaining > 0, "JOE acquisition exhausted the shared operation budget")
    deadline = started + remaining
    commands = [
        ("autoconf-version", [tools["autoreconf"], "--version"], build_source),
        ("make-version", [tools["make"], "--version"], build_source),
        ("compiler-version", [tools["cc"], "--version"], build_source),
        ("autoreconf", [tools["autoreconf"], "-fi"], build_source),
        ("configure", [str(build_source / "configure"), "--prefix=" + str(install_prefix)], build_source),
        ("make", [tools["make"], "-j2"], build_source),
        ("install", [tools["make"], "install"], build_source),
    ]
    for index, (name, argv, cwd) in enumerate(commands, 1):
        if time.monotonic() >= deadline:
            raise TimeoutError("JOE native build exceeded its shared twenty-minute budget")
        log = logs / f"{index:02d}-{name}.log"
        row = run_bounded(argv, cwd, env, log, deadline,
                          command_rows, operation="JOE " + name)
        require(log.stat().st_size <= MAX_OUTPUT, "JOE build output exceeded cap")
    binary = install_prefix / "bin/joe"
    require(binary.is_file() and not binary.is_symlink(), "JOE install did not produce an owned joe executable")
    files, total = safe_tree(target, allow_install_aliases=True)
    runtime = {"schema_version": 1, "project": "joe", "kind": "native",
               "native": str(binary.resolve(strict=True)), "native_sha256": sha256(binary),
               "host": host, "architecture": arch, "project_admission_credit": 0}
    immutable_json(target / "runtime.json", runtime)
    build = {"schema_version": 1, "project": "joe", "repository": "joe-editor/joe", "pin": PIN,
             "host": host, "architecture": arch, "source_archive_sha256": acquisition["archive_sha256"],
             "source_file_count": acquisition["entries"],
             "source_map_sha256": hashlib.sha256(json.dumps(acquisition["source_files"], sort_keys=True,
                 ensure_ascii=True, separators=(",", ":")).encode()).hexdigest(),
             "binary_relative_path": "install/bin/joe", "binary_sha256": sha256(binary),
             "binary_bytes": binary.stat().st_size, "build_started_at_utc": started_utc,
             "build_seconds": time.monotonic() - started, "tool_paths": tools,
             "relative_variant_links": {name: "joe" for name in ("jmacs", "jstar", "rjoe", "jpico")
                                        if (install_prefix / "bin" / name).is_symlink()},
             "commands": command_rows, "owned_tree_files": files, "owned_tree_bytes": total,
             "upstream_test_target": "none declared in pinned Automake files",
             "project_admission_credit": 0,
             "scope": "Native source build and staged install only; no qualification scenarios or admission credit."}
    immutable_json(target / "build.json", build)
    if args.operation_started_epoch is not None and int(time.time()) - args.operation_started_epoch > MAX_SECONDS:
        raise TimeoutError("JOE acquisition and build exceeded the shared declared operation budget")
    print("Built pinned JOE:", host, arch, "binary", build["binary_sha256"], "seconds", round(build["build_seconds"], 2))


if __name__ == "__main__":
    main()
