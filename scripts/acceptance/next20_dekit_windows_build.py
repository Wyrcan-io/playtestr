"""Rebuild pinned dekit on Windows with isolated, locked toolchain inputs."""
from datetime import datetime, timezone
import ctypes
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = RAW / "active" / "dekit"
SOURCE = PROJECT / "src"
TARGET = PROJECT / "cargo-target"
ATTEMPT = PROJECT / "build-windows-v3"
LOG = ATTEMPT / "cargo-build.log"
RECEIPT = ATTEMPT / "receipt.json"
PROCESS_RECEIPT = ATTEMPT / "process-cleanup.json"
MAX_SECONDS = 20 * 60
MAX_LOG_BYTES = 64 * 1024**2


def main() -> None:
    if ATTEMPT.exists():
        raise ValueError("preserve existing dekit Windows rebuild attempt")
    old_build = json.loads((PROJECT / "build.json").read_text(encoding="utf-8"))
    source_review_path = ROOT / "docs" / "validation" / "runner-readiness-next-twenty-project-pass" / "dekit" / "source-review-v1.json"
    source_review = json.loads(source_review_path.read_text(encoding="utf-8"))
    if old_build.get("pin") != "da2acca491298c902d3f2e828204b98087123323":
        raise ValueError("pinned dekit build receipt differs")
    ATTEMPT.mkdir()
    home = PROJECT / "home"
    temp = PROJECT / "tmp"
    for directory in (home / "appdata", home / "localappdata", home / "xdg-config",
                      home / "xdg-data", home / "xdg-cache", home / "xdg-runtime", temp):
        directory.mkdir(parents=True, exist_ok=True)
    keys = (
        "PATH", "SystemRoot", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATHEXT",
        "HOMEDRIVE", "HOMEPATH", "OS", "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_IDENTIFIER", "NUMBER_OF_PROCESSORS", "COMPUTERNAME",
    )
    env = {key: os.environ[key] for key in keys if key in os.environ}
    env.update({
        "HOME": str(home),
        "USERPROFILE": str(home),
        "APPDATA": str(home / "appdata"),
        "LOCALAPPDATA": str(home / "localappdata"),
        "TEMP": str(temp),
        "TMP": str(temp),
        "XDG_CONFIG_HOME": str(home / "xdg-config"),
        "XDG_DATA_HOME": str(home / "xdg-data"),
        "XDG_CACHE_HOME": str(home / "xdg-cache"),
        "XDG_RUNTIME_DIR": str(home / "xdg-runtime"),
        "CARGO_HOME": str(PROJECT / "cargo-home"),
        "CARGO_TARGET_DIR": str(TARGET),
        "RUSTUP_HOME": os.environ.get("RUSTUP_HOME", str(Path.home() / ".rustup")),
        "CARGO_NET_OFFLINE": "true",
        "CARGO_INCREMENTAL": "0",
        "CARGO_PROFILE_DEV_DEBUG": "0",
        "CARGO_PROFILE_BUILD_OVERRIDE_DEBUG": "0",
        "CARGO_TERM_COLOR": "never",
    })
    vs_dev_cmd = Path("C:/Program Files (x86)/Microsoft Visual Studio/2022/BuildTools/Common7/Tools/VsDevCmd.bat")
    short_path = ctypes.create_unicode_buffer(1024)
    if not vs_dev_cmd.is_file():
        raise ValueError("Visual Studio Build Tools environment script is absent")
    short_length = ctypes.windll.kernel32.GetShortPathNameW(str(vs_dev_cmd), short_path, len(short_path))
    vs_command = short_path.value if short_length else str(vs_dev_cmd)
    bootstrap = subprocess.run(
        [env["COMSPEC"], "/d", "/c", f"call {vs_command} -arch=x64 -host_arch=x64 >nul && set"],
        cwd=SOURCE, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=60, check=False,
    )
    if bootstrap.returncode:
        raise RuntimeError("Visual Studio environment initialization failed")
    for line in bootstrap.stdout.decode("utf-8", "replace").splitlines():
        key, separator, value = line.partition("=")
        if separator and key:
            env[key] = value
    command = ["cargo", "build", "--workspace", "--locked", "--offline",
               "--target", "x86_64-pc-windows-msvc"]
    log_handle = LOG.open("wb")
    started = datetime.now(timezone.utc)
    start_clock = time.monotonic()
    process = subprocess.Popen(command, cwd=SOURCE, env=env, stdout=log_handle,
                               stderr=subprocess.STDOUT,
                               creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
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
        subprocess.run([str(taskkill), "/PID", str(process.pid), "/T", "/F"], env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                       check=False, timeout=30)
    exit_code = process.wait(timeout=30)
    log_handle.close()
    elapsed = time.monotonic() - start_clock
    binary = TARGET / "x86_64-pc-windows-msvc" / "debug" / "dekit.exe"
    binary_hash = sha256(binary) if binary.is_file() else None
    cargo_path = shutil.which("cargo", path=env.get("PATH"))
    rustc_path = shutil.which("rustc", path=env.get("PATH"))
    ps = Path(env["SystemRoot"]) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    cleanup_script = ATTEMPT / "cleanup-target-processes.ps1"
    cleanup_script.write_text(
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
    cleanup = subprocess.run(
        [str(ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(cleanup_script), str(TARGET), str(PROCESS_RECEIPT)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60, check=False,
    )
    process_info = json.loads(PROCESS_RECEIPT.read_text(encoding="utf-8-sig")) if PROCESS_RECEIPT.exists() else {}
    rustc_version = subprocess.run(["rustc", "--version", "--verbose"], cwd=SOURCE,
                                   env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   timeout=30, check=False)
    result = {
        "schema_version": 1,
        "project": "dekit",
        "pin": old_build["pin"],
        "source_archive_sha256": old_build["source_archive_sha256"],
        "source_tree_sha256": source_review["primary_tree_sha256"],
        "source_review_sha256": sha256(source_review_path),
        "host": "windows-x86_64-pc-windows-msvc",
        "target": "x86_64-pc-windows-msvc",
        "command": command,
        "network": "offline; --locked",
        "environment": "Allowlisted system/tool paths; HOME, USERPROFILE, APPDATA, LOCALAPPDATA, TEMP and XDG roots task-owned; credentials excluded.",
        "started_at_utc": started.isoformat(),
        "elapsed_seconds": round(elapsed, 3),
        "exit_code": exit_code,
        "timed_out": timed_out,
        "log_limited": log_limited,
        "log": str(LOG.relative_to(ROOT)),
        "log_bytes": LOG.stat().st_size,
        "log_sha256": sha256(LOG),
        "binary": str(binary.relative_to(ROOT)) if binary.is_file() else None,
        "binary_bytes": binary.stat().st_size if binary.is_file() else None,
        "binary_sha256": binary_hash,
        "cargo": cargo_path,
        "cargo_sha256": sha256(Path(cargo_path)) if cargo_path else None,
        "rustc": rustc_path,
        "rustc_sha256": sha256(Path(rustc_path)) if rustc_path else None,
        "rustc_version": rustc_version.stdout.decode("utf-8", "replace").strip(),
        "visual_studio_linker": shutil.which("link", path=env.get("PATH")),
        "visual_studio_environment": env.get("VCToolsInstallDir"),
        "process_cleanup": str(PROCESS_RECEIPT.relative_to(ROOT)),
        "all_target_processes_absent": process_info.get("all_target_processes_absent", False),
        "cleanup_exit_code": cleanup.returncode,
        "scope": "Native Windows workspace build from exact pinned source; no test suite or application scenario.",
    }
    immutable_json(RECEIPT, result)
    print(json.dumps({"exit_code": exit_code, "elapsed_seconds": result["elapsed_seconds"],
                      "binary_sha256": binary_hash, "all_target_processes_absent": result["all_target_processes_absent"],
                      "receipt": str(RECEIPT.relative_to(ROOT))}, sort_keys=True))
    if (exit_code or timed_out or log_limited or cleanup.returncode or
            not result["all_target_processes_absent"] or not binary_hash):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
