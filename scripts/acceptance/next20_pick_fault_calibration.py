"""Run pristine/faulted/restored Pick source calibrations on a native host."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_pick_build import ARCHIVE_SHA256, PIN, file_map
from readiness_evidence import immutable_json, sha256

HOSTS = {"Linux": "linux", "Darwin": "darwin"}
DECLARATION = DOC / "pick" / "fault-declaration-v1.json"


def require(value, message):
    if not value:
        raise ValueError(message)


def load_declaration():
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    scenario_path = ROOT / declaration["scenario_declaration"]
    freeze_path = ROOT / declaration["candidate_freeze"]
    scenarios = json.loads(scenario_path.read_text(encoding="utf-8"))
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    require(declaration.get("project") == "pick" and declaration.get("pin") == PIN
            and declaration.get("source_archive_sha256") == ARCHIVE_SHA256
            and sha256(scenario_path) == declaration.get("scenario_declaration_sha256")
            and sha256(freeze_path) == declaration.get("candidate_freeze_sha256")
            and declaration.get("candidate") == freeze.get("version") == "v0.4.0-rc.8"
            and declaration.get("series") == freeze.get("series") == "native-exit-v3"
            and scenarios.get("candidate") == freeze.get("version")
            and len(declaration.get("faults", [])) == 3,
            "Pick fault declaration/source/scenario/candidate identity differs")
    rows = []
    for row in declaration["faults"]:
        manifest_path = (DOC / row["manifest"]).resolve(strict=True)
        manifest_path.relative_to((DOC / "pick").resolve(strict=True))
        fault = json.loads(manifest_path.read_text(encoding="utf-8"))
        require(fault.get("id") == row["id"] and fault.get("scenario_id") == row["scenario_id"]
                and fault.get("project") == "pick" and fault.get("pin") == PIN
                and fault.get("source_archive_sha256") == ARCHIVE_SHA256
                and fault.get("baseline_source_sha256") ==
                    "b2a9252d7c684da668b5d306b8e41ed5fcb169a60fd3bb29e0897031a70c890a",
                "Pick fault manifest identity differs")
        patch_path = (DOC / fault["patch"]).resolve(strict=True)
        patch_path.relative_to((DOC / "pick").resolve(strict=True))
        require(sha256(patch_path) == fault.get("patch_sha256"), "Pick source patch bytes differ")
        scenario = next(item for item in scenarios["scenarios"] if item["id"] == fault["scenario_id"])
        scenario_spec = json.loads((DOC / scenario["spec_path"]).read_text(encoding="utf-8"))
        require(fault.get("expected_failure_step") <= len(scenario_spec.get("steps", []))
                and fault.get("expected_failure_categories"), "Pick fault oracle step/category is undeclared")
        rows.append((fault, manifest_path, scenario))
    require(len({fault["id"] for fault, _, _ in rows}) == 3
            and len({fault["scenario_id"] for fault, _, _ in rows}) == 3,
            "Pick fault IDs and scenario IDs must each be distinct")
    return declaration, scenarios, freeze, rows


def target_environment(binary):
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env.update({"PATH": str(binary.parent) + os.pathsep + env.get("PATH", ""),
                "TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "TMPDIR": str(RAW / "tmp"), "TMP": str(RAW / "tmp"), "TEMP": str(RAW / "tmp")})
    (RAW / "tmp").mkdir(parents=True, exist_ok=True)
    return env


async def command(argv, project, label, phase, *, expected=0, timeout=1800, env=None):
    return await execute(list(map(str, argv)), project, label, cwd=ROOT,
                         env=env or dict(os.environ), timeout=timeout, expected=expected,
                         campaign=NextCampaign(phase=phase))


def check_report(path, fault, phase):
    report = json.loads(path.read_text(encoding="utf-8"))
    require(report.get("report_version") == 3 and len(report.get("results", [])) == 1,
            "Pick calibration report schema/denominator differs")
    case = report["results"][0]
    require(case.get("invocation_id") and case.get("cleanup", {}).get("confirmed_exited") is True
            and case.get("workspace", {}).get("cleaned") is True,
            "Pick calibration did not positively confirm target/workspace cleanup")
    failed_steps = [step for step in case.get("steps", []) if step.get("status") == "failed"]
    if phase == "source-fault-corrupted":
        expected = set(fault["expected_failure_categories"])
        require(case.get("status") == "failed" and case.get("failure", {}).get("category") in expected
                and len(failed_steps) == 1
                and failed_steps[0].get("number") == fault["expected_failure_step"]
                and case.get("target", {}).get("exited") is True,
                "unchanged Pick contract missed or misclassified the declared source fault")
        return case, "expected-target-fault-rejection", failed_steps[0]
    require(case.get("status") == "passed" and case.get("failure") is None
            and not failed_steps and case.get("target", {}).get("exited") is True,
            "pristine/restored Pick target did not pass unchanged scenario")
    return case, "passed", None


async def run_phase(host, fault, manifest_path, scenario, phase_name, run_id):
    target_root = RAW / "active" / "pick"
    evidence = RAW / "pick" / "fault-calibration" / "v1" / fault["id"] / phase_name / host
    evidence.mkdir(parents=True, exist_ok=False)
    phase = {"baseline": "source-fault-baseline", "fault": "source-fault-corrupted",
             "restored": "source-fault-restored"}[phase_name]
    mutated_path = None
    original_bytes = None
    build = None
    result = None
    cleanup_result = None
    try:
        await command([sys.executable, "-B", "scripts/acceptance/next20_acquire.py", "pick"],
                      "core", f"pick-{fault['id']}-{phase_name}-{host}-acquire", phase)
        acquisition_path = target_root / "acquisition.json"
        acquisition = json.loads(acquisition_path.read_text(encoding="utf-8"))
        original_map = acquisition.get("source_files")
        source = target_root / "src"
        require(acquisition.get("pin") == PIN and acquisition.get("archive_sha256") == ARCHIVE_SHA256
                and sha256(target_root / "source.tar.gz") == ARCHIVE_SHA256,
                "Pick acquired source differs from the reviewed pin")
        if phase_name == "fault":
            mutated_path = (source / fault["source_file"]).resolve(strict=True)
            mutated_path.relative_to(source.resolve(strict=True))
            original_bytes = mutated_path.read_bytes()
            require(sha256(mutated_path) == fault["baseline_source_sha256"],
                    "Pick fault source does not begin at the exact pristine bytes")
        build_argv = [sys.executable, "-B", "scripts/acceptance/next20_pick_build.py",
                      "--expected-host", host]
        if phase_name == "fault":
            build_argv += ["--source-fault-manifest", manifest_path.relative_to(ROOT).as_posix(),
                           "--skip-upstream-tests"]
        await command(build_argv, "core", f"pick-{fault['id']}-{phase_name}-{host}-build", phase)
        build_path = target_root / "build.json"
        build = json.loads(build_path.read_text(encoding="utf-8"))
        require(build.get("pin") == PIN and build.get("host") == host
                and build.get("binary_sha256") == sha256(target_root / "install/bin/pick")
                and build.get("source_archive_sha256") == ARCHIVE_SHA256,
                "Pick phase build is not bound to its target executable/source")
        mutation = build.get("source_mutation")
        if phase_name == "fault":
            require(mutation and mutation.get("id") == fault["id"]
                    and mutation.get("mutated_source_sha256") == fault["mutated_source_sha256"],
                    "Pick fault build receipt omits the exact declared source mutation")
            mutated_root = evidence / "mutated-source"
            mutated_root.mkdir()
            (mutated_root / fault["source_file"]).write_bytes(mutated_path.read_bytes())
            require(sha256(mutated_root / fault["source_file"]) == fault["mutated_source_sha256"],
                    "retained mutated Pick source differs")
        else:
            require(mutation is None and build.get("upstream_tests") == "passed",
                    "pristine/recovery build has an unexpected mutation or skipped tests")

        runner = executable("native-exit-v3", host)
        candidate_cell = next(row for row in json.loads(
            (DOC / "replacement-candidate-freeze-native-exit-v3.json").read_text())["cells"]
            if row["host"] == host)
        installed = json.loads((runner.parent / "installed.json").read_text(encoding="utf-8"))
        require(installed.get("archive_sha256") == candidate_cell["archive_sha256"]
                and installed.get("binary_sha256") == candidate_cell["binary_sha256"],
                "Pick calibration runner differs from the exact frozen rc.8 archive")
        report_path = evidence / "report.json"
        artifacts = evidence / "artifacts"
        artifacts.mkdir()
        argv = [runner, "test", "--report", report_path.relative_to(ROOT),
                "--artifacts-dir", artifacts.relative_to(ROOT),
                (DOC / scenario["spec_path"]).relative_to(ROOT)]
        command_result = await command(argv, "pick",
            f"pick-{fault['id']}-{phase_name}-{host}-{scenario['id']}", phase,
            expected=1 if phase_name == "fault" else 0,
            timeout=180, env=target_environment(target_root / "install" / "bin" / "pick"))
        case, classification, failed_step = check_report(report_path, fault, phase)
        result = {"fault_id": fault["id"], "host": host, "phase": phase_name,
                  "evidence_phase": phase, "scenario_id": scenario["id"],
                  "scenario_sha256": sha256(DOC / scenario["spec_path"]),
                  "source_archive_sha256": ARCHIVE_SHA256,
                  "source_binary_sha256": build["binary_sha256"],
                  "source_mutation": mutation,
                  "candidate_archive_sha256": candidate_cell["archive_sha256"],
                  "candidate_binary_sha256": candidate_cell["binary_sha256"],
                  "runner_command_id": command_result["id"],
                  "report": report_path.relative_to(ROOT).as_posix(),
                  "report_sha256": sha256(report_path),
                  "status": classification,
                  "failure_category": case.get("failure", {}).get("category") if failed_step else None,
                  "failed_step": failed_step.get("number") if failed_step else None,
                  "target_exit": case.get("target", {}).get("exit_code"),
                  "target_cleanup_confirmed": case["cleanup"]["confirmed_exited"],
                  "workspace_cleaned": case["workspace"]["cleaned"],
                  "upstream_tests": build.get("upstream_tests")}
    finally:
        if phase_name == "fault" and mutated_path is not None and original_bytes is not None:
            mutated_path.write_bytes(original_bytes)
            require(sha256(mutated_path) == fault["baseline_source_sha256"],
                    "Pick source fault failed byte-exact restoration")
            restored_map, _ = file_map(target_root / "src")
            require(restored_map == original_map, "Pick fault restoration differs from pristine source map")
        window = f"rebuild-fault-{fault['id'].lower()}-{phase_name}-{host}"[:63]
        cleanup_log = evidence / "cleanup.log"
        cleanup_result = await command([sys.executable, "-B", "scripts/acceptance/next20_target_cleanup.py",
                                        "--project", "pick", "--include-active-case-evidence",
                                        "--window", window], "core",
            f"pick-{fault['id']}-{phase_name}-{host}-cleanup", "fault-calibration", timeout=600)
        cleanup_log.write_text(cleanup_result["output"], encoding="utf-8")
        require(not target_root.exists(), "Pick fault phase left its owned source/build tree")
    receipt = {"schema_version": 1, "project": "pick", "run_id": run_id,
               "fault_id": fault["id"], "host": host, "phase": phase_name,
               "started_at_utc": datetime.now(timezone.utc).isoformat(),
               "phase_result": result, "cleanup": {"command_id": cleanup_result["id"],
               "log_sha256": sha256(cleanup_log), "active_target_absent": True,
               "source_restored_exact": True}}
    immutable_json(evidence / "phase-receipt.json", receipt)
    return receipt


async def main_async(host):
    actual_host = HOSTS.get(platform.system())
    require(actual_host == host, "Pick fault workflow host differs from actual native host")
    declaration, scenarios, freeze, faults = load_declaration()
    installed = executable("native-exit-v3", host)
    require(installed.is_file(), "exact frozen rc.8 runner executable is missing")
    run_id = os.environ.get("GITHUB_RUN_ID", "local")
    results = []
    for fault, manifest_path, scenario in faults:
        rows = []
        for phase_name in ("baseline", "fault", "restored"):
            rows.append(await run_phase(host, fault, manifest_path, scenario, phase_name, run_id))
        baseline, corrupted, restored = [row["phase_result"] for row in rows]
        require(baseline["status"] == restored["status"] == "passed"
                and baseline["source_binary_sha256"] == restored["source_binary_sha256"]
                and corrupted["status"] == "expected-target-fault-rejection"
                and corrupted["source_mutation"]["mutated_source_sha256"] == fault["mutated_source_sha256"],
                "Pick baseline/fault/restored triplet did not qualify against unchanged exact contract")
        result_path = RAW / "pick" / "fault-calibration" / "v1" / fault["id"] / host / "triplet.json"
        immutable_json(result_path, {"schema_version": 1, "fault_id": fault["id"],
            "host": host, "scenario_id": scenario["id"], "pin": PIN,
            "baseline": baseline, "corrupted": corrupted, "restored": restored,
            "fault_manifest": manifest_path.relative_to(ROOT).as_posix(),
            "fault_manifest_sha256": sha256(manifest_path), "admission_credit": 0})
        results.append({"fault_id": fault["id"], "scenario_id": scenario["id"],
                        "baseline": baseline["status"], "corrupted": corrupted["status"],
                        "restored": restored["status"],
                        "baseline_binary_sha256": baseline["source_binary_sha256"],
                        "mutated_binary_sha256": corrupted["source_binary_sha256"],
                        "restored_binary_sha256": restored["source_binary_sha256"]})
    summary = {"schema_version": 1, "project": "pick", "host": host,
               "run_id": run_id, "phase": "fault-calibration", "pin": PIN,
               "candidate": freeze["version"], "candidate_series": freeze["series"],
               "scenario_declaration_sha256": sha256(DOC / "pick" / "scenario-declaration-v10.json"),
               "fault_declaration": DECLARATION.relative_to(ROOT).as_posix(),
               "fault_declaration_sha256": sha256(DECLARATION),
               "faults": results, "phase_count": len(results) * 3,
               "passed_pristine_and_restored": len(results) * 2,
               "rejected_corrupted": len(results), "false_greens": 0,
               "admission_credit": 0}
    immutable_json(RAW / "pick" / "fault-calibration" / "v1" / host / "summary.json", summary)
    print(json.dumps({"project": "pick", "host": host, "faults": len(results),
                      "phases": summary["phase_count"], "false_greens": 0}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    args = parser.parse_args()
    asyncio.run(main_async(args.host))


if __name__ == "__main__":
    main()
