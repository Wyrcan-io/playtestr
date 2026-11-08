"""Verify and remove only Taskell's generated Stack source work directory."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess

from next20_check import DOC, NAME, RAW, ROOT
from readiness_evidence import immutable_json, sha256

MAX_FILES = 250000
MAX_FILE_BYTES = 1024**3
MAX_TOTAL_BYTES = 4 * 1024**3


def inventory_work_directory(path, target):
    """Hash a bounded, regular-file-only .stack-work tree without following links."""
    path = Path(path)
    target = Path(target).resolve(strict=True)
    if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
        raise ValueError('Taskell Stack work root is linked')
    resolved = path.resolve(strict=True)
    resolved.relative_to(target)
    files = {}
    total = 0
    pending = [path]
    while pending:
        directory = pending.pop()
        for entry in os.scandir(directory):
            item = Path(entry.path)
            relative = item.relative_to(path).as_posix()
            info = entry.stat(follow_symlinks=False)
            if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_reparse_tag', 0):
                raise ValueError('Taskell Stack work contains a link/reparse point: ' + relative)
            if stat.S_ISDIR(info.st_mode):
                pending.append(item)
            elif stat.S_ISREG(info.st_mode):
                total += info.st_size
                if len(files) >= MAX_FILES or info.st_size > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
                    raise ValueError('Taskell Stack work inventory exceeds reviewed bounds')
                files[relative] = dict(bytes=info.st_size, sha256=sha256(item))
            else:
                raise ValueError('Taskell Stack work contains a special file: ' + relative)
    return dict(files=files, file_count=len(files), total_bytes=total)


def process_rows(target):
    result = subprocess.run(['ps', '-axo', 'pid=,lstart=,args='], capture_output=True,
                            timeout=5, check=True)
    if len(result.stdout) > 1024**2:
        raise ValueError('Taskell process observer exceeded its output bound')
    target_bytes = str(target).encode()
    return [line.decode('utf-8', 'replace')[:2048] for line in result.stdout.splitlines()
            if target_bytes in line]


def prepare(project='taskell', host='linux', run_id=None):
    if project != 'taskell' or host not in {'linux', 'darwin'}:
        raise ValueError('Taskell source cleanup accepts only its native Linux/macOS hosts')
    target = RAW / 'active' / project
    target.resolve(strict=True).relative_to(RAW / 'active')
    for ancestor in (ROOT / 'artifacts', RAW, RAW / 'active', target):
        if ancestor.is_symlink() or getattr(ancestor, 'is_junction', lambda: False)():
            raise ValueError('linked Taskell cleanup ancestor')
    owner = json.loads((target / 'task-owned.json').read_text(encoding='utf-8'))
    acquisition = json.loads((target / 'acquisition.json').read_text(encoding='utf-8'))
    provenance_path = DOC / project / 'source-provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    if (owner.get('workspace') != str(ROOT) or owner.get('campaign') != NAME or owner.get('slug') != project or
            acquisition.get('pin') != provenance.get('pin') or acquisition.get('source_files') != provenance.get('files')):
        raise ValueError('Taskell target ownership or frozen source identity differs')
    if process_rows(target):
        raise ValueError('Taskell process arguments still reference the owned target')

    source = target / 'src'
    if source.is_symlink() or getattr(source, 'is_junction', lambda: False)():
        raise ValueError('Taskell source root is linked')
    expected = provenance['files']
    actual = {}
    modes = {}
    scanned = 0
    for path in source.rglob('*'):
        scanned += 1
        if scanned > 300000:
            raise ValueError('Taskell source cleanup scan exceeded its path bound')
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('Taskell source contains a linked path')
        if path.is_file():
            relative = path.relative_to(source).as_posix()
            if relative == '.stack-work' or relative.startswith('.stack-work/'):
                continue
            if path.stat().st_size > (2 * 1024**2 if relative == 'taskell.cabal' else 8 * 1024**2):
                raise ValueError('Taskell source cleanup file exceeds its reviewed bound: ' + relative)
            actual[relative] = sha256(path)
            modes[relative] = '100755' if path.stat().st_mode & stat.S_IXUSR else '100644'
    unexpected = set(actual) - set(expected) - {'taskell.cabal'}
    mismatched = {name for name in set(actual) & set(expected) if actual[name] != expected[name]}
    missing = set(expected) - set(actual)
    mode_mismatched = {name for name in set(modes) & set(provenance['git_modes'])
                       if modes[name] != provenance['git_modes'][name]}
    if unexpected or mismatched or missing or mode_mismatched:
        raise ValueError('Taskell source differs from pinned inputs: ' + json.dumps(dict(
            unexpected=sorted(unexpected)[:20], mismatched=sorted(mismatched)[:20],
            missing=sorted(missing)[:20], mode_mismatched=sorted(mode_mismatched)[:20]), sort_keys=True))

    work = source / '.stack-work'
    work_inventory = inventory_work_directory(work, source) if work.exists() else dict(
        files={}, file_count=0, total_bytes=0)
    generated = {}
    cabal = source / 'taskell.cabal'
    if cabal.is_file() and 'taskell.cabal' not in expected:
        if cabal.stat().st_size > 2 * 1024**2:
            raise ValueError('Taskell generated Cabal metadata exceeds its bound')
        generated['taskell.cabal'] = dict(sha256=sha256(cabal))
    elif 'taskell.cabal' in actual and 'taskell.cabal' not in expected:
        raise ValueError('Taskell generated Cabal metadata is not a regular file')

    run_id = run_id or os.environ.get('GITHUB_RUN_ID') or 'local'
    if not run_id.isdigit() and run_id != 'local':
        raise ValueError('Unsafe Taskell cleanup run identity')
    output = RAW / project / 'cleanup-preparation' / run_id / host
    output.mkdir(parents=True, exist_ok=False)
    manifest = output / 'generated-source-manifest.json'
    immutable_json(manifest, dict(schema_version=1,
        primary_source_provenance_sha256=sha256(provenance_path), generated_files=generated,
        scope='Only Hpack-generated taskell.cabal is added to pinned primary source identity.'))
    if work.exists():
        inventory_path = output / 'stack-work-inventory.json'
        immutable_json(inventory_path, dict(schema_version=1, project=project, host=host,
            owned_path=str(work), inventory=work_inventory,
            scope='Bounded file-hash inventory of the exact owned Stack-generated .stack-work directory before removal.'))
        if inventory_work_directory(work, source) != work_inventory:
            raise ValueError('Taskell Stack work directory changed after inventory')
        shutil.rmtree(work)
        if work.exists():
            raise ValueError('Taskell Stack work directory remains after checked removal')
    receipt = output / 'source-cleanup.json'
    immutable_json(receipt, dict(schema_version=1, project=project, host=host,
        source_manifest_sha256=sha256(provenance_path), generated_source_manifest_sha256=sha256(manifest),
        generated_files=generated, stack_work_inventory_sha256=sha256(output / 'stack-work-inventory.json')
            if (output / 'stack-work-inventory.json').is_file() else None,
        stack_work_removed=not work.exists(), source_primary_files_match=True,
        checked_processes=process_rows(target),
        scope='Process check, exact pinned-source comparison, generated Hpack metadata binding, and bounded Stack work removal.'))
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=['linux', 'darwin'], required=True)
    parser.add_argument('--run-id')
    args = parser.parse_args()
    print(prepare(host=args.host, run_id=args.run_id))


if __name__ == '__main__':
    main()
