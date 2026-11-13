"""Exercise Pick's technical spec-selection, migration, reporting and rerecord route."""
import argparse
import asyncio
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import shutil

from adversarial_process import execute
from next20_candidate import executable
from next20_check import RAW, ROOT, NextCampaign
from readiness_evidence import immutable_json, sha256

PROJECT = "pick"
PIN = "caae95938359b2e814b3e7406f396f486c9d99fb"
HOSTS = {"linux": "Linux", "darwin": "Darwin"}
PUBLIC = RAW / PROJECT / "public-route-v1"
OUTPUT = RAW / PROJECT / "technical-route-v1"
FIXTURE = ("".join(f"item{index:02d}:Item description {index:02d}\n" for index in range(29))
           + "tail-choice:Tail unique description\n").encode("ascii")


def need(condition, message):
    if not condition:
        raise ValueError(message)


def passed_report(path, expected_version):
    report = json.loads(path.read_text(encoding="utf-8"))
    need(report.get("report_version") == expected_version and len(report.get("results", [])) == 1,
         f"Pick technical report schema/denominator differs: {path.name}")
    result = report["results"][0]
    need(result.get("status") == "passed" and result.get("cleanup", {}).get("confirmed_exited") is True
         and result.get("workspace", {}).get("cleaned") is True
         and all(step.get("status") == "passed" for step in result.get("steps", [])),
         f"Pick technical route lacks positive target evidence or cleanup: {path.name}")
    return report, result


