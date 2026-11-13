"""Exercise Pick's documented record/review/replay/save and maintenance route."""
import argparse
import asyncio
from datetime import datetime, timezone
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

PROJECT = "pick"
PIN = "caae95938359b2e814b3e7406f396f486c9d99fb"
ARCHIVE_SHA256 = "e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653"
HOSTS = {"linux": "Linux", "darwin": "Darwin"}
INITIAL_FIXTURE = (b"".join(f"item{index:02d}\n".encode("ascii") for index in range(29))
                   + b"tail-choice\n")
RECORDER_CONTROLS = [
    "/expect item00", "/snapshot initial-menu.txt", "/key End",
    "/expect tail-choice", "/key Enter", "/exit 0",
    "/review", "/replay", "/save",
]
MAINTENANCE_CONTROLS = [
    '/replace 4 {"expect":"revised-tail-choice"}',
    "/review", "/replay", "/save",
]
DECLARATION = DOC / "pick/public-route-declaration-v1.json"


def need(value, message):
    if not value:
        raise ValueError(message)


def report_result(path, status):
    report = json.loads(path.read_text(encoding="utf-8"))
    need(report.get("report_version") == 3 and len(report.get("results", [])) == 1,
         "Pick public route report schema/denominator differs")
    result = report["results"][0]
    need(result.get("status") == status, f"Pick public route expected {status} result")
    need(result.get("cleanup", {}).get("confirmed_exited") is True
         and result.get("workspace", {}).get("cleaned") is True,
         "Pick public route report lacks target/workspace cleanup confirmation")
    if status == "passed":
        need(all(step.get("status") == "passed" for step in result.get("steps", [])),
             "passing Pick public route report has a non-passing step")
    return result


