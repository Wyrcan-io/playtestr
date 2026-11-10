"""Retrieve and independently audit every provider artifact in an mg final series."""
import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

from next20_check import DOC, RAW, ROOT
from next20_mg_final_declare import tree_sha256
from next20_mg_final_series import BATCHES, CASES
from next20_mg_scenario import apply_final_variation
from readiness_evidence import immutable_json, sha256


REPO = "Wyrcan-io/playtestr"
BUILD_RUN = 42815619413
SERIES = "mg-final-series-v2"


def github_env():
    env = dict(os.environ)
    lines = subprocess.run(["git", "credential", "fill"], input="protocol=https\nhost=github.com\n\n",
                           text=True, capture_output=True, timeout=15, check=False).stdout.splitlines()
    password = next((line.partition("=")[2] for line in lines if line.startswith("password=")), None)
    if not password:
        raise RuntimeError("GitHub credential helper returned no token")
    env["GH_TOKEN"] = password
    return env


def gh_bytes(args, env):
    result = subprocess.run(["gh", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, timeout=90, check=False)
    if result.returncode:
        raise RuntimeError(f"gh {' '.join(args[:4])} failed: {result.stderr[-2000:].decode(errors='replace')}")
    return result.stdout


def gh_json(args, env):
    return json.loads(gh_bytes(args, env).decode("utf-8"))


def artifact_index(run_id, env):
    result = gh_json(["api", f"repos/{REPO}/actions/runs/{run_id}/artifacts?per_page=100"], env)
    if result.get("total_count") != len(result.get("artifacts", [])):
        raise ValueError(f"artifact list for run {run_id} was incomplete")
    return result["artifacts"]


def retrieve_artifact(row, destination, env):
    if row.get("expired") or not row.get("digest", "").startswith("sha256:"):
        raise ValueError(f"provider artifact expired or has no digest: {row.get('name')}")
    blob = gh_bytes(["api", f"repos/{REPO}/actions/artifacts/{row['id']}/zip"], env)
    actual_digest = hashlib.sha256(blob).hexdigest()
    expected_digest = row["digest"].removeprefix("sha256:")
    if len(blob) != row["size_in_bytes"] or actual_digest != expected_digest:
        raise ValueError(f"provider digest/size mismatch for {row['name']}")
    archive = zipfile.ZipFile(io.BytesIO(blob))
    bad_member = archive.testzip()
    if bad_member:
        raise ValueError(f"provider ZIP CRC failure in {row['name']}: {bad_member}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if sha256(destination) != actual_digest:
            raise ValueError(f"retrieved artifact path already has different bytes: {destination}")
    else:
        with destination.open("xb") as stream:
            stream.write(blob)
    return archive, {"name": row["name"], "artifact_id": row["id"],
                     "size_bytes": len(blob), "sha256": actual_digest,
                     "provider_digest": row["digest"], "zip_entries": len(archive.namelist()),
                     "crc": "passed", "retrieved_zip": destination.relative_to(ROOT).as_posix()}


def member_index(archive):
    return {name: name for name in archive.namelist() if not name.endswith("/")}


def one_named(index, suffix):
    rows = [name for name in index if name.endswith(suffix)]
    if len(rows) != 1:
        raise ValueError(f"expected one ZIP member ending {suffix}; found {len(rows)}")
    return rows[0]


def json_member(archive, index, suffix):
    name = one_named(index, suffix)
    return name, json.loads(archive.read(name).decode("utf-8"))


def audit_batch(row, archive, declaration, declaration_sha, build_receipts, freeze):
    name = row["name"]
    parts = name.removeprefix("next20-mg-final-").rsplit("-", 2)
    if len(parts) != 3 or parts[2] != str(AUDIT_RUN):
        raise ValueError(f"unexpected final artifact name: {name}")
    host, batch_text = parts[0], parts[1].removeprefix("b")
    batch = int(batch_text)
    expected_host = next((cell for cell in declaration["native_cells"] if cell["host"] == host), None)
    if expected_host is None or not 0 <= batch < 12:
        raise ValueError(f"undeclared host or batch in {name}")
    index = member_index(archive)
    batch_name, batch_decl = json_member(archive, index, "/batch-declaration.json")
    receipt_name, batch_receipt = json_member(archive, index, "/batch-receipt.json")
    if batch_decl.get("host") != host or batch_decl.get("batch") != batch:
        raise ValueError(f"batch declaration host/index mismatch: {name}")
    if batch_decl.get("qualification_declaration_sha256") != declaration_sha:
        raise ValueError(f"batch declaration is not bound to v2: {name}")
    if batch_decl.get("mg_binary_sha256") != build_receipts[host]["binary_sha256"]:
        raise ValueError(f"batch declaration target build hash mismatch: {name}")
    expected_contract_rows = {(case, contract) for case, contract in CASES}
    observed = {(item.get("canonical_case"), item.get("contract"))
                for item in batch_receipt.get("results", [])}
    if (batch_receipt.get("status") != "passed" or batch_receipt.get("batch") != batch or
            batch_receipt.get("host") != host or batch_receipt.get("variation") != BATCHES[batch] or
            batch_receipt.get("expected_contract_executions") != len(CASES) or
            batch_receipt.get("attempted_contract_executions") != len(CASES) or
            batch_receipt.get("passed_contract_executions") != len(CASES) or
            batch_receipt.get("failed_contract_executions") != 0 or
            batch_receipt.get("failures") or observed != expected_contract_rows):
        raise ValueError(f"batch receipt is incomplete or failed: {name}")
    if len(batch_receipt.get("results", [])) != len(CASES):
        raise ValueError(f"wrong contract-attempt count: {name}")
    attempt_members = [item for item in index if item.endswith("/attempt.json") and
                       f"/final-qualification/{host}/{batch}/" in item]
    if len(attempt_members) != len(CASES):
        raise ValueError(f"expected {len(CASES)} attempt records in {name}; got {len(attempt_members)}")
    freeze_cell = next(cell for cell in freeze["cells"] if cell["host"] == host)
    attempts_audited = []
    for attempt_path in attempt_members:
        attempt_dir = str(PurePosixPath(attempt_path).parent)
        attempt = json.loads(archive.read(attempt_path).decode("utf-8"))
        receipt_path = attempt_dir + "/scenario-receipt.json"
        finished_path = attempt_dir + "/finished.json"
        report_path = attempt_dir + "/report.json"
        log_path = attempt_dir + "/runner.log"
        variant_path = attempt.get("contract", "")
        variant_basename = PurePosixPath(variant_path).name
        archived_variant = one_named(index, "/" + variant_basename)
        receipt = json.loads(archive.read(receipt_path).decode("utf-8"))
        finished = json.loads(archive.read(finished_path).decode("utf-8"))
        report_bytes = archive.read(report_path)
        report = json.loads(report_bytes.decode("utf-8"))
        log_bytes = archive.read(log_path)
        attempt_id = attempt["attempt_id"]
        if (attempt.get("project") != "mg" or attempt.get("phase") != "final-qualification" or
                attempt.get("batch") != batch or attempt.get("host") != host or
                attempt.get("target_pin") != declaration["source_pin"] or
                attempt.get("target_binary_sha256") != build_receipts[host]["binary_sha256"] or
                attempt.get("candidate") != freeze["version"] or
                attempt.get("candidate_archive_sha256") != freeze_cell["archive_sha256"] or
                attempt.get("candidate_binary_sha256") != freeze_cell["binary_sha256"] or
                attempt.get("contract_sha256") != sha256_bytes(archive.read(archived_variant)) or
                receipt.get("attempt_id") != attempt_id or receipt.get("host") != host or
                receipt.get("scenario_id") != attempt.get("scenario_id") or
                receipt.get("candidate") != freeze["version"] or receipt.get("status") != "scenario-passed" or
                receipt.get("runner_binary_sha256") != freeze_cell["binary_sha256"] or
                receipt.get("candidate_archive_sha256") != freeze_cell["archive_sha256"] or
                receipt.get("target_pin") != declaration["source_pin"] or
                receipt.get("target_binary_sha256") != build_receipts[host]["binary_sha256"] or
                receipt.get("contract_sha256") != attempt.get("contract_sha256") or
                receipt.get("report_sha256") != sha256_bytes(report_bytes) or
                receipt.get("runner_log_sha256") != sha256_bytes(log_bytes) or
                finished.get("attempt_id") != attempt_id or finished.get("failure") is not None or
                finished.get("report_sha256") != sha256_bytes(report_bytes)):
            raise ValueError(f"identity, hash, receipt, or finished-event mismatch: {attempt_path}")
        for event in ("started.json", "identified.json", "launched.json", "finished.json"):
            event_path = attempt_dir + "/" + event
            if event_path not in index:
                raise ValueError(f"missing lifecycle event {event}: {attempt_path}")
            event_data = json.loads(archive.read(event_path).decode("utf-8"))
            if event_data.get("attempt_id") != attempt_id:
                raise ValueError(f"lifecycle event belongs to another attempt: {event_path}")
        rows = report.get("results", [])
        cleanup = rows[0].get("cleanup", {}) if len(rows) == 1 else {}
        if (report.get("runner_version") != freeze["version"] or
                report.get("summary") != {"total": 1, "passed": 1, "failed": 0,
                                           "cancelled": 0, "not_run": 0} or
                len(rows) != 1 or rows[0].get("status") != "passed" or
                any(step.get("status") != "passed" for step in rows[0].get("steps", [])) or
                not cleanup.get("attempted") or not cleanup.get("confirmed_exited")):
            raise ValueError(f"public report lacks positive steps or confirmed target cleanup: {report_path}")
        if (not isinstance(receipt.get("runner_process_group_cleanup"), str) or
                "no owned descendants remain" not in receipt["runner_process_group_cleanup"]):
            raise ValueError(f"runner process tree cleanup is not confirmed: {attempt_path}")
        canonical = next((path for case, path in CASES
                          if attempt["scenario_id"] == Path(path).stem.lower()), None)
        if canonical is None:
            raise ValueError(f"attempt names an undeclared canonical scenario: {attempt_path}")
        original = json.loads((DOC / "mg" / canonical).read_text(encoding="utf-8"))
        varied = apply_final_variation(original, batch)
        expected_variant = (json.dumps(varied, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode("utf-8")
        actual_variant = archive.read(archived_variant)
        if actual_variant != expected_variant:
            raise ValueError(f"executed variation differs from the deterministic batch rule: {archived_variant}")
        if batch in (8, 9):
            worker = next((item.get("worker_cleanup") for item in batch_receipt["results"]
                           if item.get("contract") == canonical), None)
            if not worker or not worker.get("attempted") or not worker.get("confirmed_exited"):
                raise ValueError(f"bounded contention worker cleanup is absent: {attempt_path}")
        attempts_audited.append({"attempt_id": attempt_id, "scenario_id": attempt["scenario_id"],
                                 "report_sha256": sha256_bytes(report_bytes),
                                 "runner_log_sha256": sha256_bytes(log_bytes),
                                 "target_exit_confirmed": True,
                                 "runner_process_tree_confirmed": True,
                                 "executed_contract_sha256": attempt["contract_sha256"]})
    if len(attempts_audited) != len(CASES):
        raise ValueError(f"batch attempt audit count mismatch: {name}")
    return {"artifact": name, "host": host, "batch": batch,
            "variation": BATCHES[batch], "canonical_scenarios": 20,
            "contract_executions": len(attempts_audited),
            "attempts": attempts_audited,
            "batch_receipt_sha256": sha256_bytes(archive.read(receipt_name)),
            "batch_declaration_sha256": sha256_bytes(archive.read(batch_name))}


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def audit_build(row, host, declaration, destination, env):
    archive, provider = retrieve_artifact(row, destination, env)
    index = member_index(archive)
    build_path, build = json_member(archive, index, "active/mg/build.json")
    target_path = one_named(index, "active/mg/install/bin/mg")
    target = archive.read(target_path)
    cell = next(item for item in declaration["native_cells"] if item["host"] == host)
    provider_arch = {"linux": "x86_64", "darwin": "arm64"}[host]
    if (build.get("project") != "mg" or build.get("host") != host or
            build.get("architecture") != provider_arch or
            build.get("pin") != declaration["source_pin"] or
            build.get("binary_sha256") != sha256_bytes(target)):
        raise ValueError(f"native mg build receipt/binary mismatch for {host}")
    provider.update({"build_receipt_member": build_path, "target_binary_sha256": sha256_bytes(target),
                     "source_pin": build["pin"], "host": host,
                     "architecture": build["architecture"]})
    return provider, build


def main():
    global AUDIT_RUN
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=int, required=True)
    args = parser.parse_args()
    AUDIT_RUN = args.run_id
    declaration_path = DOC / "mg/final-qualification-declaration-v2.json"
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    declaration_digest = sha256(declaration_path)
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v1.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    if declaration.get("candidate_freeze_sha256") != sha256(freeze_path):
        raise ValueError("v2 qualification declaration is not bound to the current candidate freeze")
    for case in declaration["scenarios"]:
        contract_path = ROOT / case["contract"]
        fixture_path = DOC / "mg" / case["fixture"]
        if sha256(contract_path) != case["contract_sha256"] or tree_sha256(fixture_path) != case["fixture_tree_sha256"]:
            raise ValueError(f"declared canonical contract/fixture changed: {case['id']} {case['contract']}")
    env = github_env()
    run = gh_json(["run", "view", str(args.run_id), "--json", "headSha,status,conclusion"], env)
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        raise ValueError(f"native workflow run is not complete and successful: {run}")
    api_run = gh_json(["api", f"repos/{REPO}/actions/runs/{args.run_id}"], env)
    if api_run.get("event") != "push" or api_run.get("head_sha") != run["headSha"]:
        raise ValueError("workflow provider event/revision identity mismatch")
    tooling_paths = [
        ".github/workflows/runner-readiness-next20-mg-pilot.yml",
        "scripts/acceptance/next20_mg_final_declare.py",
        "scripts/acceptance/next20_mg_final_redeclare_v2.py",
        "scripts/acceptance/next20_mg_final_series.py",
        "scripts/acceptance/next20_mg_scenario.py",
        "scripts/acceptance/test_next20_mg_final_series.py",
        "scripts/acceptance/test_next20_mg_scenario.py",
    ]
    tooling = {}
    for path in tooling_paths:
        content = subprocess.run(["git", "show", f"{run['headSha']}:{path}"],
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=20, check=False)
        if content.returncode:
            raise ValueError(f"workflow revision lacks qualification tooling file {path}")
        tooling[path] = sha256_bytes(content.stdout)
    artifact_rows = artifact_index(args.run_id, env)
    expected_names = {f"next20-mg-final-{host}-b{batch}-{args.run_id}"
                      for host in ("linux", "darwin") for batch in range(12)}
    selected = {row["name"]: row for row in artifact_rows if row["name"].startswith("next20-mg-final-")}
    if set(selected) != expected_names:
        raise ValueError(f"missing/extra final artifacts: missing={sorted(expected_names-set(selected))}, extra={sorted(set(selected)-expected_names)}")
    root = RAW / f"mg/final-series-retrieved/run-{args.run_id}"
    if root.is_symlink():
        raise ValueError("retrieved artifact root cannot be linked")
    root.mkdir(parents=True, exist_ok=True)
    provider_audits, batch_audits = [], []
    build_rows = {row["name"]: row for row in artifact_index(BUILD_RUN, env)}
    build_receipts = {}
    for host in ("linux", "darwin"):
        build_name = f"next20-mg-build-{host}-{BUILD_RUN}"
        if build_name not in build_rows:
            raise ValueError(f"missing exact successful native source-build artifact: {build_name}")
        provider, build = audit_build(build_rows[build_name], host, declaration,
                                      root / f"{build_name}.zip", env)
        provider_audits.append(provider)
        build_receipts[host] = build
    for name in sorted(expected_names):
        provider_row = selected[name]
        archive, provider = retrieve_artifact(provider_row, root / f"{name}.zip", env)
        provider_audits.append(provider)
        batch_audits.append(audit_batch(provider_row, archive, declaration,
                                        declaration_digest, build_receipts, freeze))
    if len(batch_audits) != 24 or sum(row["contract_executions"] for row in batch_audits) != 504:
        raise ValueError("complete 24-cell/504-contract denominator was not audited")
    by_host = {host: sum(row["contract_executions"] for row in batch_audits if row["host"] == host)
               for host in ("linux", "darwin")}
    report = {
        "schema_version": 1, "series_id": SERIES, "status": "native-matrix-audited",
        "project_admission_credit": 0,
        "run_id": args.run_id, "provider_run_url": api_run["html_url"],
        "provider_head_sha": run["headSha"], "provider_event": api_run["event"],
        "provider_workflow_name": api_run.get("name"),
        "qualification_tooling_git_tree": tooling,
        "declaration": declaration_path.relative_to(ROOT).as_posix(),
        "declaration_sha256": declaration_digest,
        "candidate": freeze["version"], "candidate_freeze_sha256": sha256(freeze_path),
        "source_pin": declaration["source_pin"], "native_cells": 24,
        "canonical_scenarios": 20, "ordinary_executions": 480,
        "additional_e10_branch_executions": 24,
        "contract_executions": 504, "contract_executions_by_host": by_host,
        "failed_contract_executions": 0,
        "hosted_jobs_all_success": True,
        "provider_artifacts": provider_audits,
        "batches": sorted(batch_audits, key=lambda row: (row["host"], row["batch"])),
        "audited_at_utc": datetime.now(timezone.utc).isoformat(),
        "remaining_admission_gates": [
            "authoring route and beginner usability evidence", "diagnosis and maintenance controls",
            "relocation and delivered workflow route", "fault-calibration package independent audit",
            "whole-project package and cleanup/storage/readback audit",
        ],
    }
    destination = DOC / f"mg/final-qualification-artifact-audit-run-{args.run_id}-v1.json"
    immutable_json(destination, report)
    print(json.dumps({"audit": destination.relative_to(ROOT).as_posix(),
                      "status": report["status"], "native_cells": 24,
                      "contract_executions": 504, "failed_contract_executions": 0,
                      "project_admission_credit": 0,
                      "provider_artifacts": len(provider_audits)}, sort_keys=True))


if __name__ == "__main__":
    AUDIT_RUN = 0
    main()