async def main_async(host):
    need(platform.system() == HOSTS[host], "actual native host differs from Pick technical-route host")
    route_root = PUBLIC / host
    route_receipt_path = route_root / "receipt.json"
    route_receipt = json.loads(route_receipt_path.read_text(encoding="utf-8"))
    need(route_receipt.get("project") == PROJECT and route_receipt.get("host") == host
         and route_receipt.get("candidate") == "v0.4.0-rc.8"
         and route_receipt.get("source_pin") == PIN and route_receipt.get("admission_credit") == 0
         and route_receipt.get("first_use", {}).get("status") == "passed",
         "Pick technical route does not consume the exact successful public-route packet")
    target_root = RAW / "active" / PROJECT
    target = target_root / "install/bin/pick"
    target_build = json.loads((target_root / "build.json").read_text(encoding="utf-8"))
    runner = executable("native-exit-v3", host)
    need(target_build.get("project") == PROJECT and target_build.get("pin") == PIN
         and target_build.get("host") == host and sha256(target) == route_receipt["target_binary_sha256"]
         and sha256(runner) == route_receipt["runner_sha256"],
         "Pick technical-route target or candidate differs from the public route")
    need(not OUTPUT.joinpath(host).exists(), "preserve existing Pick technical-route evidence")
    output = OUTPUT / host
    output.mkdir(parents=True)
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env["PATH"] = str(target.parent) + os.pathsep + env.get("PATH", "")
    env.update({"TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "IFS": ":",
                "PLAYTESTR_PICK_TECHNICAL_ROUTE": "explicit-rc8"})
    campaign = NextCampaign(phase="technical-authoring")
    attempts = []

    async def run(argv, label, *, input_text=None, timeout=180):
        result = await execute(list(map(str, argv)), PROJECT, label, cwd=ROOT, env=env,
                               input=input_text, expected=0, timeout=timeout, campaign=campaign)
        attempts.append({"id": result["id"], "label": label, "returncode": result["returncode"],
                         "seconds": round(result["seconds"], 3)})
        return result

    version = await run([runner, "--version"], "pick-technical-route-runner-version")
    need(version["output"].strip() == "playtestr v0.4.0-rc.8",
         "technical route did not invoke the exact frozen candidate")

    public_spec_path = route_root / "project/pick-blue.json"
    public_spec = json.loads(public_spec_path.read_text(encoding="utf-8"))
    need(sha256(public_spec_path) == route_receipt["first_use"]["spec_sha256"]
         and public_spec.get("env", {}).get("IFS") == ":"
         and (route_root / "project/fixtures/choices.txt").read_bytes() == FIXTURE,
         "technical route public spec/fixture input changed")

    manual_root = output / "manual selection"
    manual_root.mkdir(parents=True)
    shutil.copytree(route_root / "project/fixtures", manual_root / "fixtures")
    shutil.copytree(route_root / "project/snapshots", manual_root / "snapshots")
    manual_spec = manual_root / "pick-manual-v3.json"
    manual = json.loads(json.dumps(public_spec))
    manual["name"] = "Pick technical manual spec edit and input preservation"
    manual["env"]["PLAYTESTR_PICK_TECHNICAL_ROUTE"] = "explicit-rc8"
    query_steps = [step for step in manual["steps"] if step.get("text") == "tail"]
    need(len(query_steps) == 1, "manual technical edit cannot locate the intended fuzzy query")
    query_steps[0]["text"] = "tail-choice"
    manual["steps"].append({"state": {"path": "choices.txt", "kind": "file",
                                      "bytes_base64": base64.b64encode(FIXTURE).decode("ascii")}})
    manual_spec.write_text(json.dumps(manual, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8", newline="\n")

    selection = output / "suite-selection"
    selection.mkdir()
    shutil.copytree(manual_root / "fixtures", selection / "fixtures")
    shutil.copytree(manual_root / "snapshots", selection / "snapshots")
    shutil.copy2(manual_spec, selection / "chosen.json")
    unselected = json.loads(json.dumps(manual))
    unselected["name"] = "Unselected Pick suite member"
    (selection / "separate.json").write_text(json.dumps(unselected, sort_keys=True, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    listed = await run([runner, "test", "--list", selection.relative_to(ROOT)],
                       "pick-technical-suite-selection")
    need("Selected 2 specs:" in listed["output"] and "chosen.json" in listed["output"]
         and "separate.json" in listed["output"],
         "candidate did not list the complete selected two-spec suite")

    manual_report = output / "reports/manual-v3.json"
    manual_artifacts = output / "artifacts/manual-v3"
    await run([runner, "test", "--report", manual_report.relative_to(ROOT), "--artifacts-dir",
               manual_artifacts.relative_to(ROOT), manual_spec.relative_to(ROOT)],
              "pick-technical-manual-edit-selected-test")
    manual_doc, manual_result = passed_report(manual_report, 3)
    html = output / "reports/manual-v3.html"
    await run([runner, "report", "--input", manual_report.relative_to(ROOT), "--evidence-root",
               manual_artifacts.relative_to(ROOT), "--output", html.relative_to(ROOT)],
              "pick-technical-machine-to-html-report")
    html_bytes = html.read_bytes()
    need(len(html_bytes) > 1024 and b"<!doctype html>" in html_bytes
         and b'class="status status-passed">passed</span>' in html_bytes
         and b"<strong>1</strong>Passed" in html_bytes,
         "offline HTML report is missing or does not summarize its passing machine report")

    migration_root = output / "migration"
    migration_root.mkdir()
    shutil.copytree(manual_root / "fixtures", migration_root / "fixtures")
    shutil.copytree(manual_root / "snapshots", migration_root / "snapshots")
    migration_spec = migration_root / "pick-migration.json"
    legacy = json.loads(json.dumps(manual))
    legacy["version"] = 2
    legacy["steps"] = [step for step in legacy["steps"] if "state" not in step]
    migration_spec.write_text(json.dumps(legacy, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8", newline="\n")
    legacy_copy = output / "reports/version-2-before-migration.json"
    shutil.copy2(migration_spec, legacy_copy)
    v2_report = output / "reports/version-2.json"
    await run([runner, "test", "--report", v2_report.relative_to(ROOT), "--artifacts-dir",
               (output / "artifacts/version-2").relative_to(ROOT), migration_spec.relative_to(ROOT)],
              "pick-technical-version-2-before-migration")
    passed_report(v2_report, 2)
    need(json.loads(migration_spec.read_text(encoding="utf-8")) == legacy,
         "version-2 execution unexpectedly rewrote its source spec")
    migration_spec.write_text(json.dumps(manual, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8", newline="\n")
    migrated_report = output / "reports/version-3-after-migration.json"
    await run([runner, "test", "--report", migrated_report.relative_to(ROOT), "--artifacts-dir",
               (output / "artifacts/version-3").relative_to(ROOT), migration_spec.relative_to(ROOT)],
              "pick-technical-version-3-after-migration")
    migrated_doc, migrated_result = passed_report(migrated_report, 3)
    need(migrated_result.get("invocation_id") != manual_result.get("invocation_id"),
         "version migration reused an earlier execution identity")

    rerecord_root = output / "suffix-rerecord"
    rerecord_root.mkdir()
    shutil.copytree(route_root / "project/fixtures", rerecord_root / "fixtures")
    shutil.copytree(route_root / "project/snapshots", rerecord_root / "snapshots")
    rerecord_spec = rerecord_root / "pick-blue.json"
    shutil.copy2(public_spec_path, rerecord_spec)
    prefix = public_spec["steps"][:2]
    controls = ["/rerecord 2", '/text "tail-choice"', "/expect Tail unique description",
                "/key Enter", "/exit 0", "/file choices.txt", "/review", "/replay", "/save"]
    edited = await run([runner, "record", "--edit", rerecord_spec.relative_to(ROOT)],
                       "pick-technical-suffix-rerecord", input_text="\n".join(controls) + "\n", timeout=300)
    rerecorded = json.loads(rerecord_spec.read_text(encoding="utf-8"))
    need(rerecorded.get("steps", [])[:2] == prefix
         and rerecorded.get("steps", [])[2:] == [
             {"text": "tail-choice"}, {"expect": "Tail unique description"}, {"key": "Enter"},
             {"exit": 0}, {"state": {"path": "choices.txt", "kind": "file",
                                     "bytes_base64": base64.b64encode(FIXTURE).decode("ascii")}}]
         and edited["returncode"] == 0,
         "suffix rerecord did not preserve the reviewed prefix and capture only its new suffix")
    suffix_report = output / "reports/suffix-rerecord.json"
    await run([runner, "test", "--report", suffix_report.relative_to(ROOT), "--artifacts-dir",
               (output / "artifacts/suffix-rerecord").relative_to(ROOT), rerecord_spec.relative_to(ROOT)],
              "pick-technical-suffix-rerecord-ordinary-test")
    suffix_doc, suffix_result = passed_report(suffix_report, 3)

    receipt = {
        "schema_version": 1, "status": "technical-route-passed-not-admitted", "project": PROJECT,
        "host": host, "source_pin": PIN, "candidate": "v0.4.0-rc.8", "candidate_series": "native-exit-v3",
        "candidate_binary_sha256": sha256(runner), "target_binary_sha256": sha256(target),
        "public_route_receipt_sha256": sha256(route_receipt_path),
        "public_route_declaration_sha256": route_receipt["route_declaration_sha256"],
        "public_spec_sha256": sha256(public_spec_path), "manual_v3_spec_sha256": sha256(manual_spec),
        "manual_v3_report_sha256": sha256(manual_report), "manual_html_sha256": sha256(html),
        "v2_spec_sha256": sha256(legacy_copy), "v2_report_sha256": sha256(v2_report),
        "migrated_v3_spec_sha256": sha256(migration_spec), "migrated_v3_report_sha256": sha256(migrated_report),
        "suffix_spec_sha256": sha256(rerecord_spec), "suffix_report_sha256": sha256(suffix_report),
        "suite_selection": {"status": "passed", "specs": 2, "attempt_id": listed["id"]},
        "manual_edit": {"status": "passed", "explicit_environment": "PLAYTESTR_PICK_TECHNICAL_ROUTE=explicit-rc8",
                        "unchanged_input_file_state": True, "invocation_id": manual_result["invocation_id"]},
        "machine_report": {"status": "passed", "version": manual_doc["report_version"]},
        "html_report": {"status": "passed", "bytes": len(html_bytes)},
        "migration": {"status": "passed", "from": 2, "to": 3,
                      "v2_attempt_id": next(row["id"] for row in attempts
                                             if row["label"] == "pick-technical-version-2-before-migration"),
                      "v3_invocation_id": migrated_result["invocation_id"]},
        "suffix_rerecord": {"status": "passed", "retained_prefix_steps": 2,
                            "invocation_id": suffix_result["invocation_id"], "controls": controls},
        "attempts": attempts, "human_participants": 0, "usability": "unmeasured", "admission_credit": 0,
        "completed_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    immutable_json(output / "receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "project": PROJECT, "host": host,
                      "attempts": len(attempts), "admission_credit": 0}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    asyncio.run(main_async(parser.parse_args().host))


if __name__ == "__main__":
    main()
