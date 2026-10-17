"""Workspace-owned immutable records for runner-readiness work, not admission proof."""
import hashlib
import json
import os
from pathlib import Path
import platform
import uuid

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'artifacts/runner-readiness-ten-project-pass'


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(65536):
            digest.update(block)
    return digest.hexdigest()


def immutable_json(path, value):
    """Publish a complete exclusive record; interrupted files stay visibly partial."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(value, sort_keys=True, ensure_ascii=True, indent=2)+'\n').encode()
    temporary = path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.partial')
    with temporary.open('xb') as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        os.link(temporary, path)
    finally:
        temporary.unlink()


def fixture_inputs(base,relative):
    """Collect only the selected fixture, refusing links before traversal."""
    base=Path(base).resolve();base.relative_to(ROOT)
    selected=base/relative
    selected.resolve(strict=True).relative_to(base)
    current=selected
    while current!=base:
        if current.is_symlink() or getattr(current,'is_junction',lambda:False)():raise ValueError('linked fixture identity')
        current=current.parent
    pending=[selected];files=[];directories=[selected.relative_to(ROOT).as_posix()];count=0
    while pending:
        directory=pending.pop()
        for entry in directory.iterdir():
            count+=1
            if count>2000:raise ValueError('fixture identity count bound')
            if entry.is_symlink() or getattr(entry,'is_junction',lambda:False)():raise ValueError('linked fixture identity')
            if entry.is_dir():pending.append(entry);directories.append(entry.relative_to(ROOT).as_posix())
            elif entry.is_file():files.append(entry)
            else:raise ValueError('special fixture identity')
    return files,directories


class Campaign:
    def __init__(self, raw=RAW):
        self.raw = Path(raw).resolve()
        self.raw.relative_to(ROOT)
        self.raw.mkdir(parents=True, exist_ok=True)
        # Downloaded SDK/target Go sources are evidence, not packages in the
        # Playtestr module. A nested module keeps ordinary ./... checks scoped.
        boundary = self.raw/'go.mod'
        module = b'module playtestr.invalid/runner-readiness-artifacts\n\ngo 1.25.0\n'
        try:
            with boundary.open('xb') as stream:
                stream.write(module)
        except FileExistsError:
            if boundary.read_bytes() != module:
                raise ValueError('unexpected campaign module boundary')

    def append(self, row):
        if set(('id', 'event', 'project', 'label'))-row.keys():
            raise ValueError('incomplete event')
        if len(row['id']) != 32 or any(c not in '0123456789abcdef' for c in row['id']):
            raise ValueError('invalid attempt id')
        if row['event'] not in {'started', 'identified', 'launched', 'finished'}:
            raise ValueError('invalid event')
        row = dict(row, schema_version=1, campaign='runner-readiness-ten-project-pass',phase='development')
        immutable_json(self.raw/'events'/(row['id']+'-'+row['event']+'.json'), row)

    def identity(self, project, argv):
        paths = [ROOT/'go.mod', ROOT/'go.sum']
        if (self.raw/'toolchain/sdk.json').is_file():paths.append(self.raw/'toolchain/sdk.json')
        for directory in ['scripts/acceptance','scripts/ci']:
            paths.extend((ROOT/directory).rglob('*.py'))
        paths.extend((ROOT/'schema').glob('*.json'))
        directories=[]
        values=list(map(str,argv))
        if len(values)>1 and values[1]=='record' and '--output' in values and '--fixture' in values:
            output=Path(values[values.index('--output')+1])
            if not output.is_absolute():output=ROOT/output
            selected,folders=fixture_inputs(output.parent,values[values.index('--fixture')+1])
            paths.extend(selected);directories.extend(folders)
        if Path(str(argv[0])).name in {'go', 'go.exe', 'powershell', 'powershell.exe'}:
            for directory in ['internal', 'cmd']:
                paths.extend((ROOT/directory).rglob('*.go'))
        for argument in argv:
            path = Path(str(argument))
            if not path.is_absolute():
                path = ROOT/path
            if path.is_file() and path.resolve().is_relative_to(ROOT):
                paths.append(path)
                if path.suffix=='.json' and path.stat().st_size<=1_000_000:
                    try:spec=json.loads(path.read_text(encoding='utf-8-sig'))
                    except (ValueError,UnicodeError):continue
                    if isinstance(spec,dict) and spec.get('version') in {1,2,3} and isinstance(spec.get('steps'),list):
                        command=spec.get('command')
                        if isinstance(command,list) and command and isinstance(command[0],str):
                            executable=Path(command[0])
                            if not executable.is_absolute() and any(c in command[0] for c in '/\\'):
                                executable=(path.parent if spec['version']>=2 else ROOT)/executable
                            if executable.is_absolute() and executable.is_file() and executable.resolve().is_relative_to(ROOT):
                                paths.append(executable)
                        for step in spec['steps']:
                            if isinstance(step,dict) and isinstance(step.get('snapshot'),str):
                                baseline=(path.parent/'snapshots'/step['snapshot']).resolve()
                                if not baseline.is_relative_to(path.parent.resolve()):raise ValueError('baseline identity escapes package')
                                if baseline.is_file():paths.append(baseline)
                        fixture=spec.get('workspace',{}).get('fixture') if isinstance(spec.get('workspace'),dict) else None
                        if fixture:
                            selected,folders=fixture_inputs(path.parent,fixture)
                            paths.extend(selected);directories.extend(folders)
        target=self.raw/'active'/project
        if (target/'task-owned.json').is_file():
            paths.append(target/'task-owned.json')
            if (target/'acquisition.json').is_file():paths.append(target/'acquisition.json')
            if (target/'build.json').is_file():paths.append(target/'build.json')
            if (target/'runtime.json').is_file():paths.append(target/'runtime.json')
            if project=='plop':
                paths.extend((target/'src/packages/plop/src').rglob('*.js'))
                paths.extend((target/'src/packages/plop/bin').rglob('*.js'))
                paths.extend((target/'src/packages/node-plop/src').rglob('*.js'))
                paths=[p for p in paths if 'node_modules' not in p.relative_to(ROOT).parts]
                paths.append(target/'src/yarn.lock')
            elif project=='poetry':
                paths.extend((target/'src/src/poetry').rglob('*.py'))
                paths.extend([target/'src/pyproject.toml',target/'src/poetry.lock'])
                if (target/'wheels.json').is_file():paths.append(target/'wheels.json')
            elif project=='papis':
                paths.extend((target/'src/papis').rglob('*.py'))
                paths.append(target/'src/pyproject.toml')
                if (target/'wheels.json').is_file():paths.append(target/'wheels.json')
                paths.extend((target/'wheel-manifests').glob('*.json'))
                if (target/'dependency-review').is_dir():
                    paths.extend(p for p in (target/'dependency-review').rglob('*') if p.is_file())
            elif project=='rubygems':
                paths.extend(p for p in (target/'src/lib').rglob('*') if p.is_file())
                paths.extend(p for p in (target/'src/exe').iterdir() if p.is_file())
                paths.append(target/'src/bundler.gemspec')
            elif project=='edit':
                paths.extend(p for p in (target/'src').rglob('*') if p.is_file() and
                    (p.suffix in {'.rs','.toml','.lock','.rc','.manifest'} or p.name=='LICENSE'))
                if (target/'dependencies.json').is_file():paths.append(target/'dependencies.json')
                if (target/'build.json').is_file():
                    build=json.loads((target/'build.json').read_text())
                    binary=target/build['binary_relative_path']
                    binary.resolve(strict=True).relative_to(target.resolve())
                    if binary.is_symlink() or getattr(binary,'is_junction',lambda:False)():raise ValueError('linked editor binary')
                    paths.append(binary)
            elif project=='fff':
                for name in ['fff','Makefile','LICENSE.md']:
                    source=target/'src'/name
                    if source.is_symlink() or getattr(source,'is_junction',lambda:False)():raise ValueError('linked shell target source')
                    if source.is_file():
                        source.resolve(strict=True).relative_to(target.resolve())
                        paths.append(source)
            elif project=='vis':
                paths.extend(p for p in (target/'src').rglob('*') if p.is_file() and
                    (p.suffix in {'.c','.h','.inc','.mk'} or p.name in {'configure','Makefile','LICENSE'}))
                if (target/'build.json').is_file():
                    build=json.loads((target/'build.json').read_text())
                    binary=target/build['binary_relative_path']
                    binary.resolve(strict=True).relative_to(target.resolve())
                    if binary.is_symlink() or getattr(binary,'is_junction',lambda:False)():raise ValueError('linked native editor binary')
                    paths.append(binary)
        if any(p.stat().st_size>128*1024*1024 for p in paths):raise ValueError('identity file byte bound')
        identity = {'project': project, 'host': platform.system(), 'architecture': platform.machine(),
                    'fixture_directories':sorted(set(directories)),
                    'files': {p.relative_to(ROOT).as_posix(): sha256(p) for p in sorted(set(paths))}}
        data = (json.dumps(identity, sort_keys=True, ensure_ascii=True, indent=2)+'\n').encode()
        digest = hashlib.sha256(data).hexdigest()
        path = self.raw/'identities'/(digest+'.json')
        try:
            immutable_json(path, identity)
        except FileExistsError:
            if path.read_bytes() != data:
                raise ValueError('identity collision')
        return {'sha256': digest, 'manifest': str(path.relative_to(self.raw))}

    def attempts(self):
        directory = self.raw/'events'
        if any(directory.glob('*.partial')):
            raise ValueError('interrupted event publication')
        attempts = {}
        for path in sorted(directory.glob('*.json')):
            row = json.loads(path.read_text(encoding='utf-8'))
            if path.name != row['id']+'-'+row['event']+'.json':
                raise ValueError('event filename identity mismatch')
            events = attempts.setdefault(row['id'], {})
            if row['event'] in events:
                raise ValueError('duplicate event')
            events[row['event']] = row
        for events in attempts.values():
            if not {'started', 'finished'} <= events.keys():
                raise ValueError('incomplete attempt')
            if 'identified' not in events:
                finished=events['finished']
                if ('launched' in events or finished.get('category')!='harness_error'
                    or finished.get('harness_cleanup')!='not_started'
                    or finished.get('exit_code') is not None):
                    raise ValueError('missing prelaunch identity')
                # A complete rejected setup still belongs in the denominator.
                # It has no qualifying identity and cannot earn execution credit.
            if 'launched' not in events:
                finished=events['finished']
                if (finished.get('category') not in {'harness_error','harness_timeout','harness_cancelled'}
                    or finished.get('harness_cleanup')!='not_started'
                    or finished.get('exit_code') is not None):
                    raise ValueError('missing launch witness')
            if len({(r['project'], r['label']) for r in events.values()}) != 1:
                raise ValueError('attempt identity mismatch')
        return attempts
