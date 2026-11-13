"""Calibrate three declared fzy source faults on each frozen native host."""
import argparse
import asyncio
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_fzy_build import ARCHIVE_SHA256, PIN, file_map, run_bounded
from readiness_evidence import immutable_json, sha256


PROJECT = DOC / "fzy"
DECLARATION = PROJECT / "fault-declaration-v1.json"
HOSTS = {"Linux": "linux", "Darwin": "darwin"}
PHASES = {"baseline": "source-fault-baseline", "fault": "source-fault-corrupted",
          "restored": "source-fault-restored"}


def cleanup_window(fault_id, phase_name, host):
    return f"rebuild-fault-{fault_id.lower()}-{phase_name}-{host}"


def require(value, message):
    if not value:
        raise ValueError(message)


def target_environment(binary):
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env.update({"PATH": str(binary.parent) + os.pathsep + env.get("PATH", ""),
                "TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "TMPDIR": str(RAW / "tmp"), "TMP": str(RAW / "tmp"), "TEMP": str(RAW / "tmp")})
    (RAW / "tmp").mkdir(parents=True, exist_ok=True)
    return env


def load_contract():
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    scenario_path = PROJECT / "scenario-declaration-v1.json"
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v3.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    require(declaration.get("project") == "fzy" and declaration.get("pin") == PIN
            and declaration.get("source_archive_sha256") == ARCHIVE_SHA256
            and declaration.get("candidate") == freeze.get("version") == "v0.4.0-rc.8"
            and declaration.get("candidate_series") == freeze.get("series") == "native-exit-v3"
            and declaration.get("candidate_freeze_sha256") == sha256(freeze_path)
            and declaration.get("scenario_declaration") == "fzy/scenario-declaration-v1.json"
            and declaration.get("scenario_declaration_sha256") == sha256(scenario_path)
            and scenario.get("project") == "fzy" and len(declaration.get("faults", [])) == 3,
            "fzy fault/candidate/scenario declaration identity differs")
    rows = []
    for fault in declaration["faults"]:
        before = base64.b64decode(fault["before_base64"], validate=True)
        after = base64.b64decode(fault["after_base64"], validate=True)
        require(before and after and before != after and fault["scenario_id"] in
                {row["id"] for row in scenario["scenarios"]},
                "fzy source fault patch or scenario identity is invalid")
        case = next(row for row in scenario["scenarios"] if row["id"] == fault["scenario_id"])
        spec_path = DOC / case["spec_path"]
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        require(fault["expected_failure_step"] <= len(spec["steps"])
                and isinstance(fault["expected_failure_category"], str),
                "fzy fault detection boundary is not covered by its public contract")
        rows.append((fault, case, spec_path))
    require(len({row[0]["id"] for row in rows}) == 3
            and len({row[1]["id"] for row in rows}) == 3,
            "fzy faults and detection scenarios must be distinct")
    return declaration, scenario, freeze, rows


async def command(argv, project, label, phase, *, expected=0, timeout=2400, env=None):
    try:
        return await execute(list(map(str, argv)), project, label, cwd=ROOT,
                             env=env or dict(os.environ), timeout=timeout, expected=expected,
                             campaign=NextCampaign(phase=phase))
    except Exception as error:
        directory = getattr(error, "evidence_directory", None)
        console = Path(directory) / "console.log" if directory else None
        if console and console.is_file():
            detail = console.read_text(encoding="utf-8", errors="replace")[-12000:]
            raise RuntimeError(f"{error}\n--- bounded helper output ---\n{detail}") from error
        raise


def build_fault_binary(target, fault, evidence):
    source = target / "src"
    baseline_map, _ = file_map(source)
    mutation_path = (source / fault["source_file"]).resolve(strict=True)
    mutation_path.relative_to(source.resolve(strict=True))
    require(baseline_map.get(fault["source_file"]) == fault["baseline_source_sha256"]
            and sha256(mutation_path) == fault["baseline_source_sha256"],
            "fzy fault source does not match the pinned baseline file")
    before = base64.b64decode(fault["before_base64"], validate=True)
    after = base64.b64decode(fault["after_base64"], validate=True)
    data = mutation_path.read_bytes()
    require(data.count(before) == 1, "fzy fault patch must replace one exact reviewed source region")
    source_copy = target / "fault-build" / fault["id"] / "source"
    if source_copy.exists():
        raise ValueError("preserve existing fzy fault build source")
    source_copy.parent.mkdir(parents=True)
    shutil.copytree(source, source_copy)
    copied_path = source_copy / fault["source_file"]
    mutated = copied_path.read_bytes().replace(before, after, 1)
    copied_path.write_bytes(mutated)
    require(sha256(copied_path) == fault["mutated_source_sha256"],
            "fzy fault source bytes differ from declared mutation")
    make = shutil.which("make")
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    require(make and compiler, "native make/C compiler missing for fzy fault build")
    build_root = target / "fault-build" / fault["id"]
    logs = build_root / "logs"
    logs.mkdir()
    env = target_environment(target / "install" / "bin" / "fzy")
    env["CC"] = compiler
    env["MAKEFLAGS"] = ""
    env["MFLAGS"] = ""
    deadline = time.monotonic() + 20 * 60
    commands = []
    started = datetime.now(timezone.utc).isoformat()
    run_bounded([make, "-j2"], source_copy, env, logs / "build.log", deadline, commands,
                operation="fzy declared source fault build")
    binary = source_copy / "fzy"
    require(binary.is_file() and not binary.is_symlink(), "fault build produced no owned fzy executable")
    install_binary = target / "install/bin/fzy"
    install_binary.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(binary, install_binary)
    require(sha256(install_binary) == sha256(binary), "installed fzy fault binary changed during copy")
    source_map_after = file_map(source)[0]
    require(source_map_after == baseline_map, "fault build modified the pristine acquired fzy source")
    build_receipt_path = target / "build.json"
    build_receipt = json.loads(build_receipt_path.read_text(encoding="utf-8"))
    pristine_binary_sha256 = build_receipt["binary_sha256"]
    require(pristine_binary_sha256 != sha256(install_binary),
            "declared source mutation did not change the native fzy executable")
    mutation = {"id": fault["id"], "source_file": fault["source_file"],
                "baseline_source_sha256": fault["baseline_source_sha256"],
                "mutated_source_sha256": fault["mutated_source_sha256"],
                "pristine_binary_sha256": pristine_binary_sha256,
                "mutated_binary_sha256": sha256(install_binary),
                "upstream_tests": "passed on pristine source before mutation",
                "fault_binary_build_commands": commands}
    build_receipt["binary_sha256"] = sha256(install_binary)
    build_receipt["source_mutation"] = mutation
    build_receipt["fault_binary_build_started_at_utc"] = started
    build_receipt_path.write_text(json.dumps(build_receipt, sort_keys=True, indent=2) + "\n",
                                  encoding="utf-8", newline="\n")
    runtime_path = target / "runtime.json"
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    runtime["native_sha256"] = sha256(install_binary)
    runtime_path.write_text(json.dumps(runtime, sort_keys=True, indent=2) + "\n",
                            encoding="utf-8", newline="\n")
    shutil.copy2(copied_path, evidence / "mutated-source.c")
    shutil.copy2(install_binary, evidence / "mutated-fzy")
    immutable_json(evidence / "fault-build-v1.json", {
        "schema_version": 1, "project": "fzy", "fault_id": fault["id"],
        "pin": PIN, "source_archive_sha256": ARCHIVE_SHA256,
        "source_file": fault["source_file"], "mutated_source_sha256": sha256(copied_path),
        "pristine_binary_sha256": pristine_binary_sha256,
        "mutated_binary_sha256": sha256(install_binary), "commands": commands,
        "upstream_tests": "passed on pristine source before source mutation",
        "pristine_acquired_source_unchanged": True,
    })
    shutil.copytree(logs, evidence / "fault-build-logs")
    return mutation


def verify_case_report(report_path, fault, phase_name, expected_exit):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    require(report.get("report_version") == 3 and report.get("runner_version") == "v0.4.0-rc.8"
            and report.get("summary", {}).get("total") == 1
            and len(report.get("results", [])) == 1,
            "fzy fault report schema/candidate/denominator differs")
    result = report["results"][0]
    require(result.get("target", {}).get("exited") is True
            and result.get("cleanup", {}).get("confirmed_exited") is True
            and result.get("workspace", {}).get("cleaned") is True,
            "fzy fault calibration lacks target/descendant/workspace cleanup evidence")
    failed = [step for step in result.get("steps", []) if step.get("status") == "failed"]
    if phase_name == "fault":
        require(result.get("status") == "failed" and result.get("failure", {}).get("category")
                == fault["expected_failure_category"] and len(failed) == 1
                and failed[0].get("number") == fault["expected_failure_step"]
                and report["summary"].get("failed") == 1,
                "declared fzy source mutation escaped its public scenario or failed at another boundary")
        return result, failed[0], "expected-target-fault-rejection"
    require(result.get("status") == "passed" and result.get("failure") is None
            and not failed and result.get("target", {}).get("exit_code") == expected_exit
            and all(step.get("status") == "passed" for step in result.get("steps", [])),
            "pristine or restored fzy scenario did not pass its unchanged contract")
    return result, None, "passed"


async def phase_run(host, fault, case, spec_path, phase_name, candidate, freeze):
    evidence = RAW / "fzy" / "fault-calibration-v1" / fault["id"] / phase_name / host
    evidence.mkdir(parents=True, exist_ok=False)
    phase = PHASES[phase_name]
    await command([sys.executable, "-B", "scripts/acceptance/next20_acquire.py", "fzy"],
                  "core", f"fzy-{fault['id']}-{phase_name}-{host}-acquire", phase)
    target = RAW / "active/fzy"
    acquisition = json.loads((target / "acquisition.json").read_text(encoding="utf-8"))
    require(acquisition.get("pin") == PIN and acquisition.get("archive_sha256") == ARCHIVE_SHA256
            and sha256(target / "source.tar.gz") == ARCHIVE_SHA256,
            "fzy fault calibration acquired a different source")
    await command([sys.executable, "-B", "scripts/acceptance/next20_fzy_build.py",
                   "--expected-host", host], "core",
                  f"fzy-{fault['id']}-{phase_name}-{host}-pristine-build", phase)
    build = json.loads((target / "build.json").read_text(encoding="utf-8"))
    binary = target / "install/bin/fzy"
    require(build.get("upstream_tests") == "passed" and build.get("pin") == PIN
            and build.get("host") == host and build.get("binary_sha256") == sha256(binary),
            "fzy baseline build did not pass on the exact acquired source")
    shutil.copytree(target / "build-logs", evidence / "pristine-build-logs")
    shutil.copy2(target / "build.json", evidence / "pristine-build.json")
    shutil.copy2(target / "runtime.json", evidence / "pristine-runtime.json")
    mutation = None
    if phase_name == "fault":
        mutation = build_fault_binary(target, fault, evidence)
        binary = target / "install/bin/fzy"
        build = json.loads((target / "build.json").read_text(encoding="utf-8"))
    cell = next(row for row in freeze["cells"] if row["host"] == host)
    runner = executable("native-exit-v3", host)
    installed = json.loads((runner.parent / "installed.json").read_text(encoding="utf-8"))
    require(installed.get("archive_sha256") == cell["archive_sha256"]
            and installed.get("binary_sha256") == cell["binary_sha256"],
            "fzy source fault runner differs from the exact frozen rc.8 candidate")
    report_path = evidence / "report.json"
    artifacts = evidence / "artifacts"
    artifacts.mkdir()
    command_result = await execute(
        [runner, "test", "--report", report_path.relative_to(ROOT), "--artifacts-dir",
         artifacts.relative_to(ROOT), spec_path.relative_to(ROOT)],
        "fzy", f"fzy-{fault['id']}-{phase_name}-{host}-{case['id']}", cwd=ROOT,
        env=target_environment(binary), timeout=180, expected=1 if phase_name == "fault" else 0,
        campaign=NextCampaign(phase=phase))
    result, failed_step, classification = verify_case_report(
        report_path, fault, phase_name, case["expected_target_exit"])
    phase_receipt = {
        "schema_version": 1, "project": "fzy", "fault_id": fault["id"],
        "phase": phase_name, "evidence_phase": phase, "host": host,
        "scenario_id": case["id"], "scenario_sha256": sha256(spec_path),
        "source_archive_sha256": acquisition["archive_sha256"],
        "target_binary_sha256": build["binary_sha256"], "source_mutation": mutation,
        "candidate_archive_sha256": cell["archive_sha256"],
        "candidate_binary_sha256": cell["binary_sha256"],
        "runner_attempt_id": command_result["id"], "invocation_id": result["invocation_id"],
        "report": report_path.relative_to(ROOT).as_posix(),
        "report_sha256": sha256(report_path), "classification": classification,
        "failure_category": result.get("failure", {}).get("category") if failed_step else None,
        "failed_step": failed_step.get("number") if failed_step else None,
        "target_exit": result.get("target", {}).get("exit_code"),
        "target_cleanup_confirmed": result["cleanup"]["confirmed_exited"],
        "workspace_cleaned": result["workspace"]["cleaned"],
        "upstream_tests": "passed on pristine source",
    }
    immutable_json(evidence / "phase-result-v1.json", phase_receipt)
    window = cleanup_window(fault["id"], phase_name, host)
    await command([sys.executable, "-B", "scripts/acceptance/next20_target_cleanup.py",
                   "--project", "fzy", "--include-active-case-evidence", "--window", window],
                  "core", f"fzy-{fault['id']}-{phase_name}-{host}-cleanup", phase)
    require(not target.exists(), "fzy owned target tree remains after source-fault cleanup")
    return phase_receipt


async def run(host):
    if platform.system() != {"linux": "Linux", "darwin": "Darwin"}[host]:
        raise RuntimeError("actual native host differs from fzy fault declaration")
    declaration, scenario_decl, freeze, faults = load_contract()
    results = []
    for fault, case, spec_path in faults:
        for phase_name in ("baseline", "fault", "restored"):
            results.append(await phase_run(host, fault, case, spec_path, phase_name,
                                           scenario_decl["candidate"], freeze))
    root = RAW / "fzy" / "fault-calibration-v1"
    final = root / f"run-{os.environ.get('GITHUB_RUN_ID', 'local')}-{host}.json"
    immutable_json(final, {
        "schema_version": 1, "project": "fzy", "repository": "jhawthorn/fzy",
        "pin": PIN, "candidate": scenario_decl["candidate"],
        "candidate_series": scenario_decl["candidate_series"], "host": host,
        "fault_declaration_sha256": sha256(DECLARATION),
        "scenario_declaration_sha256": sha256(PROJECT / "scenario-declaration-v1.json"),
        "results": results, "phase_execution_count": len(results),
        "distinct_detected_source_faults": sum(row["phase"] == "fault" for row in results),
        "admission_credit": 0,
    })
    require(len(results) == 9 and sum(row["classification"] == "expected-target-fault-rejection"
                                      for row in results) == 3,
            "fzy source-fault matrix did not produce three detected faults and nine phases")
    print(json.dumps({"project": "fzy", "host": host,
                      "faults": declaration["distinct_detected_faults"],
                      "phase_execution_count": len(results), "admission_credit": 0}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    args = parser.parse_args()
    asyncio.run(run(args.host))


if __name__ == "__main__":
    main()
