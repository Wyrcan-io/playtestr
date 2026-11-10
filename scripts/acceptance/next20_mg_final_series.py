"""Run one of mg's twelve frozen native exact-candidate qualification batches."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

from next20_check import DOC, RAW, ROOT
from next20_mg_final_declare import tree_sha256
from readiness_evidence import immutable_json, sha256


MG = DOC / "mg"
CASES = [
    ("N01", "pilot-n01.json"),
    ("N02", "n02-edit-append.json"), ("N03", "n03-query-replace.json"),
    ("N04", "n04-cut-yank.json"), ("N05", "n05-undo-redo.json"),
    ("N06", "n06-save-as.json"), ("N07", "n07-buffer-switch.json"),
    ("N08", "n08-utf8-wide.json"),
    ("E01", "e01-empty-save.json"), ("E02", "e02-buffer-boundaries.json"),
    ("E03", "e03-backspace-join.json"), ("E04", "e04-extended-line.json"),
    ("E05", "e05-wide-backspace.json"), ("E06", "e06-readonly-buffer.json"),
    ("E07", "e07-missing-parent.json"), ("E08", "e08-filename-spaces.json"),
    ("E09", "e09-cancel-filename.json"),
    ("E10", "e10a-decline-overwrite.json"),
    ("E10", "e10b-accept-overwrite.json"),
    ("E11", "e11-resize-save.json"), ("E12", "e12-refuse-unsaved-quit.json"),
]
BATCHES = [
    "ordinary-cold-1", "ordinary-warm-1", "ordinary-cold-2", "ordinary-warm-2",
    "widened-viewport", "spaced-unicode-home-temp", "normal-input-readiness",
    "segmented-printable-input", "bounded-contention-1", "bounded-contention-2",
    "small-viewport-boundary", "tight-startup-boundary",
]


def worker():
    """Return a tiny bounded CPU worker command for contention batches."""
    code = ("import hashlib,time; end=time.monotonic()+2; b=b'x'*1048576; "
            "n=0\nwhile time.monotonic()<end: hashlib.sha256(b).digest(); n+=1\n")
    return [sys.executable, "-c", code]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", choices=("linux", "darwin"), required=True)
    parser.add_argument("--batch", type=int, choices=range(12), required=True)
    parser.add_argument("--mg-build-root", required=True)
    args = parser.parse_args()
    native = {"Linux": "linux", "Darwin": "darwin"}.get(platform.system())
    if native != args.host:
        raise RuntimeError(f"native host mismatch: expected {args.host}, got {native}")
    build_root = Path(args.mg_build_root).resolve(strict=True)
    build_root.relative_to(ROOT.resolve())
    build = json.loads((build_root / "active/mg/build.json").read_text(encoding="utf-8"))
    if build.get("project") != "mg" or build.get("host") != args.host:
        raise ValueError("pinned native mg build identity mismatch")
    declaration_path = DOC / "mg/final-qualification-declaration-v2.json"
    declaration = json.loads(declaration_path.read_text(encoding="utf-8"))
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v1.json"
    if declaration.get("candidate_freeze_sha256") != sha256(freeze_path):
        raise ValueError("final qualification declaration no longer matches the candidate freeze")
    if declaration.get("source_pin") != build.get("pin"):
        raise ValueError("final qualification declaration no longer matches the pinned mg source")
    if args.host not in {cell["host"] for cell in declaration.get("native_cells", [])}:
        raise ValueError("final qualification declaration does not include this native host")
    if BATCHES[args.batch] != declaration["batches"][args.batch]["variation"]:
        raise ValueError("final qualification batch differs from its frozen schedule")
    frozen = {(row["id"], row["contract"].rsplit("/", 1)[-1]): row
              for row in declaration["scenarios"]}
    for case, name in CASES:
        row = frozen.get((case, name))
        if row is None or row["contract_sha256"] != sha256(MG / name):
            raise ValueError(f"canonical contract changed after declaration: {case} {name}")
        if row["fixture_tree_sha256"] != tree_sha256(MG / row["fixture"]):
            raise ValueError(f"canonical fixture changed after declaration: {case} {name}")
    out = RAW / f"mg/final-series/{args.host}/{args.batch}"
    out.mkdir(parents=True, exist_ok=False)
    started = datetime.now(timezone.utc).isoformat()
    declaration = {
        "schema_version": 1, "project": "mg", "host": args.host,
        "batch": args.batch, "variation": BATCHES[args.batch],
        "candidate": "v0.4.0-rc.6", "mg_pin": build["pin"],
        "mg_binary_sha256": build["binary_sha256"],
        "qualification_declaration_sha256": sha256(declaration_path),
        "canonical_scenarios": 20, "contract_executions": len(CASES),
        "cases": [{"id": case, "contract": f"mg/{name}", "sha256": sha256(MG / name)}
                  for case, name in CASES],
        "started_at_utc": started,
    }
    immutable_json(out / "batch-declaration.json", declaration)
    results, failures = [], []
    helper = ROOT / "scripts/acceptance/next20_mg_scenario.py"
    for index, (case, name) in enumerate(CASES):
        command = [sys.executable, "-B", str(helper), "--host", args.host,
                   "--mg-build-root", str(build_root), "--spec", str(MG / name),
                   "--phase", "final-qualification", "--batch", str(args.batch)]
        worker_process = None
        worker_cleanup = {"attempted": args.batch in (8, 9), "confirmed_exited": True}
        if args.batch in (8, 9):
            worker_process = subprocess.Popen(worker(), cwd=ROOT,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, close_fds=True)
            worker_cleanup.update(pid=worker_process.pid, resource_bound="one process, 1 MiB input, 2 seconds")
        start = time.monotonic()
        try:
            completed = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                       encoding="utf-8", errors="replace", timeout=150,
                                       check=False)
            result = {
                "index": index, "canonical_case": case, "contract": name,
                "contract_sha256": sha256(MG / name), "returncode": completed.returncode,
                "stdout": completed.stdout[-8000:], "stderr": completed.stderr[-8000:],
                "elapsed_seconds": round(time.monotonic() - start, 3),
                "worker_cleanup": worker_cleanup,
            }
            if completed.returncode:
                failures.append({"index": index, "case": case, "contract": name,
                                 "reason": "scenario helper nonzero", "returncode": completed.returncode})
        except Exception as error:
            result = {"index": index, "canonical_case": case, "contract": name,
                      "contract_sha256": sha256(MG / name),
                      "elapsed_seconds": round(time.monotonic() - start, 3),
                      "error": f"{type(error).__name__}: {error}",
                      "worker_cleanup": worker_cleanup}
            failures.append({"index": index, "case": case, "contract": name,
                             "reason": result["error"]})
        finally:
            if worker_process is not None:
                if worker_process.poll() is None:
                    worker_process.terminate()
                    try:
                        worker_process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        worker_process.kill()
                        worker_process.wait(timeout=3)
                worker_cleanup["confirmed_exited"] = worker_process.poll() is not None
                if not worker_cleanup["confirmed_exited"]:
                    failures.append({"index": index, "case": case, "reason": "contention worker cleanup unconfirmed"})
        immutable_json(out / f"{index:02d}-{case}-{Path(name).stem}.json", result)
        results.append(result)
        print(args.host, args.batch, case, name, "passed" if result.get("returncode") == 0 else "failed", flush=True)
        if not worker_cleanup["confirmed_exited"]:
            failures.append({"index": index, "case": case, "reason": "unsafe worker cleanup"})
            break
    receipt = {
        "schema_version": 1, "project": "mg", "host": args.host,
        "batch": args.batch, "variation": BATCHES[args.batch],
        "candidate": "v0.4.0-rc.6", "expected_contract_executions": len(CASES),
        "attempted_contract_executions": len(results),
        "passed_contract_executions": sum(x.get("returncode") == 0 for x in results),
        "failed_contract_executions": len(failures), "failures": failures,
        "results": results, "started_at_utc": started,
        "finished_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "passed" if not failures and len(results) == len(CASES) else "failed",
    }
    immutable_json(out / "batch-receipt.json", receipt)
    print(json.dumps({key: receipt[key] for key in (
        "host", "batch", "attempted_contract_executions", "passed_contract_executions",
        "failed_contract_executions", "status")}, sort_keys=True), flush=True)
    if failures or len(results) != len(CASES):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
