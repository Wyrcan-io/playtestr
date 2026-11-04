"""Create one credential-free synthetic Git Town repository fixture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = 'git-town'
FIXTURE = DOC / PROJECT / 'fixtures' / 'branch-repo'


def run(argv, cwd, env):
    result = subprocess.run(argv, cwd=cwd, env=env, capture_output=True,
                            timeout=30, check=False)
    if result.returncode:
        raise RuntimeError(f'{argv[0]} failed ({result.returncode}): '
                           f'{result.stderr[-4096:].decode("utf-8", "replace")}')
    return result.stdout


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--replace-fixture', action='store_true')
    parser.add_argument('--refresh-existing', action='store_true')
    args = parser.parse_args()
    target = RAW / 'active' / PROJECT
    marker = json.loads((target / 'task-owned.json').read_text())
    if marker['campaign'] != 'runner-readiness-next-twenty-project-pass' or marker['slug'] != PROJECT:
        raise ValueError('Git Town fixture target ownership differs')
    if not (target / 'build.json').is_file():
        raise ValueError('Git Town fixture requires the reviewed native build')
    manifest = target / 'fixture-source.json'
    if FIXTURE.exists():
        if args.refresh_existing:
            if not FIXTURE.is_dir() or FIXTURE.is_symlink() or getattr(FIXTURE, 'is_junction', lambda: False)():
                raise ValueError('linked Git Town fixture root')
            prior = target / 'fixture-source-v1.json'
            if prior.exists():
                old = json.loads(prior.read_text())
                if old.get('project') != PROJECT or old.get('source_pin') != marker['pin']:
                    raise ValueError('prior Git Town fixture manifest owner differs')
                if manifest.exists():
                    raise ValueError('both Git Town fixture manifests v1 and current exist')
            elif manifest.exists():
                manifest.replace(prior)
            else:
                raise ValueError('Git Town fixture has no exact prior manifest to preserve')
        elif not args.replace_fixture and (FIXTURE / '.git').exists():
            raise ValueError('Git Town repository fixture already exists; inspect it or use the exact refresh option')
        elif not args.replace_fixture:
            entries = {p.relative_to(FIXTURE).as_posix() for p in FIXTURE.rglob('*') if p.is_file()}
            if entries != {'README.md'} or (FIXTURE / 'README.md').read_bytes() != b'Synthetic Git Town repository.\n':
                raise ValueError('Git Town fixture seed differs from its one-file reviewed form')
        else:
            if FIXTURE.is_symlink() or getattr(FIXTURE, 'is_junction', lambda: False)():
                raise ValueError('linked Git Town fixture root')
            import shutil
            shutil.rmtree(FIXTURE)
        if args.replace_fixture and manifest.exists():
            prior = json.loads(manifest.read_text())
            if prior.get('project') != PROJECT or prior.get('source_pin') != marker['pin']:
                raise ValueError('Git Town fixture manifest owner differs')
            manifest.unlink()
    if not FIXTURE.exists():
        FIXTURE.mkdir(parents=True, exist_ok=True)
    home = target / 'home'
    temp = target / 'tmp'
    for path in (home, temp, home / 'config', home / 'cache', home / 'data', home / 'appdata'):
        path.mkdir(parents=True, exist_ok=True)
    global_config = home / 'empty.gitconfig'
    global_config.write_bytes(b'')
    env = {key: value for key, value in os.environ.items()
           if key.upper() in {'PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC',
                              'SYSTEMDRIVE', 'PROGRAMFILES', 'PROGRAMFILES(X86)', 'PROGRAMW6432'}}
    env.update(HOME=str(home), USERPROFILE=str(home), APPDATA=str(home / 'appdata'),
               LOCALAPPDATA=str(home / 'localappdata'), XDG_CONFIG_HOME=str(home / 'config'),
               XDG_CACHE_HOME=str(home / 'cache'), XDG_DATA_HOME=str(home / 'data'),
               TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp), GIT_CONFIG_NOSYSTEM='1',
               GIT_CONFIG_GLOBAL=str(global_config), GIT_TERMINAL_PROMPT='0',
               GIT_CEILING_DIRECTORIES=str(target), GIT_AUTHOR_NAME='Campaign Fixture',
               GIT_AUTHOR_EMAIL='fixture@example.invalid', GIT_COMMITTER_NAME='Campaign Fixture',
               GIT_COMMITTER_EMAIL='fixture@example.invalid',
               GIT_AUTHOR_DATE='2026-01-02T03:04:05+00:00',
               GIT_COMMITTER_DATE='2026-01-02T03:04:05+00:00')
    if os.name == 'nt':
        env['PATH'] = str(target / 'bin') + os.pathsep + env.get('PATH', '')
    else:
        env['PATH'] = str(target / 'bin') + os.pathsep + env.get('PATH', '')
    if not (FIXTURE / '.git').is_dir():
        template = target / 'empty-git-template'
        template.mkdir(exist_ok=True)
        run(['git', 'init', '--template=' + str(template), '--initial-branch=main'], FIXTURE, env)
        run(['git', 'config', 'core.filemode', 'false'], FIXTURE, env)
        run(['git', 'config', 'core.symlinks', 'false'], FIXTURE, env)
        run(['git', 'config', 'core.ignorecase', 'true'], FIXTURE, env)
        run(['git', 'config', 'user.name', 'Campaign Fixture'], FIXTURE, env)
        run(['git', 'config', 'user.email', 'fixture@example.invalid'], FIXTURE, env)
        run(['git', 'config', 'git-town.main-branch', 'main'], FIXTURE, env)
        (FIXTURE / 'README.md').write_bytes(b'Synthetic Git Town repository.\n')
        run(['git', 'add', 'README.md'], FIXTURE, env)
        run(['git', 'commit', '-m', 'synthetic initial commit'], FIXTURE, env)
        run(['git', 'branch', 'feat-blue'], FIXTURE, env)
    if args.refresh_existing:
        run(['git', '-c', 'safe.directory=' + str(FIXTURE.resolve()), 'config', '--local',
             'git-town-branch.feat-blue.parent', 'main'], FIXTURE, env)
    run(['git', 'config', 'git-town-branch.feat-blue.parent', 'main'], FIXTURE, env)
    head = (FIXTURE / '.git' / 'HEAD').read_bytes()
    if head != b'ref: refs/heads/main\n':
        raise ValueError('unexpected synthetic fixture HEAD bytes')
    if run(['git', 'remote'], FIXTURE, env).strip():
        raise ValueError('synthetic Git Town fixture unexpectedly has a remote')
    files = {}
    total = 0
    for path in sorted(FIXTURE.rglob('*')):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('linked Git Town fixture member')
        if path.is_file():
            data = path.read_bytes()
            total += len(data)
            files[path.relative_to(FIXTURE).as_posix()] = {
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    if total > 4 * 1024 * 1024 or len(files) > 5000:
        raise ValueError('synthetic Git Town fixture exceeds campaign bounds')
    immutable_json(manifest, dict(schema_version=1, project=PROJECT,
        repository='synthetic local repository', initial_branch='main',
        secondary_branch='feat-blue', remote_count=0, head_sha256=hashlib.sha256(head).hexdigest(),
        files=files, total_bytes=total, source_pin=marker['pin'],
        scope='Synthetic fixture only; no real remote, credential, user Git configuration, or forge token.'))
    print('Created credential-free Git Town fixture:', len(files), 'files,', total,
          'bytes; manifest', sha256(manifest))


if __name__ == '__main__':
    main()
