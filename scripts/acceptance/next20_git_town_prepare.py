"""Verify and build the exact Git Town pin inside the campaign-owned root."""
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tarfile

from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = 'git-town'
REPOSITORY = 'git-town/git-town'
PIN = '8d039892574d4852e1843020c31d423234042e78'


def run(argv, *, cwd, env, timeout=300):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                           timeout=timeout, check=False)
    if result.returncode:
        raise RuntimeError(f'{argv[0]} exited {result.returncode}: '
                           f'{result.stderr[-4096:].decode("utf-8", "replace")}')
    return result


def main():
    target = RAW / 'active' / PROJECT
    source = target / 'src'
    binary_dir = target / 'bin'
    home = target / 'home'
    temp = target / 'tmp'
    for path in (target, binary_dir, home, temp, home / 'appdata',
                 home / 'localappdata', home / 'go-cache', target / 'go-mod-cache'):
        path.mkdir(parents=True, exist_ok=True)
    marker = target / 'task-owned.json'
    ownership = dict(workspace=str(ROOT), campaign='runner-readiness-next-twenty-project-pass',
                     project=REPOSITORY, slug=PROJECT, pin=PIN, source_only=False)
    if marker.exists():
        if json.loads(marker.read_text(encoding='utf-8')) != ownership:
            raise ValueError('Git Town target ownership differs')
    else:
        immutable_json(marker, ownership)

    provenance_path = DOC / PROJECT / 'source-provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    if provenance.get('repository') != REPOSITORY or provenance.get('pin') != PIN:
        raise ValueError('tracked source provenance pin differs')
    if not source.is_dir() or source.is_symlink() or getattr(source, 'is_junction', lambda: False)():
        raise ValueError('pinned Git Town checkout is missing or linked')
    commit = run(['git', 'rev-parse', 'HEAD'], cwd=source, env=os.environ).stdout.decode().strip()
    if commit != PIN:
        raise ValueError('Git Town checkout commit differs from declared immutable pin')
    dirty = run(['git', 'status', '--porcelain=v1', '--untracked-files=no'],
                cwd=source, env=os.environ).stdout
    if dirty:
        if os.name != 'nt':
            raise ValueError('Git Town pinned checkout has tracked modifications: ' +
                             dirty.decode('utf-8', 'replace')[:4096])
        # GitHub's Windows checkout can leave Go files CRLF-converted even
        # after core.autocrlf is disabled and checkout-index is forced. Restore
        # the already reviewed commit from Git's archive bytes, writing only
        # paths declared by the immutable provenance manifest.
        expected = provenance['files']
        archive_path = target / 'pinned-source.tar'
        with archive_path.open('wb') as archive_file:
            archived = subprocess.run(['git', 'archive', '--format=tar', PIN],
                cwd=source, env=os.environ, stdout=archive_file,
                stderr=subprocess.PIPE, timeout=120, check=False)
        if archived.returncode:
            archive_path.unlink(missing_ok=True)
            raise RuntimeError('Git Town canonical source archive failed: ' +
                archived.stderr[-2048:].decode('utf-8', 'replace'))
        restored = set()
        with tarfile.open(archive_path, 'r:') as tar:
            members = tar.getmembers()
            if len(members) != len(expected):
                raise ValueError('Git Town canonical archive member count differs')
            for member in members:
                name = Path(member.name).as_posix()
                if name not in expected or name in restored or not member.isfile():
                    raise ValueError('Git Town canonical archive contains an unreviewed member: ' + name)
                payload = tar.extractfile(member).read()
                destination = source / Path(name)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(payload)
                restored.add(name)
        archive_path.unlink()
        if restored != set(expected):
            raise ValueError('Git Town canonical archive did not restore every reviewed source file')
        dirty = run(['git', 'status', '--porcelain=v1', '--untracked-files=no'],
                    cwd=source, env=os.environ).stdout
    if dirty:
        raise ValueError('Git Town pinned checkout has tracked modifications: ' +
                         dirty.decode('utf-8', 'replace')[:4096])

    expected = provenance['files']
    actual = {}
    for path in sorted(source.rglob('*')):
        if '.git' in path.relative_to(source).parts:
            continue
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('Git Town source contains an unreviewed link')
        if path.is_file():
            relative = path.relative_to(source).as_posix()
            if relative not in expected:
                raise ValueError('unexpected Git Town source file: ' + relative)
            actual[relative] = sha256(path)
    if actual != expected:
        mismatched = next((name for name in sorted(set(actual) | set(expected))
                           if actual.get(name) != expected.get(name)), 'unknown')
        raise ValueError('Git Town source differs from canonical pinned provenance: ' + mismatched)
    immutable_json(target / 'acquisition.json', dict(
        repository=REPOSITORY, pin=PIN, acquisition_method='pinned Git checkout',
        source_archive_sha256='2a47fe65b7f21f6a99bfeefd00dfeffce394dd7db733b47e5b87904c9947ab8a',
        source_provenance_sha256=sha256(provenance_path), source_commit=commit,
        source_files=len(actual), source_tree_sha256=provenance['primary_tree_sha256'],
        network_module_resolution=False, build_hooks_executed=False))

    go_version = run(['go', 'version'], cwd=ROOT, env=os.environ, timeout=20).stdout.decode().strip()
    env = dict(os.environ)
    env.update(GOTOOLCHAIN='local', GOWORK=str(source / 'go.work'), GOPROXY='off',
               GOSUMDB='off', CGO_ENABLED='0', GOENV='off',
               GOMODCACHE=str(target / 'go-mod-cache'), GOCACHE=str(home / 'go-cache'),
               GOPATH=str(home / 'go-path'), HOME=str(home), USERPROFILE=str(home),
               APPDATA=str(home / 'appdata'), LOCALAPPDATA=str(home / 'localappdata'),
               TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    is_windows = os.name == 'nt'
    executable = binary_dir / ('git-town.exe' if is_windows else 'git-town')
    build_command = ['go', 'build', '-mod=vendor', '-trimpath', '-o', str(executable), '.']
    result = run(build_command, cwd=source, env=env)
    if not executable.is_file() or executable.is_symlink():
        raise ValueError('native Git Town executable is missing or linked')
    binary_sha = sha256(executable)
    version = run([str(executable), '--version'], cwd=source, env=env, timeout=20).stdout.decode().strip()
    if version != 'Git Town 24.1.0':
        raise ValueError('native Git Town version output differs: ' + version)
    receipt = dict(schema_version=1, project=PROJECT, pin=PIN,
        runtime_kind='native', binary_relative_path=executable.relative_to(target).as_posix(),
        binary_sha256=binary_sha, build_command='go build -mod=vendor -trimpath -o <owned-bin>/git-town .',
        working_directory='src', go_version=go_version, host_os=platform.system().lower(),
        host_arch=platform.machine().lower(), toolchain_settings={key: env[key] for key in
            ['GOTOOLCHAIN','GOWORK','GOPROXY','GOSUMDB','CGO_ENABLED','GOMODCACHE','GOCACHE']},
        dependency_mode='pinned go.work workspace vendor only', network_module_resolution='disabled',
        automatic_toolchain_download='disabled', build_hooks_executed=False,
        build_succeeded=True, stdout_tail=result.stdout.decode('utf-8','replace')[-2048:],
        stderr_tail=result.stderr.decode('utf-8','replace')[-2048:])
    immutable_json(target / 'build.json', receipt)
    runtime = dict(schema_version=1, kind='native', project=PROJECT, pin=PIN,
        native=str(executable.resolve()), native_sha256=binary_sha,
        binary=executable.relative_to(target).as_posix(), binary_sha256=binary_sha,
        version='24.1.0')
    immutable_json(target / 'runtime.json', runtime)
    print('Verified pinned Git Town source files:', len(actual), 'built:', binary_sha,
          'version:', version)


if __name__ == '__main__':
    main()
