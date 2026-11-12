"""Independently audit retained JOE rc.7 oracle-calibration host artifacts."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256

PIN = "3874898078005d1f5e519235401fab4fd428dd9b"
CANDIDATE = "v0.4.0-rc.7"
SERIES = "native-exit-v2"
CASES = {
    "correct-all-kinds-and-byte-families": "passed",
    "same-size-wrong-file-bytes": "failed",
    "missing-required-file": "failed",
    "wrong-type-directory-as-file": "failed",
    "absence-rejects-present-file": "failed",
    "absence-rejects-present-directory": "failed",
    "directory-rejects-missing-path": "failed",
    "directory-rejects-file": "failed",
    "entries-reject-missing-name": "failed",
    "entries-reject-extra-name": "failed",
    "entries-reject-file": "failed",
}
BYTE_FIXTURES = {
    "bytes-lf.txt": b"line one\nline two\n",
    "bytes-crlf.txt": b"line one\r\nline two\r\n",
    "bytes-empty.txt": b"",
    "bytes-nul.txt": b"left\x00middle\x00right\r\n",
    "bytes-no-final-newline.txt": b"final line without terminator",
    "bytes-unicode.txt": "café 雪 🧪\n".encode("utf-8"),
}


def require(value, message):
    if not value:
        raise ValueError(message)


def json_member(payloads, name):
    require(name in payloads, "missing required oracle artifact: " + name)
    value = json.loads(payloads[name].decode("utf-8"))
    require(isinstance(value, dict), "oracle artifact is not an object: " + name)
    return value


def load_packet(path, size, expected_sha):
    raw = Path(path).read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    require(len(raw) == size and digest == expected_sha,
            "downloaded oracle artifact differs from GitHub provider size/SHA")
    payloads = {}
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos]
        require(len(names) == len(set(names)), "oracle ZIP has duplicate member names")
        total = 0
        for info in infos:
            name = info.filename
            parts = PurePosixPath(name)
            require(not parts.is_absolute() and ".." not in parts.parts and "\\" not in name and
                    not info.flag_bits & 1, "oracle ZIP has an unsafe/encrypted path")
            require(info.file_size <= 32 * 1024 * 1024, "oracle ZIP member exceeds bound")
            total += info.file_size
            require(total <= 512 * 1024 * 1024, "oracle ZIP expansion exceeds bound")
            if not info.is_dir():
                data = archive.read(info)
                require(len(data) == info.file_size, "truncated oracle ZIP member")
                payloads[name] = data
        require(archive.testzip() is None, "oracle ZIP CRC validation failed")
    return payloads, len(infos), total


def verify_host(host, path, size, provider_sha):
    payloads, members, expanded = load_packet(path, size, provider_sha)
    root = "joe/oracle-calibration-v1/"
    plan = json_member(payloads, root + host + "-plan.json")
    receipt = json_member(payloads, root + host + "-receipt.json")
    freeze = json.loads((DOC / f"replacement-candidate-freeze-{SERIES}.json").read_text(encoding="utf-8"))
    cell = next(row for row in freeze["cells"] if row["host"] == host)
    installed = json_member(payloads, f"candidate-{SERIES}/{host}/installed.json")
    route_host = json_member(payloads, f"joe/public-route-v2/{host}/receipt.json")
    require(installed.get("version") == CANDIDATE and
            installed.get("archive_sha256") == cell["archive_sha256"] and
            installed.get("binary_sha256") == cell["binary_sha256"],
            "provider packet omitted or changed the exact frozen candidate installation")
    require(plan.get("host") == host and plan.get("candidate") == CANDIDATE and
            plan.get("candidate_series") == SERIES and plan.get("source_pin") == PIN and
            plan.get("candidate_archive_sha256", cell["archive_sha256"]) == cell["archive_sha256"] and
            plan.get("runner_sha256") == cell["binary_sha256"] and
            receipt.get("candidate") == CANDIDATE and receipt.get("host") == host and
            receipt.get("candidate_archive_sha256", cell["archive_sha256"]) == cell["archive_sha256"] and
            receipt.get("source_pin") == PIN and receipt.get("runner_sha256") == cell["binary_sha256"] and
            plan.get("target_binary_sha256") == receipt.get("target_binary_sha256") == route_host["target_binary_sha256"] and
            route_host.get("candidate") == CANDIDATE and route_host.get("source_pin") == PIN and
            route_host.get("runner_sha256") == cell["binary_sha256"],
            "JOE oracle plan/receipt candidate or target identity differs")
    require(receipt.get("status") == "oracle-calibration-passed-not-admitted" and
            receipt.get("admission_credit") == 0 and len(receipt.get("cases", [])) == len(CASES),
            "JOE oracle receipt is incomplete or grants invalid credit")
    by_case = {row.get("case"): row for row in receipt["cases"]}
    require(set(by_case) == set(CASES), "oracle case identities differ from the frozen matrix")
    observed = []
    for name, expected_status in CASES.items():
        prefix = root + "cases/" + host + "/" + name + "/"
        report_path = prefix + "report.json"
        report_raw = payloads.get(report_path)
        require(report_raw is not None and sha256_bytes(report_raw) == by_case[name].get("report_sha256"),
                "retained oracle report differs from its receipt: " + name)
        report = json.loads(report_raw.decode("utf-8"))
        require(report.get("report_version") == 3 and report.get("runner_version") == CANDIDATE and
                report.get("summary", {}).get("total") == 1 and len(report.get("results", [])) == 1,
                "oracle report candidate/denominator differs: " + name)
        result = report["results"][0]
        require(result.get("status") == expected_status and result.get("target", {}).get("exit_code") == 0 and
                result.get("cleanup", {}).get("confirmed_exited") and result.get("workspace", {}).get("cleaned"),
                "oracle outcome/target cleanup differs: " + name)
        steps = result.get("steps", [])
        state_steps = [step for step in steps if step.get("action") == "state"]
        require(state_steps and all(step.get("status") == "passed" for step in steps if step.get("action") != "state"),
                "oracle case lacks positive terminal and exact-exit evidence: " + name)
        require(all(step.get("state", {}).get("invocation_id") == result.get("invocation_id") and
                    step.get("state", {}).get("workspace_id") == result.get("invocation_id")
                    for step in state_steps), "oracle state came from a different invocation/workspace: " + name)
        if expected_status == "passed":
            require(all(step.get("status") == "passed" and step.get("state", {}).get("outcome") == "matched"
                        for step in state_steps), "positive oracle state was not independently matched")
        else:
            require(state_steps[-1].get("status") == "failed" and
                    (result.get("failure") or {}).get("category") == "state_assertion_failure",
                    "negative case did not fail at its saved-state assertion: " + name)
        spec_path = prefix + "project/create-note.json"
        spec = json_member(payloads, spec_path)
        require(spec.get("version") == 3 and spec.get("command", [None])[0] == "joe" and
                spec.get("steps", [])[-1].get("state") is not None,
                "calibration case is not a public v3 JOE contract: " + name)
        attempt = by_case[name]
        require(len(attempt.get("attempt_id", "")) == 32 and attempt.get("status") == expected_status,
                "oracle receipt attempt identity/status differs: " + name)
        attempt_id = attempt["attempt_id"]
        event_root = "events/"
        events = {kind: json_member(payloads, event_root + attempt_id + "-" + kind + ".json")
                  for kind in ("started", "identified", "launched", "finished")}
        require(all(event.get("id") == attempt_id and event.get("project") == "joe" and
                    event.get("label") == "joe-oracle-" + name and
                    event.get("phase") == "oracle-calibration" for event in events.values()),
                "oracle attempt lifecycle identity/phase differs: " + name)
        require(events["launched"].get("pid", 0) > 0 and
                events["finished"].get("exit_code") == (0 if expected_status == "passed" else 1) and
                events["finished"].get("harness_cleanup") == "harness_process_reaped" and
                not events["finished"].get("cleanup_errors"),
                "oracle attempt lacks positive launch, expected exit or harness cleanup: " + name)
        observed.append({"case": name, "status": expected_status,
                         "attempt_id": attempt_id, "report_sha256": sha256_bytes(report_raw),
                         "state_steps": len(state_steps), "same_invocation_state": True,
                         "target_exit_zero": True, "cleanup_confirmed": True})

    positive = json_member(payloads, root + "cases/" + host + "/correct-all-kinds-and-byte-families/project/create-note.json")
    positive_states = [step.get("state", {}) for step in positive["steps"] if "state" in step]
    require({row.get("kind") for row in positive_states} >= {"file", "absent", "directory", "entries"},
            "positive oracle case does not cover every public state kind")
    require({row.get("path") for row in positive_states} >= set(BYTE_FIXTURES),
            "positive oracle case omitted byte-family fixtures")
    for name, expected in BYTE_FIXTURES.items():
        actual = next(row for row in positive_states if row.get("path") == name)
        require(base64_decode(actual.get("bytes_base64")) == expected,
                "positive expected byte-family oracle differs: " + name)
    return {"host": host, "provider_artifact_size": size, "provider_artifact_sha256": provider_sha,
            "zip_members": members, "zip_expanded_bytes": expanded,
            "candidate_archive_sha256": cell["archive_sha256"], "runner_sha256": cell["binary_sha256"],
            "target_binary_sha256": receipt["target_binary_sha256"], "cases": observed,
            "positive_cases": 1, "negative_cases": 10, "all_negative_state_rejections": True,
            "admission_credit": 0}


def base64_decode(value):
    import base64
    return base64.b64decode(value, validate=True)


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", type=int, required=True)
    parser.add_argument("--head", required=True)
    for host in ("linux", "darwin"):
        parser.add_argument(f"--{host}-zip", type=Path, required=True)
        parser.add_argument(f"--{host}-artifact-id", type=int, required=True)
        parser.add_argument(f"--{host}-artifact-bytes", type=int, required=True)
        parser.add_argument(f"--{host}-artifact-sha256", required=True)
    args = parser.parse_args()
    require(len(args.head) == 40 and all(c in "0123456789abcdef" for c in args.head), "invalid workflow head SHA")
    hosts = {}
    for host in ("linux", "darwin"):
        hosts[host] = verify_host(host, getattr(args, host + "_zip"),
                                  getattr(args, host + "_artifact_bytes"),
                                  getattr(args, host + "_artifact_sha256"))
        hosts[host]["provider_artifact_id"] = getattr(args, host + "_artifact_id")
        require(hosts[host]["provider_artifact_id"] > 0, "invalid GitHub provider artifact id")
    output = {
        "schema_version": 1, "project": "joe", "workflow_run": args.run_id,
        "workflow_head_sha": args.head, "candidate": CANDIDATE, "source_pin": PIN,
        "hosts": hosts, "ordinary_oracle_cases": 22, "negative_state_rejections": 20,
        "oracle_kinds": ["file", "absent", "directory", "entries"],
        "byte_families": list(BYTE_FIXTURES), "admission_credit": 0,
        "scope": "Independent provider ZIP/SHA/CRC/member/report/contract/attempt readback for exact rc.7 JOE oracle calibration; both native hosts and all same-invocation state outcomes are retained.",
    }
    destination = DOC / "joe" / f"oracle-calibration-artifact-audit-run{args.run_id}-v1.json"
    immutable_json(destination, output)
    print("Independently audited JOE oracle artifacts:", args.run_id, "22 cases, 20 rejected controls, 0 admission credit.")


if __name__ == "__main__":
    main()
