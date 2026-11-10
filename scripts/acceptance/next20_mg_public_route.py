"""Exercise mg through the exact candidate's documented public authoring route."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_mg_pilot import ensure_executable
from readiness_evidence import immutable_json, sha256


PROJECT = "mg"
PIN = "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66"
MARKER = "MG_PUBLIC_ROUTE_RC6"


def report_result(path, expected_status):
    value = json.loads(path.read_text(encoding="utf-8"))
    if len(value.get("results", [])) != 1:
        raise ValueError("mg public route did not produce one ordinary result")
    result = value["results"][0]
    if result.get("status") != expected_status:
        raise ValueError(f"expected mg public report status {expected_status}")
    if not result.get("workspace", {}).get("cleaned") or not result.get("cleanup", {}).get("confirmed_exited"):
        raise ValueError("mg public route did not confirm process/workspace cleanup")
    if expected_status == "passed" and any(step.get("status") != "passed" for step in result.get("steps", [])):
        raise ValueError("passing mg public report has a non-passing step")
    return result


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mg-build-root", required=True)
    args = parser.parse_args()
    host = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    if host != "linux":
        raise RuntimeError("the mg authoring route is declared for Linux only")

    package = DOC / PROJECT
    output = RAW / PROJECT / "public-route-native-exit-v1"
    if output.exists():
        raise ValueError("refusing an existing mg public-route evidence root")
    build_root = Path(args.mg_build_root).resolve(strict=True)
    build_root.relative_to(ROOT.resolve())
    build = json.loads((build_root / "active/mg/build.json").read_text(encoding="utf-8"))
    original_target = (build_root / "active/mg/install/bin/mg").resolve(strict=True)
    if build.get("project") != PROJECT or build.get("pin") != PIN or build.get("host") != host:
        raise ValueError("mg public route source pin or native build identity mismatch")
    original_hash = sha256(original_target)
    if original_hash != build.get("binary_sha256"):
        raise ValueError("mg public-route executable differs from reviewed native build")

    output.mkdir(parents=True)
    canonical = output / "project"
    (canonical / "bin").mkdir(parents=True)
    (canonical / "fixtures").mkdir()
    initial_bytes = b"MG_PUBLIC_ROUTE_START\n"
    (canonical / "fixtures" / "public-note.txt").write_bytes(initial_bytes)
    target_copy = canonical / "bin" / "mg"
    shutil.copy2(original_target, target_copy)
    if sha256(target_copy) != original_hash:
        raise ValueError("mg public-route target copy changed bytes")
    target_copy_mode = ensure_executable(target_copy)

    runner = executable("native-exit-v1", "linux")
    installed = json.loads((runner.parent / "installed.json").read_text(encoding="utf-8"))
    env = dict(os.environ)
    env["PATH"] = str(target_copy.parent) + os.pathsep + env.get("PATH", "")
    env["LANG"] = "C.UTF-8"
    env["LC_ALL"] = "C.UTF-8"
    campaign = NextCampaign(phase="public-authoring")
    attempts = []
    controls = [
        "/expect MG_PUBLIC_ROUTE_START",
        "/key Escape",
        '/text ">"',
        f"/text \"{MARKER}\"",
        f"/expect {MARKER}",
        "/key CtrlX",
        "/key CtrlS",
        "/expect Wrote",
        "/key CtrlX",
        "/key CtrlC",
        "/exit 0",
        "/file public-note.txt",
        "/review",
        "/replay",
        "/save",
    ]
    planned = dict(
        schema_version=1, project=PROJECT, phase="public-authoring", source_pin=PIN,
        candidate="v0.4.0-rc.6", candidate_archive_sha256=installed["archive_sha256"],
        runner_sha256=sha256(runner), target_binary_sha256=original_hash,
        host=platform.platform(), architecture=platform.machine(),
        target_build_run="42815619413", target_build_duration_seconds=build.get("duration_seconds"),
        target_build_artifact_binary_sha256=build.get("binary_sha256"),
        target_copy_mode=target_copy_mode,
        initial_fixture_sha256=sha256(canonical / "fixtures" / "public-note.txt"),
        no_handwritten_first_use_spec=True, initial_shell_invocations_expected=3,
        first_use_controls=controls,
        expected_first_run="record, review, fresh replay, save, then ordinary candidate test passes and cleans its managed workspace",
        seeded_diagnosis="deliberately wrong rendered-screen expectation fails with category and evidence",
        maintenance="change intended text, observe stale file state fail, then rerecord only that state through documented maintenance",
        relocation="move the complete spec, fixture and target beneath a spaced Unicode path and rerun",
        delivered_workflow="generate and review a source-pinned free-workflow preview; do not dispatch or create a PR",
        command_timeout_seconds=180, route_timeout_seconds=1200,
        storage_root=output.relative_to(ROOT).as_posix())
    immutable_json(output / "planned.json", planned)

    async def run(argv, label, *, input=None, expected=0, timeout=180):
        result = await execute(argv, PROJECT, label, cwd=ROOT, env=env, input=input,
                               expected=expected, timeout=timeout, campaign=campaign)
        attempts.append(dict(id=result["id"], label=label, returncode=result["returncode"],
                             seconds=round(result["seconds"], 3)))
        return result

    version = await run([runner, "--version"], "mg-public-route-runner-version")
    if version["output"].strip() != "playtestr v0.4.0-rc.6":
        raise ValueError("mg public route did not use the exact private candidate")

    spec = canonical / "create-note.json"
    command = [runner, "record", "--output", spec.relative_to(ROOT),
               "--name", "Append and save a note in mg", "--fixture", "fixtures",
               "--temporary-home", "--temporary-temp", "--width", "80", "--height", "24",
               "--timeout-ms", "15000", "--run-timeout-ms", "60000",
               "--env", "TERM=xterm-256color", "--env", "LANG=C.UTF-8", "--env", "LC_ALL=C.UTF-8",
               "--inherit-env", "PATH", "--", "mg", "-S", "-n", "public-note.txt"]
    await run(command, "mg-first-public-record-review-replay-save",
              input="\n".join(controls) + "\n", timeout=240)
    recorded = json.loads(spec.read_text(encoding="utf-8"))
    if recorded.get("version") != 3 or recorded.get("command", [])[-4:] != ["mg", "-S", "-n", "public-note.txt"]:
        raise ValueError("mg public recorder export differs from the reviewed command")
    if recorded.get("workspace", {}).get("fixture") != "fixtures":
        raise ValueError("mg public recorder did not export the managed fixture route")
    states = [step["state"] for step in recorded.get("steps", [])
              if step.get("state", {}).get("path") == "public-note.txt"]
    if len(states) != 1 or states[0].get("kind") != "file":
        raise ValueError("mg recorder did not export exactly one reviewed saved-file expectation")
    expected_bytes = base64.b64encode(initial_bytes + (MARKER).encode()).decode("ascii")
    if states[0].get("bytes_base64") != expected_bytes:
        raise ValueError("mg recorder saved bytes differ from the independently declared intended note")
    if sum(step.get("expect") == MARKER for step in recorded.get("steps", [])) != 1:
        raise ValueError("mg public route lacks its unique positive rendered-screen checkpoint")

    first_report = output / "first-use-report.json"
    await run([runner, "test", "--report", first_report.relative_to(ROOT), "--artifacts-dir",
               (output / "first-use-artifacts").relative_to(ROOT), spec.relative_to(ROOT)],
              "mg-first-public-ordinary-test")
    first_result = report_result(first_report, "passed")

    diagnosis = output / "diagnosis"
    shutil.copytree(canonical, diagnosis)
    wrong_spec = diagnosis / "create-note.json"
    broken = json.loads(wrong_spec.read_text(encoding="utf-8"))
    wrong = [step for step in broken["steps"] if step.get("expect") == MARKER]
    if len(wrong) != 1:
        raise ValueError("mg seeded diagnosis cannot identify one exact screen expectation")
    wrong[0]["expect"] = "WRONG_MG_NOTE_EXPECTATION"
    wrong_spec.write_text(json.dumps(broken, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    diagnosis_report = output / "diagnosis-report.json"
    await run([runner, "test", "--report", diagnosis_report.relative_to(ROOT), "--artifacts-dir",
               (output / "diagnosis-artifacts").relative_to(ROOT), wrong_spec.relative_to(ROOT)],
              "mg-first-public-seeded-screen-diagnosis", expected=1)
    diagnosed = report_result(diagnosis_report, "failed")
    failure = diagnosed.get("failure") or {}
    if not failure.get("category") or not failure.get("message"):
        raise ValueError("mg seeded assertion failure lacks a useful category and message")

    maintenance = output / "maintenance"
    shutil.copytree(canonical, maintenance)
    maintenance_spec = maintenance / "create-note.json"
    changed = json.loads(maintenance_spec.read_text(encoding="utf-8"))
    text_steps = [step for step in changed["steps"] if step.get("text") == MARKER]
    screen_steps = [step for step in changed["steps"] if step.get("expect") == MARKER]
    if len(text_steps) != 1 or len(screen_steps) != 1:
        raise ValueError("mg selected maintenance cannot identify the intended text and screen fields")
    revised_marker = "MG_PUBLIC_ROUTE_RC6_UPDATED"
    text_steps[0]["text"] = revised_marker
    screen_steps[0]["expect"] = revised_marker
    maintenance_spec.write_text(json.dumps(changed, sort_keys=True, indent=2) + "\n",
                                encoding="utf-8", newline="\n")
    before_report = output / "maintenance-before-report.json"
    await run([runner, "test", "--report", before_report.relative_to(ROOT), "--artifacts-dir",
               (output / "maintenance-before-artifacts").relative_to(ROOT),
               maintenance_spec.relative_to(ROOT)], "mg-intended-change-before-state-update", expected=1)
    before_result = report_result(before_report, "failed")
    before_failure = before_result.get("failure") or {}
    if not before_failure.get("category") or not before_failure.get("message"):
        raise ValueError("mg stale file-state failure lacks a useful category and message")
    state_index = next(i for i, step in enumerate(changed["steps"], 1)
                       if step.get("state", {}).get("path") == "public-note.txt")
    edit_controls = [f"/update-state {state_index}", "/review", "/replay", "/save"]
    await run([runner, "record", "--edit", maintenance_spec.relative_to(ROOT)],
              "mg-selected-file-state-maintenance", input="\n".join(edit_controls) + "\n", timeout=240)
    maintained = json.loads(maintenance_spec.read_text(encoding="utf-8"))
    new_states = [step["state"] for step in maintained["steps"]
                  if step.get("state", {}).get("path") == "public-note.txt"]
    expected_updated = base64.b64encode(initial_bytes + revised_marker.encode()).decode("ascii")
    if len(new_states) != 1 or new_states[0].get("bytes_base64") != expected_updated:
        raise ValueError("mg selected maintenance did not capture the independently declared new bytes")
    expected_maintenance = json.loads(json.dumps(changed))
    expected_state = next(step["state"] for step in expected_maintenance["steps"]
                          if step.get("state", {}).get("path") == "public-note.txt")
    expected_state["bytes_base64"] = expected_updated
    if maintained != expected_maintenance:
        raise ValueError("mg selected maintenance changed fields beyond the intended input, screen and saved state")
    maintenance_report = output / "maintenance-report.json"
    await run([runner, "test", "--report", maintenance_report.relative_to(ROOT), "--artifacts-dir",
               (output / "maintenance-artifacts").relative_to(ROOT),
               maintenance_spec.relative_to(ROOT)], "mg-maintained-public-ordinary-test")
    report_result(maintenance_report, "passed")
    relocated = output / "relocated space café 雪"
    shutil.copytree(maintenance, relocated)
    relocation_report = output / "relocation-report.json"
    await run([runner, "test", "--report", relocation_report.relative_to(ROOT), "--artifacts-dir",
               (output / "relocation-artifacts").relative_to(ROOT),
               (relocated / "create-note.json").relative_to(ROOT)], "mg-public-unicode-relocation")
    relocation_result = report_result(relocation_report, "passed")

    for copy_root in [canonical, diagnosis, maintenance, relocated]:
        if sha256(copy_root / "fixtures" / "public-note.txt") != sha256(
                canonical / "fixtures" / "public-note.txt"):
            raise ValueError("mg public-route fixture changed during diagnosis, maintenance, or relocation")

    source_revision = os.environ.get("GITHUB_SHA", "")
    if len(source_revision) != 40 or any(c not in "0123456789abcdef" for c in source_revision):
        source_revision = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True,
                                         capture_output=True, text=True, timeout=10).stdout.strip()
    setup = ("mkdir -p artifacts/runner-readiness-next-twenty-project-pass/active/mg/source && "
             "git clone --no-checkout https://github.com/troglobit/mg.git "
             "artifacts/runner-readiness-next-twenty-project-pass/active/mg/source && "
             "git -C artifacts/runner-readiness-next-twenty-project-pass/active/mg/source checkout --detach " + PIN)
    build_command = ("sudo apt-get update && sudo apt-get install -y autoconf automake make gcc m4 && "
                     "cd artifacts/runner-readiness-next-twenty-project-pass/active/mg/source && "
                     "./autogen.sh && ./configure --prefix=\"$GITHUB_WORKSPACE/artifacts/runner-readiness-next-twenty-project-pass/active/mg/native-build\" "
                     "&& make -j2 && make install")
    suite = "docs/validation/runner-readiness-next-twenty-project-pass/mg/public-route-native-exit-v1/project/create-note.json"
    generated = await run([runner, "workflow", "--source-revision", source_revision,
                           "--os", "linux", "--suite", suite, "--setup", setup,
                           "--build", build_command, "--print"], "mg-public-delivered-workflow-preview")
    workflow_file = output / "delivered-workflow-preview.yml"
    workflow_file.write_text(generated["output"], encoding="utf-8", newline="\n")
    workflow_text = workflow_file.read_text(encoding="utf-8")
    if source_revision not in workflow_text or suite not in workflow_text or setup not in workflow_text or build_command not in workflow_text or "pull_request:" not in workflow_text:
        raise ValueError("generated mg workflow omitted source, suite, setup, build, or trigger route")

    removed = []
    for copy_root in [canonical, diagnosis, maintenance, relocated]:
        binary = copy_root / "bin" / "mg"
        if sha256(binary) != original_hash:
            raise ValueError("refusing to remove an mg target copy whose identity changed")
        binary.unlink()
        binary.parent.rmdir()
        if binary.exists():
            raise ValueError("owned mg target removal was not confirmed")
        removed.append(dict(path=binary.relative_to(ROOT).as_posix(), sha256=original_hash, absent=True))

    receipt = dict(schema_version=1, status="public-agent-route-passed-not-admitted", project=PROJECT,
                   source_pin=PIN, candidate="v0.4.0-rc.6", runner_sha256=sha256(runner),
                   planned_sha256=sha256(output / "planned.json"), target_binary_sha256=original_hash,
                   target_build_run="42815619413", target_build_duration_seconds=build.get("duration_seconds"),
                   target_copy_mode=target_copy_mode,
                   first_use_target_version=build.get("version_output"),
                   shell_invocations_to_first_reviewed_ordinary_pass=3,
                   first_window_controls=len(controls), handwritten_first_use_json=False,
                   first_spec_sha256=sha256(spec), first_report_sha256=sha256(first_report),
                   first_invocation=first_result["invocation_id"],
                   diagnosis=dict(report_sha256=sha256(diagnosis_report), status="failed-as-seeded",
                                  category=failure["category"], message=failure["message"]),
                   maintenance=dict(before_report_sha256=sha256(before_report),
                                    update_report_sha256=sha256(maintenance_report), intended_text=revised_marker,
                                    exact_state_bytes_verified=True),
                   relocation=dict(path="relocated space café 雪", report_sha256=sha256(relocation_report),
                                   invocation=relocation_result["invocation_id"], passed=True),
                   delivered_workflow=dict(source_revision=source_revision, os="linux", suite=suite,
                                           setup=setup, build=build_command,
                                           preview_sha256=sha256(workflow_file), provider_run="not-dispatched",
                                           scope="Generated and reviewed locally; no PR or external repository mutation."),
                   target_copy_removal=removed, attempts=attempts, human_participants=0,
                   human_time="unmeasured", assistance="Agent engineering route; no beginner inference.",
                   scope="Exact rc.6 public record/review/replay/save/test, seeded screen diagnosis, selected file-state maintenance, Unicode relocation and free-workflow preview. Admission remains gated on independent oracle, controls and complete campaign closure.")
    immutable_json(output / "receipt.json", receipt)
    print(json.dumps(dict(status=receipt["status"], output=str(output), attempts=len(attempts)), sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
