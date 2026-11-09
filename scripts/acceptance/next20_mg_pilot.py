"""Run the exact frozen rc.6 candidate against mg's first-use PTY journey."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import stat
import time
import uuid

from next20_candidate import executable
from next20_check import DOC, RAW, ROOT
from next20_mg_build import run_bounded
from readiness_evidence import immutable_json, sha256


PIN = "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66"
EXPECTED_BYTES = b"MG_PTY_PILOT_RC6\n"


def ensure_executable(path):
    """Restore the user execute bit that Actions artifact ZIPs do not retain."""
    path = Path(path)
    if path.is_symlink():
        raise ValueError("mg target binary is linked")
    mode = path.stat().st_mode
    if not stat.S_ISREG(mode):
        raise ValueError("mg target is not a regular file")
    original_mode = stat.S_IMODE(mode)
    if not mode & stat.S_IXUSR:
        os.chmod(path, original_mode | stat.S_IXUSR)
    if not os.access(path, os.X_OK):
        raise ValueError("mg target is not executable by the current user")
    return {"mode_before": oct(original_mode),
            "mode_after": oct(stat.S_IMODE(path.stat().st_mode))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    parser.add_argument("--mg-build-root", required=True)
    args = parser.parse_args()
    host = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    if host != args.host:
        raise RuntimeError(f"native host mismatch: expected {args.host}, got {host}")

    mg_root = Path(args.mg_build_root).resolve(strict=True)
    mg_root.relative_to(ROOT.resolve())
    build_path = mg_root / "active/mg/build.json"
    runtime_path = mg_root / "active/mg/runtime.json"
    target = mg_root / "active/mg/install/bin/mg"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    if build["project"] != "mg" or build["pin"] != PIN or build["host"] != host:
        raise ValueError("mg build artifact mismatch: "
                         f"project={build.get('project')!r}, pin={build.get('pin')!r}, "
                         f"host={build.get('host')!r}; expected mg/{PIN}/{host}; "
                         f"receipt={build_path}")
    if target.is_symlink() or sha256(target) != build["binary_sha256"]:
        raise ValueError("mg target binary differs from its native build receipt")
    target_mode = ensure_executable(target)
    if runtime["source_pin"] != PIN or runtime["native_sha256"] != build["binary_sha256"]:
        raise ValueError("mg runtime receipt does not match its build receipt")

    runner = executable("native-exit-v1", host)
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v1.json").read_text(encoding="utf-8"))
    candidate = next(row for row in freeze["cells"] if row["host"] == host)
    if freeze["version"] != "v0.4.0-rc.6" or sha256(runner) != candidate["binary_sha256"]:
        raise ValueError("runner executable is not the frozen rc.6 candidate")

    spec = DOC / "mg/pilot-n01.json"
    fixture = DOC / "mg/fixtures/pilot-n01/.keep"
    spec_bytes = spec.read_bytes()
    spec_data = json.loads(spec_bytes)
    if spec_data["version"] != 3 or spec_data["workspace"]["fixture"] != "fixtures/pilot-n01":
        raise ValueError("pilot spec changed its reviewed contract")
    declared_state = spec_data["steps"][-1]["state"]
    if base64.b64decode(declared_state["bytes_base64"], validate=True) != EXPECTED_BYTES:
        raise ValueError("pilot saved-byte expectation changed")
    if not fixture.is_file() or fixture.is_symlink():
        raise ValueError("pilot fixture is missing or linked")

    attempt_id = uuid.uuid4().hex
    attempt_dir = RAW / "mg/pilot-development" / host / attempt_id
    attempt_dir.mkdir(parents=True, exist_ok=False)
    report = attempt_dir / "report.json"
    report_artifacts = attempt_dir / "report-artifacts"
    log = attempt_dir / "runner.log"
    commands = []
    attempt = {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "project": "mg",
        "phase": "first-use N01 PTY pilot",
        "candidate": freeze["version"],
        "candidate_archive_sha256": candidate["archive_sha256"],
        "candidate_binary_sha256": candidate["binary_sha256"],
        "target_pin": PIN,
        "target_binary_sha256": build["binary_sha256"],
        "target_build_receipt_sha256": sha256(build_path),
        "target_executable_mode": target_mode,
        "host": host,
        "architecture": build["architecture"],
        "contract": spec.relative_to(ROOT).as_posix(),
        "contract_sha256": hashlib.sha256(spec_bytes).hexdigest(),
        "fixture": fixture.relative_to(ROOT).as_posix(),
        "fixture_sha256": sha256(fixture),
        "expected_saved_bytes": len(EXPECTED_BYTES),
        "expected_saved_sha256": hashlib.sha256(EXPECTED_BYTES).hexdigest(),
        "limits": {"command_seconds": 120, "runner_output_bytes": 4 * 1024 * 1024,
                   "step_timeout_ms": spec_data["timeout_ms"],
                   "run_timeout_ms": spec_data["run_timeout_ms"]},
        "expected": "one passing native PTY test; exact saved bytes; target and runner exited",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    immutable_json(attempt_dir / "attempt.json", attempt)
    immutable_json(attempt_dir / "started.json", {"schema_version": 1, "attempt_id": attempt_id,
                    "event": "started", "at_utc": attempt["started_at_utc"]})
    immutable_json(attempt_dir / "identified.json", {"schema_version": 1, "attempt_id": attempt_id,
                    "event": "identified", "runner_sha256": candidate["binary_sha256"],
                    "target_sha256": build["binary_sha256"], "contract_sha256": attempt["contract_sha256"]})

    env_root = attempt_dir / "runner-environment"
    home, temp = env_root / "home", env_root / "temp"
    home.mkdir(parents=True)
    temp.mkdir()
    env = {"PATH": str(target.parent) + os.pathsep + os.environ.get("PATH", ""),
           "HOME": str(home), "TMP": str(temp), "TEMP": str(temp), "TMPDIR": str(temp)}
    argv = [str(runner), "test", "--report", report.relative_to(ROOT).as_posix(),
            "--artifacts-dir", report_artifacts.relative_to(ROOT).as_posix(),
            spec.relative_to(ROOT).as_posix()]
    result = None
    report_data = None
    failure = None
    try:
        result = run_bounded(argv, ROOT, env, log, time.monotonic() + 120, commands,
                             operation="frozen rc.6 pilot runner")
        report_data = json.loads(report.read_text(encoding="utf-8"))
        rows = report_data.get("results", [])
        steps = rows[0].get("steps", []) if len(rows) == 1 else []
        cleanup = rows[0].get("cleanup", {}) if len(rows) == 1 else {}
        if (report_data.get("runner_version") != freeze["version"] or
                report_data.get("summary") != {"total": 1, "passed": 1, "failed": 0, "cancelled": 0, "not_run": 0} or
                len(rows) != 1 or rows[0].get("status") != "passed" or
                not cleanup.get("attempted") or not cleanup.get("confirmed_exited")):
            raise RuntimeError("rc.6 report lacks a single passing case and confirmed target exit")
        if len(steps) != 10 or any(step.get("status") != "passed" for step in steps):
            raise RuntimeError("rc.6 report does not show all ten reviewed PTY/state steps passing")
        if steps[-1].get("action") != "state":
            raise RuntimeError("rc.6 report does not end with the exact saved-state assertion")
    except Exception as error:
        failure = f"{type(error).__name__}: {error}"
    if commands:
        if report.is_file():
            try:
                report_data = json.loads(report.read_text(encoding="utf-8"))
                target_cleanup = report_data.get("results", [{}])[0].get("cleanup", {})
            except (json.JSONDecodeError, IndexError, AttributeError):
                target_cleanup = {}
        else:
            target_cleanup = {}
        immutable_json(attempt_dir / "launched.json", {
            "schema_version": 1, "attempt_id": attempt_id, "event": "launched",
            "runner_pid": commands[-1]["pid"],
            "runner_started_at_utc": commands[-1]["started_at_utc"],
            "target_attempted": target_cleanup.get("attempted", False),
            "target_confirmed_exited": target_cleanup.get("confirmed_exited", False)})
    finished = {"schema_version": 1, "attempt_id": attempt_id, "event": "finished",
                "at_utc": datetime.now(timezone.utc).isoformat(),
                "runner_command": commands[-1] if commands else None,
                "report_sha256": sha256(report) if report.is_file() else None,
                "report_artifacts_present": report_artifacts.is_dir(),
                "failure": failure}
    immutable_json(attempt_dir / "finished.json", finished)
    if failure:
        raise RuntimeError(failure)
    receipt = {"schema_version": 1, "attempt_id": attempt_id, "host": host,
                      "candidate": freeze["version"],
                      "status": "pilot-passed", "report_sha256": sha256(report),
                      "runner_log_sha256": sha256(log), "runner_process_group_cleanup": result["process_tree_cleanup"],
                      "target_cleanup": report_data["results"][0]["cleanup"],
                      "candidate_archive_sha256": candidate["archive_sha256"],
                      "runner_binary_sha256": candidate["binary_sha256"],
                      "target_pin": PIN, "target_binary_sha256": build["binary_sha256"],
                      "contract_sha256": attempt["contract_sha256"],
                      "expected_saved_sha256": attempt["expected_saved_sha256"]}
    immutable_json(attempt_dir / "pilot-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
