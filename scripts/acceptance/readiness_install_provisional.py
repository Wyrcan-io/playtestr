"""Extract and execute frozen private candidate bytes; never rebuild them."""
import argparse
import asyncio
import os
from pathlib import Path
import platform
import tarfile
import zipfile

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, help='Owned native Actions download; defaults to local frozen archive')
    args = parser.parse_args()
    host = {'Linux': 'linux', 'Darwin': 'darwin', 'Windows': 'windows'}[platform.system()]
    arch = {'x86_64': 'amd64', 'amd64': 'amd64', 'arm64': 'arm64', 'aarch64': 'arm64'}[platform.machine().lower()]
    freeze = load(ROOT / 'docs/validation/runner-readiness-ten-project-pass/provisional-candidate-freeze.json')
    cell = next(row for row in freeze['cells'] if row['host'] == host and row['architecture'] == arch)
    archive = args.archive or ROOT / cell['archive_local_only']
    archive = archive if archive.is_absolute() else ROOT / archive
    if '..' in archive.parts:
        raise RuntimeError('private archive traversal')
    archive.relative_to(RAW)
    current = archive
    while current != RAW:
        if current.is_symlink() or getattr(current, 'is_junction', lambda: False)():
            raise RuntimeError('linked private archive path')
        current = current.parent
    archive.resolve(strict=True).relative_to(RAW.resolve())
    if archive.stat().st_size != cell['archive_bytes'] or sha256(archive) != cell['archive_sha256']:
        raise RuntimeError('private archive differs from frozen bytes')
    base = 'playtestr_' + freeze['version'].removeprefix('v') + '_' + host + '_' + arch
    binary_name = 'playtestr' + ('.exe' if os.name == 'nt' else '')
    expected = {base + '/' + name for name in [binary_name, 'LICENSE', 'README.md', 'THIRD_PARTY_NOTICES.md']}
    root = RAW / 'private-install/provisional-v1' / (host + '-' + arch)
    current = root.parent
    while current != RAW:
        if current.is_symlink() or getattr(current, 'is_junction', lambda: False)():
            raise RuntimeError('linked private installation ancestor')
        current = current.parent
    root.parent.mkdir(parents=True, exist_ok=True)
    root.mkdir(exist_ok=False)
    files = {}

    def save(name, data, executable):
        if name not in expected or name in files or len(data) > 32*1024**2:
            raise RuntimeError('unexpected private archive payload')
        target = root / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes(data)
        if os.name != 'nt':
            target.chmod(0o755 if executable else 0o644)
        files[name] = sha256(target)

    if os.name == 'nt':
        with zipfile.ZipFile(archive) as stream:
            if len(stream.infolist()) != 4:
                raise RuntimeError('private archive entry bound')
            for member in stream.infolist():
                if member.file_size > 32*1024**2:
                    raise RuntimeError('private archive member bound')
                save(member.filename, stream.read(member), member.filename == base + '/' + binary_name)
    else:
        with tarfile.open(archive, 'r:gz') as stream:
            entries = stream.getmembers()
            if len(entries) != 4:
                raise RuntimeError('private archive entry bound')
            for member in entries:
                executable = member.name == base + '/' + binary_name
                if not member.isfile() or member.size > 32*1024**2 or member.mode != (0o755 if executable else 0o644):
                    raise RuntimeError('private archive member type/bound/permissions')
                save(member.name, stream.extractfile(member).read(member.size+1), executable)
    binary = root / base / binary_name
    if set(files) != expected or sha256(binary) != cell['binary_sha256']:
        raise RuntimeError('private installed binary differs')
    env = dict(os.environ)
    for name in ['TEMP', 'TMP', 'TMPDIR']:
        env[name] = str(RAW / 'tmp')
    version = await execute([binary, '--version'], 'core', 'exact-provisional-extracted-version',
                            env=env, timeout=30, campaign=Campaign())
    if version['output'].strip() != 'playtestr ' + freeze['version']:
        raise RuntimeError('private installed version differs')
    help_result = await execute([binary, '--help'], 'core', 'exact-provisional-extracted-help',
                               env=env, timeout=30, campaign=Campaign())
    immutable_json(root / 'installation.json', dict(source_revision=freeze['source_revision'],
                   version=freeze['version'], host=host, architecture=arch, archive_sha256=sha256(archive),
                   binary=binary.relative_to(ROOT).as_posix(), binary_sha256=sha256(binary), files=files,
                   version_attempt=version['id'], help_attempt=help_result['id'],
                   full_install_upgrade_rollback_qualification=False))
    print('Exact provisional candidate extracted:', binary.relative_to(ROOT))


if __name__ == '__main__':
    asyncio.run(main())
