#!/usr/bin/env python3
"""Read-only native process/runtime audit before task prerequisite deletion."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
apps = list((ROOT/'.cache/ten-project-apps').iterdir())
native = list(Path('/var/tmp').glob('playtestr-user-pass-*'))
processes = []
markers = [str(ROOT/'.cache/ten-project-apps')+'/',
           '/var/tmp/playtestr-user-pass-', str(ROOT/'.tools/ten-project-runtime')+'/']
for entry in Path('/proc').iterdir():
    if not entry.name.isdigit() or int(entry.name)==os.getpid():
        continue
    try:
        command = (entry/'cmdline').read_bytes().replace(b'\0',b' ').decode('utf-8',errors='replace')
    except (OSError,PermissionError):
        continue
    if any(marker in command for marker in markers):
        processes.append(int(entry.name))
result = dict(application_directories=[str(p) for p in apps],
              native_runtime_directories=[str(p) for p in native],target_process_ids=processes)
print(json.dumps(result))
if apps or native or processes:
    raise SystemExit('Task applications/runtimes/processes remain; refuse prerequisite deletion')
