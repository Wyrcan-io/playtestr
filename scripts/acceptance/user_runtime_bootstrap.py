#!/usr/bin/env python3
"""Reproduce the reviewed, task-local Linux prerequisites for this campaign."""
import argparse, hashlib, json, platform, tarfile, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / '.tools/ten-project-runtime'
TOOLS = {
    'uv': ('https://github.com/astral-sh/uv/releases/download/0.12.23/uv-x86_64-unknown-linux-gnu.tar.gz',
           '9167d72b3319674b6303c4cbe071854bba13ebdf3d76b1a7cbdc175471fb66d6', 'uv-x86_64-unknown-linux-gnu/uv'),
    'node': ('https://nodejs.org/dist/v24.7.0/node-v24.7.0-linux-x64.tar.xz',
             '2fb405154d017f04d21b3d2273cc1cdfa824cfeffbd4225976454d06d5e381a4', 'node-v24.7.0-linux-x64/bin/node'),
}

parser = argparse.ArgumentParser()
parser.add_argument('tool', choices=TOOLS)
args = parser.parse_args()
if platform.system() != 'Linux' or platform.machine() != 'x86_64':
    raise SystemExit('Campaign prerequisite is explicitly Linux x86_64 only')
url, expected, binary = TOOLS[args.tool]
DEST.mkdir(parents=True, exist_ok=True)
archive = DEST / url.rsplit('/', 1)[-1]
if not archive.exists():
    try:
        with urllib.request.urlopen(url, timeout=60) as response, archive.open('xb') as output:
            total = 0
            while block := response.read(1024 * 1024):
                total += len(block)
                if total > 120 * 1024 * 1024:
                    raise RuntimeError('Prerequisite download exceeds explicit bound')
                output.write(block)
    except Exception:
        archive.unlink(missing_ok=True)
        raise
if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
    raise SystemExit('Prerequisite archive digest mismatch; refuse execution')
if not (DEST / binary).exists():
    with tarfile.open(archive) as source:
        source.extractall(DEST, filter='data')
print(json.dumps(dict(tool=args.tool, url=url, archive_sha256=expected, binary=str(DEST / binary))))
