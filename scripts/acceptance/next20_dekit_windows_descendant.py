"""Probe dekit's Windows process-tree cleanup with an owned nested child."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = RAW / "active" / "dekit"
ATTEMPT = PROJECT / "windows-descendant-cleanup-v2"
WORK = ATTEMPT / "work"
HOME = ATTEMPT / "home"
TEMP = ATTEMPT / "tmp"
RECEIPT = ATTEMPT / "receipt.json"
PROCESS_RECEIPT = ATTEMPT / "process-receipt.json"
MAX_SECONDS = 30


def main() -> None:
    if ATTEMPT.exists():
        raise ValueError("preserve existing dekit descendant cleanup attempt")
    binary = PROJECT / "cargo-target" / "x86_64-pc-windows-msvc" / "debug" / "dekit.exe"
    build = PROJECT / "build-windows-v3" / "receipt.json"
    if not binary.is_file() or not build.is_file() or sha256(binary) != json.loads(build.read_text())["binary_sha256"]:
        raise ValueError("current dekit executable is not bound to the pinned rebuild")
    for directory in (WORK, HOME / "appdata", HOME / "localappdata", HOME / "xdg-config",
                      HOME / "xdg-data", HOME / "xdg-cache", HOME / "xdg-runtime", TEMP):
        directory.mkdir(parents=True)
    script = WORK / "task.ps1"
    script.write_text(
        "$ErrorActionPreference='Stop'\n"
        "$exe=Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'\n"
        "$child=Start-Process -FilePath $exe -ArgumentList '-NoProfile -Command \"Start-Sleep -Seconds 20\"' -PassThru -WindowStyle Hidden\n"
        "[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'child.pid'),[string]$child.Id)\n"
        "[IO.File]::WriteAllText((Join-Path $PSScriptRoot 'parent.pid'),[string]$PID)\n"
        "Wait-Process -Id $child.Id\n",
        encoding="utf-8",
    )
    config = (
        "tasks:\n"
        "  nested:\n"
        "    cmd: [powershell.exe, -NoProfile, -ExecutionPolicy, Bypass, -File, task.ps1]\n"
        "    autostart: true\n"
        "    ready: {file: parent.pid}\n"
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
        "HOME": str(HOME), "USERPROFILE": str(HOME),
        "APPDATA": str(HOME / "appdata"), "LOCALAPPDATA": str(HOME / "localappdata"),
        "TEMP": str(TEMP), "TMP": str(TEMP),
        "XDG_CONFIG_HOME": str(HOME / "xdg-config"),
        "XDG_DATA_HOME": str(HOME / "xdg-data"),
        "XDG_CACHE_HOME": str(HOME / "xdg-cache"),
        "XDG_RUNTIME_DIR": str(HOME / "xdg-runtime"),
    })
    prefix = [str(binary), "--chdir", str(WORK)]
    invocations = []
    start = time.monotonic()
    started = datetime.now(timezone.utc)
    def invoke(label: str, args: list[str]) -> dict:
        remaining = MAX_SECONDS - (time.monotonic() - start)
        if remaining <= 0:
            raise TimeoutError("dekit descendant scenario exceeded total deadline")
        result = subprocess.run(prefix + args, cwd=WORK, env=env,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                timeout=min(10, remaining), check=False)
        row = {"label": label, "command": prefix + args, "exit_code": result.returncode,
               "stdout": result.stdout.decode("utf-8", "replace"),
               "stderr": result.stderr.decode("utf-8", "replace")}
        invocations.append(row)
        return row
    try:
        up = invoke("up", ["up"])
        deadline = time.monotonic() + 10
        while not (WORK / "parent.pid").is_file() and time.monotonic() < deadline:
            time.sleep(0.05)
        if not (WORK / "parent.pid").is_file() or not (WORK / "child.pid").is_file():
            raise RuntimeError("task did not publish its owned parent/child PID evidence")
        parent_pid = int((WORK / "parent.pid").read_text().strip())
        child_pid = int((WORK / "child.pid").read_text().strip())
        listed = invoke("list", ["ls"])
        down = invoke("down", ["down"])
    except Exception as exc:
        parent_pid = int((WORK / "parent.pid").read_text().strip()) if (WORK / "parent.pid").is_file() else None
        child_pid = int((WORK / "child.pid").read_text().strip()) if (WORK / "child.pid").is_file() else None
        invocations.append({"label": "scenario-error", "error": f"{type(exc).__name__}: {exc}"})
        try:
            down = invoke("cleanup-down", ["down"])
        except Exception as cleanup_error:
            invocations.append({"label": "cleanup-error", "error": f"{type(cleanup_error).__name__}: {cleanup_error}"})
    immutable_json(ATTEMPT / "invocations-before-process-check.json", {
        "schema_version": 1,
        "started_at_utc": started.isoformat(),
        "parent_pid": parent_pid,
        "child_pid": child_pid,
        "invocations": invocations,
    })
    time.sleep(0.5)
    ps = Path(env["SystemRoot"]) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    query_script = ATTEMPT / "query-owned-pids.ps1"
    query_script.write_text(
        "param([int]$ParentPid,[int]$ChildPid)\n"
        "$ErrorActionPreference='Stop'; $rows=[System.Collections.Generic.List[object]]::new(); "
        "foreach($id in @($ParentPid,$ChildPid)){if($id -gt 0){$p=Get-Process -Id $id -ErrorAction SilentlyContinue; "
        "if($p){$rows.Add([pscustomobject]@{Id=$p.Id;Name=$p.ProcessName;Path=$p.Path;StartTime=$p.StartTime})}}}; "
        "ConvertTo-Json -InputObject @($rows.ToArray()) -Depth 4 -Compress\n",
        encoding="utf-8",
    )
    pid_rows = subprocess.run([str(ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(query_script),
                               str(parent_pid or 0), str(child_pid or 0)], env=env,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                              timeout=30, check=False)
    alive = []
    if pid_rows.stdout.strip():
        parsed = json.loads(pid_rows.stdout.decode("utf-8-sig", "replace"))
        alive = parsed if isinstance(parsed, list) else [parsed]
    owned_pids = [pid for pid in (parent_pid, child_pid) if pid]
    stop_script = ATTEMPT / "stop-owned-pid.ps1"
    stop_script.write_text(
        "param([int]$ProcessId,[string]$ExpectedPath)\n"
        "$p=Get-Process -Id $ProcessId -ErrorAction SilentlyContinue; "
        "if($p -and $p.Path -eq $ExpectedPath){Stop-Process -Id $p.Id -Force}\n",
        encoding="utf-8",
    )
    expected_powershell = str(Path(env["SystemRoot"]) / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe")
    if alive:
        # These PIDs were emitted by the task's own script. Record then stop
        # only those exact still-live test processes before leaving the run.
        for row in alive:
            if str(row.get("Path", "")).lower() != expected_powershell.lower():
                continue
            subprocess.run([str(ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
                            str(stop_script), str(row["Id"]), expected_powershell], env=env,
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=10, check=False)
    recheck = subprocess.run([str(ps), "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(query_script),
                              str(parent_pid or 0), str(child_pid or 0)], env=env,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                             timeout=30, check=False)
    if recheck.stdout.strip():
        parsed = json.loads(recheck.stdout.decode("utf-8-sig", "replace"))
        remaining = parsed if isinstance(parsed, list) else [parsed]
    else:
        remaining = []
    process_row = {
        "schema_version": 1,
        "parent_pid": parent_pid,
        "child_pid": child_pid,
        "alive_after_runner_down": alive,
        "manually_terminated_owned_pids": [row["Id"] for row in alive],
        "remaining_owned_pids": remaining,
        "all_owned_task_pids_absent": not remaining and pid_rows.returncode == 0 and recheck.returncode == 0,
        "scope": "Only the exact PowerShell PIDs written by the synthetic task were queried or terminated.",
    }
    immutable_json(PROCESS_RECEIPT, process_row)
    observed = {
        "schema_version": 1,
        "project": "dekit",
        "pin": "da2acca491298c902d3f2e828204b98087123323",
        "host": "native-windows-x86_64-pc-windows-msvc",
        "executable_sha256": sha256(binary),
        "build_receipt_sha256": sha256(build),
        "workspace": str(WORK.relative_to(ROOT)),
        "config_sha256": sha256(config_path),
        "task_script_sha256": sha256(script),
        "environment": "Allowlisted system/tool paths; task-owned HOME, APPDATA, LOCALAPPDATA, TEMP and XDG roots; credentials excluded.",
        "started_at_utc": started.isoformat(),
        "invocations": invocations,
        "parent_pid": parent_pid,
        "child_pid": child_pid,
        "process_receipt": str(PROCESS_RECEIPT.relative_to(ROOT)),
        "all_owned_task_pids_absent": process_row["all_owned_task_pids_absent"],
        "scope": "Synthetic nested PowerShell child lifecycle smoke only; no admission or scenario credit.",
    }
    immutable_json(RECEIPT, observed)
    print(json.dumps({"exit_codes": {row["label"]: row.get("exit_code") for row in invocations},
                      "parent_pid": parent_pid, "child_pid": child_pid,
                      "alive_after_runner_down": alive,
                      "all_owned_task_pids_absent": process_row["all_owned_task_pids_absent"],
                      "receipt": str(RECEIPT.relative_to(ROOT))}, sort_keys=True))
    if alive or remaining or any(row.get("exit_code", 0) for row in invocations if row.get("label") in {"up", "list", "down"}):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
