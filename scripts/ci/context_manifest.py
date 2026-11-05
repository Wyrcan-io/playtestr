#!/usr/bin/env python3
"""Capture bounded PR/build/contract identities, never commands or environment values."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

MAX_FILES = 1000
MAX_TOTAL = 128 * 1024 * 1024
MAX_MANIFEST = 256 * 1024
SHA = re.compile(r"^[a-f0-9]{40}$")


def bounded(path, maximum):
    with path.open("rb") as stream:
        data = stream.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("identity input exceeds bound")
    return data


def create(selection, runner, event, env, tested, root):
    lines = bounded(selection, 256 * 1024).decode("utf-8-sig").splitlines()
    if not lines or not re.fullmatch(r"Selected [1-9][0-9]* specs:", lines[0]):
        raise ValueError("selection missing or empty")
    specs = lines[1:]
    if len(specs) != int(lines[0].split()[1]) or len(specs) > 1000:
        raise ValueError("selection count mismatch")
    if not SHA.fullmatch(tested):
        raise ValueError("invalid tested revision")
    trigger = env.get("GITHUB_EVENT_NAME", "local")
    if trigger not in ("local", "push", "pull_request", "workflow_dispatch"):
        raise ValueError("unsupported workflow event")
    pr = event.get("pull_request", {})
    head, base = pr.get("head", {}).get("sha"), pr.get("base", {}).get("sha")
    if trigger == "pull_request" and (not isinstance(head, str) or not SHA.fullmatch(head)
                                      or not isinstance(base, str) or not SHA.fullmatch(base)):
        raise ValueError("missing PR identity")
    declared = env.get("GITHUB_SHA", tested)
    if declared != tested:
        raise ValueError("checkout differs from workflow tested revision")
    files, executable_files, total = {}, {}, 0

    def add(path, collection, external=False):
        nonlocal total
        path = Path(path)
        if path.is_symlink():
            raise ValueError("identity path is a link")
        resolved = path.resolve(strict=True)
        if not external and not resolved.is_relative_to(root):
            raise ValueError("contract path escapes checkout")
        label = resolved.name if external else resolved.relative_to(root).as_posix()
        if len(label) > 256 or len(files) + len(executable_files) >= MAX_FILES:
            raise ValueError("identity inventory exceeds bound")
        if label in collection:
            return
        data = bounded(resolved, MAX_TOTAL - total)
        total += len(data)
        collection[label] = hashlib.sha256(data).hexdigest()

    for name in specs:
        if len(name) > 256 or "\x00" in name:
            raise ValueError("invalid selected path")
        path = root / name
        spec = json.loads(bounded(path, 1_000_000))
        add(path, files)
        for step in spec["steps"]:
            if step.get("snapshot"):
                add(path.parent / "snapshots" / step["snapshot"], files)
        workspace = spec.get("workspace")
        if workspace:
            fixture = path.parent / workspace["fixture"]
            if fixture.is_symlink() or not fixture.resolve().is_relative_to(path.parent.resolve()):
                raise ValueError("invalid fixture root")
            visited = 0
            for directory, dirs, names in os.walk(fixture, followlinks=False):
                visited += len(dirs) + len(names)
                if visited > 2000:
                    raise ValueError("fixture inventory exceeds bound")
                for entry in dirs + names:
                    child = Path(directory) / entry
                    if child.is_symlink():
                        raise ValueError("fixture link")
                for entry in names:
                    add(Path(directory) / entry, files)
        command = spec["command"][0]
        if "/" in command or "\\" in command:
            binary = (path.parent if workspace else root) / command
            if not binary.exists() and os.name == "nt":
                binary = Path(str(binary) + ".exe")
        else:
            located = shutil.which(command)
            binary = Path(located) if located else None
        if binary is not None and binary.is_file():
            add(binary, executable_files, not binary.resolve().is_relative_to(root))
    runner_hash = hashlib.sha256(bounded(runner, 128 * 1024 * 1024)).hexdigest()
    result = dict(context_version=1, event=trigger, repository=env.get("GITHUB_REPOSITORY", "local"),
                  run_id=env.get("GITHUB_RUN_ID", "local"), attempt=env.get("GITHUB_RUN_ATTEMPT", "1"),
                  pr_number=event.get("number"), head_sha=head, base_sha=base,
                  tested_sha=tested, checkout_strategy="github-merge" if trigger == "pull_request" else "exact-checkout",
                  runner_sha256=runner_hash, selected_specs=specs,
                  contract_files=dict(sorted(files.items())), target_binaries=dict(sorted(executable_files.items())))
    raw = json.dumps(result, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    if len(raw) > MAX_MANIFEST:
        raise ValueError("context exceeds 256 KiB")
    return raw


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = Path.cwd().resolve()
        event_path = os.environ.get("GITHUB_EVENT_PATH")
        event = json.loads(bounded(Path(event_path), 8 * 1024 * 1024)) if event_path else {}
        tested = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        data = create(args.selection, args.runner, event, os.environ, tested, root)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_bytes(data)
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError):
        print("Playtestr context unavailable: selection, identity or bounded input invalid.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
