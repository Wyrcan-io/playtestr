"""Independently audit a retained hosted mg public-route provider artifact."""
import argparse
import base64
import hashlib
import json
from pathlib import PurePosixPath
from pathlib import Path
import zipfile


RUNNER = "e302a46eb090772d91aab7018b51eea0d1fb92247846f4a63375e1009e29309a"
TARGET = "6eb334f5ea96687983c51b073b1b8a11434ea85a46e69ca6e28e57b76b4e88e5"
PIN = "2209e2087eab34ffceb6bfaa0d62f9e4c36e3c66"
MARKER = "MG_PUBLIC_ROUTE_RC6"
INITIAL = b"MG_PUBLIC_ROUTE_START\n"
LABELS = [
    "mg-public-route-runner-version", "mg-first-public-record-review-replay-save",
    "mg-first-public-ordinary-test", "mg-first-public-seeded-screen-diagnosis",
    "mg-intended-change-before-state-update", "mg-selected-file-state-maintenance",
    "mg-maintained-public-ordinary-test", "mg-public-unicode-relocation",
    "mg-public-delivered-workflow-preview",
]
ORACLE_CASES = ["correct-file-bytes", "correct-directory-entries", "same-size-wrong-bytes",
                "missing-required-output", "unexpected-extra-entry", "wrong-type-directory-as-file"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--zip", required=True)
    parser.add_argument("--run-id", required=True, type=int)
    parser.add_argument("--artifact-id", required=True, type=int)
    parser.add_argument("--size", required=True, type=int)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    blob = open(args.zip, "rb").read()
    if len(blob) != args.size or digest(blob) != args.sha256:
        raise ValueError("provider ZIP size or SHA-256 differs from GitHub metadata")
    with zipfile.ZipFile(args.zip) as z:
        if z.testzip() is not None:
            raise ValueError("provider ZIP CRC verification failed")
        members = {PurePosixPath(n).as_posix(): z.read(n) for n in z.namelist()
                   if not n.endswith("/")}

    def obj(path):
        return json.loads(members[path].decode("utf-8"))

    receipt = obj("mg/public-route-native-exit-v1/receipt.json")
    plan = obj("mg/public-route-native-exit-v1/planned.json")
    root = "mg/public-route-native-exit-v1/"
    if (receipt["status"] != "public-agent-route-passed-not-admitted" or
            receipt["project"] != "mg" or receipt["source_pin"] != PIN or
            receipt["candidate"] != "v0.4.0-rc.6" or receipt["runner_sha256"] != RUNNER or
            receipt["target_binary_sha256"] != TARGET or digest(members[root+"planned.json"]) != receipt["planned_sha256"]):
        raise ValueError("route receipt identity or plan binding differs")
    if (plan["initial_shell_invocations_expected"] != 2 or len(plan["first_use_controls"]) != 15 or
            plan["no_handwritten_first_use_spec"] is not True or plan["runner_sha256"] != RUNNER or
            plan["target_binary_sha256"] != TARGET or plan["source_pin"] != PIN):
        raise ValueError("route plan does not bind the declared runner, target, pin, and controls")

    attempts = receipt["attempts"]
    if len(attempts) != len(LABELS) or [a["label"] for a in attempts] != LABELS:
        raise ValueError("route attempt list is incomplete or out of order")
    ids = {a["id"] for a in attempts}
    if len(ids) != len(attempts):
        raise ValueError("route attempt IDs are not unique")
    consoles = []
    identities = set()
    audited_attempts = []
    for attempt in attempts:
        ident, label = attempt["id"], attempt["label"]
        events = {}
        for kind in ("started", "identified", "launched", "finished"):
            event = obj(f"events/{ident}-{kind}.json")
            if (event.get("id") != ident or event.get("event") != kind or
                    event.get("project") != "mg" or event.get("phase") != "public-authoring" or
                    event.get("label") != label):
                raise ValueError(f"attempt lifecycle identity differs: {ident}/{kind}")
            events[kind] = event
        if not isinstance(events["launched"].get("pid"), int) or events["launched"]["pid"] <= 0:
            raise ValueError(f"attempt lacks positive launch evidence: {ident}")
        finished = events["finished"]
        if finished.get("cleanup_errors") or finished.get("harness_cleanup") != "harness_process_reaped":
            raise ValueError(f"attempt harness cleanup is incomplete: {ident}")
        console_path = f"mg/{ident}/console.log"
        console = members[console_path]
        if digest(console) != finished["console_sha256"] or len(console) != finished["output_bytes"]:
            raise ValueError(f"attempt console hash/length differs: {ident}")
        expected_rc = 1 if label in {LABELS[3], LABELS[4]} else 0
        if finished.get("exit_code") != expected_rc or attempt["returncode"] != expected_rc:
            raise ValueError(f"attempt exit differs from its declared outcome: {label}")
        manifest_ref = events["identified"]["identity"]
        path = manifest_ref["manifest"]
        if PurePosixPath(path).is_absolute() or ".." in PurePosixPath(path).parts:
            raise ValueError("unsafe identity manifest path")
        manifest = members[path]
        if digest(manifest) != manifest_ref["sha256"]:
            raise ValueError(f"identity manifest hash differs: {path}")
        identities.add(path)
        consoles.append(console_path)
        audited_attempts.append({"id": ident, "label": label,
                                 "exit_code": finished["exit_code"],
                                 "seconds": attempt["seconds"],
                                 "console_sha256": finished["console_sha256"],
                                 "identity_manifest": path,
                                 "identity_sha256": manifest_ref["sha256"],
                                 "launch_pid": events["launched"]["pid"],
                                 "harness_cleanup": finished["harness_cleanup"]})
    if not identities:
        raise ValueError("identity manifest coverage is empty")

    first = obj(root + "first-use-report.json")
    result = first["results"][0]
    if (first["runner_version"] != "v0.4.0-rc.6" or result["invocation_id"] != receipt["first_invocation"] or
            digest(members[root+"project/create-note.json"]) != receipt["first_spec_sha256"] or
            digest(members[root+"first-use-report.json"]) != receipt["first_report_sha256"] or
            result["status"] != "passed" or any(s["status"] != "passed" for s in result["steps"]) or
            not result["cleanup"]["confirmed_exited"] or not result["workspace"]["cleaned"]):
        raise ValueError("first ordinary candidate report lacks positive evidence and cleanup")
    spec = obj(root + "project/create-note.json")
    expected_bytes = INITIAL + MARKER.encode()
    state = [s["state"] for s in spec["steps"] if "state" in s]
    if (len(state) != 1 or base64.b64decode(state[0]["bytes_base64"], validate=True) != expected_bytes or
            spec["steps"][4].get("expect") != MARKER):
        raise ValueError("recorded public spec lacks the reviewed screen and exact saved bytes")

    diagnosis = obj(root + "diagnosis-report.json")["results"][0]
    if (diagnosis["status"] != "failed" or diagnosis["failure"]["category"] != "assertion_timeout" or
            diagnosis["steps"][4]["status"] != "failed" or not diagnosis["cleanup"]["confirmed_exited"]):
        raise ValueError("seeded diagnosis did not fail at the altered screen expectation with cleanup")
    before = obj(root + "maintenance-before-report.json")["results"][0]
    if before["status"] != "failed" or before["failure"]["category"] != "state_assertion_failure":
        raise ValueError("stale saved-state expectation did not fail for the intended reason")
    for name in ("maintenance-report.json", "relocation-report.json"):
        report = obj(root + name)["results"][0]
        if (report["status"] != "passed" or any(s["status"] != "passed" for s in report["steps"]) or
                not report["cleanup"]["confirmed_exited"] or not report["workspace"]["cleaned"]):
            raise ValueError(f"ordinary repaired route lacks positive evidence or cleanup: {name}")
    relocated = "relocated space caf\u00e9 \u96ea"
    if receipt["relocation"]["path"] != relocated or f"{root}{relocated}/create-note.json" not in members:
        raise ValueError("spaced Unicode relocation path was not retained exactly")
    for name in ("project/fixtures/public-note.txt", "diagnosis/fixtures/public-note.txt",
                 "maintenance/fixtures/public-note.txt", f"{relocated}/fixtures/public-note.txt"):
        if members[root+name] != INITIAL:
            raise ValueError(f"original fixture bytes changed: {name}")
    removed = receipt["target_copy_removal"]
    if len(removed) != 4 or any(not row["absent"] or row["sha256"] != TARGET for row in removed):
        raise ValueError("target-copy cleanup evidence is incomplete")

    expected_window = {"shell_invocations": 3, "controls": 15, "passed": True}
    if receipt.get("repaired_window") != expected_window or receipt.get("human_participants") != 0:
        raise ValueError("repaired route measurement or human-participant accounting differs")
    if receipt.get("initial_window", {}).get("passed") is not False:
        raise ValueError("failed initial route window was omitted or relabelled")
    preview = members[root+"delivered-workflow-preview.yml"].decode("utf-8")
    for required in (receipt["delivered_workflow"]["source_revision"],
                     receipt["delivered_workflow"]["suite"], "pull_request:"):
        if required not in preview:
            raise ValueError("generated free workflow omits source revision, suite, or PR trigger")
    if receipt["delivered_workflow"]["provider_run"] != "not-dispatched":
        raise ValueError("route audit found an unapproved workflow dispatch")

    oracle_root = "mg/oracle-calibration-native-exit-v1/"
    oracle_receipt_path = oracle_root + "receipt.json"
    oracle_summary = None
    if oracle_receipt_path in members:
        oracle = obj(oracle_receipt_path)
        oracle_plan = obj(oracle_root + "planned.json")
        if (oracle.get("status") != "saved-state-oracle-calibration-passed-not-admitted" or
                oracle.get("project") != "mg" or oracle.get("source_pin") != PIN or
                oracle.get("candidate") != "v0.4.0-rc.6" or
                oracle.get("runner_sha256") != RUNNER or oracle.get("target_binary_sha256") != TARGET or
                oracle.get("planned_sha256") != digest(members[oracle_root + "planned.json"]) or
                oracle.get("admission_credit") != 0 or oracle_plan.get("cases") != ORACLE_CASES or
                oracle_plan.get("route_spec_sha256") != receipt["first_spec_sha256"] or
                oracle_plan.get("runner_sha256") != RUNNER or oracle_plan.get("target_binary_sha256") != TARGET):
            raise ValueError("saved-state oracle calibration identity or declared plan differs")
        oracle_attempts = oracle.get("attempts", [])
        if len(oracle_attempts) != len(ORACLE_CASES) or [a.get("name") for a in oracle_attempts] != ORACLE_CASES:
            raise ValueError("saved-state oracle calibration cases are incomplete or out of order")
        expected_bytes_b64 = oracle_plan["independent_expected_bytes"]
        expected_bytes = base64.b64decode(expected_bytes_b64, validate=True)
        if expected_bytes != INITIAL + MARKER.encode():
            raise ValueError("independent saved-state expected bytes changed")
        oracle_events = []
        for name, attempt in zip(ORACLE_CASES, oracle_attempts):
            ident = attempt.get("id", "")
            if ident in ids or len(ident) != 32 or any(c not in "0123456789abcdef" for c in ident):
                raise ValueError("oracle calibration attempt identity is invalid or collides")
            ids.add(ident)
            event_rows = {}
            for kind in ("started", "identified", "launched", "finished"):
                event = obj(f"events/{ident}-{kind}.json")
                if (event.get("id") != ident or event.get("event") != kind or
                        event.get("project") != "mg" or event.get("phase") != "oracle-calibration" or
                        event.get("label") != "mg-state-oracle-" + name):
                    raise ValueError(f"oracle calibration lifecycle identity differs: {ident}/{kind}")
                event_rows[kind] = event
            finished = event_rows["finished"]
            console_path = f"mg/{ident}/console.log"
            console = members[console_path]
            if (finished.get("cleanup_errors") or finished.get("harness_cleanup") != "harness_process_reaped" or
                    digest(console) != finished.get("console_sha256") or len(console) != finished.get("output_bytes")):
                raise ValueError(f"oracle calibration console or process cleanup differs: {name}")
            negative = name not in ORACLE_CASES[:2]
            expected_rc = 1 if negative else 0
            if finished.get("exit_code") != expected_rc or attempt.get("returncode") != expected_rc:
                raise ValueError(f"oracle calibration process exit differs: {name}")
            manifest_ref = event_rows["identified"].get("identity", {})
            manifest_path = manifest_ref.get("manifest", "")
            if (not manifest_path or PurePosixPath(manifest_path).is_absolute() or
                    ".." in PurePosixPath(manifest_path).parts or manifest_path not in members or
                    digest(members[manifest_path]) != manifest_ref.get("sha256")):
                raise ValueError(f"oracle calibration contract identity differs: {name}")
            report_path = oracle_root + f"reports/{name}.json"
            report_bytes = members[report_path]
            if digest(report_bytes) != attempt.get("report_sha256"):
                raise ValueError(f"oracle calibration report digest differs: {name}")
            report = json.loads(report_bytes.decode("utf-8"))
            result = report["results"][0]
            expected_status = "failed" if negative else "passed"
            if (report.get("runner_version") != "v0.4.0-rc.6" or len(report.get("results", [])) != 1 or
                    result.get("invocation_id") != attempt.get("invocation_id") or
                    result.get("status") != expected_status or
                    not result.get("cleanup", {}).get("confirmed_exited") or
                    not result.get("workspace", {}).get("cleaned")):
                raise ValueError(f"oracle calibration report lacks outcome or cleanup evidence: {name}")
            state_steps = [step for step in result.get("steps", []) if step.get("action") == "state"]
            if not state_steps or state_steps[-1].get("status") != ("failed" if negative else "passed"):
                raise ValueError(f"oracle calibration did not reach its final state oracle: {name}")
            if negative and (result.get("failure", {}).get("category") != "state_assertion_failure" or
                             any(step.get("status") != "passed" for step in result["steps"][:-1])):
                raise ValueError(f"negative oracle calibration failed outside the final state oracle: {name}")
            case_spec_path = oracle_root + f"cases/{name}/create-note.json"
            case_spec = obj(case_spec_path)
            file_states = [step["state"] for step in case_spec["steps"] if step.get("state", {}).get("kind") == "file"]
            if name in {ORACLE_CASES[0], ORACLE_CASES[2], ORACLE_CASES[3], ORACLE_CASES[4]}:
                if len(file_states) != 1:
                    raise ValueError(f"oracle calibration file case is malformed: {name}")
                state = file_states[0]
                if name == ORACLE_CASES[0] and (state.get("path") != "public-note.txt" or state.get("bytes_base64") != expected_bytes_b64):
                    raise ValueError("positive saved-file oracle does not match independent bytes")
                if name == ORACLE_CASES[2]:
                    wrong = base64.b64decode(state["bytes_base64"], validate=True)
                    if (state.get("path") != "public-note.txt" or len(wrong) != len(expected_bytes) or
                            wrong == expected_bytes or wrong[1:] != expected_bytes[1:]):
                        raise ValueError("same-size wrong-byte case does not isolate the first byte")
                if name == ORACLE_CASES[3] and state.get("path") != "missing-public-note.txt":
                    raise ValueError("missing-output case does not assert a missing path")
            if name == ORACLE_CASES[1] and not any(s.get("state", {}).get("kind") == "entries" and
                                                       s["state"].get("path") == "." and
                                                       s["state"].get("entries") == ["public-note.txt"]
                                                       for s in case_spec["steps"]):
                raise ValueError("positive directory-entry oracle differs")
            if name == ORACLE_CASES[4] and oracle_root + f"cases/{name}/fixtures/unexpected-extra.txt" not in members:
                raise ValueError("unexpected directory entry fixture was not retained")
            if name == ORACLE_CASES[5]:
                if (len(file_states) != 2 or not any(s.get("state", {}).get("path") == "directory-marker" and
                                                    s["state"].get("kind") == "file" for s in case_spec["steps"]) or
                        oracle_root + f"cases/{name}/fixtures/directory-marker/inside.txt" not in members):
                    raise ValueError("wrong-type directory case lacks its retained directory fixture")
            oracle_events.append({"id": ident, "case": name, "exit_code": expected_rc,
                                  "report_sha256": digest(report_bytes),
                                  "console_sha256": finished["console_sha256"],
                                  "identity_manifest": manifest_path})
        if (oracle.get("positive_correct_bytes") is not True or
                oracle.get("positive_correct_entries") is not True or
                oracle.get("same_size_wrong_bytes_rejected") is not True or
                oracle.get("missing_required_output_rejected") is not True or
                oracle.get("unexpected_extra_entry_rejected") is not True or
                oracle.get("wrong_type_rejected") is not True or
                oracle.get("all_negative_cases_failed_at_final_state_checkpoint") is not True or
                oracle.get("target_copy_removed") is not True):
            raise ValueError("saved-state oracle calibration receipt omits a required outcome or cleanup")
        oracle_summary = {"status": oracle["status"], "attempt_count": len(oracle_events),
                          "cases": oracle_events, "project_admission_credit": 0}
    report = {
        "schema_version": 1,
        "status": "public-route-evidence-audited-not-admitted",
        "project_admission_credit": 0,
        "provider": {"run_id": args.run_id, "artifact_id": args.artifact_id,
                     "size_bytes": len(blob), "sha256": args.sha256,
                     "crc": "passed", "zip_entries": len(members)},
        "candidate": "v0.4.0-rc.6", "runner_sha256": RUNNER,
        "source_pin": PIN, "target_binary_sha256": TARGET,
        "planned_sha256": digest(members[root+"planned.json"]),
        "receipt_sha256": digest(members[root+"receipt.json"]),
        "attempts": audited_attempts,
        "attempt_count": len(attempts), "console_count": len(consoles),
        "identity_manifest_count": len(identities),
        "first_window": {"run_id": 42830712855, "shell_invocations": 2,
                         "controls": 15, "passed": False,
                         "failure": "candidate did not find mg before executable-bit repair"},
        "repaired_window": {"shell_invocations": 3, "controls": 15, "passed": True},
        "recorded_first_spec_and_reviewed_state": True,
        "seeded_screen_diagnosis": "assertion_timeout at deliberately altered step 5; target cleanup confirmed",
        "selected_saved_state_maintenance": "stale state failed; selected update passed; exact bytes checked by harness",
        "unicode_relocation": "relocated space café 雪; ordinary run passed",
        "delivered_workflow": {"source_revision": receipt["delivered_workflow"]["source_revision"],
                              "suite": receipt["delivered_workflow"]["suite"],
                              "provider_run": "not-dispatched"},
        "target_copy_cleanup_count": len(removed),
        "human_participants": 0, "human_time": "unmeasured",
        "saved_state_oracle_calibration": oracle_summary,
        "limits": ["Agent operation only; no beginner-usability claim.",
                   "Route evidence is not project admission; campaign and storage gates remain."],
    }
    output = args.output or Path(__file__).resolve().parents[2] / "docs" / "validation" / \
        "runner-readiness-next-twenty-project-pass" / "mg" / \
        f"public-route-audit-run-{args.run_id}-v1.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, sort_keys=True, ensure_ascii=True, indent=2) + "\n",
                      encoding="utf-8", newline="\n")
    print(json.dumps({"audit": str(output), "status": report["status"],
                      "run_id": args.run_id, "attempts": len(attempts),
                      "identity_manifests": len(identities), "project_admission_credit": 0},
                     sort_keys=True))


if __name__ == "__main__":
    main()
