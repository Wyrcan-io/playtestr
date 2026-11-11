"""Exercise JOE's documented first-use and selected maintenance routes."""
import argparse
import asyncio
import base64
import hashlib
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

PROJECT = "joe"
PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
MARKER = "JOE_PUBLIC_ROUTE_RC6"
INITIAL = b"JOE_PUBLIC_ROUTE_START\n"
EXPECTED_HOST = {"linux": "Linux", "darwin": "Darwin"}
CONTROL_SEQUENCE = [
    "/expect JOE_PUBLIC_ROUTE_START",
    "/snapshot initial-note.txt",
    "/key End",
    f"/text {json.dumps(MARKER)}",
    f"/expect {MARKER}",
    "/key CtrlK",
    '/text "x"',
    "/exit 0",
    "/file public-note.txt",
    "/review",
    "/replay",
    "/save",
]


def report_result(path, status):
    value = json.loads(path.read_text(encoding="utf-8"))
    if len(value.get("results", [])) != 1:
        raise ValueError("JOE route did not produce exactly one report result")
    result = value["results"][0]
    if result.get("status") != status:
        raise ValueError(f"expected JOE report status {status}")
    if not result.get("cleanup", {}).get("confirmed_exited") or not result.get("workspace", {}).get("cleaned"):
        raise ValueError("JOE candidate report lacks target/workspace cleanup confirmation")
    if status == "passed" and any(step.get("status") != "passed" for step in result.get("steps", [])):
        raise ValueError("passing JOE report has a non-passing step")
    return result


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    args = parser.parse_args()
    host = args.host
    if platform.system() != EXPECTED_HOST[host]:
        raise RuntimeError("actual native host differs from declared JOE public-route host")
    target_root = RAW / "active" / PROJECT
    build_path = target_root / "build.json"
    runtime_path = target_root / "runtime.json"
    binary = target_root / "install/bin/joe"
    build = json.loads(build_path.read_text(encoding="utf-8"))
    runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
    if (build.get("project") != PROJECT or build.get("pin") != PIN or build.get("host") != host or
            build.get("runtime_kind") != "native" or runtime.get("runtime_kind") != "native" or
            sha256(binary) != build.get("binary_sha256") or
            runtime.get("native_sha256") != build.get("binary_sha256")):
        raise ValueError("JOE public route target does not match its exact native build receipt")

    runner = executable("native-exit-v1", host)
    installed = json.loads((runner.parent / "installed.json").read_text(encoding="utf-8"))
    if installed.get("archive_sha256") != next(row["archive_sha256"] for row in
            json.loads((DOC / "replacement-candidate-freeze-native-exit-v1.json").read_text())["cells"]
            if row["host"] == host):
        raise ValueError("JOE public route did not install the exact frozen rc.6 archive")

    output = RAW / PROJECT / "public-route-v1" / host
    if output.exists():
        raise ValueError("preserve an existing JOE public-route evidence directory")
    output.mkdir(parents=True)
    build_log_root = output / "build-logs"
    build_log_root.mkdir()
    retained_build_logs = []
    if len(build.get("commands", [])) != 7:
        raise ValueError("JOE public route requires the seven-command reviewed native build receipt")
    for index, command in enumerate(build["commands"], 1):
        declared_log = ROOT / command["log"]
        if declared_log.is_symlink() or getattr(declared_log, "is_junction", lambda: False)():
            raise ValueError("JOE build command log cannot be a link")
        source_log = declared_log.resolve(strict=True)
        source_log.relative_to(target_root.resolve())
        if source_log.is_symlink() or not source_log.is_file() or source_log.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("JOE build command log is not a bounded owned regular file")
        if len(retained_build_logs) >= 7 or sha256(source_log) != command.get("output_sha256"):
            raise ValueError("JOE build command log differs from its pre-cleanup receipt")
        destination = build_log_root / f"{index:02d}-{source_log.name}"
        with destination.open("xb") as stream:
            stream.write(source_log.read_bytes())
        retained_build_logs.append({"command_id": command["id"], "log": destination.name,
                                    "bytes": destination.stat().st_size, "sha256": sha256(destination),
                                    "exit_code": command["exit_code"],
                                    "process_tree_cleanup": command["process_tree_cleanup"]})
    if len(retained_build_logs) != 7:
        raise ValueError("JOE public route did not retain all seven native build command logs")
    immutable_json(output / "build-logs.json", {"schema_version": 1, "project": PROJECT,
                                                  "host": host, "pin": PIN,
                                                  "commands": retained_build_logs})
    project_root = output / "project"
    fixtures = project_root / "fixtures"
    fixtures.mkdir(parents=True)
    (fixtures / "public-note.txt").write_bytes(INITIAL)

    env = dict(os.environ)
    env["PATH"] = str(binary.parent) + os.pathsep + env.get("PATH", "")
    env.update(TERM="xterm-256color", LANG="C.UTF-8", LC_ALL="C.UTF-8")
    campaign = NextCampaign(phase="public-authoring")
    attempts = []
    planned = {
        "schema_version": 1, "project": PROJECT, "phase": "public-authoring",
        "candidate": "v0.4.0-rc.6", "candidate_archive_sha256": installed["archive_sha256"],
        "runner_sha256": sha256(runner), "source_pin": PIN, "target_binary_sha256": sha256(binary),
        "target_build_run": os.environ.get("GITHUB_RUN_ID"), "host": host,
        "architecture": platform.machine(), "fixture_bytes_base64": base64.b64encode(INITIAL).decode(),
        "no_handwritten_first_use_spec": True, "first_use_controls": CONTROL_SEQUENCE,
        "first_use_shell_invocations_expected": 3, "first_use_control_count": len(CONTROL_SEQUENCE),
        "diagnosis": "wrong rendered-screen expectation; retain category, useful evidence and next action",
        "maintenance": "change intended text and screen expectation, observe stale saved bytes fail, rerecord only that state",
        "relocation": "complete project copy beneath a spaced Unicode path",
        "delivered_workflow": "generate/review a pinned free workflow preview only; do not dispatch",
        "target_runtime": "explicitly trusted pinned JOE executable; no JOE shell/command feature used",
        "project_admission_credit": 0,
    }
    immutable_json(output / "planned.json", planned)

    async def run(argv, label, *, input=None, expected=0, timeout=180):
        result = await execute(argv, PROJECT, label, cwd=ROOT, env=env, input=input,
                               expected=expected, timeout=timeout, campaign=campaign)
        attempts.append({"id": result["id"], "label": label, "returncode": result["returncode"],
                         "seconds": round(result["seconds"], 3)})
        return result

    version = await run([runner, "--version"], "joe-public-route-runner-version")
    if version["output"].strip() != "playtestr v0.4.0-rc.6":
        raise ValueError("public route did not use the exact private runner candidate")

    spec = project_root / "create-note.json"
    record_argv = [runner, "record", "--output", spec.relative_to(ROOT),
                   "--name", "Append and save a note in JOE", "--fixture", "fixtures",
                   "--temporary-home", "--temporary-temp", "--width", "80", "--height", "24",
                   "--timeout-ms", "12000", "--run-timeout-ms", "60000",
                   "--env", "TERM=xterm-256color", "--env", "LANG=C.UTF-8", "--env", "LC_ALL=C.UTF-8",
                   "--inherit-env", "PATH", "--", "joe", "-nobackups", "public-note.txt"]
    try:
        await run(record_argv, "joe-first-public-record-review-replay-save",
                  input="\n".join(CONTROL_SEQUENCE) + "\n", timeout=240)
    except RuntimeError as error:
        evidence_dir = Path(getattr(error, "evidence_directory", ""))
        console = evidence_dir / "console.log"
        if console.is_file() and console.resolve().is_relative_to(RAW.resolve()):
            content = console.read_bytes()
            failure = {"schema_version": 1, "project": PROJECT, "host": host,
                       "phase": "public-authoring", "attempt_id": getattr(error, "evidence_id", None),
                       "error": str(error)[:2048], "console_sha256": sha256(console),
                       "console_bytes": len(content), "console_tail": content[-4096:].decode("utf-8", "replace"),
                       "admission_credit": 0}
            immutable_json(output / "first-record-failure.json", failure)
            print("JOE recorder failure console tail:\n" + failure["console_tail"], file=sys.stderr)
        raise
    if not spec.is_file():
        raise ValueError("JOE recorder did not export the first-use spec")
    recorded = json.loads(spec.read_text(encoding="utf-8"))
    states = [step["state"] for step in recorded.get("steps", [])
              if step.get("state", {}).get("path") == "public-note.txt"]
    expected_bytes = base64.b64encode(INITIAL[:-1] + MARKER.encode() + INITIAL[-1:]).decode("ascii")
    if (recorded.get("version") != 3 or recorded.get("command", [])[-2:] != ["-nobackups", "public-note.txt"] or
            recorded.get("workspace", {}).get("fixture") != "fixtures" or len(states) != 1 or
            states[0].get("kind") != "file" or states[0].get("bytes_base64") != expected_bytes or
            sum(step.get("snapshot") == "initial-note.txt" for step in recorded.get("steps", [])) != 1):
        raise ValueError("JOE public recorder output does not match the reviewed screen and exact file bytes")

    first_report = output / "first-use-report.json"
    await run([runner, "test", "--report", first_report.relative_to(ROOT), "--artifacts-dir",
               (output / "first-use-artifacts").relative_to(ROOT), spec.relative_to(ROOT)],
              "joe-first-public-ordinary-test")
    first_result = report_result(first_report, "passed")
    first_window_shells = 3
    first_window_controls = len(CONTROL_SEQUENCE)

    diagnosis = output / "diagnosis"
    shutil.copytree(project_root, diagnosis)
    wrong_spec = diagnosis / "create-note.json"
    broken = json.loads(wrong_spec.read_text(encoding="utf-8"))
    matches = [step for step in broken["steps"] if step.get("expect") == MARKER]
    if len(matches) != 1:
        raise ValueError("JOE seeded diagnosis cannot identify one unique screen checkpoint")
    matches[0]["expect"] = "WRONG_JOE_SCREEN_EXPECTATION"
    wrong_spec.write_text(json.dumps(broken, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    diagnosis_report = output / "diagnosis-report.json"
    await run([runner, "test", "--report", diagnosis_report.relative_to(ROOT), "--artifacts-dir",
               (output / "diagnosis-artifacts").relative_to(ROOT), wrong_spec.relative_to(ROOT)],
              "joe-public-seeded-screen-diagnosis", expected=1)
    diagnosis_result = report_result(diagnosis_report, "failed")
    failure = diagnosis_result.get("failure") or {}
    if not failure.get("category") or not failure.get("message"):
        raise ValueError("JOE seeded failure lacks a useful category/message")

    maintenance = output / "maintenance"
    shutil.copytree(project_root, maintenance)
    maintenance_spec = maintenance / "create-note.json"
    changed = json.loads(maintenance_spec.read_text(encoding="utf-8"))
    new_marker = MARKER + "_UPDATED"
    text_steps = [step for step in changed["steps"] if step.get("text") == MARKER]
    screen_steps = [step for step in changed["steps"] if step.get("expect") == MARKER]
    if len(text_steps) != 1 or len(screen_steps) != 1:
        raise ValueError("JOE selected maintenance cannot locate the intended input and screen fields")
    text_steps[0]["text"] = new_marker
    screen_steps[0]["expect"] = new_marker
    maintenance_spec.write_text(json.dumps(changed, sort_keys=True, indent=2) + "\n",
                                encoding="utf-8", newline="\n")
    before_report = output / "maintenance-before-report.json"
    await run([runner, "test", "--report", before_report.relative_to(ROOT), "--artifacts-dir",
               (output / "maintenance-before-artifacts").relative_to(ROOT), maintenance_spec.relative_to(ROOT)],
              "joe-intended-change-before-file-state-update", expected=1)
    before_result = report_result(before_report, "failed")
    if not (before_result.get("failure") or {}).get("category"):
        raise ValueError("JOE stale saved-file failure lacks a category")
    state_index = next(i for i, step in enumerate(changed["steps"], 1)
                       if step.get("state", {}).get("path") == "public-note.txt")
    edit_controls = [f"/update-state {state_index}", "/review", "/replay", "/save"]
    await run([runner, "record", "--edit", maintenance_spec.relative_to(ROOT)],
              "joe-selected-saved-file-state-maintenance", input="\n".join(edit_controls) + "\n", timeout=240)
    maintained = json.loads(maintenance_spec.read_text(encoding="utf-8"))
    new_states = [step["state"] for step in maintained["steps"]
                  if step.get("state", {}).get("path") == "public-note.txt"]
    updated_bytes = INITIAL[:-1] + new_marker.encode() + INITIAL[-1:]
    expected_updated = base64.b64encode(updated_bytes).decode("ascii")
    expected_document = json.loads(json.dumps(changed))
    expected_state = next(step["state"] for step in expected_document["steps"]
                          if step.get("state", {}).get("path") == "public-note.txt")
    expected_state["bytes_base64"] = expected_updated
    if len(new_states) != 1 or new_states[0].get("bytes_base64") != expected_updated or maintained != expected_document:
        raise ValueError("JOE selected maintenance changed unrelated spec bytes or captured wrong state")
    maintenance_report = output / "maintenance-report.json"
    await run([runner, "test", "--report", maintenance_report.relative_to(ROOT), "--artifacts-dir",
               (output / "maintenance-artifacts").relative_to(ROOT), maintenance_spec.relative_to(ROOT)],
              "joe-maintained-public-ordinary-test")
    report_result(maintenance_report, "passed")

    relocated = output / "relocated space café 雪"
    shutil.copytree(maintenance, relocated)
    relocation_spec = relocated / "create-note.json"
    relocation_report = output / "relocation-report.json"
    relocation = await run([runner, "test", "--report", relocation_report.relative_to(ROOT), "--artifacts-dir",
                            (output / "relocation-artifacts").relative_to(ROOT), relocation_spec.relative_to(ROOT)],
                           "joe-public-unicode-path-relocation")
    relocation_result = report_result(relocation_report, "passed")

    revision = os.environ.get("GITHUB_SHA", "")
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                  capture_output=True, text=True, timeout=10).stdout.strip()
    setup = ("git clone --no-checkout https://github.com/joe-editor/joe.git joe-source && "
             "git -C joe-source checkout --detach " + PIN)
    build_command = ("cd joe-source && autoreconf -fi && ./configure --prefix=\"$HOME/.local\" "
                     "&& make -j2 && make install")
    suite = spec.relative_to(ROOT).as_posix()
    generated = await run([runner, "workflow", "--source-revision", revision, "--os", "linux",
                           "--suite", suite, "--setup", setup, "--build", build_command, "--print"],
                          "joe-public-delivered-workflow-preview")
    workflow_file = output / "delivered-workflow-preview.yml"
    workflow_file.write_text(generated["output"], encoding="utf-8", newline="\n")
    workflow_text = workflow_file.read_text(encoding="utf-8")
    if any(value not in workflow_text for value in (revision, suite, PIN, setup, build_command, "pull_request:")):
        raise ValueError("generated JOE workflow preview omitted revision, suite, pin, setup/build or trigger")

    receipt = {
        "schema_version": 1, "project": PROJECT, "candidate": "v0.4.0-rc.6", "source_pin": PIN,
        "host": host, "architecture": platform.machine(), "runner_sha256": sha256(runner),
        "target_binary_sha256": sha256(binary), "target_build_run": os.environ.get("GITHUB_RUN_ID"),
        "planned_sha256": sha256(output / "planned.json"),
        "build_command_logs_sha256": sha256(output / "build-logs.json"), "attempts": attempts,
        "first_use": {"status": "passed", "shell_invocations": first_window_shells,
                      "controls": first_window_controls, "handwritten_spec": False,
                      "spec_sha256": sha256(spec), "report_sha256": sha256(first_report),
                      "invocation_id": first_result["invocation_id"], "saved_state_bytes_verified": True},
        "seeded_diagnosis": {"status": "failed-as-seeded", "category": failure["category"],
                             "message": failure["message"], "report_sha256": sha256(diagnosis_report)},
        "maintenance": {"stale_state_failure_report_sha256": sha256(before_report),
                        "updated_report_sha256": sha256(maintenance_report),
                        "selected_state_only": maintained == expected_document,
                        "updated_bytes_sha256": hashlib.sha256(updated_bytes).hexdigest()},
        "relocation": {"path": "relocated space café 雪", "passed": True,
                       "report_sha256": sha256(relocation_report),
                       "invocation_id": relocation_result["invocation_id"]},
        "delivered_workflow_preview": {"revision": revision, "suite": suite, "setup": setup,
                                       "build": build_command, "sha256": sha256(workflow_file),
                                       "provider_run": None, "dispatched": False},
        "human_participants": 0, "human_usability": "unmeasured",
        "project_admission_credit": 0,
        "scope": "Exact-candidate public record/review/replay/save/test, screen diagnosis, selective file-state maintenance, Unicode relocation and generated workflow preview. Technical route and independent oracle/fault/model controls remain separate.",
    }
    immutable_json(output / "receipt.json", receipt)
    print(json.dumps({"status": "public-agent-route-passed-not-admitted", "host": host,
                      "attempt_count": len(attempts), "output": str(output)}, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
