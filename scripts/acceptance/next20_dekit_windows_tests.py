"""Run dekit's locked Windows test lane with isolated env and checked cleanup."""
from datetime import datetime, timezone
import hashlib
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = RAW / "active" / "dekit"
SOURCE = PROJECT / "src"
TARGET = PROJECT / "cargo-target"
ATTEMPT = "v3"
TEST_ARGS = sys.argv[1:]
if TEST_ARGS and TEST_ARGS[0].startswith("--attempt="):
    ATTEMPT = TEST_ARGS.pop(0).split("=", 1)[1]
TEST_ROOT = PROJECT / f"windows-test-{ATTEMPT}"
LOG = TEST_ROOT / "cargo-test.log"
RECEIPT = TEST_ROOT / "receipt.json"
PROCESS_RECEIPT = TEST_ROOT / "process-cleanup.json"
TEMP_RECEIPT = TEST_ROOT / "temp-cleanup.json"
MAX_SECONDS = 20 * 60
MAX_LOG_BYTES = 64 * 1024**2


def main() -> None:
    if RECEIPT.exists() or TEST_ROOT.exists():
        raise ValueError("preserve any existing dekit Windows test attempt")
    if not SOURCE.is_dir() or not TARGET.is_dir():
        raise ValueError("pinned source or owned Cargo target is absent")
    TEST_ROOT.mkdir()
    sandbox_home = PROJECT / "home"
    temp_parent = Path(os.environ.get(
        "NEXT20_DEKIT_TEMP_PARENT", os.environ.get("TEMP", str(PROJECT / "tmp"))
    )).resolve()
    temp = temp_parent / f"playtestr-next20-dekit-{ATTEMPT}"
    if temp.exists():
        raise ValueError(f"task-owned external test temp root already exists: {temp}")
    for directory in (
        sandbox_home / "appdata",
        sandbox_home / "localappdata",
        sandbox_home / "xdg-config",
        sandbox_home / "xdg-data",
        sandbox_home / "xdg-cache",
        sandbox_home / "xdg-runtime",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    env_names = (
        "PATH", "SystemRoot", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATHEXT",
        "HOMEDRIVE", "HOMEPATH", "OS", "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_IDENTIFIER", "NUMBER_OF_PROCESSORS", "COMPUTERNAME",
    )
    env = {key: os.environ[key] for key in env_names if key in os.environ}
    env.update({
        "HOME": str(sandbox_home),
        "USERPROFILE": str(sandbox_home),
        "APPDATA": str(sandbox_home / "appdata"),
        "LOCALAPPDATA": str(sandbox_home / "localappdata"),
        "XDG_CONFIG_HOME": str(sandbox_home / "xdg-config"),
        "XDG_DATA_HOME": str(sandbox_home / "xdg-data"),
        "XDG_CACHE_HOME": str(sandbox_home / "xdg-cache"),
        "XDG_RUNTIME_DIR": str(sandbox_home / "xdg-runtime"),
        "CARGO_HOME": str(PROJECT / "cargo-home"),
        "CARGO_TARGET_DIR": str(TARGET),
        "RUSTUP_HOME": os.environ.get("RUSTUP_HOME", str(Path.home() / ".rustup")),
        "CARGO_NET_OFFLINE": "true",
        "CARGO_INCREMENTAL": "0",
        "CARGO_PROFILE_DEV_DEBUG": "0",
        "CARGO_PROFILE_TEST_DEBUG": "0",
        "CARGO_PROFILE_BUILD_OVERRIDE_DEBUG": "0",
        "CARGO_TERM_COLOR": "never",
    })
    temp.mkdir(parents=False)
    env["TEMP"] = str(temp)
    env["TMP"] = str(temp)
    command = [
        "cargo", "test", "--workspace", "--locked", "--offline",
        "--target", "x86_64-pc-windows-msvc",
        *TEST_ARGS,
    ]
    started = datetime.now(timezone.utc)
    start_clock = time.monotonic()
    vs_dev_cmd = Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/Tools/VsDevCmd.bat")
    if not vs_dev_cmd.is_file():
        raise ValueError("verified Visual Studio Build Tools environment script is absent")
    short_path = ctypes.create_unicode_buffer(1024)
    short_path_length = ctypes.windll.kernel32.GetShortPathNameW(
        str(vs_dev_cmd), short_path, len(short_path)
    )
    vs_dev_command = short_path.value if short_path_length else str(vs_dev_cmd)
    bootstrap = subprocess.run(
        [env["COMSPEC"], "/d", "/c",
         f"call {vs_dev_command} -arch=x64 -host_arch=x64 >nul && set"],
        cwd=SOURCE, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=60, check=False,
    )
    if bootstrap.returncode:
        raise RuntimeError("Visual Studio environment initialization failed")
    for line in bootstrap.stdout.decode("utf-8", "replace").splitlines():
        key, separator, value = line.partition("=")
        if separator and key:
            env[key] = value
    process = subprocess.Popen(
        command,
        cwd=SOURCE,
        env=env,
        stdout=LOG.open("wb"),
        stderr=subprocess.STDOUT,
        creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
    )
    timed_out = False
    log_limited = False
    while process.poll() is None:
        if LOG.stat().st_size > MAX_LOG_BYTES:
            log_limited = True
            break
        if time.monotonic() - start_clock > MAX_SECONDS:
            timed_out = True
            break
        time.sleep(1)
    if timed_out or log_limited:
        taskkill = Path(env["SystemRoot"]) / "System32" / "taskkill.exe"
        subprocess.run(
            [str(taskkill), "/PID", str(process.pid), "/T", "/F"],
            env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            check=False, timeout=30,
        )
    exit_code = process.wait(timeout=30)
    elapsed = time.monotonic() - start_clock
    log_hash = sha256(LOG)
    script = TEST_ROOT / "cleanup-target-processes.ps1"
    script.write_text(
        "$ErrorActionPreference='Stop'\n"
        "$root=[IO.Path]::GetFullPath($args[0]).TrimEnd([char]92)+[char]92\n"
        "$rows=@(Get-Process | Where-Object { try { $_.Path -and $_.Path.StartsWith($root,[StringComparison]::OrdinalIgnoreCase) } catch { $false } } | Select-Object Id,Name,Path,StartTime)\n"
        "foreach($row in $rows){ Stop-Process -Id $row.Id -Force -ErrorAction SilentlyContinue }\n"
        "$remaining=@(Get-Process | Where-Object { try { $_.Path -and $_.Path.StartsWith($root,[StringComparison]::OrdinalIgnoreCase) } catch { $false } } | Select-Object Id,Name,Path,StartTime)\n"
        "$result=[ordered]@{schema_version=1;target_root=$root;found_before=$rows;remaining=$remaining;all_target_processes_absent=($remaining.Count -eq 0)}\n"
        "$result|ConvertTo-Json -Depth 5|Set-Content -LiteralPath $args[1] -Encoding UTF8\n"
        "if($remaining.Count){exit 2}\n",
        encoding="utf-8",
    )
    ps = Path(env["SystemRoot"]) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    cleanup = subprocess.run(
        [str(ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(script), str(TARGET), str(PROCESS_RECEIPT)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=60, check=False,
    )
    if cleanup.stdout:
        (TEST_ROOT / "cleanup-output.log").write_bytes(cleanup.stdout[:1024 * 1024])
    cleanup_receipt = json.loads(PROCESS_RECEIPT.read_text(encoding="utf-8-sig")) if PROCESS_RECEIPT.exists() else {}
    leftovers = []
    leftover_bytes = 0
    for path in sorted(temp.rglob("*")):
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            raise ValueError(f"linked path appeared under owned test temp: {path}")
        if path.is_file():
            size = path.stat().st_size
            leftovers.append({"path": path.relative_to(temp).as_posix(), "bytes": size, "sha256": sha256(path)})
            leftover_bytes += size
    immutable_json(TEMP_RECEIPT, {
        "schema_version": 1,
        "root": str(temp),
        "files_before_cleanup": leftovers,
        "file_count": len(leftovers),
        "bytes_before_cleanup": leftover_bytes,
        "all_paths_hashed_before_cleanup": True,
        "scope": "Exclusive task-owned Windows temp root used only by this dekit cargo test invocation.",
    })
    if cleanup_receipt.get("all_target_processes_absent") is True:
        resolved_temp = temp.resolve(strict=True)
        if resolved_temp.parent != temp_parent or resolved_temp.name != f"playtestr-next20-dekit-{ATTEMPT}":
            raise ValueError("task-owned Windows temp cleanup target escaped its parent")
        shutil.rmtree(resolved_temp)
    temp_absent = not temp.exists()
    result = {
        "schema_version": 1,
        "project": "dekit",
        "source_pin": "da2acca491298c902d3f2e828204b98087123323",
        "source_tree_sha256": "9241a9dfc5797ce54db093471be03e6e5cf55af91c2b557e51dac48fba7e7fcf",
        "host": "windows-x86_64-pc-windows-msvc",
        "command": command,
        "test_filter": TEST_ARGS,
        "working_directory": str(SOURCE),
        "cargo_home": env["CARGO_HOME"],
        "cargo_target_dir": env["CARGO_TARGET_DIR"],
        "network": "offline; --locked",
        "environment": "Allowlisted toolchain/system variables; HOME, USERPROFILE, TEMP, APPDATA, LOCALAPPDATA and XDG roots are task-owned; user credentials and ambient application secrets are excluded.",
        "started_at_utc": started.isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "log_limited": log_limited,
        "log_bytes": LOG.stat().st_size,
        "log_sha256": log_hash,
        "log": str(LOG.relative_to(ROOT)),
        "process_cleanup": str(PROCESS_RECEIPT.relative_to(ROOT)),
        "owned_target_processes_terminated": cleanup_receipt.get("found_before", []),
        "all_owned_target_processes_absent": cleanup_receipt.get("all_target_processes_absent", False),
        "process_cleanup_exit_code": cleanup.returncode,
        "external_temp_root": str(temp),
        "external_temp_manifest": str(TEMP_RECEIPT.relative_to(ROOT)),
        "external_temp_file_count": len(leftovers),
        "external_temp_bytes_before_cleanup": leftover_bytes,
        "external_temp_removed_after_hashing": temp_absent,
        "receipt": str(RECEIPT.relative_to(ROOT)),
        "scope": "Upstream Rust workspace tests only; no release, canary, installer, updater or external application workflow.",
    }
    immutable_json(RECEIPT, result)
    print(json.dumps({key: result[key] for key in (
        "exit_code", "elapsed_seconds", "timed_out", "log_limited", "log_bytes",
        "all_owned_target_processes_absent", "process_cleanup_exit_code", "receipt",
    )}, sort_keys=True))
    if (timed_out or log_limited or exit_code or cleanup.returncode or
            not cleanup_receipt.get("all_target_processes_absent") or not temp_absent):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
