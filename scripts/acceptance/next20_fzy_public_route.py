"""Exercise fzy's public record, review, replay, maintenance and preview routes."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256


PROJECT = "fzy"
PACKAGE = DOC / PROJECT
DECLARATION = PACKAGE / "public-route-declaration-v1.json"
PIN = "34b88869d022e861da4846c4463aea3ddfb3ff30"
ARCHIVE_SHA256 = "d55d4d0dcbced2daa0dd16b42ee0fc31654bd038ff6a147b38580c233d62c967"
HOSTS = {"linux": "Linux", "darwin": "Darwin"}


def require(value, message):
    if not value:
        raise ValueError(message)


def verify_report(path, status):
    report = json.loads(path.read_text(encoding="utf-8"))
    require(report.get("report_version") == 3 and report.get("runner_version") == "v0.4.0-rc.8"
            and report.get("summary", {}).get("total") == 1
            and len(report.get("results", [])) == 1,
            "fzy public-route report schema/candidate/denominator differs")
    result = report["results"][0]
    require(result.get("status") == status
            and result.get("cleanup", {}).get("confirmed_exited") is True
            and result.get("workspace", {}).get("cleaned") is True,
            "fzy public-route status or target/workspace cleanup differs")
    if status == "passed":
        require(all(step.get("status") == "passed" for step in result.get("steps", [])),
                "passing fzy public route contains a failed or unrun step")
    return report, result


def report_state(report):
    states = [step.get("state", {}) for step in report["results"][0].get("steps", [])
              if step.get("action") == "state"]
    require(len(states) == 1 and states[0].get("path") == "result.txt"
            and states[0].get("kind") == "file" and states[0].get("outcome") == "matched",
            "fzy public route report does not confirm the selected result.txt bytes matched")


async def main_async(host):
    require(platform.system() == HOSTS[host], "actual native host differs from fzy public-route host")
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    freeze_path = ROOT / declaration["candidate_freeze"]
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    scenario_path = ROOT / declaration["scenario_declaration"]
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))
    require(declaration.get("project") == PROJECT and declaration.get("source_pin") == PIN
            and declaration.get("source_archive_sha256") == ARCHIVE_SHA256
            and declaration.get("candidate") == freeze.get("version") == "v0.4.0-rc.8"
            and declaration.get("candidate_series") == freeze.get("series") == "native-exit-v3"
            and declaration.get("candidate_freeze_sha256") == sha256(freeze_path)
            and declaration.get("scenario_declaration_sha256") == sha256(scenario_path)
            and scenario.get("saved_state_coverage_credit") == 0
            and declaration.get("hosts") == ["linux", "darwin"],
            "fzy public-route source/candidate/scenario declaration differs")
    initial_fixture = base64.b64decode(declaration["first_use_fixture_base64"], validate=True)
    maintenance_fixture = base64.b64decode(declaration["maintenance_fixture_base64"], validate=True)
    runner = executable("native-exit-v3", host)
    installed = json.loads((runner.parent / "installed.json").read_text(encoding="utf-8"))
    cell = next(row for row in freeze["cells"] if row["host"] == host)
    require(installed.get("archive_sha256") == cell["archive_sha256"]
            and installed.get("binary_sha256") == cell["binary_sha256"],
            "fzy public route candidate archive differs from exact frozen rc.8")
    active = RAW / "active/fzy"
    target_binary = active / "install/bin/fzy"
    build = json.loads((active / "build.json").read_text(encoding="utf-8"))
    runtime = json.loads((active / "runtime.json").read_text(encoding="utf-8"))
    require(build.get("pin") == PIN and build.get("host") == host
            and build.get("upstream_tests") == "passed"
            and sha256(target_binary) == build.get("binary_sha256")
            and runtime.get("native_sha256") == build.get("binary_sha256"),
            "fzy public route target differs from its native build/runtime receipt")

    output = RAW / PROJECT / "public-route-v1" / host
    output.mkdir(parents=True, exist_ok=False)
    project = output / "project"
    fixtures = project / "fixtures"
    fixtures.mkdir(parents=True)
    fixture = fixtures / "choices.txt"
    fixture.write_bytes(initial_fixture)
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env["PATH"] = str(target_binary.parent) + os.pathsep + env.get("PATH", "")
    env.update({"TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"})
    campaign = NextCampaign(phase="public-authoring")
    attempts = []

    async def run(argv, label, *, input_text=None, expected=0, timeout=180):
        try:
            result = await execute(list(map(str, argv)), PROJECT, label, cwd=ROOT, env=env,
                                   input=input_text, expected=expected, timeout=timeout,
                                   campaign=campaign)
        except Exception as error:
            evidence = Path(getattr(error, "evidence_directory", ""))
            console = evidence / "console.log"
            if console.is_file() and console.resolve().is_relative_to(RAW.resolve()):
                detail = console.read_text(encoding="utf-8", errors="replace")[-4096:]
                raise RuntimeError(f"{error}\n--- bounded public-route output ---\n{detail}") from error
            raise
        attempts.append({"attempt_id": result["id"], "label": label,
                         "returncode": result["returncode"], "seconds": round(result["seconds"], 3)})
        return result

    version = await run([runner, "--version"], "fzy-public-route-candidate-version")
    require(version["output"].strip() == "playtestr v0.4.0-rc.8",
            "fzy public route did not invoke the frozen candidate")
    spec = project / "fzy-select.json"
    command = "exec fzy < choices.txt > result.txt"
    record_argv = [runner, "record", "--output", spec.relative_to(ROOT),
                   "--name", "Select a fzy choice and review exact emitted bytes",
                   "--fixture", "fixtures", "--temporary-home", "--temporary-temp",
                   "--width", "80", "--height", "12", "--timeout-ms", "12000",
                   "--run-timeout-ms", "60000", "--env", "TERM=xterm-256color",
                   "--env", "LANG=C.UTF-8", "--env", "LC_ALL=C.UTF-8",
                   "--inherit-env", "PATH", "--", "/bin/sh", "-c", command]
    controls = declaration["record_controls"]
    await run(record_argv, "fzy-first-use-record-review-replay-save",
              input_text="\n".join(controls) + "\n", timeout=240)
    require(spec.is_file(), "fzy public recorder did not export the first-use test")
    recorded = json.loads(spec.read_text(encoding="utf-8"))
    require(recorded.get("version") == 3 and recorded.get("command") == ["/bin/sh", "-c", command]
            and recorded.get("workspace", {}).get("fixture") == "fixtures"
            and recorded.get("inherit_env") == ["PATH"]
            and recorded.get("steps", [])[-2:] == [
                {"exit": 0}, {"state": {"path": "result.txt", "kind": "file",
                                      "bytes_base64": declaration["first_use_output_base64"]}}],
            "fzy public recorder export differs from its recorded CLI/fixture/output contract")
    first_report_path = output / "first-use-report.json"
    await run([runner, "test", "--report", first_report_path.relative_to(ROOT), "--artifacts-dir",
               (output / "first-use-artifacts").relative_to(ROOT), spec.relative_to(ROOT)],
              "fzy-public-first-use-ordinary-test")
    first_report, _ = verify_report(first_report_path, "passed")
    report_state(first_report)

    diagnosis = output / "diagnosis"
    shutil.copytree(project, diagnosis)
    broken_spec = diagnosis / spec.name
    broken = json.loads(broken_spec.read_text(encoding="utf-8"))
    states = [step for step in broken["steps"] if "state" in step]
    require(len(states) == 1, "fzy diagnosis cannot find its unique result-file state")
    states[0]["state"]["bytes_base64"] = "AQ=="
    broken_spec.write_text(json.dumps(broken, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8", newline="\n")
    diagnosis_report_path = output / "diagnosis-report.json"
    await run([runner, "test", "--report", diagnosis_report_path.relative_to(ROOT), "--artifacts-dir",
               (output / "diagnosis-artifacts").relative_to(ROOT), broken_spec.relative_to(ROOT)],
              "fzy-seeded-saved-output-diagnosis", expected=1)
    diagnosis_report, diagnosis_result = verify_report(diagnosis_report_path, "failed")
    failed_steps = [step for step in diagnosis_result.get("steps", []) if step.get("status") == "failed"]
    require(diagnosis_result.get("failure", {}).get("category") == "state_assertion_failure"
            and len(failed_steps) == 1 and failed_steps[0].get("number") == 4
            and diagnosis_report.get("summary", {}).get("failed") == 1,
            "fzy seeded wrong-file-bytes diagnosis missed its exact state failure")

    maintenance = output / "maintenance"
    shutil.copytree(project, maintenance)
    maintenance_fixture_path = maintenance / "fixtures/choices.txt"
    maintenance_fixture_path.write_bytes(maintenance_fixture)
    maintenance_spec = maintenance / spec.name
    before = json.loads(maintenance_spec.read_text(encoding="utf-8"))
    maintenance_controls = declaration["maintenance_controls"]
    await run([runner, "record", "--edit", maintenance_spec.relative_to(ROOT)],
              "fzy-selected-output-maintenance", input_text="\n".join(maintenance_controls) + "\n",
              timeout=240)
    maintained = json.loads(maintenance_spec.read_text(encoding="utf-8"))
    expected = json.loads(json.dumps(before))
    expected["steps"][-1]["state"]["bytes_base64"] = declaration["maintenance_output_base64"]
    require(maintained == expected, "fzy public maintenance changed an unselected spec field")
    maintenance_report_path = output / "maintenance-report.json"
    await run([runner, "test", "--report", maintenance_report_path.relative_to(ROOT), "--artifacts-dir",
               (output / "maintenance-artifacts").relative_to(ROOT), maintenance_spec.relative_to(ROOT)],
              "fzy-maintained-contract-ordinary-test")
    maintenance_report, _ = verify_report(maintenance_report_path, "passed")
    report_state(maintenance_report)

    relocated = output / "relocated space café 雪"
    shutil.copytree(maintenance, relocated)
    relocated_spec = relocated / spec.name
    relocation_report_path = output / "relocation-report.json"
    await run([runner, "test", "--report", relocation_report_path.relative_to(ROOT), "--artifacts-dir",
               (output / "relocation-artifacts").relative_to(ROOT), relocated_spec.relative_to(ROOT)],
              "fzy-public-unicode-space-relocation")
    relocation_report, _ = verify_report(relocation_report_path, "passed")
    report_state(relocation_report)

    revision = os.environ.get("GITHUB_SHA", "")
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                  capture_output=True, text=True, timeout=10).stdout.strip()
    setup = "git clone --no-checkout https://github.com/jhawthorn/fzy.git fzy-source && git -C fzy-source checkout --detach " + PIN
    build_command = 'cd fzy-source && make -j2 && make test && make PREFIX="$HOME/.local" install'
    suite = relocated_spec.relative_to(ROOT).as_posix()
    preview = await run([runner, "workflow", "--source-revision", revision, "--os", "linux",
                         "--suite", suite, "--setup", setup, "--build", build_command, "--print"],
                        "fzy-public-workflow-preview")
    preview_path = output / "workflow-preview.yml"
    preview_path.write_text(preview["output"], encoding="utf-8", newline="\n")
    preview_text = preview_path.read_text(encoding="utf-8")
    require(all(value in preview_text for value in
                (revision, suite, PIN, setup, build_command, "pull_request:")),
            "fzy workflow preview omitted reviewed source, suite, pin, build or event")

    receipt = {
        "schema_version": 1, "project": PROJECT, "host": host,
        "architecture": platform.machine(), "repository": "jhawthorn/fzy",
        "source_pin": PIN, "source_archive_sha256": ARCHIVE_SHA256,
        "candidate": freeze["version"], "candidate_series": freeze["series"],
        "candidate_archive_sha256": cell["archive_sha256"],
        "candidate_binary_sha256": cell["binary_sha256"],
        "runner_sha256": sha256(runner), "target_binary_sha256": sha256(target_binary),
        "build_receipt_sha256": sha256(active / "build.json"),
        "route_declaration_sha256": sha256(DECLARATION),
        "scenario_declaration_sha256": sha256(scenario_path),
        "recorded_spec_sha256": sha256(spec), "maintenance_spec_sha256": sha256(maintenance_spec),
        "fixture_initial_sha256": sha256(fixtures / "choices.txt"),
        "fixture_maintenance_sha256": sha256(maintenance_fixture_path),
        "first_use": "passed", "first_use_output_base64": declaration["first_use_output_base64"],
        "diagnosis": "state_assertion_failure at step 4", "maintenance": "passed-selected-state-update",
        "relocation": "passed-unicode-and-spaces", "workflow_preview": "reviewed-only-not-dispatched",
        "preview_sha256": sha256(preview_path), "attempts": attempts,
        "target_cleanup_confirmed": all(item.get("cleanup", {}).get("confirmed_exited") is True
                                         and item.get("workspace", {}).get("cleaned") is True
                                         for report in (first_report, diagnosis_report,
                                                        maintenance_report, relocation_report)
                                         for item in report.get("results", [])),
        "human_participants": 0, "usability": "unmeasured", "admission_credit": 0,
        "saved_state_coverage_credit": 0,
    }
    immutable_json(output / "receipt-v1.json", receipt)
    print(json.dumps({"project": PROJECT, "host": host, "first_use": "passed",
                      "diagnosis": "state_assertion_failure at step 4",
                      "maintenance": "passed", "relocation": "passed",
                      "attempts": len(attempts), "admission_credit": 0}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    args = parser.parse_args()
    asyncio.run(main_async(args.host))


if __name__ == "__main__":
    main()
