"""Bounded engineering commands in the explicitly invoked next-twenty campaign.

Historical readiness helpers retain their original roots and default behavior.
This adapter reuses their process lifecycle and exclusive event publication.
"""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True

from adversarial_process import execute
from readiness_evidence import Campaign, ROOT, immutable_json, sha256

NAME = 'runner-readiness-next-twenty-project-pass'
RAW = ROOT / 'artifacts' / NAME
DOC = ROOT / 'docs/validation' / NAME


class NextCampaign(Campaign):
    def __init__(self, raw=RAW, *, phase=None):
        selected = raw.resolve()
        selected.relative_to(RAW.resolve())
        super().__init__(selected, phase=phase)

    def append(self, row):
        if not {'id', 'event', 'project', 'label'} <= row.keys():
            raise ValueError('incomplete event')
        if len(row['id']) != 32 or any(c not in '0123456789abcdef' for c in row['id']):
            raise ValueError('invalid attempt id')
        if row['event'] not in {'started', 'identified', 'launched', 'finished'}:
            raise ValueError('invalid event')
        immutable_json(self.raw/'events'/(row['id']+'-'+row['event']+'.json'),
                       dict(row, schema_version=1, campaign=NAME, phase=self.phase))

    def identity(self, project, argv):
        base=super().identity(project,argv)
        target=self.raw/'active'/project
        if not target.exists():
            return base
        target.resolve(strict=True).relative_to(self.raw/'active')
        if target.is_symlink() or getattr(target,'is_junction',lambda:False)():
            raise ValueError('linked target identity root')
        files={}
        for name in ['task-owned.json','acquisition.json','runtime.json','build.json','wheels.json','dependency-review.json','launch-runtime-catalog.json']:
            path=target/name
            if path.is_file():files[path.relative_to(ROOT).as_posix()]=sha256(path)
        source=target/'src'
        count=0;total=0
        if source.exists():
            for path in sorted(source.rglob('*')):
                if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
                    raise ValueError('linked actual source identity')
                if not path.is_file():continue
                count+=1;total+=path.stat().st_size
                if count>10000 or total>64*1024**2:raise ValueError('source identity bound')
                files[path.relative_to(ROOT).as_posix()]=sha256(path)
        executable=Path(str(argv[0]))
        if executable.is_file() and executable.resolve().is_relative_to(target):
            files[executable.relative_to(ROOT).as_posix()]=sha256(executable)
        runtime=target/'runtime.json'
        if runtime.is_file():
            value=json.loads(runtime.read_text())
            kind=value.get('kind','python')
            if kind not in {'python','node'}:raise ValueError('unreviewed runtime executable kind')
            executable=Path(value[kind])
            executable.resolve(strict=True).relative_to(target)
            if executable.is_symlink() or getattr(executable,'is_junction',lambda:False)():raise ValueError('linked runtime executable')
            if sha256(executable)!=value[kind+'_sha256']:raise ValueError('actual owned '+kind+' executable changed')
            files[executable.relative_to(ROOT).as_posix()]=value[kind+'_sha256']
        catalog=dict(schema_version=1,project=project,files=files,
            dependency_scope='Installed dependency inventory must additionally be verified before/after each batch; no summary-only runtime credit')
        encoded=(json.dumps(catalog,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
        digest=hashlib.sha256(encoded).hexdigest()
        path=self.raw/'identities/catalogs'/(digest+'.json')
        try:immutable_json(path,catalog)
        except FileExistsError:
            if path.read_bytes()!=encoded:raise ValueError('target identity collision')
        manifest=dict(schema_version=1,project=project,base=base,
            target_catalog=dict(manifest=path.relative_to(self.raw).as_posix(),sha256=digest))
        encoded=(json.dumps(manifest,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
        digest=hashlib.sha256(encoded).hexdigest();path=self.raw/'identities'/(digest+'.json')
        try:immutable_json(path,manifest)
        except FileExistsError:
            if path.read_bytes()!=encoded:raise ValueError('combined identity collision')
        return dict(manifest=path.relative_to(self.raw).as_posix(),sha256=digest)


def owned_environment():
    env = dict(os.environ)
    env.update(PYTHONIOENCODING='utf-8', PYTHONDONTWRITEBYTECODE='1',
               GODEBUG='http2client=0')
    # APPDATA remains the existing authentication source for read-only gh calls.
    # Target launches must use an additional explicit isolated target environment.
    for name, folder in [('TEMP', 'tmp'), ('TMP', 'tmp'), ('TMPDIR', 'tmp'),
                         ('GOTMPDIR', 'tmp'), ('GOCACHE', 'go-cache'),
                         ('GOPATH', 'gopath'), ('GOMODCACHE', 'gopath/pkg/mod'),
                         ('XDG_CACHE_HOME', 'gh-cache'),
                         ('LOCALAPPDATA', 'gh-cache')]:
        path = RAW/folder
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    cache = RAW/'shell-cache/module-analysis'
    cache.parent.mkdir(parents=True, exist_ok=True)
    env['PSModuleAnalysisCachePath'] = str(cache)
    return env


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--label', required=True)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--expected', type=int, default=0)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.command
    if argv and argv[0] == '--':
        argv = argv[1:]
    if not argv or not 1 <= args.timeout <= 1200:
        parser.error('command and bounded timeout required')
    try:
        result = asyncio.run(execute(argv, 'core', args.label, cwd=ROOT,
                                    env=owned_environment(), timeout=args.timeout,
                                    expected=args.expected, campaign=NextCampaign()))
    except Exception as error:
        directory=getattr(error,'evidence_directory',None)
        if directory:
            path=Path(directory).resolve(strict=True)
            path.relative_to(RAW.resolve())
            console=path/'console.log'
            if console.is_file():
                with console.open('rb') as stream:
                    stream.seek(max(0,console.stat().st_size-12000))
                    print(stream.read(12000).decode('utf-8',errors='replace'),flush=True)
            print('Evidence:',path.relative_to(ROOT),flush=True)
        raise
    print(result['output'][-12000:])
    print('Evidence:', result['directory'].relative_to(ROOT))


if __name__ == '__main__':
    main()
