"""Measure Percol's first useful public Playtestr authoring route."""
import argparse
import asyncio
import base64
import hashlib
import json
import os
import platform
import sys
from pathlib import Path

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256


PROJECT = "percol"
PIN = "4b28037e328da3d0fe8165c11b800cbaddcb525e"
SERIES = "native-exit-v3"


def required_environment():
    keys = ("PATH", "PERCOL_PYTHON", "PERCOL_SOURCE", "PYTHONPATH",
            "DYLD_LIBRARY_PATH", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT")
    return {key: os.environ[key] for key in keys if key in os.environ}


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    args = parser.parse_args()
    expected_os = {"linux": "Linux", "darwin": "Darwin"}[args.host]
    if platform.system() != expected_os:
        raise SystemExit("public Percol route must execute on its declared native host")

    target = RAW / "active" / PROJECT
    package = DOC / PROJECT
    receipt = RAW / PROJECT / "public-first-use-v1"
    if receipt.exists():
        raise SystemExit("preserve existing Percol public first-use evidence")
    receipt.mkdir(parents=True)
    spec = receipt / "selection.json"
    fixture = receipt / "fixture"
    fixture.mkdir()
    inputs = {"choices.txt": b"apple\nbanana\n", "sentinel.txt": b"independent fixture sentinel\n"}
    for name, data in inputs.items():
        (fixture / name).write_bytes(data)

    acquisition = json.loads((target / "acquisition.json").read_text(encoding="utf-8"))
    runtime = json.loads((target / "runtime.json").read_text(encoding="utf-8"))
    build = json.loads((target / "build.json").read_text(encoding="utf-8"))
    if acquisition.get("repository") != "mooz/percol" or acquisition.get("pin") != PIN:
        raise ValueError("public route must use the selected pinned Percol source")
    python_path = Path(runtime["python"])
    if sha256(python_path) != runtime.get("python_sha256"):
        raise ValueError("public route runtime identity changed")
    if build.get("pin") != PIN or build.get("python_sha256") != runtime["python_sha256"]:
        raise ValueError("public route runtime/build receipt differs")

    runner = executable(SERIES, args.host)
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v3.json").read_text(encoding="utf-8"))
    if freeze.get("version") != "v0.4.0-rc.8":
        raise ValueError("public route requires the frozen rc.8 candidate")

    controls = ["/expect apple", "/key Enter", "/exit 0", "/file result.txt",
                "/file choices.txt", "/file sentinel.txt", "/entries .", "/review",
                "/replay", "/save"]
    env = required_environment()
    env.update({"TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "TMPDIR": str(RAW / "tmp"), "TMP": str(RAW / "tmp"), "TEMP": str(RAW / "tmp")})
    (RAW / "tmp").mkdir(parents=True, exist_ok=True)
    campaign = NextCampaign(phase="public-authoring")
    attempts = []

    async def run(argv, label, input_data=None):
        row = await execute(argv, PROJECT, label, cwd=ROOT, env=env, input=input_data,
                            timeout=180, campaign=campaign)
        attempts.append(row["id"])
        return row

    version = await run([runner, "--version"], "percol-first-use-runner-version")
    if version["output"].strip() != "playtestr v0.4.0-rc.8":
        raise ValueError("public route invoked the wrong candidate")

    command = ["/bin/sh", "-c",
               'exec "$PERCOL_PYTHON" "$PERCOL_SOURCE/bin/percol" < choices.txt > result.txt']
    argv = [runner, "record", "--output", spec.relative_to(ROOT).as_posix(),
            "--name", "Select the first Percol candidate", "--fixture",
            fixture.name, "--fixture-cwd", ".",
            "--temporary-home", "--temporary-temp", "--width", "80", "--height", "12",
            "--timeout-ms", "10000", "--run-timeout-ms", "120000",
            "--env", "TERM=xterm-256color", "--env", "LANG=C.UTF-8", "--env", "LC_ALL=C.UTF-8",
            "--env", "PYTHONDONTWRITEBYTECODE=1",
            "--inherit-env", "PATH", "--inherit-env", "PERCOL_PYTHON",
            "--inherit-env", "PERCOL_SOURCE", "--inherit-env", "PYTHONPATH",
            "--inherit-env", "DYLD_LIBRARY_PATH", "--", *command]
    await run(argv, "percol-first-public-record-review-replay-export", "\n".join(controls + [""]))

    captured = json.loads(spec.read_text(encoding="utf-8"))
    states = {step["state"]["path"]: step["state"]
              for step in captured.get("steps", []) if "state" in step}
    approved = {"result.txt": b"apple\n", **inputs}
    for name, body in approved.items():
        state = states.get(name)
        if state is None or base64.b64decode(state["bytes_base64"], validate=True) != body:
            raise ValueError("public recorder bytes differ from independently reviewed oracle: " + name)
    if set(states.get(".", {}).get("entries", [])) != {"choices.txt", "sentinel.txt", "result.txt"}:
        raise ValueError("public route captured an unexpected fixture directory listing")

    report = receipt / "ordinary-report.json"
    ordinary = await run([runner, "test", "--report", report.relative_to(ROOT).as_posix(),
                          "--artifacts-dir", (receipt / "ordinary-evidence").relative_to(ROOT).as_posix(),
                          spec.relative_to(ROOT).as_posix()], "percol-first-reviewed-ordinary-test")
    report_json = json.loads(report.read_text(encoding="utf-8"))
    result = report_json["results"][0]
    if (ordinary["returncode"] != 0 or result.get("status") != "passed"
            or result.get("target", {}).get("exit_code") != 0
            or result.get("cleanup", {}).get("confirmed_exited") is not True
            or result.get("workspace", {}).get("cleaned") is not True
            or any(step.get("status") != "passed" for step in result.get("steps", []))):
        raise ValueError("ordinary fresh Percol public route did not pass")

    immutable_json(package / "public-first-use-v1.json", {
        "schema_version": 1, "project": PROJECT, "status": "public-route-passed-not-admitted",
        "candidate": "v0.4.0-rc.8", "candidate_series": SERIES, "host": args.host,
        "source_pin": PIN, "runtime_python_sha256": runtime["python_sha256"],
        "runner_sha256": sha256(runner), "spec_sha256": sha256(spec),
        "ordinary_report_sha256": sha256(report),
        "independent_expected_file_sha256": {name: hashlib.sha256(data).hexdigest()
                                             for name, data in approved.items()},
        "shell_invocations": 3, "recorder_controls": len(controls),
        "attempt_ids": attempts, "handwritten_playtestr_json": False,
        "human_participants": 0, "human_time": "unmeasured",
        "measurement": "Prepared-agent first-use window; target keystrokes and fixture preparation are separate from three candidate shell invocations and ten public recorder controls.",
        "scope": "The actual pinned Percol UI selected apple, wrote exact stdout to a fresh fixture file, and was recorded/reviewed/replayed/exported with public commands before an ordinary test. Not a human usability result or project admission."
    })
    print(json.dumps({"project": PROJECT, "host": args.host, "shell_invocations": 3,
                      "recorder_controls": len(controls), "public_route": "passed",
                      "admission_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
