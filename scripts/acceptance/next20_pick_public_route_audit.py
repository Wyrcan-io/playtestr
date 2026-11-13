"""Independently audit exact GitHub ZIPs for Pick's native public route."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC, ROOT

RUN_ID = 43347165865
HEAD_SHA = "0e03cce32b1281b574f00d7d429b1866d5293801"
PIN = "caae95938359b2e814b3e7406f396f486c9d99fb"
SOURCE_SHA256 = "e308cf7fca8eb50bc3d90e31347377f0cf955e07eb77793343743deaee72c653"
DECLARATION = DOC / "pick/public-route-declaration-v1.json"
FREEZE = DOC / "replacement-candidate-freeze-native-exit-v3.json"
OUTPUT = DOC / "pick"
PROVIDERS = {
    "linux": {"artifact_id": 14002421456, "name": "next20-pick-public-route-linux-43347165865",
              "bytes": 694425, "sha256": "3f324f6c1826275d6b0fadeef588e2ea1a1722ebf56cf180fbedc6ef96cbb742"},
    "darwin": {"artifact_id": 14002521603, "name": "next20-pick-public-route-darwin-43347165865",
               "bytes": 694551, "sha256": "90cb2ba40067f64e048f8cab7918da61e0ee6f84fb5f3d63fc4f8bc0be1d05b7"},
}
LABELS = [
    "pick-public-route-runner-version", "pick-first-use-record-review-replay-save",
    "pick-first-use-ordinary-test", "pick-seeded-rendered-screen-diagnosis",
    "pick-maintenance-original-contract", "pick-selective-query-and-oracle-maintenance",
    "pick-maintained-ordinary-test", "pick-unicode-space-relocation", "pick-public-workflow-preview",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def audit_host(host, zip_path, freeze, declaration):
    provider = PROVIDERS[host]
    blob = Path(zip_path).read_bytes()
    need(len(blob) == provider["bytes"] and digest(blob) == provider["sha256"],
         f"{host}: provider ZIP size/digest differs from GitHub metadata")
    with zipfile.ZipFile(zip_path) as archive:
        need(archive.testzip() is None, f"{host}: provider ZIP CRC check failed")
        names = archive.namelist()
        for name in names:
            path = PurePosixPath(name)
            need(not path.is_absolute() and ".." not in path.parts,
                 f"{host}: unsafe ZIP member path")
        members = {name: archive.read(name) for name in names if not name.endswith("/")}

    def raw(path):
        try:
            return members[path]
        except KeyError as error:
            raise ValueError(f"{host}: missing provider member {path}") from error

    def obj(path):
        return json.loads(raw(path).decode("utf-8"))

    base = f"pick/public-route-v1/{host}/"
    receipt_bytes = raw(base + "receipt.json")
    receipt = json.loads(receipt_bytes.decode("utf-8"))
    candidate = next(row for row in freeze["cells"] if row["host"] == host)
    need(receipt.get("schema_version") == 1 and receipt.get("project") == "pick"
         and receipt.get("host") == host and receipt.get("source_pin") == PIN
         and receipt.get("source_archive_sha256") == SOURCE_SHA256
         and receipt.get("candidate") == freeze["version"] == "v0.4.0-rc.8"
         and receipt.get("candidate_series") == freeze["series"] == "native-exit-v3"
         and receipt.get("candidate_archive_sha256") == candidate["archive_sha256"]
         and receipt.get("candidate_binary_sha256") == candidate["binary_sha256"]
         and receipt.get("route_declaration_sha256") == digest(DECLARATION.read_bytes())
         and receipt.get("admission_credit") == 0,
         f"{host}: route/candidate/credit identity differs")
    need(receipt.get("record_controls") == declaration["record_controls"]
         and receipt.get("maintenance_controls") == declaration["maintenance_controls"],
         f"{host}: controls differ from frozen declaration")
    attempts = receipt.get("attempts", [])
    need([row.get("label") for row in attempts] == LABELS and len({row.get("id") for row in attempts}) == 9,
         f"{host}: command attempt ledger incomplete or duplicated")
    need(all(row.get("returncode") == (1 if row.get("label") == "pick-seeded-rendered-screen-diagnosis" else 0)
             for row in attempts), f"{host}: command exit differs from declared success/diagnosis outcome")

    installed = obj(f"candidate-native-exit-v3/{host}/installed.json")
    need(installed.get("archive_sha256") == candidate["archive_sha256"]
         and installed.get("binary_sha256") == candidate["binary_sha256"]
         and receipt.get("runner_sha256") == candidate["binary_sha256"]
         and installed.get("version") == "v0.4.0-rc.8"
         and installed.get("series") == "native-exit-v3",
         f"{host}: installed runner differs from frozen candidate")
    source_root = "pick/retained-source/"
    build = obj(source_root + "build.json")
    runtime = obj(source_root + "runtime.json")
    need(build.get("project") == "pick" and build.get("pin") == PIN and build.get("host") == host
         and build.get("source_archive_sha256") == SOURCE_SHA256 and build.get("upstream_tests") == "passed"
         and build.get("source_mutation") is None and runtime.get("native_sha256") == build.get("binary_sha256")
         and receipt.get("target_binary_sha256") == build.get("binary_sha256"),
         f"{host}: target build/runtime identity or upstream tests differ")
    inventory = obj(source_root + "cleanup-inventory.json")
    removed = obj(source_root + "removed.json")
    process = raw("pick/process-proof.json")
    need(inventory.get("source_restored_exact") is True
         and inventory.get("actual_reports_with_confirmed_cleanup") == 5
         and inventory.get("project") == "pick"
         and inventory.get("process_proof_sha256") == digest(process)
         and removed.get("removed") is True and removed.get("source_restored_exact") is True
         and removed.get("cleanup_inventory_sha256") == digest(raw(source_root + "cleanup-inventory.json")),
         f"{host}: source restoration, process proof, or exact cleanup receipt differs")
    need(obj("pick/process-proof.json").get("confirmed_no_matching_live_processes") is True,
         f"{host}: owned target process remains live")
    for relative, identity in inventory.get("retained", {}).items():
        content = raw(source_root + relative)
        need(digest(content) == identity,
             f"{host}: retained source/build inventory mismatch: {relative}")

    project_spec_path = base + "project/pick-blue.json"
    spec_bytes = raw(project_spec_path)
    spec = json.loads(spec_bytes.decode("utf-8"))
    need(digest(spec_bytes) == receipt["first_use"]["spec_sha256"]
         and spec.get("version") == 3 and spec.get("command") == ["/bin/sh", "-c", "exec pick -d < choices.txt"]
         and spec.get("env", {}).get("IFS") == ":"
         and spec.get("workspace", {}).get("fixture") == "fixtures"
         and spec.get("steps") == [
             {"expect": "item00"}, {"snapshot": "initial-menu.txt"}, {"text": "tail"},
             {"expect": "Tail unique description"}, {"key": "Enter"}, {"exit": 0}],
         f"{host}: recorder export differs from the reviewed public route")
    fixture = b"".join(f"item{i:02d}:Item description {i:02d}\n".encode("ascii") for i in range(29))
    fixture += b"tail-choice:Tail unique description\n"
    need(raw(base + "project/fixtures/choices.txt") == fixture,
         f"{host}: original fixture bytes differ")
    need(raw(base + "project/snapshots/initial-menu.txt").decode("utf-8").find("item00") >= 0,
         f"{host}: first-use snapshot lacks positive initial state")

    def report(name, expected):
        content = raw(base + name)
        parsed = json.loads(content.decode("utf-8"))
        if expected.get("receipt_hash"):
            declared_hash = receipt
            for field in expected["receipt_hash"].split("."):
                declared_hash = declared_hash[field]
            need(digest(content) == declared_hash, f"{host}: {name} hash differs from route receipt")
        rows = parsed.get("results", [])
        need(parsed.get("report_version") == 3 and len(rows) == 1,
             f"{host}: {name} report schema/denominator differs")
        result = rows[0]
        need(result.get("status") == expected["status"]
             and result.get("cleanup", {}).get("confirmed_exited") is True
             and result.get("workspace", {}).get("cleaned") is True,
             f"{host}: {name} outcome or cleanup differs")
        if expected["status"] == "passed":
            need(all(step.get("status") == "passed" for step in result.get("steps", [])),
                 f"{host}: {name} contains non-passing step")
        else:
            need(result.get("failure", {}).get("category") == "assertion_timeout"
                 and any(step.get("status") == "failed" for step in result.get("steps", [])),
                 f"{host}: seeded diagnosis failure category differs")
        return content, parsed, result

    first_bytes, first_doc, first_result = report("first-use-report.json", {
        "status": "passed", "receipt_hash": "first_use.report_sha256"})
    need(first_result.get("invocation_id") == receipt["first_use"]["invocation_id"]
         and receipt["first_use"].get("handwritten_spec") is False,
         f"{host}: public first-use invocation or authorship differs")
    diagnosis_bytes, diagnosis_doc, diagnosis_result = report("diagnosis-report.json", {
        "status": "failed", "receipt_hash": "diagnosis.report_sha256"})
    broken = json.loads(raw(base + "diagnosis/pick-blue.json").decode("utf-8"))
    need(any(step.get("expect") == "IMPOSSIBLE_PICK_SCREEN_MARKER" for step in broken.get("steps", [])),
         f"{host}: seeded diagnosis mutation differs")
    before_bytes, before_doc, _ = report("maintenance-before-report.json", {
        "status": "passed"})
    maintenance_bytes, _, _ = report("maintenance-report.json", {
        "status": "passed", "receipt_hash": "maintenance.report_sha256"})
    maintained = json.loads(raw(base + "maintenance/pick-blue.json").decode("utf-8"))
    before = json.loads(spec_bytes.decode("utf-8"))
    expected = json.loads(json.dumps(before))
    expected["steps"][2]["text"] = "tail-choice"
    need(maintained == expected and receipt["maintenance"].get("selected_steps_only") is True,
         f"{host}: selective maintenance modified unrelated steps")
    relocation_bytes, _, _ = report("relocation-report.json", {
        "status": "passed", "receipt_hash": "relocation.report_sha256"})
    relocated = next(name for name in members if name.startswith(base + "relocated space ")
                     and name.endswith("/pick-blue.json"))
    need(digest(raw(relocated)) == digest(raw(base + "maintenance/pick-blue.json"))
         and receipt["relocation"].get("status") == "passed",
         f"{host}: relocated spec differs from maintained project")

    preview = raw(base + "delivered-workflow-preview.yml")
    preview_info = receipt["delivered_workflow_preview"]
    preview_text = preview.decode("utf-8")
    setup = "git clone --no-checkout https://github.com/mptre/pick.git pick-source && git -C pick-source checkout --detach " + PIN
    build_command = 'cd pick-source && ./configure --prefix="$HOME/.local" && make -j2 && make test && make install'
    need(digest(preview) == preview_info.get("sha256") and preview_info.get("revision") == HEAD_SHA
         and preview_info.get("provider_run") is None
         and preview_info.get("suite") == "artifacts/runner-readiness-next-twenty-project-pass/" + base + "project/pick-blue.json"
         and all(value in preview_text for value in (HEAD_SHA, PIN, "pull_request:", setup, build_command)),
         f"{host}: delivered workflow preview content/boundary differs")

    return {
        "host": host, "provider": {**provider, "observed_bytes": len(blob), "observed_sha256": digest(blob)},
        "candidate_archive_sha256": candidate["archive_sha256"],
        "candidate_binary_sha256": candidate["binary_sha256"],
        "target_binary_sha256": build["binary_sha256"],
        "recorded_spec_sha256": digest(spec_bytes), "first_use_report_sha256": digest(first_bytes),
        "diagnosis_report_sha256": digest(diagnosis_bytes), "maintenance_before_report_sha256": digest(before_bytes),
        "maintenance_report_sha256": digest(maintenance_bytes), "relocation_report_sha256": digest(relocation_bytes),
        "first_use": "passed", "seeded_diagnosis": "assertion_timeout with cleanup", "maintenance": "passed",
        "relocation": "passed", "delivered_workflow_preview": "reviewed-not-dispatched",
        "source_restored_exact": True, "target_removed": True, "no_matching_processes": True,
        "admission_credit": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--linux-zip", required=True, type=Path)
    parser.add_argument("--darwin-zip", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    args = parser.parse_args()
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    freeze_bytes = FREEZE.read_bytes()
    need(digest(freeze_bytes) == declaration.get("candidate_freeze_sha256"),
         "candidate freeze digest differs from Pick route declaration")
    freeze = json.loads(freeze_bytes.decode("utf-8"))
    results = [audit_host("linux", args.linux_zip, freeze, declaration),
               audit_host("darwin", args.darwin_zip, freeze, declaration)]
    now = datetime.now(timezone.utc).isoformat()
    summary = {"schema_version": 1, "status": "public-route-evidence-audited-not-admitted",
               "project": "pick", "run_id": RUN_ID, "head_sha": HEAD_SHA, "hosts": results,
               "human_participants": 0, "usability": "unmeasured", "admission_credit": 0,
               "audited_at_utc": now}
    manifest = {"schema_version": 1, "run_id": RUN_ID, "providers": [
        {"host": row["host"], **row["provider"]} for row in results], "admission_credit": 0,
        "audited_at_utc": now}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    audit_path = args.output_dir / f"public-route-audit-run{RUN_ID}-v1.json"
    manifest_path = args.output_dir / f"public-route-provider-manifest-run{RUN_ID}-v1.json"
    audit_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": summary["status"], "run_id": RUN_ID, "hosts": 2,
                      "audited_provider_artifacts": 2, "admission_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
