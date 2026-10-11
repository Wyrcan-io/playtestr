"""Install a digest-pinned task-only Go toolchain for WSL exploration."""
import hashlib
import json
import os
from pathlib import Path
import tarfile
import urllib.request
from adversarial_process import ROOT, DOC, run


def main():
    if os.name == 'nt':
        raise RuntimeError('Run this installer on the exploratory Linux host')
    version = '1.27.0'
    digest = '675c26c449cbb18fc24b74650de1eabbae6e16f64326fd85a283fb3b58280685'
    size = 70523269
    root = Path('/var/tmp/playtestr-adversarial-runtime')
    owner = dict(campaign='ten-new-project-adversarial-pass', workspace=str(ROOT),
                 toolchain='go' + version, archive_sha256=digest)
    if root.is_symlink():
        raise RuntimeError('Refuse linked runtime directory')
    root.mkdir(exist_ok=True)
    marker = root / 'task-runtime-owned.json'
    if marker.exists():
        if json.loads(marker.read_text()) != owner:
            raise RuntimeError('Unknown existing runtime ownership')
    elif any(root.iterdir()):
        raise RuntimeError('Refuse nonempty unmarked runtime directory')
    marker.write_text(json.dumps(owner) + '\n')
    archive = root / ('go' + version + '.linux-amd64.tar.gz')
    url = 'https://go.dev/dl/' + archive.name
    if not archive.exists():
        with urllib.request.urlopen(url, timeout=60) as response, archive.open('xb') as output:
            total = 0
            while block := response.read(1024 * 1024):
                total += len(block)
                if total > size:
                    raise RuntimeError('Toolchain archive exceeds exact official size')
                output.write(block)
    if archive.stat().st_size != size or hashlib.sha256(archive.read_bytes()).hexdigest() != digest:
        raise RuntimeError('Toolchain archive differs from verified official manifest')
    executable = root / 'go/bin/go'
    if not executable.exists():
        with tarfile.open(archive) as tar:
            members = tar.getmembers()
            if len(members) > 50000 or sum(m.size for m in members) > 500 * 1024 * 1024:
                raise RuntimeError('Toolchain extraction bound')
            for member in members:
                name = Path(member.name)
                if name.is_absolute() or '..' in name.parts or name.parts[0] != 'go':
                    raise RuntimeError('Toolchain extraction path differs from official layout')
            tar.extractall(root, filter='data')
    result = run([executable, 'version'], 'core', 'exploratory-native-go-version', timeout=15)
    record = dict(owner, source='https://go.dev/dl/?mode=json&include=all',
                  downloaded_url=url, exact_archive_bytes=size, root=str(root),
                  actual_version=result['output'].strip(), evidence_id=result['id'],
                  qualification='WSL exploration; hosted native Linux remains required')
    (DOC / 'core/linux-exploratory-toolchain.json').write_text(json.dumps(record, indent=2) + '\n')
    print(str(executable))


if __name__ == '__main__':
    main()
