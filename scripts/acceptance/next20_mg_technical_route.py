"""Exercise mg with manually edited, selected, migrated and suffix-rerecorded specs."""
import base64
import atexit
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
RUNNER_SHA = "e302a46eb090772d91aab7018b51eea0d1fb92247846f4a63375e1009e29309a"
TARGET_SHA = "6eb334f5ea96687983c51b073b1b8a11434ea85a46e69ca6e28e57b76b4e88e5"
OUTPUT = RAW / "mg/technical-route-native-exit-v1"
INITIAL = b"MG_PUBLIC_ROUTE_START\n"
MARKER = "MG_PUBLIC_ROUTE_RC6"


async def run_technical(route_root, mg_build_root):
    if platform.system() != "Linux":
        raise RuntimeError("mg technical route is declared for hosted Linux only")
    if OUTPUT.exists():
        raise ValueError("preserve existing mg technical-route evidence")
    route_root = Path(route_root).resolve(strict=True)
    route_root.relative_to(ROOT.resolve())
    mg_build_root = Path(mg_build_root).resolve(strict=True)
    mg_build_root.relative_to(ROOT.resolve())
    route_receipt = json.loads((route_root / "receipt.json").read_text(encoding="utf-8"))
    base_path = route_root / "project/create-note.json"
    if (route_receipt.get("target_binary_sha256") != TARGET_SHA or
            route_receipt.get("runner_sha256") != RUNNER_SHA or
            sha256(base_path) != route_receipt.get("first_spec_sha256")):
        raise ValueError("technical route input does not match the audited public route")
    build = json.loads((mg_build_root / "active/mg/build.json").read_text(encoding="utf-8"))
    original = (mg_build_root / "active/mg/install/bin/mg").resolve(strict=True)
    if build.get("project") != "mg" or build.get("pin") != PIN or sha256(original) != TARGET_SHA:
        raise ValueError("technical route target differs from the pinned native mg build")
    runner = executable("native-exit-v1", "linux")
    if sha256(runner) != RUNNER_SHA:
        raise ValueError("technical route did not resolve the exact frozen candidate")

    OUTPUT.mkdir(parents=True)
    target = OUTPUT / "target/bin/mg"
    target.parent.mkdir(parents=True)
    shutil.copy2(original, target)
    def cleanup_target():
        if target.exists():
            if sha256(target) != TARGET_SHA:
                raise RuntimeError("technical-route target identity changed; refusing cleanup")
            target.unlink()
        if target.parent.exists() and not any(target.parent.iterdir()):
            target.parent.rmdir()
    atexit.register(cleanup_target)
    mode = ensure_executable(target)
    if sha256(target) != TARGET_SHA:
        raise ValueError("technical-route target copy changed bytes")
    env = dict(os.environ)
    env["PATH"] = str(target.parent) + os.pathsep + env.get("PATH", "")
    env["LANG"] = "C.UTF-8"
    env["LC_ALL"] = "C.UTF-8"
    campaign = NextCampaign(phase="technical-authoring")
    attempts = []
    edited_marker = MARKER + "_TECH"
    suffix_marker = MARKER + "_SUFFIX"
    index = 4
    plan = {"schema_version": 1, "project": "mg", "source_pin": PIN,
            "candidate": "v0.4.0-rc.6", "runner_sha256": RUNNER_SHA,
            "target_binary_sha256": TARGET_SHA, "public_route_spec_sha256": route_receipt["first_spec_sha256"],
            "manual_edit": {"field": "typed text, rendered screen expectation and saved file bytes",
                            "marker": edited_marker, "explicit_environment": "PLAYTESTR_TECHNICAL_ROUTE=explicit-rc6"},
            "suite_selection": {"listed_specs": 2, "selected_test": "chosen.json"},
            "reports": ["versioned JSON machine report", "self-contained offline HTML report"],
            "migration": {"from_spec": 2, "to_spec": 3, "state_assertion_added": True},
            "suffix_rerecord": {"prefix_steps": index, "marker": suffix_marker,
                                "state_bytes_sha256": __import__("hashlib").sha256(INITIAL + suffix_marker.encode()).hexdigest()},
            "target_copy_mode": mode,
            "attempts": [{"label": label, "expected_exit": 0} for label in [
                "mg-technical-suite-selection", "mg-technical-manual-edit-selected-test",
                "mg-technical-machine-to-html-report", "mg-technical-version-2-before-migration",
                "mg-technical-version-3-after-migration", "mg-technical-suffix-rerecord",
                "mg-technical-suffix-rerecord-ordinary-test"]]}
    immutable_json(OUTPUT / "planned.json", plan)
    manual = OUTPUT / "manual-edit/create-note.json"
    manual.parent.mkdir(parents=True)
    shutil.copytree(route_root / "project/fixtures", manual.parent / "fixtures")
    source = json.loads(base_path.read_text(encoding="utf-8"))
    old_text = [step for step in source["steps"] if step.get("text") == MARKER]
    old_expect = [step for step in source["steps"] if step.get("expect") == MARKER]
    old_state = [step["state"] for step in source["steps"] if step.get("state", {}).get("path") == "public-note.txt"]
    if len(old_text) != 1 or len(old_expect) != 1 or len(old_state) != 1:
        raise ValueError("technical route cannot locate exact public-route text, screen and file fields")
    old_text[0]["text"] = edited_marker
    old_expect[0]["expect"] = edited_marker
    old_state[0]["bytes_base64"] = base64.b64encode(INITIAL + edited_marker.encode()).decode("ascii")
    source["env"]["PLAYTESTR_TECHNICAL_ROUTE"] = "explicit-rc6"
    manual.write_text(json.dumps(source, ensure_ascii=True, sort_keys=True, indent=2) + "\n",
                      encoding="utf-8", newline="\n")

    selection = OUTPUT / "selection"
    selection.mkdir()
    shutil.copytree(manual.parent / "fixtures", selection / "fixtures")
    chosen = selection / "chosen.json"
    shutil.copy2(manual, chosen)
    unselected = json.loads(json.dumps(source))
    unselected["name"] = "A separate mg technical-route spec"
    (selection / "separate.json").write_text(json.dumps(unselected, sort_keys=True, indent=2) + "\n",
                                               encoding="utf-8", newline="\n")
    listed = await execute([runner, "test", "--list", selection.relative_to(ROOT)], "mg",
                           "mg-technical-suite-selection", cwd=ROOT, env=env, timeout=60,
                           campaign=campaign)
    if listed["returncode"] != 0 or "Selected 2 specs:" not in listed["output"]:
        raise ValueError("candidate did not report exact two-spec suite selection")
    attempts.append({"label": "mg-technical-suite-selection", "id": listed["id"], "returncode": 0,
                     "output_sha256": __import__("hashlib").sha256(listed["output"].encode()).hexdigest()})

    async def test_spec(name, spec, label):
        report = OUTPUT / "reports" / (name + ".json")
        artifacts = OUTPUT / "artifacts" / name
        result = await execute([runner, "test", "--report", report.relative_to(ROOT), "--artifacts-dir",
                                artifacts.relative_to(ROOT), spec.relative_to(ROOT)], "mg", label,
                               cwd=ROOT, env=env, timeout=180, campaign=campaign)
        doc = json.loads(report.read_text(encoding="utf-8"))
        if (result["returncode"] != 0 or len(doc.get("results", [])) != 1 or
                doc["results"][0].get("status") != "passed" or
                not doc["results"][0].get("cleanup", {}).get("confirmed_exited") or
                not doc["results"][0].get("workspace", {}).get("cleaned")):
            raise ValueError("technical-route ordinary test lacks passing report and cleanup: " + name)
        attempt = {"label": label, "id": result["id"], "returncode": 0,
                   "report_sha256": sha256(report)}
        if doc["results"][0].get("invocation_id"):
            attempt["invocation_id"] = doc["results"][0]["invocation_id"]
        attempts.append(attempt)
        return report, artifacts

    report, artifacts = await test_spec("manual-edit-selected", chosen, "mg-technical-manual-edit-selected-test")
    html = OUTPUT / "reports/manual-edit-selected.html"
    rendered = await execute([runner, "report", "--input", report.relative_to(ROOT), "--evidence-root",
                              artifacts.relative_to(ROOT), "--output", html.relative_to(ROOT)], "mg",
                             "mg-technical-machine-to-html-report", cwd=ROOT, env=env, timeout=120,
                             campaign=campaign)
    if rendered["returncode"] != 0 or not html.is_file() or b"MG_PUBLIC_ROUTE_RC6_TECH" in html.read_bytes():
        raise ValueError("candidate HTML report generation failed or embedded an excluded screen expression")
    attempts.append({"label": "mg-technical-machine-to-html-report", "id": rendered["id"],
                     "returncode": 0, "html_sha256": sha256(html)})

    migration = OUTPUT / "migration/create-note.json"
    migration.parent.mkdir()
    shutil.copytree(manual.parent / "fixtures", migration.parent / "fixtures")
    shutil.copy2(manual, migration)
    legacy = json.loads(migration.read_text(encoding="utf-8"))
    legacy["version"] = 2
    legacy["steps"] = [step for step in legacy["steps"] if "state" not in step]
    migration.write_text(json.dumps(legacy, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    legacy_copy = OUTPUT / "migration/version-2-before-migration.json"
    shutil.copy2(migration, legacy_copy)
    v2_report, _ = await test_spec("version-2-before-migration", migration,
                                   "mg-technical-version-2-before-migration")
    migrated = json.loads(migration.read_text(encoding="utf-8"))
    migrated["version"] = 3
    migrated["steps"].append({"state": {"path": "public-note.txt", "kind": "file",
                                        "bytes_base64": base64.b64encode(INITIAL + edited_marker.encode()).decode("ascii")}})
    migration.write_text(json.dumps(migrated, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    v3_report, _ = await test_spec("version-3-after-migration", migration,
                                   "mg-technical-version-3-after-migration")

    rerecorded = OUTPUT / "suffix-rerecord/create-note.json"
    rerecorded.parent.mkdir()
    shutil.copytree(route_root / "project/fixtures", rerecorded.parent / "fixtures")
    shutil.copy2(base_path, rerecorded)
    value = json.loads(rerecorded.read_text(encoding="utf-8"))
    text = [step for step in value["steps"] if step.get("text") == MARKER]
    if len(text) != 1:
        raise ValueError("suffix rerecord cannot identify one intended recorded text step")
    text[0]["text"] = suffix_marker
    index = next(i for i, step in enumerate(value["steps"], 1) if step.get("text") == suffix_marker)
    rerecorded.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8", newline="\n")
    controls = [f"/rerecord {index}", f"/expect {suffix_marker}", "/key CtrlX", "/key CtrlS",
                "/expect Wrote", "/key CtrlX", "/key CtrlC", "/exit 0", "/file public-note.txt",
                "/review", "/replay", "/save"]
    edited = await execute([runner, "record", "--edit", rerecorded.relative_to(ROOT)], "mg",
                           "mg-technical-suffix-rerecord", cwd=ROOT, env=env,
                           input="\n".join(controls) + "\n", timeout=300, campaign=campaign)
    rerecorded_spec = json.loads(rerecorded.read_text(encoding="utf-8"))
    final_state = [step["state"] for step in rerecorded_spec["steps"]
                   if step.get("state", {}).get("path") == "public-note.txt"]
    if (edited["returncode"] != 0 or len(final_state) != 1 or
            base64.b64decode(final_state[0]["bytes_base64"], validate=True) != INITIAL + suffix_marker.encode()):
        raise ValueError("selected suffix rerecord failed to retain prefix and capture exact new file bytes")
    attempts.append({"label": "mg-technical-suffix-rerecord", "id": edited["id"], "returncode": 0,
                     "controls": controls, "spec_sha256": sha256(rerecorded)})
    suffix_report, _ = await test_spec("suffix-rerecord-ordinary-pass", rerecorded,
                                       "mg-technical-suffix-rerecord-ordinary-test")

    if sha256(target) != TARGET_SHA:
        raise ValueError("refusing to remove changed technical-route target copy")
    target.unlink()
    target.parent.rmdir()
    if target.exists():
        raise ValueError("technical-route target copy remains")
    receipt = {"schema_version": 1, "status": "technical-authoring-route-passed-not-admitted",
               "project": "mg", "source_pin": PIN, "candidate": "v0.4.0-rc.6",
               "runner_sha256": RUNNER_SHA, "target_binary_sha256": TARGET_SHA,
               "planned_sha256": sha256(OUTPUT / "planned.json"), "attempt_count": len(attempts),
               "attempts": attempts,
               "version2_report_sha256": sha256(v2_report), "version3_report_sha256": sha256(v3_report),
               "manual_edit_report_sha256": sha256(report), "html_report_sha256": sha256(html),
               "suffix_ordinary_report_sha256": sha256(suffix_report),
               "rerecorded_spec_sha256": sha256(rerecorded),
               "target_copy_sha256": TARGET_SHA, "target_copy_removed": not target.exists(),
               "admission_credit": 0}
    immutable_json(OUTPUT / "receipt.json", receipt)
    return receipt