async def main_async(host):
    need(platform.system() == HOSTS[host], "actual native host differs from Pick public-route host")
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    freeze_path = ROOT / declaration["candidate_freeze"]
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    need(declaration.get("project") == PROJECT and declaration.get("source_pin") == PIN
         and declaration.get("source_archive_sha256") == ARCHIVE_SHA256
         and declaration.get("candidate") == freeze.get("version") == "v0.4.0-rc.8"
         and declaration.get("candidate_series") == freeze.get("series") == "native-exit-v3"
         and declaration.get("candidate_freeze_sha256") == sha256(freeze_path)
         and declaration.get("hosts") == ["linux", "darwin"]
         and declaration.get("record_controls") == RECORDER_CONTROLS
         and declaration.get("maintenance_controls") == MAINTENANCE_CONTROLS,
         "Pick public-route declaration/source/candidate identity differs")
    runner = executable("native-exit-v3", host)
    target_root = RAW / "active" / PROJECT
    target = target_root / "install/bin/pick"
    build = json.loads((target_root / "build.json").read_text(encoding="utf-8"))
    runtime = json.loads((target_root / "runtime.json").read_text(encoding="utf-8"))
    need(build.get("project") == PROJECT and build.get("pin") == PIN and build.get("host") == host
         and build.get("runtime_kind") == "native" and sha256(target) == build.get("binary_sha256")
         and runtime.get("native_sha256") == build.get("binary_sha256"),
         "Pick public route target differs from its native build receipt")
    candidate = next(cell for cell in freeze["cells"] if cell["host"] == host)
    installed_path = runner.parent / "installed.json"
    installed = json.loads(installed_path.read_text(encoding="utf-8"))
    need(installed.get("archive_sha256") == candidate["archive_sha256"]
         and installed.get("binary_sha256") == candidate["binary_sha256"],
         "Pick public route does not use the exact frozen candidate archive")
    output = RAW / PROJECT / "public-route-v1" / host
    need(not output.exists(), "preserve existing Pick public-route evidence")
    output.mkdir(parents=True)
    project = output / "project"
    fixtures = project / "fixtures"
    fixtures.mkdir(parents=True)
    (fixtures / "choices.txt").write_bytes(INITIAL_FIXTURE)
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env["PATH"] = str(target.parent) + os.pathsep + env.get("PATH", "")
    env.update({"TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"})
    campaign = NextCampaign(phase="public-authoring")
    attempts = []

    async def run(argv, label, *, input_text=None, expected=0, timeout=180):
        result = await execute(list(map(str, argv)), PROJECT, label, cwd=ROOT, env=env,
                               input=input_text, expected=expected, timeout=timeout,
                               campaign=campaign)
        attempts.append({"id": result["id"], "label": label, "returncode": result["returncode"],
                         "seconds": round(result["seconds"], 3)})
        return result

    version = await run([runner, "--version"], "pick-public-route-runner-version")
    need(version["output"].strip() == "playtestr " + freeze["version"],
         "public route did not invoke the frozen candidate version")
    spec = project / "pick-blue.json"
    record_argv = [runner, "record", "--output", spec.relative_to(ROOT),
                   "--name", "Select a named Pick choice beyond the initial viewport", "--fixture", "fixtures",
                   "--temporary-home", "--temporary-temp", "--width", "80", "--height", "8",
                   "--timeout-ms", "12000", "--run-timeout-ms", "60000",
                   "--env", "TERM=xterm-256color", "--env", "LANG=C.UTF-8", "--env", "LC_ALL=C.UTF-8",
                   "--inherit-env", "PATH", "--", "/bin/sh", "-c", "exec pick < choices.txt"]
    try:
        await run(record_argv, "pick-first-use-record-review-replay-save",
                  input_text="\n".join(RECORDER_CONTROLS) + "\n", timeout=240)
    except RuntimeError as error:
        evidence_dir = Path(getattr(error, "evidence_directory", ""))
        console = evidence_dir / "console.log"
        if console.is_file() and console.resolve().is_relative_to(RAW.resolve()):
            data = console.read_bytes()
            failure_receipt = {"schema_version": 1, "project": PROJECT, "host": host,
                               "phase": "public-authoring", "attempt_id": getattr(error, "evidence_id", None),
                               "error": str(error)[:2048], "console_sha256": sha256(console),
                               "console_bytes": len(data),
                               "console_tail": data[-4096:].decode("utf-8", "replace"),
                               "admission_credit": 0}
            immutable_json(output / "first-record-failure.json", failure_receipt)
            print("Pick first-use recorder failure console tail:\n" +
                  failure_receipt["console_tail"], file=sys.stderr)
        raise
    need(spec.is_file(), "Pick recorder did not export the first-use spec")
    recorded = json.loads(spec.read_text(encoding="utf-8"))
    steps = recorded.get("steps", [])
    need(recorded.get("version") == 3 and recorded.get("command") ==
         ["/bin/sh", "-c", "exec pick < choices.txt"]
         and recorded.get("workspace", {}).get("fixture") == "fixtures"
         and any(step.get("snapshot") == "initial-menu.txt" for step in steps)
         and any(step.get("key") == "End" for step in steps)
         and any(step.get("expect") == "tail-choice" for step in steps)
         and steps[-1] == {"exit": 0},
         "Pick public recorder export differs from reviewed first-use controls")

    first_report = output / "first-use-report.json"
    await run([runner, "test", "--report", first_report.relative_to(ROOT), "--artifacts-dir",
               (output / "first-use-artifacts").relative_to(ROOT), spec.relative_to(ROOT)],
              "pick-first-use-ordinary-test")
    first_result = report_result(first_report, "passed")

    diagnosis = output / "diagnosis"
    shutil.copytree(project, diagnosis)
    broken_spec = diagnosis / spec.name
    broken = json.loads(broken_spec.read_text(encoding="utf-8"))
    item_expectations = [step for step in broken["steps"] if step.get("expect") == "tail-choice"]
    need(len(item_expectations) == 1, "Pick diagnosis cannot find a unique selected-item assertion")
    item_expectations[0]["expect"] = "IMPOSSIBLE_PICK_SCREEN_MARKER"
    broken_spec.write_text(json.dumps(broken, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    diagnosis_report = output / "diagnosis-report.json"
    await run([runner, "test", "--report", diagnosis_report.relative_to(ROOT), "--artifacts-dir",
               (output / "diagnosis-artifacts").relative_to(ROOT), broken_spec.relative_to(ROOT)],
              "pick-seeded-rendered-screen-diagnosis", expected=1)
    diagnosis_result = report_result(diagnosis_report, "failed")
    failure = diagnosis_result.get("failure") or {}
    need(failure.get("category") == "assertion_timeout" and failure.get("message"),
         "Pick screen diagnosis lacks an actionable assertion category/message")

    maintenance = output / "maintenance"
    shutil.copytree(project, maintenance)
    maintenance_choices = maintenance / "fixtures" / "choices.txt"
    maintenance_choices.write_bytes(maintenance_choices.read_bytes().replace(
        b"tail-choice\n", b"revised-tail-choice\n"))
    maintenance_spec = maintenance / spec.name
    before = json.loads(maintenance_spec.read_text(encoding="utf-8"))
    before_report = output / "maintenance-before-report.json"
    await run([runner, "test", "--report", before_report.relative_to(ROOT), "--artifacts-dir",
               (output / "maintenance-before-artifacts").relative_to(ROOT), maintenance_spec.relative_to(ROOT)],
              "pick-maintenance-original-contract")
    report_result(before_report, "passed")
    edit_controls = ['/replace 4 {"expect":"revised-tail-choice"}', "/review", "/replay", "/save"]
    await run([runner, "record", "--edit", maintenance_spec.relative_to(ROOT)],
              "pick-selective-query-and-oracle-maintenance",
              input_text="\n".join(edit_controls) + "\n", timeout=240)
    maintained = json.loads(maintenance_spec.read_text(encoding="utf-8"))
    expected = json.loads(json.dumps(before))
    for step in expected["steps"]:
        if step.get("expect") == "tail-choice":
            step["expect"] = "revised-tail-choice"
    need(maintained == expected, "Pick selective maintenance changed unrelated recorded steps")
    maintained_report = output / "maintenance-report.json"
    await run([runner, "test", "--report", maintained_report.relative_to(ROOT), "--artifacts-dir",
               (output / "maintenance-artifacts").relative_to(ROOT), maintenance_spec.relative_to(ROOT)],
              "pick-maintained-ordinary-test")
    maintained_result = report_result(maintained_report, "passed")

    relocated = output / "relocated space cafÃ© é›ª"
    shutil.copytree(maintenance, relocated)
    relocated_spec = relocated / spec.name
    relocation_report = output / "relocation-report.json"
    await run([runner, "test", "--report", relocation_report.relative_to(ROOT), "--artifacts-dir",
               (output / "relocation-artifacts").relative_to(ROOT), relocated_spec.relative_to(ROOT)],
              "pick-unicode-space-relocation")
    relocation_result = report_result(relocation_report, "passed")

    revision = os.environ.get("GITHUB_SHA", "")
    if len(revision) != 40 or any(char not in "0123456789abcdef" for char in revision):
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                  capture_output=True, text=True, timeout=10).stdout.strip()
    setup = "git clone --no-checkout https://github.com/mptre/pick.git pick-source && git -C pick-source checkout --detach " + PIN
    build = 'cd pick-source && ./configure --prefix="$HOME/.local" && make -j2 && make test && make install'
    suite = spec.relative_to(ROOT).as_posix()
    preview = await run([runner, "workflow", "--source-revision", revision, "--os", "linux",
                         "--suite", suite, "--setup", setup, "--build", build, "--print"],
                        "pick-public-workflow-preview")
    preview_path = output / "delivered-workflow-preview.yml"
    preview_path.write_text(preview["output"], encoding="utf-8", newline="\n")
    preview_text = preview_path.read_text(encoding="utf-8")
    need(all(value in preview_text for value in (revision, suite, PIN, setup, build, "pull_request:")),
         "Pick delivered-workflow preview omitted source revision, suite, pin, setup/build or event")

    receipt = {
        "schema_version": 1, "project": PROJECT, "host": host, "architecture": platform.machine(),
        "source_pin": PIN, "source_archive_sha256": ARCHIVE_SHA256,
        "candidate": freeze["version"], "candidate_series": freeze["series"],
        "candidate_archive_sha256": candidate["archive_sha256"],
        "candidate_binary_sha256": candidate["binary_sha256"],
        "runner_sha256": sha256(runner), "target_binary_sha256": sha256(target),
        "build_sha256": sha256(target_root / "build.json"), "route_declaration_sha256": sha256(DECLARATION),
        "record_controls": RECORDER_CONTROLS, "maintenance_controls": edit_controls,
        "attempts": attempts,
        "first_use": {"status": "passed", "handwritten_spec": False, "spec_sha256": sha256(spec),
                      "report_sha256": sha256(first_report), "invocation_id": first_result["invocation_id"]},
        "diagnosis": {"status": "failed-as-seeded", "category": failure["category"],
                      "message": failure["message"], "report_sha256": sha256(diagnosis_report)},
        "maintenance": {"status": "passed", "selected_steps_only": maintained == expected,
                         "fixture_oracle_updated": maintenance_choices.read_bytes().endswith(b"revised-tail-choice\n"),
                         "report_sha256": sha256(maintained_report),
                         "invocation_id": maintained_result["invocation_id"]},
        "relocation": {"status": "passed", "path": "relocated space cafÃ© é›ª",
                       "report_sha256": sha256(relocation_report),
                       "invocation_id": relocation_result["invocation_id"]},
        "delivered_workflow_preview": {"status": "generated-reviewed-not-dispatched", "revision": revision,
                                       "suite": suite, "sha256": sha256(preview_path),
                                       "provider_run": None},
        "human_participants": 0, "usability": "unmeasured", "admission_credit": 0,
        "scope": "Exact rc.8 record/review/replay/save, seeded failure diagnosis, selective query/oracle maintenance, Unicode relocation and source-built free workflow preview.",
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    immutable_json(output / "receipt.json", receipt)
    print(json.dumps({"status": "public-route-passed-not-admitted", "project": PROJECT,
                      "host": host, "attempts": len(attempts), "admission_credit": 0}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    asyncio.run(main_async(parser.parse_args().host))


if __name__ == "__main__":
    main()
