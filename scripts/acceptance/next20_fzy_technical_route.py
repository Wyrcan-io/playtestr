"""Exercise fzy technical suite, reporting, migration and suffix-rerecord paths."""
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

PROJECT = "fzy"
PACKAGE = DOC / PROJECT
PIN = "34b88869d022e861da4846c4463aea3ddfb3ff30"
HOSTS = {"linux": "Linux", "darwin": "Darwin"}
DECLARATION = PACKAGE / "public-route-declaration-v1.json"
PUBLIC_RECEIPT = PACKAGE / "public-route-run43364417379-v1.json"
OUTPUT = RAW / PROJECT / "technical-route-v1"


def need(condition, message):
    if not condition:
        raise ValueError(message)


def passing_report(path, version):
    report = json.loads(path.read_text(encoding="utf-8"))
    need(report.get("report_version") == version and len(report.get("results", [])) == 1,
         f"fzy technical report version/denominator differs: {path.name}")
    result = report["results"][0]
    need(result.get("status") == "passed"
         and result.get("cleanup", {}).get("confirmed_exited") is True
         and result.get("workspace", {}).get("cleaned") is True
         and all(step.get("status") == "passed" for step in result.get("steps", [])),
         f"fzy technical route lacks positive target/cleanup evidence: {path.name}")
    return report, result


