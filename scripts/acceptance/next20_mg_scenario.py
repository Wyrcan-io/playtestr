"""Run one reviewed mg public-spec scenario against the frozen native rc.6."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import time
import uuid

from next20_candidate import executable
from next20_check import DOC, RAW, ROOT
from next20_mg_build import MAX_OUTPUT, PIN, run_bounded
from next20_mg_pilot import ensure_executable
from readiness_evidence import immutable_json, sha256


def apply_final_variation(spec, batch):
    """Apply one exact declared final-series contract variation in memory."""
    if batch == 4:
        spec["width"] = spec.get("width", 80) + 10
        spec["height"] = spec.get("height", 24) + 2
    elif batch == 7:
        segmented = []
        for step in spec["steps"]:
            if set(step) == {"text"} and len(step["text"]) > 3 and all(
                    ord(char) >= 32 and ord(char) != 127 for char in step["text"]):
                segmented.extend({"text": step["text"][offset:offset + 3]}
                                 for offset in range(0, len(step["text"]), 3))
            else:
                segmented.append(step)
        spec["steps"] = segmented
    elif batch == 10:
        spec["width"] = 70
        spec["height"] = 12
    elif batch == 11:
        spec["startup_timeout_ms"] = min(spec.get("startup_timeout_ms", 15000), 5000)
    return spec


def load_contract(value):
    original = Path(value)
    if original.is_symlink():
        raise ValueError("scenario contract cannot be linked")
    path = original.resolve(strict=True)
    mg_root = (DOC / "mg").resolve(strict=True)
    path.relative_to(mg_root)
    if path.is_symlink() or not path.is_file():
        raise ValueError("scenario contract must be a regular file under docs/.../mg")
    data = path.read_bytes()
    spec = json.loads(data)
    if spec.get("version") != 3:
        raise ValueError("mg scenario must use public spec version 3")
    if not spec.get("name") or not isinstance(spec.get("steps"), list) or not spec["steps"]:
        raise ValueError("mg scenario needs a name and nonempty public steps")
    if spec.get("command", [None])[0] != "mg":
        raise ValueError("mg scenario must exercise the named public mg command")
    fixture_rel = spec.get("workspace", {}).get("fixture", "")
    fixture_input = path.parent / fixture_rel
    if fixture_input.is_symlink():
        raise ValueError("mg scenario fixture root cannot be linked")
    fixture = fixture_input.resolve(strict=True)
    fixture.relative_to((DOC / "mg" / "fixtures").resolve(strict=True))
    if fixture.is_symlink() or not fixture.is_dir():
        raise ValueError("mg scenario fixture must be a regular owned fixture directory")
    if any(p.is_symlink() for p in fixture.rglob("*")):
        raise ValueError("mg scenario fixture must not contain linked entries")
    return path, data, spec, fixture


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    parser.add_argument("--mg-build-root", required=True)
    parser.add_argument("--spec", required=True)
    parser.add_argument("--phase", choices=("scenario-development", "final-qualification"),
                        default="scenario-development")
    parser.add_argument("--batch", type=int, choices=range(12))
    args = parser.parse_args()
    if (args.phase == "final-qualification") != (args.batch is not None):
        raise ValueError("final qualification requires one declared batch; development has no batch")
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
    if build.get("project") != "mg" or build.get("pin") != PIN or build.get("host") != host:
        raise ValueError("mg build packet identity does not match the reviewed project, pin and host")
    if target.is_symlink() or sha256(target) != build.get("binary_sha256"):
        raise ValueError("mg target binary differs from its native build receipt")
    target_mode = ensure_executable(target)
    if runtime.get("source_pin") != PIN or runtime.get("native_sha256") != build.get("binary_sha256"):
        raise ValueError("mg runtime receipt does not match its build receipt")

    contract, contract_bytes, spec, fixture = load_contract(args.spec)
    if args.phase == "final-qualification":
        spec = apply_final_variation(json.loads(contract_bytes), args.batch)
        variant_path = (DOC / "mg" /
                        f".final-series-{host}-{args.batch}-{contract.stem}.json")
        with variant_path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(spec, sort_keys=True, ensure_ascii=True, indent=2) + "\n")
        contract = variant_path
        contract_bytes = variant_path.read_bytes()
    runner = executable("native-exit-v1", host)
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v1.json").read_text(encoding="utf-8"))
    frozen = next(row for row in freeze["cells"] if row["host"] == host)
    if freeze.get("version") != "v0.4.0-rc.6" or sha256(runner) != frozen["binary_sha256"]:
        raise ValueError("runner executable is not the frozen rc.6 candidate")

    scenario_id = Path(args.spec).stem.lower()
    attempt_id = uuid.uuid4().hex
    attempt_dir = RAW / f"mg/{args.phase}/{host}/{args.batch if args.batch is not None else 'development'}/{scenario_id}/{attempt_id}"
    attempt_dir.mkdir(parents=True, exist_ok=False)
    report = attempt_dir / "report.json"
    report_artifacts = attempt_dir / "report-artifacts"
    log = attempt_dir / "runner.log"
    commands = []
    env_root = attempt_dir / "runner-environment"
    if args.phase == "final-qualification" and args.batch == 5:
        env_root = attempt_dir / "relocated café 雪"
    home, temp = env_root / "home", env_root / "temp"
    home.mkdir(parents=True)
    temp.mkdir()
    env = {"PATH": str(target.parent) + os.pathsep + os.environ.get("PATH", ""),
           "HOME": str(home), "TMP": str(temp), "TEMP": str(temp), "TMPDIR": str(temp)}
    attempt = {
        "schema_version": 1,
        "attempt_id": attempt_id,
        "project": "mg",
        "phase": args.phase,
        "batch": args.batch,
        "scenario_id": scenario_id,
        "candidate": freeze["version"],
        "candidate_archive_sha256": frozen["archive_sha256"],
        "candidate_binary_sha256": frozen["binary_sha256"],
        "target_pin": PIN,
        "target_binary_sha256": build["binary_sha256"],
        "target_build_receipt_sha256": sha256(build_path),
        "target_executable_mode": target_mode,
        "host": host,
        "architecture": build["architecture"],
        "contract": contract.relative_to(ROOT).as_posix(),
        "contract_sha256": hashlib.sha256(contract_bytes).hexdigest(),
        "fixture": fixture.relative_to(ROOT).as_posix(),
        "limits": {"command_seconds": 120, "runner_output_bytes": MAX_OUTPUT,
                   "step_timeout_ms": spec["timeout_ms"], "run_timeout_ms": spec["run_timeout_ms"]},
        "expected": "all reviewed public steps pass; exact state assertions match; target exits cleanly",
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    immutable_json(attempt_dir / "attempt.json", attempt)
    immutable_json(attempt_dir / "started.json", {"schema_version": 1, "attempt_id": attempt_id,
                    "event": "started", "at_utc": attempt["started_at_utc"]})
    immutable_json(attempt_dir / "identified.json", {"schema_version": 1, "attempt_id": attempt_id,
                    "event": "identified", "runner_sha256": frozen["binary_sha256"],
                    "target_sha256": build["binary_sha256"], "contract_sha256": attempt["contract_sha256"]})

    argv = [str(runner), "test", "--report", report.relative_to(ROOT).as_posix(),
            "--artifacts-dir", report_artifacts.relative_to(ROOT).as_posix(),
            contract.relative_to(ROOT).as_posix()]
    result = None
    report_data = None
    failure = None
    try:
        result = run_bounded(argv, ROOT, env, log, time.monotonic() + 120, commands,
                             operation=f"frozen rc.6 {scenario_id} runner")
        report_data = json.loads(report.read_text(encoding="utf-8"))
        rows = report_data.get("results", [])
        steps = rows[0].get("steps", []) if len(rows) == 1 else []
        cleanup = rows[0].get("cleanup", {}) if len(rows) == 1 else {}
        if args.phase == "final-qualification" and args.batch == 5:
            if "café 雪" not in str(temp) or list(temp.glob("playtestr-workspace-*")):
                raise RuntimeError("Unicode temp-root qualification left an unexpected workspace")
        if (report_data.get("runner_version") != freeze["version"] or
                report_data.get("summary") != {"total": 1, "passed": 1, "failed": 0, "cancelled": 0, "not_run": 0} or
                len(rows) != 1 or rows[0].get("status") != "passed" or
                len(steps) != len(spec["steps"]) or any(step.get("status") != "passed" for step in steps) or
                not cleanup.get("attempted") or not cleanup.get("confirmed_exited")):
            raise RuntimeError("rc.6 report lacks a single passing case, all passing steps and confirmed target exit")
        if not any("exit" in step for step in spec["steps"]):
            raise RuntimeError("scenario does not assert an exact target exit")
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
            "runner_pid": commands[-1]["pid"], "target_attempted": target_cleanup.get("attempted", False),
            "target_confirmed_exited": target_cleanup.get("confirmed_exited", False)})
    finished = {"schema_version": 1, "attempt_id": attempt_id, "event": "finished",
                "at_utc": datetime.now(timezone.utc).isoformat(),
                "runner_command": commands[-1] if commands else None,
                "report_sha256": sha256(report) if report.is_file() else None,
                "report_artifacts_present": report_artifacts.is_dir(), "failure": failure}
    immutable_json(attempt_dir / "finished.json", finished)
    if failure:
        raise RuntimeError(failure)
    receipt = {"schema_version": 1, "attempt_id": attempt_id, "scenario_id": scenario_id,
              "host": host, "candidate": freeze["version"], "status": "scenario-passed",
              "report_sha256": sha256(report), "runner_log_sha256": sha256(log),
              "runner_process_group_cleanup": result["process_tree_cleanup"],
              "target_cleanup": report_data["results"][0]["cleanup"],
              "candidate_archive_sha256": frozen["archive_sha256"],
              "runner_binary_sha256": frozen["binary_sha256"], "target_pin": PIN,
              "target_binary_sha256": build["binary_sha256"],
              "contract_sha256": attempt["contract_sha256"]}
    immutable_json(attempt_dir / "scenario-receipt.json", receipt)
    print(json.dumps(receipt, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
