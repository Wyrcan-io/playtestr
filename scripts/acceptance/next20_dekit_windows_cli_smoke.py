"""Exercise one bounded dekit CLI task lifecycle in an owned workspace."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import time

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = RAW / "active" / "dekit"
ATTEMPT = PROJECT / "windows-cli-smoke-v1"
WORK = ATTEMPT / "work"
HOME = ATTEMPT / "home"
TEMP = ATTEMPT / "tmp"
RECEIPT = ATTEMPT / "receipt.json"
PROCESS_RECEIPT = ATTEMPT / "process-cleanup.json"
MAX_SECONDS = 15


def main() -> None:
    if ATTEMPT.exists():
        raise ValueError("preserve existing dekit CLI smoke attempt")
    binary = PROJECT / "cargo-target" / "x86_64-pc-windows-msvc" / "debug" / "dekit.exe"
    build = PROJECT / "build-windows-v3" / "receipt.json"
    if not build.is_file():
        build = PROJECT / "build.json"
    if not binary.is_file() or not build.is_file():
        raise ValueError("pinned Windows dekit executable/build receipt is absent")
    exe_hash = sha256(binary)
    build_receipt = json.loads(build.read_text(encoding="utf-8"))
    if build_receipt.get("binary_sha256") != exe_hash:
        raise ValueError("dekit executable differs from pinned build receipt")
    for directory in (WORK, HOME / "appdata", HOME / "localappdata",
                      HOME / "xdg-config", HOME / "xdg-data", HOME / "xdg-cache",
                      HOME / "xdg-runtime", TEMP):
        directory.mkdir(parents=True)
    config = (
        "tasks:\n"
        "  greeting:\n"
        "    cmd: [cmd.exe, /d, /c, \"echo READY & timeout /t 3 /nobreak > nul\"]\n"
        "    autostart: true\n"
        "    ready: {log: READY}\n"
    ).encode("utf-8")
    config_path = WORK / "dekit.yaml"
    config_path.write_bytes(config)
    env_keys = (
        "PATH", "SystemRoot", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATHEXT",
        "HOMEDRIVE", "HOMEPATH", "OS", "PROCESSOR_ARCHITECTURE",
        "PROCESSOR_IDENTIFIER", "NUMBER_OF_PROCESSORS",
    )
    env = {key: os.environ[key] for key in env_keys if key in os.environ}
    env.update({
        "HOME": str(HOME),
        "USERPROFILE": str(HOME),
        "APPDATA": str(HOME / "appdata"),
        "LOCALAPPDATA": str(HOME / "localappdata"),
        "TEMP": str(TEMP),
        "TMP": str(TEMP),
        "XDG_CONFIG_HOME": str(HOME / "xdg-config"),
        "XDG_DATA_HOME": str(HOME / "xdg-data"),
        "XDG_CACHE_HOME": str(HOME / "xdg-cache"),
        "XDG_RUNTIME_DIR": str(HOME / "xdg-runtime"),
    })
    prefix = [str(binary), "--chdir", str(WORK)]
    invocations = []
    started = datetime.now(timezone.utc)
    deadline = time.monotonic() + MAX_SECONDS
    for label, args in (
        ("up", ["up"]),
        ("list", ["ls"]),
        ("screen", ["screen", "greeting"]),
        ("down", ["down"]),
    ):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("dekit CLI lifecycle exceeded total deadline")
        command = prefix + args
        result = subprocess.run(
            command, cwd=WORK, env=env, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, timeout=min(10, remaining), check=False,
        )
        stdout = result.stdout.decode("utf-8", "replace")
        stderr = result.stderr.decode("utf-8", "replace")
        invocations.append({
            "label": label,
            "command": command,
            "exit_code": result.returncode,
            "stdout": stdout,
            "stderr": stderr,
        })
    ps = Path(env["SystemRoot"]) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    cleanup_script = ATTEMPT / "cleanup-owned-processes.ps1"
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
        [str(ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(cleanup_script), str(PROJECT / "cargo-target"), str(PROCESS_RECEIPT)],
        env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=60, check=False,
    )
    process_receipt = json.loads(PROCESS_RECEIPT.read_text(encoding="utf-8-sig")) if PROCESS_RECEIPT.exists() else {}
    observed = {
        "schema_version": 1,
        "project": "dekit",
        "pin": "da2acca491298c902d3f2e828204b98087123323",
        "host": "native-windows-x86_64-pc-windows-msvc",
        "executable": str(binary.relative_to(ROOT)),
        "executable_sha256": exe_hash,
        "build_receipt_sha256": sha256(build),
        "workspace": str(WORK.relative_to(ROOT)),
        "config_sha256": sha256(config_path),
        "environment": "Allowlisted system/tool paths; HOME, USERPROFILE, APPDATA, LOCALAPPDATA, TEMP and XDG roots task-owned; credentials excluded.",
        "started_at_utc": started.isoformat(),
        "invocations": invocations,
        "positive_task_evidence": (
            invocations[0]["exit_code"] == 0 and
            any(row["label"] == "list" and "greeting" in row["stdout"] for row in invocations) and
            any(row["label"] == "screen" and "READY" in row["stdout"] for row in invocations)
        ),
        "process_cleanup": str(PROCESS_RECEIPT.relative_to(ROOT)),
        "owned_processes_terminated": process_receipt.get("found_before", []),
        "all_owned_processes_absent": process_receipt.get("all_target_processes_absent", False),
        "cleanup_exit_code": cleanup.returncode,
        "scope": "One synthetic, finite command task using the pinned binary; CLI smoke only, no TUI, native cell or admission credit.",
    }
    immutable_json(RECEIPT, observed)
    print(json.dumps({
        "exit_codes": {row["label"]: row["exit_code"] for row in invocations},
        "positive_task_evidence": observed["positive_task_evidence"],
        "all_owned_processes_absent": observed["all_owned_processes_absent"],
        "cleanup_exit_code": cleanup.returncode,
        "receipt": str(RECEIPT.relative_to(ROOT)),
    }, sort_keys=True))
    if (any(row["exit_code"] for row in invocations) or not observed["positive_task_evidence"] or
            cleanup.returncode or not observed["all_owned_processes_absent"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
