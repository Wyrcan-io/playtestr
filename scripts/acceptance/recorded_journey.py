#!/usr/bin/env python3
"""Bounded native P1 example record/replay/target-defect/recovery evidence.

Only synthetic repo fixtures are mutated, restored in finally. No network or
outreach. Requires compiled candidate, demo, fixture and pinned Gum v0.17.0.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
EXT = ".exe" if os.name == "nt" else ""
BIN = ROOT / "bin" / ("playtestr" + EXT)
EVIDENCE = ROOT / "artifacts" / "p0-p2-recorded"


def command(args, name, env=None, input=None, expected=0):
    result = subprocess.run([str(a) for a in args], cwd=ROOT, env=env, input=input,
                            text=True, encoding="utf-8", errors="strict",
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=90)
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    (EVIDENCE / (name + ".log")).write_text(result.stdout, encoding="utf-8")
    if result.returncode != expected:
        raise RuntimeError(f"{name}: expected {expected}, got {result.returncode}; first failure preserved")
    return result


def digest(paths):
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


async def record_with_file_oracle(args, controls, env, name):
    """Inspect actual synthetic saved state before recorder teardown/replay.

    The assertion belongs to this harness, not to the target's success message.
    Each pipe read and the full child lifetime are bounded; no background thread.
    """
    proc = await asyncio.create_subprocess_exec(*map(str, args), cwd=ROOT, env=env,
                                              stdin=asyncio.subprocess.PIPE,
                                              stdout=asyncio.subprocess.PIPE,
                                              stderr=asyncio.subprocess.STDOUT,
                                              limit=256 * 1024)
    lines = []
    try:
        proc.stdin.write((controls + "/screen\n").encode("utf-8"))
        await proc.stdin.drain()
        working = None
        while True:
            line = await asyncio.wait_for(proc.stdout.readline(), timeout=25)
            if not line:
                raise RuntimeError("recorder exited before independent state oracle")
            text = line.decode("utf-8")
            lines.append(text)
            if sum(map(len, lines)) > 256 * 1024:
                raise RuntimeError("recorder preview exceeds harness bound")
            match = re.search(r'working-directory=(".*")', text)
            if match:
                working = Path(json.loads(match[1]))
            if "Saved and verified atlas:synthetic" in text:
                if working is None or not working.parent.name.startswith("playtestr-workspace-"):
                    raise RuntimeError("missing owned synthetic workspace identity")
                saved = working / "result.txt"
                if saved.stat().st_size > 1024 or saved.read_bytes() != b"atlas:synthetic":
                    raise RuntimeError("independent saved-file oracle failed")
                break
        proc.stdin.write(b"/review\n/replay\n/save\n")
        await proc.stdin.drain()
        proc.stdin.close()
        remainder = await asyncio.wait_for(proc.stdout.read(), timeout=60)
        lines.append(remainder.decode("utf-8"))
        await asyncio.wait_for(proc.wait(), timeout=5)
        if proc.returncode != 0:
            raise RuntimeError("recorded wizard failed after state oracle")
    finally:
        if proc.returncode is None:
            # Signal normal cancellation so the recorder restores/cleans up.
            try:
                proc.stdin.write(b"/quit\n")
                await proc.stdin.drain()
                await asyncio.wait_for(proc.wait(), timeout=5)
            except (BrokenPipeError, ConnectionResetError, asyncio.TimeoutError):
                proc.kill()
                await proc.wait()
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        (EVIDENCE / (name + ".log")).write_text("".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--export-examples", action="store_true", help="create absent reviewed examples")
    args = parser.parse_args()
    os.chdir(ROOT)
    env = dict(os.environ, PLAYTESTR_DELAY_MS="0", PLAYTESTR_GUM=str(ROOT / ".tools" / "external" / ("gum" + EXT)))
    command([env["PLAYTESTR_GUM"], "--version"], "gum-version", env)
    cases = {
        "wizard": dict(target="fixture", mode="wizard", fixture="wizard", controls=(
            "/expect Project name? (synthetic workspace)\n/text \"atlas\"\n/resize 100 30\n/key Enter\n"
            "/expect Confirm project atlas at 100x30; seed=synthetic\n/snapshot recorded-wizard-confirm.txt\n"
            "/text \"y\"\n/expect Saved and verified atlas:synthetic\n/exit 0\n/snapshot recorded-wizard-saved.txt\n")),
        "selector": dict(target="fixture", mode="gum", fixture="selector", controls=(
            "/expect Pick deployment\n/key ArrowDown\n/key Enter\n/exit 0\n/expect Beta\n/snapshot recorded-gum-beta.txt\n")),
        "fullscreen": dict(target="demo", mode=None, fixture=None, controls=(
            "/expect PLAYTESTR / mission control\n/key ArrowDown\n/key Enter\n"
            "/expect Diagnostics: all systems healthy.\n/snapshot recorded-diagnostics.txt\n/text \"q\"\n/exit 0\n")),
    }
    output_dir = ROOT / "examples" / "recorded" if args.export_examples else ROOT / ".cache" / "p0-p2" / "recorded-cases"
    if not args.export_examples:
        # A unique directory preserves every prior attempt and avoids overwrites.
        import tempfile
        (ROOT / ".cache" / "p0-p2").mkdir(parents=True, exist_ok=True)
        output_dir = Path(tempfile.mkdtemp(prefix="recorded-", dir=ROOT / ".cache" / "p0-p2"))
        shutil.copytree(ROOT / "examples" / "recorded" / "fixtures", output_dir / "fixtures")
    output_dir.mkdir(parents=True, exist_ok=True)
    observations = []
    for name, case in cases.items():
        path = output_dir / (name + ".json")
        binary = ROOT / "bin" / case["target"]
        target = os.path.relpath(binary, output_dir).replace(os.sep, "/") if case["fixture"] else "./bin/demo"
        flags = [BIN, "record", "--output", path, "--name", "Recorded " + name, "--timeout-ms", "15000", "--run-timeout-ms", "60000", "--inherit-env", "PLAYTESTR_DELAY_MS"]
        if case["fixture"]:
            flags += ["--fixture", "fixtures/" + case["fixture"], "--temporary-home", "--temporary-temp"]
        if name == "selector":
            flags += ["--inherit-env", "PLAYTESTR_GUM"]
        flags += ["--", target]
        if case["mode"]:
            flags += [case["mode"]]
        controls = case["controls"] + "/review\n/replay\n/save\n"
        if name == "wizard":
            asyncio.run(record_with_file_oracle(flags, case["controls"], env, name + "-record"))
        else:
            command(flags, name + "-record", env, controls)
        spec = json.loads(path.read_text(encoding="utf-8"))
        snapshots = [path.parent / "snapshots" / s["snapshot"] for s in spec["steps"] if "snapshot" in s]
        before = digest([path] + snapshots)
        for attempt, delay in enumerate([0, 25, 100, 5, 60, 150, 10, 80, 40, 120], 1):
            varied = dict(env, PLAYTESTR_DELAY_MS=str(delay))
            command([BIN, "test", "--artifacts-dir", EVIDENCE / name / f"replay-{attempt}", "--report", EVIDENCE / name / f"replay-{attempt}.json", path], f"{name}-replay-{attempt}", varied)
        # Mutate actual target behavior/configuration; tests and baselines unchanged.
        choices = output_dir / "fixtures" / "selector" / "choices.txt"
        original_choices = choices.read_bytes() if name == "selector" else None
        try:
            if name == "selector":
                choices.write_text("Alpha Gamma Beta\n", encoding="utf-8")
            else:
                variable = "wizardSuffix" if name == "wizard" else "diagnosticsSuffix"
                command(["go", "build", "-ldflags", f"-X main.{variable}=REGRESSION", "-o", str(binary) + EXT, "./cmd/" + case["target"]], name + "-mutate-build", env)
            command([BIN, "test", "--artifacts-dir", EVIDENCE / name / "defect", "--report", EVIDENCE / name / "defect.json", path], name + "-defect", env, expected=1)
            if before != digest([path] + snapshots):
                raise RuntimeError("target mutation changed test or baseline")
        finally:
            if name == "selector":
                choices.write_bytes(original_choices)
            else:
                command(["go", "build", "-o", str(binary) + EXT, "./cmd/" + case["target"]], name + "-recover-build", env)
        command([BIN, "test", "--report", EVIDENCE / name / "recovery.json", path], name + "-recovery", env)
        # A normal hand edit, with no recorder involved, remains runnable.
        modified = dict(spec)
        modified["name"] = spec["name"] + " (manual edit)"
        editable = path.parent / (name + "-manual.json")
        editable.write_text(json.dumps(modified, indent=2) + "\n", encoding="utf-8")
        try:
            command([BIN, "test", editable], name + "-manual-edit", env)
        finally:
            editable.unlink()
        observations.append(dict(example=name, independent_saved_file_oracle=name == "wizard", capabilities=["fixture", "wizard", "resize", "saved-state"] if name == "wizard" else ["external-gum-v0.17.0", "selector"] if name == "selector" else ["full-screen"], fresh_replays=10, delays_ms=[0,25,100,5,60,150,10,80,40,120], defect_detected=True, recovery=True, unchanged_test_baseline_hashes=before))
    summary = dict(host=platform.platform(), arch=platform.machine(), examples=observations, campaign_credit=0)
    (EVIDENCE / "acceptance.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
