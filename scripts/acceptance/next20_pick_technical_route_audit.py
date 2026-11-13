"""Independently audit exact GitHub ZIPs for Pick's technical route."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC

RUN_ID = 43350106198
HEAD_SHA = "2d1ae6b85b1aa8d641602f248671c4ccfa091210"
PIN = "caae95938359b2e814b3e7406f396f486c9d99fb"
SOURCE_SHA256 = "e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653"
DECLARATION = DOC / "pick/public-route-declaration-v1.json"
FREEZE = DOC / "replacement-candidate-freeze-native-exit-v3.json"
OUTPUT = DOC / "pick"
PROVIDERS = {
    "linux": {"artifact_id": 14002993617, "name": "next20-pick-public-route-linux-43350106198",
              "bytes": 996587, "sha256": "b6f8db2a869ae5730681ed1f22dc3228873cba074b010a1968f007760aaa202d"},
    "darwin": {"artifact_id": 14003925585, "name": "next20-pick-public-route-darwin-43350106198",
               "bytes": 996678, "sha256": "9c230e418c097fc7bada68bacd2f7f3867486461fe8e8c7266574bfeca47ad54"},
}
LABELS = [
    "pick-technical-route-runner-version", "pick-technical-suite-selection",
    "pick-technical-manual-edit-selected-test", "pick-technical-machine-to-html-report",
    "pick-technical-version-2-before-migration", "pick-technical-version-3-after-migration",
    "pick-technical-suffix-rerecord", "pick-technical-suffix-rerecord-ordinary-test",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def audit_host(host, zip_path, freeze):
    provider = PROVIDERS[host]
    blob = Path(zip_path).read_bytes()
    need(len(blob) == provider["bytes"] and digest(blob) == provider["sha256"],
         f"{host}: provider ZIP size/digest differs from GitHub metadata")
    with zipfile.ZipFile(zip_path) as archive:
        need(archive.testzip() is None, f"{host}: ZIP CRC verification failed")
        names = archive.namelist()
        for name in names:
            path = PurePosixPath(name)
            need(not path.is_absolute() and ".." not in path.parts, f"{host}: unsafe ZIP member path")
        members = {name: archive.read(name) for name in names if not name.endswith("/")}

    def raw(name):
        try:
            return members[name]
        except KeyError as error:
            raise ValueError(f"{host}: missing ZIP member {name}") from error

    def obj(name):
        return json.loads(raw(name).decode("utf-8"))

    public = f"pick/public-route-v1/{host}/"
    root = f"pick/technical-route-v1/{host}/"
    receipt = obj(root + "receipt.json")
    public_receipt = obj(public + "receipt.json")
    candidate = next(row for row in freeze["cells"] if row["host"] == host)
    need(receipt.get("status") == "technical-route-passed-not-admitted"
         and receipt.get("project") == "pick" and receipt.get("host") == host
         and receipt.get("source_pin") == PIN and receipt.get("candidate") == freeze["version"] == "v0.4.0-rc.8"
         and receipt.get("candidate_series") == freeze["series"] == "native-exit-v3"
         and receipt.get("candidate_binary_sha256") == candidate["binary_sha256"]
         and public_receipt.get("target_binary_sha256") == receipt.get("target_binary_sha256")
         and receipt.get("public_route_receipt_sha256") == digest(raw(public + "receipt.json"))
         and receipt.get("public_route_declaration_sha256") == public_receipt.get("route_declaration_sha256")
         and receipt.get("public_route_declaration_sha256") == digest(DECLARATION.read_bytes())
         and receipt.get("admission_credit") == 0,
         f"{host}: technical/public route, candidate or admission identity differs")
    installed = obj(f"candidate-native-exit-v3/{host}/installed.json")
    need(installed.get("archive_sha256") == candidate["archive_sha256"]
         and installed.get("binary_sha256") == candidate["binary_sha256"]
         and installed.get("source_revision") == freeze.get("source_revision"),
         f"{host}: installed runner differs from frozen candidate")
    build = obj("pick/retained-source/build.json")
    runtime = obj("pick/retained-source/runtime.json")
    need(build.get("project") == "pick" and build.get("host") == host and build.get("pin") == PIN
         and build.get("source_archive_sha256") == SOURCE_SHA256 and build.get("upstream_tests") == "passed"
         and runtime.get("native_sha256") == build.get("binary_sha256")
         and receipt.get("target_binary_sha256") == build.get("binary_sha256"),
         f"{host}: native target identity/upstream build differs")
    inventory_bytes = raw("pick/retained-source/cleanup-inventory.json")
    inventory = json.loads(inventory_bytes.decode("utf-8"))
    removed = obj("pick/retained-source/removed.json")
    proof_bytes = raw("pick/process-proof.json")
    proof = json.loads(proof_bytes.decode("utf-8"))
    need(inventory.get("source_restored_exact") is True and inventory.get("project") == "pick"
         and inventory.get("actual_reports_with_confirmed_cleanup") == 9
         and inventory.get("process_proof_sha256") == digest(proof_bytes)
         and removed.get("removed") is True and removed.get("source_restored_exact") is True
         and removed.get("cleanup_inventory_sha256") == digest(inventory_bytes)
         and proof.get("confirmed_no_matching_live_processes") is True,
         f"{host}: exact restoration, source cleanup, or process cleanup differs")
    for relative, expected_hash in inventory.get("retained", {}).items():
        need(digest(raw("pick/retained-source/" + relative)) == expected_hash,
             f"{host}: retained source/build receipt hash differs: {relative}")

    attempts = receipt.get("attempts", [])
    need([row.get("label") for row in attempts] == LABELS and len({row.get("id") for row in attempts}) == 8
         and all(row.get("returncode") == 0 for row in attempts),
         f"{host}: technical attempt ledger is incomplete or unsuccessful")
    for row in attempts:
        events = {kind: obj(f"events/{row['id']}-{kind}.json")
                  for kind in ("started", "identified", "launched", "finished")}
        for kind, event in events.items():
            need(event.get("id") == row["id"] and event.get("event") == kind
                 and event.get("project") == "pick" and event.get("phase") == "technical-authoring"
                 and event.get("label") == row["label"],
                 f"{host}: technical event identity differs: {row['label']}/{kind}")
        need(isinstance(events["launched"].get("pid"), int) and events["launched"]["pid"] > 0,
             f"{host}: technical attempt lacks positive launch evidence: {row['label']}")
        event = events["finished"]
        console = raw(f"pick/{row['id']}/console.log")
        need(event.get("exit_code") == 0 and not event.get("cleanup_errors")
             and event.get("harness_cleanup") == "harness_process_reaped"
             and event.get("console_sha256") == digest(console) and event.get("output_bytes") == len(console),
             f"{host}: technical command event/console mismatch: {row['label']}")
        row["audit_console_sha256"] = digest(console)

    selection = next(row for row in attempts if row["label"] == "pick-technical-suite-selection")
    need(b"Selected 2 specs:" in raw(f"pick/{selection['id']}/console.log"),
         f"{host}: suite selection did not report exactly two specs")
    manual = json.loads(raw(root + "manual selection/pick-manual-v3.json").decode("utf-8"))
    fixture = b"".join(f"item{i:02d}:Item description {i:02d}\n".encode("ascii") for i in range(29))
    fixture += b"tail-choice:Tail unique description\n"
    need(raw(root + "manual selection/fixtures/choices.txt") == fixture
         and raw(root + "manual selection/snapshots/initial-menu.txt").find(b"item00") >= 0,
         f"{host}: manually edited fixture/snapshot bytes differ")
    expected_manual = json.loads(json.dumps(json.loads(raw(public + "project/pick-blue.json").decode("utf-8"))))
    expected_manual["name"] = "Pick technical manual spec edit and input preservation"
    expected_manual["env"]["PLAYTESTR_PICK_TECHNICAL_ROUTE"] = "explicit-rc8"
    expected_manual["steps"][2]["text"] = "tail-choice"
    expected_manual["steps"].append({"state": {"path": "choices.txt", "kind": "file",
                                                "bytes_base64": base64.b64encode(fixture).decode("ascii")}})
    need(manual == expected_manual and manual.get("version") == 3 and manual.get("env", {}).get("IFS") == ":"
         and manual.get("env", {}).get("PLAYTESTR_PICK_TECHNICAL_ROUTE") == "explicit-rc8"
         and digest(raw(root + "manual selection/pick-manual-v3.json")) == receipt.get("manual_v3_spec_sha256"),
         f"{host}: explicit environment, manual query edit or exact input-preservation state differs")

    def passing_report(name, version, receipt_hash=None):
        content = raw(root + name)
        report = json.loads(content.decode("utf-8"))
        need(report.get("report_version") == version and len(report.get("results", [])) == 1,
             f"{host}: report schema/denominator differs: {name}")
        result = report["results"][0]
        need(result.get("status") == "passed" and result.get("cleanup", {}).get("confirmed_exited") is True
             and result.get("workspace", {}).get("cleaned") is True
             and all(step.get("status") == "passed" for step in result.get("steps", [])),
             f"{host}: report has non-passing step or incomplete cleanup: {name}")
        if receipt_hash:
            need(digest(content) == receipt[receipt_hash], f"{host}: report hash differs from receipt: {name}")
        return report, result, digest(content)

    manual_report, manual_result, manual_hash = passing_report("reports/manual-v3.json", 3,
                                                                "manual_v3_report_sha256")
    preview_html = raw(root + "reports/manual-v3.html")
    need(digest(preview_html) == receipt.get("manual_html_sha256")
         and b"<!doctype html>" in preview_html and b'class="status status-passed">passed</span>' in preview_html,
         f"{host}: machine-to-HTML output does not match the passing report")
    v2_doc, v2_result, v2_hash = passing_report("reports/version-2.json", 2, "v2_report_sha256")
    legacy = json.loads(raw(root + "reports/version-2-before-migration.json").decode("utf-8"))
    need(legacy.get("version") == 2 and all("state" not in step for step in legacy.get("steps", []))
         and "invocation_id" not in v2_result
         and digest(raw(root + "reports/version-2-before-migration.json")) == receipt.get("v2_spec_sha256"),
         f"{host}: v2 compatibility report/schema differs")
    migrated = json.loads(raw(root + "migration/pick-migration.json").decode("utf-8"))
    need(migrated == manual and digest(raw(root + "migration/pick-migration.json")) == receipt.get("migrated_v3_spec_sha256"),
         f"{host}: v2-to-v3 migration bytes differ from manually edited v3 contract")
    _, migrated_result, migrated_hash = passing_report("reports/version-3-after-migration.json", 3,
                                                         "migrated_v3_report_sha256")
    suffix = json.loads(raw(root + "suffix-rerecord/pick-blue.json").decode("utf-8"))
    public_spec = json.loads(raw(public + "project/pick-blue.json").decode("utf-8"))
    suffix_steps = suffix.get("steps", [])
    need(suffix_steps[:2] == public_spec["steps"][:2]
         and suffix_steps[2:] == [
             {"text": "tail-choice"}, {"expect": "Tail unique description"}, {"key": "Enter"},
             {"exit": 0}, {"state": {"path": "choices.txt", "kind": "file",
             "bytes_base64": base64.b64encode(fixture).decode("ascii")}}]
         and digest(raw(root + "suffix-rerecord/pick-blue.json")) == receipt.get("suffix_spec_sha256"),
         f"{host}: suffix rerecord altered its reviewed prefix or expected suffix")
    _, suffix_result, suffix_hash = passing_report("reports/suffix-rerecord.json", 3,
                                                    "suffix_report_sha256")
    need(receipt.get("suite_selection", {}).get("status") == "passed"
         and receipt.get("manual_edit", {}).get("status") == "passed"
         and receipt.get("migration", {}).get("status") == "passed"
         and receipt.get("suffix_rerecord", {}).get("status") == "passed"
         and receipt.get("suffix_rerecord", {}).get("retained_prefix_steps") == 2,
         f"{host}: route receipt omits a technical route milestone")

    return {"host": host, "provider": {**provider, "observed_bytes": len(blob), "observed_sha256": digest(blob)},
            "candidate_archive_sha256": candidate["archive_sha256"],
            "candidate_binary_sha256": candidate["binary_sha256"],
            "target_binary_sha256": build["binary_sha256"], "technical_attempts": attempts,
            "suite_selection": "passed-two-specs", "manual_v3_report_sha256": manual_hash,
            "manual_html_sha256": digest(preview_html), "v2_report_sha256": v2_hash,
            "migrated_v3_report_sha256": migrated_hash, "suffix_report_sha256": suffix_hash,
            "manual_v3_invocation_id": manual_result["invocation_id"],
            "migrated_v3_invocation_id": migrated_result["invocation_id"],
            "suffix_invocation_id": suffix_result["invocation_id"],
            "source_restored_exact": True, "target_removed": True, "no_matching_processes": True,
            "admission_credit": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--linux-zip", required=True, type=Path)
    parser.add_argument("--darwin-zip", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    freeze_bytes = FREEZE.read_bytes()
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    need(digest(freeze_bytes) == declaration.get("candidate_freeze_sha256"),
         "Pick freeze digest differs from route declaration")
    freeze = json.loads(freeze_bytes.decode("utf-8"))
    results = [audit_host("linux", args.linux_zip, freeze), audit_host("darwin", args.darwin_zip, freeze)]
    now = datetime.now(timezone.utc).isoformat()
    audit = {"schema_version": 1, "status": "technical-route-evidence-audited-not-admitted",
             "project": "pick", "run_id": RUN_ID, "head_sha": HEAD_SHA, "hosts": results,
             "human_participants": 0, "usability": "unmeasured", "admission_credit": 0,
             "audited_at_utc": now}
    manifest = {"schema_version": 1, "run_id": RUN_ID,
                "providers": [{"host": row["host"], **row["provider"]} for row in results],
                "admission_credit": 0, "audited_at_utc": now}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / f"technical-route-audit-run{RUN_ID}-v1.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    (args.output_dir / f"technical-route-provider-manifest-run{RUN_ID}-v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": audit["status"], "run_id": RUN_ID, "hosts": 2,
                      "audited_provider_artifacts": 2, "admission_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
