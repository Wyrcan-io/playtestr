"""Calibrate mg's saved-file oracle with independently constructed state variants."""
import base64
import json
import os
from pathlib import Path
import platform
import shutil

from adversarial_process import execute
from next20_candidate import executable
from next20_check import RAW, ROOT, NextCampaign
from next20_mg_pilot import ensure_executable
from readiness_evidence import immutable_json, sha256


PIN = "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66"
TARGET_SHA = "6eb334f5ea96687983c51b073b1b8a11434ea85e5"
RUNNER_SHA = "e302a46eb090772d91aab7018b51eea0d1fb92247846f4a63375e1009e29309a"
OUTPUT = RAW / "mg/oracle-calibration-native-exit-v1"
INITIAL = b"MG_PUBLIC_ROUTE_START\n"
MARKER = b"MG_PUBLIC_ROUTE_RC6"


def report_result(path, expected_status, expected_state_status):
    report = json.loads(path.read_text(encoding="utf-8"))
    if report.get("runner_version") != "v0.4.0-rc.6" or len(report.get("results", [])) != 1:
        raise ValueError("oracle calibration report candidate/result identity differs")
    result = report["results"][0]
    if (result.get("status") != expected_status or not result.get("cleanup", {}).get("confirmed_exited") or
            not result.get("workspace", {}).get("cleaned")):
        raise ValueError("oracle calibration outcome lacks expected status or cleanup")
    state_steps = [s for s in result.get("steps", []) if s.get("action") == "state"]
    if not state_steps or state_steps[-1].get("status") != expected_state_status:
        raise ValueError("oracle calibration state checkpoint did not produce its expected outcome")
    if expected_status == "passed" and result.get("failure"):
        raise ValueError("positive oracle calibration contains failure evidence")
    if expected_status == "failed":
        failure = result.get("failure") or {}
        if failure.get("category") != "state_assertion_failure":
            raise ValueError("invalid spec/earlier action failure was counted as a state-oracle rejection")
        if any(s.get("status") != "passed" for s in result["steps"][:-1]):
            raise ValueError("state-oracle calibration failed before its final state checkpoint")
    return result


