"""Freeze mg's canonical scenario catalog and exact native qualification plan."""
import json
from pathlib import Path
import hashlib

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


MG = DOC / "mg"
NORMAL = [
    ("N01", "pilot-n01.json"), ("N02", "n02-edit-append.json"),
    ("N03", "n03-query-replace.json"), ("N04", "n04-cut-yank.json"),
    ("N05", "n05-undo-redo.json"), ("N06", "n06-save-as.json"),
    ("N07", "n07-buffer-switch.json"), ("N08", "n08-utf8-wide.json"),
]
EDGE = [
    (f"E{i:02d}", f"e{i:02d}-{name}.json") for i, name in (
        (1, "empty-save"), (2, "buffer-boundaries"), (3, "backspace-join"),
        (4, "extended-line"), (5, "wide-backspace"), (6, "readonly-buffer"),
        (7, "missing-parent"), (8, "filename-spaces"), (9, "cancel-filename"),
    )
] + [("E10", "e10a-decline-overwrite.json"), ("E10", "e10b-accept-overwrite.json"),
     ("E11", "e11-resize-save.json"), ("E12", "e12-refuse-unsaved-quit.json")]
SCHEDULE = [
    "ordinary-cold-1", "ordinary-warm-1", "ordinary-cold-2", "ordinary-warm-2",
    "widened-viewport", "spaced-unicode-home-temp", "normal-input-readiness",
    "segmented-printable-input", "bounded-contention-1", "bounded-contention-2",
    "small-viewport-boundary", "tight-startup-boundary",
]


def tree_sha256(root):
    root = Path(root).resolve(strict=True)
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        if path.is_symlink():
            raise ValueError(f"linked fixture entry: {path}")
        if path.is_file():
            relative = path.relative_to(root).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(bytes.fromhex(sha256(path)))
    return digest.hexdigest()


def main():
    destination = MG / "final-qualification-declaration-v1.json"
    if destination.exists():
        raise FileExistsError(destination)
    freeze_path = DOC / "replacement-candidate-freeze-native-exit-v1.json"
    freeze = json.loads(freeze_path.read_text(encoding="utf-8"))
    source_path = MG / "source-provenance.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    scenarios = []
    for risk, rows in (("normal", NORMAL), ("edge", EDGE)):
        for case, filename in rows:
            path = MG / filename
            raw = path.read_bytes()
            spec = json.loads(raw)
            scenarios.append({
                "id": case, "class": risk, "contract": path.relative_to(ROOT).as_posix(),
                "contract_sha256": sha256(path),
                "fixture": spec["workspace"]["fixture"],
                "fixture_tree_sha256": tree_sha256(MG / spec["workspace"]["fixture"]),
            })
    ids = {row["id"] for row in scenarios}
    if len(scenarios) != 21 or len(ids) != 20 or sum(row["class"] == "normal" for row in scenarios) != 8:
        raise ValueError("canonical catalog must be eight normal plus twelve edge identities and two E10 variants")
    if sum(row["class"] == "edge" for row in scenarios) != 13:
        raise ValueError("edge contract count must include both reviewed E10 branches")
    cells = []
    for host, architecture in (("linux", "amd64"), ("darwin", "arm64")):
        rows = [row for row in freeze["cells"] if row["host"] == host]
        if len(rows) != 1:
            raise ValueError(f"candidate freeze does not contain exactly one {host} cell")
        cell = rows[0]
        cells.append({"host": host, "architecture": architecture,
                      "candidate_run": cell["run"], "archive_sha256": cell["archive_sha256"],
                      "binary_sha256": cell["binary_sha256"]})
    declaration = {
        "schema_version": 1, "project": "mg", "status": "declared-not-yet-qualified",
        "candidate": freeze["version"], "candidate_freeze": freeze_path.relative_to(ROOT).as_posix(),
        "candidate_freeze_sha256": sha256(freeze_path),
        "source_pin": source["pin"], "source_provenance": source_path.relative_to(ROOT).as_posix(),
        "source_provenance_sha256": sha256(source_path),
        "native_cells": cells, "canonical_scenario_count": 20,
        "normal_scenarios": 8, "edge_scenarios": 12,
        "contract_executions_per_batch": 21,
        "edge_case_variant": "E10 is one canonical edge identity; decline and accept contracts both execute and remain separately receipted.",
        "batches": [{"index": i, "variation": label} for i, label in enumerate(SCHEDULE)],
        "expected_ordinary_executions": 20 * 12 * 2,
        "expected_additional_e10_branch_executions": 12 * 2,
        "expected_total_contract_executions": 21 * 12 * 2,
        "failure_policy": "No retries inside a batch or series. Preserve the first failed attempt; any replacement must be a separately declared series.",
        "contention_policy": "At most one owned 1 MiB SHA-256 worker per scenario, two seconds maximum, terminated and waited before the next scenario.",
        "fault_calibration": {"distinct_faults": 4, "hosts": ["linux", "darwin"],
                              "phases_per_fault_host": ["pristine-baseline", "mutated-source", "restored-source"],
                              "required_phase_executions": 24,
                              "readback": "mg/mg-fault-calibration-readback-v2.json"},
        "scenarios": scenarios,
    }
    immutable_json(destination, declaration)
    print(json.dumps({"path": destination.relative_to(ROOT).as_posix(),
                      "sha256": sha256(destination), "canonical_scenarios": 20,
                      "contract_executions_per_batch": 21,
                      "planned_total_contract_executions": 504}, sort_keys=True))


if __name__ == "__main__":
    main()
