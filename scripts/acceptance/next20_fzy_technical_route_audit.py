"""Independently reconstruct fzy technical-route evidence from provider ZIPs."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC

PIN = "34b88869d022e861da4846c4463aea3ddfb3ff30"
SOURCE_SHA = "d55d4d0dcbced2daa0dd16b42ee0fc31654bd038ff6a147b38580c233d62c967"
PROJECT = DOC / "fzy"
FREEZE = DOC / "replacement-candidate-freeze-native-exit-v3.json"
DECLARATION = PROJECT / "public-route-declaration-v1.json"
PUBLIC_RECEIPT = PROJECT / "public-route-run43364417379-v1.json"
LABELS = [
    "fzy-technical-route-runner-version", "fzy-technical-suite-selection",
    "fzy-technical-manual-edit-selected-test", "fzy-technical-machine-to-html-report",
    "fzy-technical-version-2-before-migration", "fzy-technical-version-3-after-migration",
    "fzy-technical-suffix-rerecord", "fzy-technical-suffix-rerecord-ordinary-test",
]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def need(value, message):
    if not value:
        raise ValueError(message)


def read_provider(path, expected_bytes, expected_sha):
    path = Path(path)
    blob = path.read_bytes()
    need(len(blob) == expected_bytes and digest(blob) == expected_sha,
         f"{path}: provider byte count/digest differs")
    with zipfile.ZipFile(path) as archive:
        need(archive.testzip() is None, f"{path}: ZIP CRC failure")
        names = archive.namelist()
        for name in names:
            member = PurePosixPath(name)
            need(not member.is_absolute() and ".." not in member.parts,
                 f"{path}: unsafe ZIP member {name}")
        members = {name: archive.read(name) for name in names if not name.endswith("/")}
    return members, {"artifact_bytes": len(blob), "artifact_sha256": digest(blob)}


def audit_host(host, zip_path, provider):
    members, observed = read_provider(zip_path, provider["bytes"], provider["sha256"])

    def raw(name):
        try:
            return members[name]
        except KeyError as error:
            raise ValueError(f"{host}: missing provider member {name}") from error

    def obj(name):
        return json.loads(raw(name).decode("utf-8"))

    root = f"fzy/technical-route-v1/{host}/"
    receipt_raw = raw(root + "receipt.json")
    receipt = json.loads(receipt_raw.decode("utf-8"))
    public_raw = PUBLIC_RECEIPT.read_bytes()
    public_doc = json.loads(public_raw.decode("utf-8"))
    freeze_raw = FREEZE.read_bytes()
    freeze = json.loads(freeze_raw.decode("utf-8"))
    cell = next(row for row in freeze["cells"] if row["host"] == host)
    build = obj("fzy/retained-source/build.json")
    runtime = obj("fzy/retained-source/runtime.json")
    installed = obj(f"candidate-native-exit-v3/{host}/installed.json")
    need(receipt.get("status") == "technical-route-passed-not-admitted"
         and receipt.get("project") == "fzy" and receipt.get("host") == host
         and receipt.get("source_pin") == PIN and receipt.get("candidate") == freeze["version"] == "v0.4.0-rc.8"
         and receipt.get("candidate_series") == freeze["series"] == "native-exit-v3"
         and receipt.get("candidate_binary_sha256") == cell["binary_sha256"]
         and receipt.get("target_binary_sha256") == build.get("binary_sha256")
         and build.get("project") == "fzy" and build.get("pin") == PIN and build.get("host") == host
         and build.get("source_archive_sha256") == SOURCE_SHA and build.get("upstream_tests") == "passed"
         and runtime.get("native_sha256") == build.get("binary_sha256")
         and installed.get("archive_sha256") == cell["archive_sha256"]
         and installed.get("binary_sha256") == cell["binary_sha256"]
         and receipt.get("public_route_receipt_sha256") == digest(public_raw)
         and public_doc.get("project") == "fzy" and public_doc.get("run_id") == 43364417379
         and public_doc.get("status") == "passed-and-independently-audited"
         and public_doc.get("independent_audit_sha256") == "503ca2151d5626749ec5dc1df20c11c754e2bbb8f60f58433b2c1f044482d218"
         and receipt.get("route_declaration_sha256") == digest(DECLARATION.read_bytes())
         and receipt.get("admission_credit") == 0,
         f"{host}: source/candidate/public route identity or zero-credit boundary differs")

    attempts = receipt.get("attempts", [])
    need([row.get("label") for row in attempts] == LABELS
         and len({row.get("id") for row in attempts}) == len(LABELS)
         and all(row.get("returncode") == 0 for row in attempts),
         f"{host}: technical attempt ledger incomplete or nonpassing")
    for row in attempts:
        identifier, label = row["id"], row["label"]
        events = {kind: obj(f"events/{identifier}-{kind}.json")
                  for kind in ("started", "identified", "launched", "finished")}
        for kind, event in events.items():
            need(event.get("id") == identifier and event.get("event") == kind
                 and event.get("project") == "fzy" and event.get("phase") == "technical-authoring"
                 and event.get("label") == label,
                 f"{host}: event chain differs for {label}/{kind}")
        need(isinstance(events["launched"].get("pid"), int) and events["launched"]["pid"] > 0,
             f"{host}: no positive process launch for {label}")
        console = raw(f"fzy/{identifier}/console.log")
        finished = events["finished"]
        need(finished.get("exit_code") == 0 and not finished.get("cleanup_errors")
             and finished.get("harness_cleanup") == "harness_process_reaped"
             and finished.get("console_sha256") == digest(console)
             and finished.get("output_bytes") == len(console),
             f"{host}: finish event or console evidence differs for {label}")
    selection = next(row for row in attempts if row["label"] == LABELS[1])
    selection_log = raw(f"fzy/{selection['id']}/console.log")
    need(b"Selected 2 specs:" in selection_log and b"chosen.json" in selection_log
         and b"separate.json" in selection_log,
         f"{host}: suite selection did not enumerate two exact specs")

    fixture = b"apple\nbanana\n"
    manual = json.loads(raw(root + "manual selection/fzy-manual-v3.json").decode("utf-8"))
    need(manual.get("version") == 3 and manual.get("env", {}).get("PLAYTESTR_FZY_TECHNICAL_ROUTE") == "explicit-rc8"
         and raw(root + "manual selection/fixtures/choices.txt") == fixture
         and manual.get("steps", [])[-1] == {"state": {"path": "choices.txt", "kind": "file",
               "bytes_base64": "YXBwbGUKYmFuYW5hCg=="}}
         and digest(raw(root + "manual selection/fzy-manual-v3.json")) == receipt.get("manual_spec_sha256"),
         f"{host}: manual spec or exact fixture input-state differs")

    def report(path, version, hash_field):
        data = raw(root + path)
        value = json.loads(data.decode("utf-8"))
        need(value.get("report_version") == version and len(value.get("results", [])) == 1,
             f"{host}: report version/denominator differs: {path}")
        result = value["results"][0]
        need(result.get("status") == "passed" and result.get("cleanup", {}).get("confirmed_exited") is True
             and result.get("workspace", {}).get("cleaned") is True
             and all(step.get("status") == "passed" for step in result.get("steps", [])),
             f"{host}: nonpassing result or incomplete cleanup: {path}")
        need(digest(data) == receipt.get(hash_field), f"{host}: report hash differs from receipt: {path}")
        return value, result, digest(data)

    manual_report, manual_result, manual_hash = report("reports/manual-v3.json", 3, "manual_report_sha256")
    html = raw(root + "reports/manual-v3.html")
    need(digest(html) == receipt.get("html_sha256") and b"<!doctype html>" in html
         and b'class="status status-passed">passed</span>' in html,
         f"{host}: HTML report not bound to the passing machine report")
    v2, v2_result, v2_hash = report("reports/version-2.json", 2, "v2_report_sha256")
    legacy = raw(root + "reports/version-2-before-migration.json")
    legacy_obj = json.loads(legacy.decode("utf-8"))
    need(legacy_obj.get("version") == 2 and all("state" not in step for step in legacy_obj["steps"])
         and digest(legacy) == receipt.get("legacy_spec_sha256"),
         f"{host}: original v2 spec changed or includes v3 state operations")
    migrated = raw(root + "migration/fzy-migration.json")
    migrated_obj = json.loads(migrated.decode("utf-8"))
    need(migrated_obj == manual and migrated_obj.get("version") == 3
         and digest(migrated) == receipt.get("migrated_spec_sha256"),
         f"{host}: migrated v3 spec is not the reviewed manual v3 contract")
    _, migrated_result, migrated_hash = report("reports/version-3-after-migration.json", 3,
                                                  "migrated_report_sha256")
    suffix = raw(root + "suffix-rerecord/fzy-suffix.json")
    suffix_obj = json.loads(suffix.decode("utf-8"))
    need(suffix_obj["steps"][:1] == manual["steps"][:1]
         and suffix_obj["steps"][1:] == [{"text": "apple"}, {"key": "Enter"}, {"exit": 0},
              {"state": {"path": "result.txt", "kind": "file", "bytes_base64": "YXBwbGUK"}}]
         and digest(suffix) == receipt.get("suffix_spec_sha256"),
         f"{host}: suffix rerecord changed prefix or expected output bytes")
    _, suffix_result, suffix_hash = report("reports/suffix-rerecord.json", 3, "suffix_report_sha256")

    inventory_bytes = raw("fzy/retained-source/cleanup-inventory.json")
    inventory = json.loads(inventory_bytes.decode("utf-8"))
    removed = obj("fzy/retained-source/removed.json")
    proof_bytes = raw("fzy/process-proof.json")
    proof = json.loads(proof_bytes.decode("utf-8"))
    need(inventory.get("source_restored_exact") is True
         and inventory.get("process_proof_sha256") == digest(proof_bytes)
         and removed.get("removed") is True and removed.get("source_restored_exact") is True
         and removed.get("cleanup_inventory_sha256") == digest(inventory_bytes)
         and proof.get("confirmed_no_matching_live_processes") is True,
         f"{host}: target/source/process cleanup proof differs")
    return {"host": host, "provider": {**provider, **observed}, "candidate_archive_sha256": cell["archive_sha256"],
            "candidate_binary_sha256": cell["binary_sha256"], "target_binary_sha256": build["binary_sha256"],
            "technical_attempts": attempts, "suite_selection": "passed-two-specs",
            "manual_report_sha256": manual_hash, "manual_invocation_id": manual_result.get("invocation_id"),
            "html_sha256": digest(html), "v2_report_sha256": v2_hash,
            "migrated_report_sha256": migrated_hash, "migrated_invocation_id": migrated_result.get("invocation_id"),
            "suffix_report_sha256": suffix_hash, "suffix_invocation_id": suffix_result.get("invocation_id"),
            "source_restored_exact": True, "target_removed": True, "no_matching_processes": True,
            "v2_invocation_id": v2_result.get("invocation_id"), "admission_credit": 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--run-attempt", type=int, required=True)
    parser.add_argument("--head-sha", required=True)
    for host in ("linux", "darwin"):
        parser.add_argument(f"--{host}-zip", type=Path, required=True)
        parser.add_argument(f"--{host}-artifact-id", type=int, required=True)
        parser.add_argument(f"--{host}-bytes", type=int, required=True)
        parser.add_argument(f"--{host}-sha256", required=True)
    args = parser.parse_args()
    freeze_raw = FREEZE.read_bytes()
    freeze = json.loads(freeze_raw.decode("utf-8"))
    declaration = json.loads(DECLARATION.read_text(encoding="utf-8"))
    need(digest(freeze_raw) == declaration.get("candidate_freeze_sha256"), "candidate freeze changed")
    results = []
    for host in ("linux", "darwin"):
        provider = {"artifact_id": getattr(args, f"{host}_artifact_id"),
                    "bytes": getattr(args, f"{host}_bytes"), "sha256": getattr(args, f"{host}_sha256")}
        results.append(audit_host(host, getattr(args, f"{host}_zip"), provider))
    destination = PROJECT / f"technical-route-audit-run{args.run_id}-v1.json"
    audit = {"schema_version": 1, "status": "technical-route-evidence-audited-not-admitted",
             "project": "fzy", "run_id": args.run_id, "run_attempt": args.run_attempt,
             "head_sha": args.head_sha, "freeze_sha256": digest(freeze_raw), "hosts": results,
             "human_participants": 0, "usability": "unmeasured", "admission_credit": 0}
    destination.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    manifest = {"schema_version": 1, "run_id": args.run_id,
                "providers": [{"host": row["host"], **row["provider"]} for row in results],
                "admission_credit": 0}
    (PROJECT / f"technical-route-provider-manifest-run{args.run_id}-v1.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"status": audit["status"], "run_id": args.run_id,
                      "hosts": 2, "admission_credit": 0}, sort_keys=True))


if __name__ == "__main__":
    main()