async def run_calibration(route_root, mg_build_root):
    if platform.system() != "Linux":
        raise RuntimeError("mg state-oracle calibration is declared for hosted Linux only")
    if OUTPUT.exists():
        raise ValueError("preserve existing mg state-oracle calibration evidence")
    route_root = Path(route_root).resolve(strict=True)
    route_root.relative_to(ROOT.resolve())
    mg_build_root = Path(mg_build_root).resolve(strict=True)
    mg_build_root.relative_to(ROOT.resolve())
    route_receipt = json.loads((route_root / "receipt.json").read_text(encoding="utf-8"))
    route_spec = route_root / "project/create-note.json"
    if (route_receipt.get("target_binary_sha256") != TARGET_SHA or
            route_receipt.get("runner_sha256") != RUNNER_SHA or
            sha256(route_spec) != route_receipt.get("first_spec_sha256")):
        raise ValueError("oracle calibration input does not match audited first-use route")
    build = json.loads((mg_build_root / "active/mg/build.json").read_text(encoding="utf-8"))
    original = (mg_build_root / "active/mg/install/bin/mg").resolve(strict=True)
    if build.get("project") != "mg" or build.get("pin") != PIN or sha256(original) != TARGET_SHA:
        raise ValueError("oracle calibration target differs from the reviewed native source build")
    runner = executable("native-exit-v1", "linux")
    if sha256(runner) != RUNNER_SHA:
        raise ValueError("oracle calibration did not resolve the frozen Linux rc.6 runner")

    OUTPUT.mkdir(parents=True)
    target = OUTPUT / "target/bin/mg"
    target.parent.mkdir(parents=True)
    shutil.copy2(original, target)
    mode = ensure_executable(target)
    if sha256(target) != TARGET_SHA:
        raise ValueError("oracle calibration target copy changed bytes")
    env = dict(os.environ)
    env["PATH"] = str(target.parent) + os.pathsep + env.get("PATH", "")
    env["LANG"] = "C.UTF-8"
    env["LC_ALL"] = "C.UTF-8"
    campaign = NextCampaign(phase="oracle-calibration")
    expected_bytes = INITIAL + MARKER
    source = json.loads(route_spec.read_text(encoding="utf-8"))
    states = [step["state"] for step in source["steps"] if step.get("state", {}).get("path") == "public-note.txt"]
    if len(states) != 1 or base64.b64decode(states[0]["bytes_base64"], validate=True) != expected_bytes:
        raise ValueError("independent route oracle no longer matches the fixture plus declared input")
    planned = {
        "schema_version": 1, "project": "mg", "source_pin": PIN,
        "candidate": "v0.4.0-rc.6", "runner_sha256": RUNNER_SHA,
        "target_binary_sha256": TARGET_SHA,
        "route_spec_sha256": route_receipt["first_spec_sha256"],
        "independent_expected_bytes": base64.b64encode(expected_bytes).decode("ascii"),
        "cases": ["correct-file-bytes", "correct-directory-entries", "same-size-wrong-bytes",
                  "missing-required-output", "unexpected-extra-entry", "wrong-type-directory-as-file"],
        "oracle_method": "Expected fixture prefix and literal typed marker are independently declared; variants change only reviewed state/fixture data and keep earlier screen/input/exit checkpoints unchanged.",
        "target_copy_mode": mode,
    }
    immutable_json(OUTPUT / "planned.json", planned)
    attempts = []

    async def exercise(name, *, change=None, fixture=None, expected=0, report_status="passed",
                       state_status="passed"):
        case_root = OUTPUT / "cases" / name
        shutil.copytree(route_root / "project", case_root)
        spec = case_root / "create-note.json"
        value = json.loads(spec.read_text(encoding="utf-8"))
        state_steps = [step for step in value["steps"] if step.get("state", {}).get("path") == "public-note.txt"]
        if len(state_steps) != 1:
            raise ValueError("calibration case lacks exactly one original saved-file assertion")
        if change:
            change(value, state_steps[0]["state"], case_root / "fixtures")
        if fixture:
            fixture(case_root / "fixtures")
        spec.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
        report = OUTPUT / "reports" / f"{name}.json"
        artifacts = OUTPUT / "artifacts" / name
        argv = [runner, "test", "--report", report.relative_to(ROOT), "--artifacts-dir",
                artifacts.relative_to(ROOT), spec.relative_to(ROOT)]
        result = await execute(argv, "mg", "mg-state-oracle-" + name, cwd=ROOT, env=env,
                               expected=expected, timeout=180, campaign=campaign)
        observed = report_result(report, report_status, state_status)
        attempts.append({"name": name, "id": result["id"], "returncode": result["returncode"],
                         "report_sha256": sha256(report), "invocation_id": observed["invocation_id"],
                         "failure_category": (observed.get("failure") or {}).get("category")})
        return observed

    def append_entries(expected_names):
        def mutate(spec, _state, _fixtures):
            spec["steps"].append({"state": {"path": ".", "kind": "entries", "entries": expected_names}})
        return mutate

    def same_size_wrong(_spec, state, _fixtures):
        wrong = bytes([expected_bytes[0] ^ 1]) + expected_bytes[1:]
        if len(wrong) != len(expected_bytes) or wrong == expected_bytes:
            raise ValueError("same-size mutation is not a distinct equal-length byte string")
        state["bytes_base64"] = base64.b64encode(wrong).decode("ascii")

    def missing_output(_spec, state, _fixtures):
        state["path"] = "missing-public-note.txt"

    def wrong_type(_spec, _state, fixtures):
        directory = fixtures / "directory-marker"
        directory.mkdir()
        (directory / "inside.txt").write_bytes(b"directory fixture marker\n")
        _spec["steps"].append({"state": {"path": "directory-marker", "kind": "file",
                                          "bytes_base64": base64.b64encode(expected_bytes).decode("ascii")}})

    def add_extra(fixtures):
        (fixtures / "unexpected-extra.txt").write_bytes(b"extra fixture entry\n")

    await exercise("correct-file-bytes")
    await exercise("correct-directory-entries", change=append_entries(["public-note.txt"]))
    await exercise("same-size-wrong-bytes", change=same_size_wrong, expected=1,
                   report_status="failed", state_status="failed")
    await exercise("missing-required-output", change=missing_output, expected=1,
                   report_status="failed", state_status="failed")
    await exercise("unexpected-extra-entry", change=append_entries(["public-note.txt"]), fixture=add_extra,
                   expected=1, report_status="failed", state_status="failed")
    await exercise("wrong-type-directory-as-file", change=wrong_type, expected=1,
                   report_status="failed", state_status="failed")

    if sha256(target) != TARGET_SHA:
        raise ValueError("refusing to remove changed mg oracle calibration target copy")
    target.unlink()
    target.parent.rmdir()
    if target.exists():
        raise ValueError("mg oracle calibration target copy remains")
    receipt = {"schema_version": 1, "status": "saved-state-oracle-calibration-passed-not-admitted",
               "project": "mg", "source_pin": PIN, "candidate": "v0.4.0-rc.6",
               "runner_sha256": RUNNER_SHA, "target_binary_sha256": TARGET_SHA,
               "planned_sha256": sha256(OUTPUT / "planned.json"), "attempts": attempts,
               "positive_correct_bytes": True, "positive_correct_entries": True,
               "same_size_wrong_bytes_rejected": True, "missing_required_output_rejected": True,
               "unexpected_extra_entry_rejected": True, "wrong_type_rejected": True,
               "all_negative_cases_failed_at_final_state_checkpoint": True,
               "target_copy_sha256": TARGET_SHA, "target_copy_removed": not target.exists(),
               "admission_credit": 0}
    immutable_json(OUTPUT / "receipt.json", receipt)
    return receipt