async def main_async(host):
    need(platform.system() == HOSTS[host], "actual native host differs from fzy technical-route host")
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    public = json.loads(PUBLIC_RECEIPT.read_text(encoding="utf-8"))
    need(declaration.get("project") == PROJECT and declaration.get("source_pin") == PIN
         and public.get("status") == "passed-and-independently-audited"
         and public.get("independent_audit_sha256") == "503ca2151d5626749ec5dc1df20c11c754e2bbb8f60f58433b2c1f044482d218"
         and public.get("project_admission_credit") == 0,
         "fzy technical route is not bound to the audited exact-source public route")
    target_root = RAW / "active" / PROJECT
    target = target_root / "install" / "bin" / "fzy"
    build = json.loads((target_root / "build.json").read_text(encoding="utf-8"))
    runtime = json.loads((target_root / "runtime.json").read_text(encoding="utf-8"))
    runner = executable("native-exit-v3", host)
    installed = json.loads((runner.parent / "installed.json").read_text(encoding="utf-8"))
    freeze = json.loads((DOC / "replacement-candidate-freeze-native-exit-v3.json").read_text(encoding="utf-8"))
    cell = next(row for row in freeze["cells"] if row["host"] == host)
    need(build.get("project") == PROJECT and build.get("pin") == PIN and build.get("host") == host
         and build.get("upstream_tests") == "passed" and sha256(target) == build.get("binary_sha256")
         and runtime.get("native_sha256") == sha256(target)
         and sha256(runner) == cell["binary_sha256"] and installed.get("archive_sha256") == cell["archive_sha256"],
         "fzy technical route target/candidate differs from exact native inputs")
    need(not OUTPUT.joinpath(host).exists(), "preserve existing fzy technical-route evidence")
    output = OUTPUT / host
    output.mkdir(parents=True)
    fixture = base64.b64decode(declaration["first_use_fixture_base64"], validate=True)
    expected = declaration["first_use_output_base64"]
    env = {key: os.environ[key] for key in
           ("PATH", "HOME", "SystemRoot", "WINDIR", "COMSPEC", "PATHEXT") if key in os.environ}
    env["PATH"] = str(target.parent) + os.pathsep + env.get("PATH", "")
    env.update({"TERM": "xterm-256color", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
                "PLAYTESTR_FZY_TECHNICAL_ROUTE": "explicit-rc8"})
    campaign = NextCampaign(phase="technical-authoring")
    attempts = []

    async def run(argv, label, *, input_text=None, timeout=180):
        result = await execute(list(map(str, argv)), PROJECT, label, cwd=ROOT, env=env,
                               input=input_text, expected=0, timeout=timeout, campaign=campaign)
        attempts.append({"id": result["id"], "label": label, "returncode": result["returncode"],
                         "seconds": round(result["seconds"], 3)})
        return result

    version = await run([runner, "--version"], "fzy-technical-route-runner-version")
    need(version["output"].strip() == "playtestr v0.4.0-rc.8", "wrong exact candidate in fzy technical route")
    manual_root = output / "manual selection"
    (manual_root / "fixtures").mkdir(parents=True)
    (manual_root / "fixtures" / "choices.txt").write_bytes(fixture)
    manual = {"version": 3, "name": "Fzy manual edit and preserved fixture input",
              "command": ["/bin/sh", "-c", "exec fzy < choices.txt > result.txt"],
              "workspace": {"cwd": ".", "fixture": "fixtures", "home": "temporary", "temp": "temporary"},
              "env": {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TERM": "xterm-256color",
                      "PLAYTESTR_FZY_TECHNICAL_ROUTE": "explicit-rc8"},
              "inherit_env": ["PATH"], "width": 80, "height": 12, "timeout_ms": 12000,
              "run_timeout_ms": 60000, "max_output_bytes": 2000000,
              "steps": [{"expect": "apple"}, {"key": "Enter"}, {"exit": 0},
                        {"state": {"path": "result.txt", "kind": "file", "bytes_base64": expected}},
                        {"state": {"path": "choices.txt", "kind": "file",
                                   "bytes_base64": base64.b64encode(fixture).decode("ascii")}}]}
    manual_spec = manual_root / "fzy-manual-v3.json"
    manual_spec.write_text(json.dumps(manual, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
                           encoding="utf-8", newline="\n")
    selection = output / "suite-selection"
    selection.mkdir()
    shutil.copytree(manual_root / "fixtures", selection / "fixtures")
    shutil.copy2(manual_spec, selection / "chosen.json")
    unselected = dict(manual, name="Unselected fzy suite member")
    (selection / "separate.json").write_text(json.dumps(unselected, sort_keys=True, indent=2) + "\n",
                                              encoding="utf-8", newline="\n")
    listed = await run([runner, "test", "--list", selection.relative_to(ROOT)],
                       "fzy-technical-suite-selection")
    need("Selected 2 specs:" in listed["output"] and "chosen.json" in listed["output"]
         and "separate.json" in listed["output"], "fzy suite selection did not enumerate exactly two specs")

    reports = output / "reports"
    reports.mkdir()
    manual_report = reports / "manual-v3.json"
    await run([runner, "test", "--report", manual_report.relative_to(ROOT), "--artifacts-dir",
               (output / "artifacts/manual-v3").relative_to(ROOT), manual_spec.relative_to(ROOT)],
              "fzy-technical-manual-edit-selected-test")
    manual_doc, manual_result = passing_report(manual_report, 3)
    manual_doc_html = output / "reports/manual-v3.html"
    await run([runner, "report", "--input", manual_report.relative_to(ROOT), "--evidence-root",
               (output / "artifacts/manual-v3").relative_to(ROOT), "--output", manual_doc_html.relative_to(ROOT)],
              "fzy-technical-machine-to-html-report")
    html = manual_doc_html.read_bytes()
    need(len(html) > 1024 and b"<!doctype html>" in html
         and b'class="status status-passed">passed</span>' in html,
         "fzy offline HTML report does not summarize successful machine evidence")

    migration_root = output / "migration"
    migration_root.mkdir()
    shutil.copytree(manual_root / "fixtures", migration_root / "fixtures")
    migration = json.loads(json.dumps(manual))
    migration["version"] = 2
    migration["steps"] = [step for step in migration["steps"] if "state" not in step]
    migration_spec = migration_root / "fzy-migration.json"
    legacy_bytes = json.dumps(migration, sort_keys=True, indent=2) + "\n"
    migration_spec.write_text(legacy_bytes, encoding="utf-8", newline="\n")
    legacy_copy = reports / "version-2-before-migration.json"
    shutil.copy2(migration_spec, legacy_copy)
    v2_report = reports / "version-2.json"
    await run([runner, "test", "--report", v2_report.relative_to(ROOT), "--artifacts-dir",
               (output / "artifacts/version-2").relative_to(ROOT), migration_spec.relative_to(ROOT)],
              "fzy-technical-version-2-before-migration")
    passing_report(v2_report, 2)
    need(migration_spec.read_text(encoding="utf-8") == legacy_bytes,
         "v2 execution rewrote its spec")
    migration["version"] = 3
    migration["steps"].extend(manual["steps"][3:])
    migration_spec.write_text(json.dumps(migration, sort_keys=True, indent=2) + "\n",
                              encoding="utf-8", newline="\n")
    migrated_report = reports / "version-3-after-migration.json"
    await run([runner, "test", "--report", migrated_report.relative_to(ROOT), "--artifacts-dir",
               (output / "artifacts/version-3").relative_to(ROOT), migration_spec.relative_to(ROOT)],
              "fzy-technical-version-3-after-migration")
    migrated_doc, migrated_result = passing_report(migrated_report, 3)
    need(migrated_result.get("invocation_id") != manual_result.get("invocation_id"),
         "migrated v3 execution reused manual execution identity")

    suffix_root = output / "suffix-rerecord"
    (suffix_root / "fixtures").mkdir(parents=True)
    (suffix_root / "fixtures" / "choices.txt").write_bytes(fixture)
    suffix_spec = suffix_root / "fzy-suffix.json"
    starter = {key: value for key, value in manual.items() if key != "steps"}
    starter["steps"] = [{"expect": "apple"}, {"key": "Enter"}, {"exit": 0},
                        {"state": {"path": "result.txt", "kind": "file", "bytes_base64": expected}}]
    suffix_spec.write_text(json.dumps(starter, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    controls = ["/rerecord 1", '/text "apple"', "/key Enter", "/exit 0", "/file result.txt", "/review", "/replay", "/save"]
    edited = await run([runner, "record", "--edit", suffix_spec.relative_to(ROOT)],
                       "fzy-technical-suffix-rerecord", input_text="\n".join(controls) + "\n", timeout=300)
    rerecorded = json.loads(suffix_spec.read_text(encoding="utf-8"))
    need(edited["returncode"] == 0 and rerecorded.get("steps", [])[:1] == starter["steps"][:1]
         and rerecorded.get("steps", [])[1:] == [{"text": "apple"}, {"key": "Enter"}, {"exit": 0},
                                                  {"state": {"path": "result.txt", "kind": "file",
                                                              "bytes_base64": expected}}],
         "fzy suffix rerecord changed reviewed prefix or failed to capture exact selected suffix")
    suffix_report = reports / "suffix-rerecord.json"
    await run([runner, "test", "--report", suffix_report.relative_to(ROOT), "--artifacts-dir",
               (output / "artifacts/suffix-rerecord").relative_to(ROOT), suffix_spec.relative_to(ROOT)],
              "fzy-technical-suffix-rerecord-ordinary-test")
    _, suffix_result = passing_report(suffix_report, 3)

    receipt = {"schema_version": 1, "status": "technical-route-passed-not-admitted", "project": PROJECT,
               "host": host, "source_pin": PIN, "candidate": freeze["version"],
               "candidate_series": freeze["series"], "candidate_binary_sha256": sha256(runner),
               "target_binary_sha256": sha256(target), "build_receipt_sha256": sha256(target_root / "build.json"),
               "public_route_receipt_sha256": sha256(PUBLIC_RECEIPT), "route_declaration_sha256": sha256(DECLARATION),
               "manual_spec_sha256": sha256(manual_spec), "manual_report_sha256": sha256(manual_report),
               "html_sha256": sha256(manual_doc_html), "legacy_spec_sha256": sha256(legacy_copy),
               "v2_report_sha256": sha256(v2_report), "migrated_spec_sha256": sha256(migration_spec),
               "migrated_report_sha256": sha256(migrated_report), "suffix_spec_sha256": sha256(suffix_spec),
               "suffix_report_sha256": sha256(suffix_report), "suite_selection": "passed-two-specs",
               "input_preservation": "passed-exact-fixture-bytes", "migration": "passed-v2-to-v3",
               "suffix_rerecord": {"status": "passed", "retained_prefix_steps": 1,
                                    "invocation_id": suffix_result.get("invocation_id"), "controls": controls},
               "manual_invocation_id": manual_result.get("invocation_id"),
               "migrated_invocation_id": migrated_result.get("invocation_id"),
               "manual_report_version": manual_doc.get("report_version"),
               "migrated_report_version": migrated_doc.get("report_version"),
               "html_bytes": len(html), "attempts": attempts, "human_participants": 0,
               "usability": "unmeasured", "admission_credit": 0}
    immutable_json(output / "receipt.json", receipt)
    print(json.dumps({"project": PROJECT, "host": host, "status": receipt["status"],
                      "attempts": len(attempts), "admission_credit": 0}, sort_keys=True))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    asyncio.run(main_async(parser.parse_args().host))


if __name__ == "__main__":
    main()
