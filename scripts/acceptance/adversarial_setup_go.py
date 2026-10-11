"""Acquire and build a pinned Go application using only campaign-owned caches."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
from adversarial_process import ROOT, DOC, run


def build(app, project, *, output=None):
    identity_path = app / 'runtime.json'
    identity = json.loads(identity_path.read_text(encoding='utf-8')) if identity_path.exists() else {}
    env = dict(os.environ)
    for name, folder in [('GOCACHE', 'go-build-cache'), ('GOMODCACHE', 'go-mod-cache'),
                         ('GOPATH', 'go-path'), ('GOTMPDIR', 'go-tmp')]:
        path = app / folder
        path.mkdir(exist_ok=True)
        env[name] = str(path)
    # Avoid automatically acquiring an unreviewed toolchain into a user cache.
    env['GOTOOLCHAIN'] = 'local'
    executable = app / 'bin' / (project + ('.exe' if os.name == 'nt' else ''))
    executable.parent.mkdir(exist_ok=True)
    go = os.environ.get('PLAYTESTR_GO', 'go')
    version = run([go, 'version'], project, 'target-go-version', env=env, timeout=15)['output'].strip()
    run([go, 'build', '-trimpath', '-o', executable, '.'], project,
        'target-build', env=env, cwd=app / 'source', timeout=600)
    identity.update(toolchain=version, binary=str(executable),
                    binary_sha256=hashlib.sha256(executable.read_bytes()).hexdigest())
    identity_path.write_text(json.dumps(identity, indent=2) + '\n', encoding='utf-8')
    return identity


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True, choices=['lf', 'superfile', 'glow'])
    parser.add_argument('--native-source', action='store_true')
    parser.add_argument('--rebuild', action='store_true')
    args = parser.parse_args()
    project = args.project
    candidate = next(c for c in json.loads((DOC / 'candidates.json').read_text(encoding='utf-8'))
                     if c['repo'].split('/')[-1] == project and c['disposition'] == 'selected')
    root = ROOT / '.cache/ten-new-project-apps'
    app = Path('/var/tmp') / ('playtestr-adversarial-' + project) if args.native_source else root / project
    root.mkdir(parents=True, exist_ok=True)
    if not args.rebuild:
        for marker in root.glob('*/task-owned.json'):
            owner = json.loads(marker.read_text(encoding='utf-8'))
            if owner['project'] != project:
                raise RuntimeError('Another owned application remains active: ' + owner['project'])
        if os.name != 'nt':
            for marker in Path('/var/tmp').glob('playtestr-adversarial-*/task-owned.json'):
                if json.loads(marker.read_text(encoding='utf-8'))['project'] != project:
                    raise RuntimeError('Another exploratory application remains active')
    owner = dict(campaign='ten-new-project-adversarial-pass', workspace=str(ROOT),
                 project=project, source_sha=candidate['sha'])
    if app.is_symlink() or getattr(app, 'is_junction', lambda: False)():
        raise RuntimeError('Refuse linked application ownership root')
    app.mkdir(parents=True, exist_ok=True)
    marker = app / 'task-owned.json'
    if marker.exists() and json.loads(marker.read_text(encoding='utf-8')) != owner:
        raise RuntimeError('Unknown existing application ownership')
    if not marker.exists() and any(app.iterdir()):
        raise RuntimeError('Refuse adopting nonempty unmarked directory')
    marker.write_text(json.dumps(owner) + '\n', encoding='utf-8')
    source = app / 'source'
    if not source.exists():
        run(['git', 'clone', '--filter=blob:none', '--no-checkout', candidate['url'] + '.git', source],
            project, 'source-acquisition', timeout=180)
        run(['git', '-C', source, 'checkout', '--detach', candidate['sha']],
            project, 'pinned-checkout', timeout=180)
    if subprocess.check_output(['git', '-C', source, 'rev-parse', 'HEAD'], text=True).strip() != candidate['sha']:
        raise RuntimeError('Source identity differs from approved pin')
    if not args.rebuild and subprocess.check_output(
            ['git', '-C', source, 'status', '--porcelain', '--untracked-files=no'], text=True).strip():
        raise RuntimeError('Pristine setup cannot adopt mutated source')
    package = DOC / project
    package.mkdir(parents=True, exist_ok=True)
    license_path = next((p for p in [source / 'LICENSE', source / 'LICENSE.md', source / 'LICENSE.txt'] if p.is_file()), None)
    if license_path is None:
        raise RuntimeError('Reviewed license file missing')
    (package / 'UPSTREAM-LICENSE.txt').write_bytes(license_path.read_bytes())
    runtime = app / 'runtime.json'
    runtime.write_text(json.dumps(dict(source=candidate['sha'], native_host=platform.platform(),
        app=str(app), source_path=str(source), path=str(app / 'bin'), editable=False), indent=2) + '\n', encoding='utf-8')
    identity = build(app, project)
    if os.environ.get('GITHUB_PATH'):
        with Path(os.environ['GITHUB_PATH']).open('a',encoding='utf-8') as path_file:
            path_file.write(str(app/'bin')+'\n')
    for name in ['go.mod', 'go.sum']:
        if (source / name).is_file():
            (package / ('target-' + name + '.txt')).write_bytes((source / name).read_bytes())
    print(json.dumps(identity, indent=2))


if __name__ == '__main__':
    main()
