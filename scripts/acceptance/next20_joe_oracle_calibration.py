"""Calibrate JOE's public v3 state oracles with independent literal bytes."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import platform
import shutil

from adversarial_process import execute
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256

PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
MARKER = b"JOE_PUBLIC_ROUTE_RC7"
INITIAL = b"JOE_PUBLIC_ROUTE_START\n"
EXPECTED = INITIAL[:-1] + MARKER + INITIAL[-1:]
HOST_OS = {"linux": "Linux", "darwin": "Darwin"}
OUTPUT = RAW / "joe" / "oracle-calibration-v1"

# Fixture bytes and their expected observations are intentionally separate
# literals. The target writes only public-note.txt; it cannot produce these
# read-only calibration files or calculate their oracle values.
FIXTURES = {
    "bytes-lf.txt": b"line one\nline two\n",
    "bytes-crlf.txt": b"line one\r\nline two\r\n",
    "bytes-empty.txt": b"",
    "bytes-nul.txt": b"left\x00middle\x00right\r\n",
    "bytes-no-final-newline.txt": b"final line without terminator",
    "bytes-unicode.txt": "café 雪 🧪\n".encode("utf-8"),
}
EXPECTED_FIXTURES = {
    "bytes-lf.txt": b"line one\nline two\n",
    "bytes-crlf.txt": b"line one\r\nline two\r\n",
    "bytes-empty.txt": b"",
    "bytes-nul.txt": b"left\x00middle\x00right\r\n",
    "bytes-no-final-newline.txt": b"final line without terminator",
    "bytes-unicode.txt": "café 雪 🧪\n".encode("utf-8"),
}


def state_file(path, data):
    return {"state": {"path": path, "kind": "file",
                       "bytes_base64": base64.b64encode(data).decode("ascii")}}


def read_result(report_path, expected_status, expected_exit):
    report = json.loads(report_path.read_text(encoding="utf-8"))
    if report.get("report_version") != 3 or report.get("runner_version") != "v0.4.0-rc.7":
        raise ValueError("JOE oracle report is not public report v3 from rc.7")
    if report.get("summary", {}).get("total") != 1 or len(report.get("results", [])) != 1:
        raise ValueError("JOE oracle report denominator differs")
    result = report["results"][0]
    if result.get("status") != expected_status or result.get("target", {}).get("exit_code") != 0:
        raise ValueError("JOE target did not produce the expected report/target exit outcome")
    if not result.get("cleanup", {}).get("confirmed_exited") or not result.get("workspace", {}).get("cleaned"):
        raise ValueError("JOE oracle report lacks target and workspace cleanup evidence")
    state_steps = [step for step in result.get("steps", []) if step.get("action") == "state"]
    if not state_steps or any(step.get("status") != "passed" for step in result["steps"][:-len(state_steps)]):
        raise ValueError("JOE oracle case failed before the terminal and exit evidence")
    if len(state_steps) == 0 or state_steps[-1].get("status") != ("passed" if expected_status == "passed" else "failed"):
        raise ValueError("JOE oracle case did not reach its final state assertion")
    if expected_status == "failed" and (result.get("failure") or {}).get("category") != "state_assertion_failure":
        raise ValueError("negative calibration was not rejected by the state oracle")
    return result


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    args = parser.parse_args()
    host = args.host
    if platform.system() != HOST_OS[host]:
        raise RuntimeError("actual native host differs from the declared JOE oracle host")
    if OUTPUT.exists():
        raise ValueError("preserve existing JOE oracle calibration evidence")

    route_root = RAW / "joe" / "public-route-v2" / host
    route_spec = route_root / "project" / "create-note.json"
    route_receipt_path = route_root / "receipt.json"
    build_root = RAW / "active" / "joe"
    build = json.loads((build_root / "build.json").read_text(encoding="utf-8"))
    binary = build_root / "install" / "bin" / "joe"
    if (build.get("project") != "joe" or build.get("pin") != PIN or build.get("host") != host or
            not binary.is_file() or sha256(binary) != build.get("binary_sha256")):
        raise ValueError("oracle calibration target differs from the reviewed native JOE build")
    route_receipt = json.loads(route_receipt_path.read_text(encoding="utf-8"))
    if (route_receipt.get("candidate") != "v0.4.0-rc.7" or
            route_receipt.get("target_binary_sha256") != sha256(binary) or
            route_receipt.get("source_pin") != PIN or
            sha256(route_spec) != route_receipt.get("first_use", {}).get("spec_sha256")):
        raise ValueError("oracle calibration inputs differ from the audited public route")
    runner = executable("native-exit-v2", host)
    if sha256(runner) != route_receipt.get("runner_sha256"):
        raise ValueError("oracle calibration did not use the exact audited rc.7 runner")
    route = json.loads(route_spec.read_text(encoding="utf-8"))
    if route.get("version") != 3 or route.get("steps", [])[-1].get("state", {}).get("path") != "public-note.txt":
        raise ValueError("audited public route no longer supplies one public file-state assertion")

    OUTPUT.mkdir(parents=True)
    immutable_json(OUTPUT / (host + "-plan.json"), {
        "schema_version": 1, "project": "joe", "host": host,
        "candidate": "v0.4.0-rc.7", "candidate_series": "native-exit-v2",
        "source_pin": PIN, "runner_sha256": sha256(runner),
        "target_binary_sha256": sha256(binary), "route_spec_sha256": sha256(route_spec),
        "independent_expected_saved_bytes_base64": base64.b64encode(EXPECTED).decode("ascii"),
        "oracle_kinds": ["file", "absent", "directory", "entries"],
        "byte_families": ["LF", "CRLF", "empty", "NUL", "no-final-newline", "UTF-8 Unicode"],
        "cases": ["correct-all-kinds-and-byte-families", "same-size-wrong-file-bytes",
                  "missing-required-file", "wrong-type-directory-as-file",
                  "absence-rejects-present-file", "absence-rejects-present-directory",
                  "directory-rejects-missing-path", "directory-rejects-file",
                  "entries-reject-missing-name", "entries-reject-extra-name",
                  "entries-reject-file"],
        "expected_values_method": "The saved output is independently derived from the reviewed fixture literal plus the exact recorded key/text sequence. Calibration fixture and expected byte families are separate literal maps; neither is generated by the application or a shared writer.",
        "admission_credit": 0,
    })

    env = dict(os.environ)
    env["PATH"] = str(binary.parent) + os.pathsep + env.get("PATH", "")
    env.update(TERM="xterm-256color", LANG="C.UTF-8", LC_ALL="C.UTF-8")
    campaign = NextCampaign(phase="oracle-calibration")
    results = []

    async def exercise(name, states, *, extra=None, expected=0, expected_status="passed"):
        case_root = OUTPUT / "cases" / host / name
        project = case_root / "project"
        fixtures = project / "fixtures"
        case_root.mkdir(parents=True, exist_ok=False)
        shutil.copytree(route_root / "project", project)
        spec_path = project / "create-note.json"
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        for file_name, data in FIXTURES.items():
            (fixtures / file_name).write_bytes(data)
        marker_dir = fixtures / "directory-marker"
        marker_dir.mkdir()
        (marker_dir / "inside.txt").write_bytes(b"independent directory fixture\n")
        if extra:
            (fixtures / extra).write_bytes(b"unexpected independent entry\n")
        spec["steps"] = [step for step in spec["steps"] if "state" not in step] + states
        spec_path.write_text(json.dumps(spec, sort_keys=True, ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8", newline="\n")
        report = case_root / "report.json"
        artifacts = case_root / "artifacts"
        argv = [runner, "test", "--report", report.relative_to(ROOT), "--artifacts-dir",
                artifacts.relative_to(ROOT), spec_path.relative_to(ROOT)]
        run_id = None
        try:
            ran = await execute(argv, "joe", "joe-oracle-" + name, cwd=ROOT, env=env,
                                expected=expected, timeout=180, campaign=campaign)
            run_id = ran["id"]
        except RuntimeError as error:
            run_id = getattr(error, "evidence_id", None)
            if expected == 0:
                raise
        result = read_result(report, expected_status, expected)
        results.append({"case": name, "attempt_id": run_id, "status": result["status"],
                        "report_sha256": sha256(report),
                        "failure_category": (result.get("failure") or {}).get("category"),
                        "state_steps": len([s for s in result["steps"] if s.get("action") == "state"])})

    fixtures_in_root = sorted([*FIXTURES, "directory-marker", "public-note.txt"])
    positive_states = [state_file("public-note.txt", EXPECTED)]
    positive_states += [state_file(name, EXPECTED_FIXTURES[name]) for name in FIXTURES]
    positive_states += [
        {"state": {"path": "missing-calibration-path", "kind": "absent"}},
        {"state": {"path": ".", "kind": "directory"}},
        {"state": {"path": ".", "kind": "entries", "entries": fixtures_in_root}},
    ]
    await exercise("correct-all-kinds-and-byte-families", positive_states)

    wrong_same_size = bytes([EXPECTED[0] ^ 1]) + EXPECTED[1:]
    if len(wrong_same_size) != len(EXPECTED) or wrong_same_size == EXPECTED:
        raise ValueError("same-size file oracle mutation is invalid")
    await exercise("same-size-wrong-file-bytes", [state_file("public-note.txt", wrong_same_size)],
                   expected=1, expected_status="failed")
    await exercise("missing-required-file", [state_file("missing-required.txt", EXPECTED)],
                   expected=1, expected_status="failed")
    await exercise("wrong-type-directory-as-file", [state_file("directory-marker", EXPECTED)],
                   expected=1, expected_status="failed")
    await exercise("absence-rejects-present-file", [{"state": {"path": "public-note.txt", "kind": "absent"}}],
                   expected=1, expected_status="failed")
    await exercise("absence-rejects-present-directory", [{"state": {"path": "directory-marker", "kind": "absent"}}],
                   expected=1, expected_status="failed")
    await exercise("directory-rejects-missing-path", [{"state": {"path": "missing-directory", "kind": "directory"}}],
                   expected=1, expected_status="failed")
    await exercise("directory-rejects-file", [{"state": {"path": "public-note.txt", "kind": "directory"}}],
                   expected=1, expected_status="failed")
    await exercise("entries-reject-missing-name", [{"state": {"path": ".", "kind": "entries",
                                                               "entries": fixtures_in_root + ["must-be-missing"]}}],
                   expected=1, expected_status="failed")
    await exercise("entries-reject-extra-name", [{"state": {"path": ".", "kind": "entries",
                                                              "entries": fixtures_in_root}}],
                   extra="unexpected-extra.txt", expected=1, expected_status="failed")
    await exercise("entries-reject-file", [{"state": {"path": "public-note.txt", "kind": "entries",
                                                       "entries": []}}],
                   expected=1, expected_status="failed")

    receipt = {
        "schema_version": 1, "status": "oracle-calibration-passed-not-admitted",
        "project": "joe", "host": host, "candidate": "v0.4.0-rc.7",
        "source_pin": PIN, "runner_sha256": sha256(runner),
        "target_binary_sha256": sha256(binary),
        "plan_sha256": sha256(OUTPUT / (host + "-plan.json")),
        "cases": results, "positive_oracle_kinds": ["file", "absent", "directory", "entries"],
        "byte_families_independently_matched": sorted(FIXTURES),
        "negative_state_assertions_rejected": sum(row["status"] == "failed" for row in results),
        "all_negative_rejections_at_state_checkpoint": all(
            row["failure_category"] == "state_assertion_failure" for row in results if row["status"] == "failed"),
        "admission_credit": 0,
    }
    if len(results) != 11 or receipt["negative_state_assertions_rejected"] != 10 or not receipt["all_negative_rejections_at_state_checkpoint"]:
        raise ValueError("JOE oracle calibration did not complete all planned positive/negative controls")
    immutable_json(OUTPUT / (host + "-receipt.json"), receipt)
    print(json.dumps(receipt, sort_keys=True))


if __name__ == "__main__":
    asyncio.run(main())
