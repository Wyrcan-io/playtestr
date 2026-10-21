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
    def __init__(self, raw=RAW, *, phase=None, catalog_project=None):
        self.phase=phase or os.environ.get('READINESS_EVIDENCE_PHASE','development')
        if self.phase not in {'development','final-archive'}:
            raise ValueError('undeclared evidence phase')
        self.catalog_project=catalog_project or os.environ.get('READINESS_IDENTITY_CATALOG_PROJECT','')
        if self.catalog_project not in {'','rclone','hygen'}:
            raise ValueError('undeclared identity catalog project')
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
        row = dict(row, schema_version=1, campaign='runner-readiness-ten-project-pass',phase=self.phase)
        immutable_json(self.raw/'events'/(row['id']+'-'+row['event']+'.json'), row)

    def identity(self, project, argv):
        paths = [ROOT/'go.mod', ROOT/'go.sum']
        if (self.raw/'toolchain/sdk.json').is_file():paths.append(self.raw/'toolchain/sdk.json')
        for directory in ['scripts/acceptance','scripts/ci']:
            paths.extend((ROOT/directory).rglob('*.py'))
        paths.extend((ROOT/'schema').glob('*.json'))
        directories=[]
        runtime_executables={}
        input_links={}
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
            elif project in {'papis','frogmouth'}:
                paths.extend((target/'src'/project).rglob('*.py'))
                paths.append(target/'src/pyproject.toml')
                if (target/'runtime.json').is_file():
                    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8-sig'))
                    interpreter=Path(runtime['python'])
                    interpreter.resolve(strict=True).relative_to(target.resolve())
                    paths.append(interpreter)
                    launcher=interpreter.parent/(project+'.exe' if os.name=='nt' else project)
                    if launcher.is_file():
                        launcher.resolve(strict=True).relative_to(target.resolve())
                        paths.append(launcher)
                if (target/'wheels.json').is_file():paths.append(target/'wheels.json')
                paths.extend((target/'wheel-manifests').glob('*.json'))
                if (target/'dependency-review').is_dir():
                    paths.extend(p for p in (target/'dependency-review').rglob('*') if p.is_file())
            elif project=='hygen':
                for directory in ['dist','node_modules']:
                    paths.extend(p for p in (target/'src'/directory).rglob('*') if p.is_file() and
                        p.suffix in {'.js','.cjs','.mjs','.json','.node','.wasm'})
                paths.extend([target/'src/package.json',target/'src/yarn.lock'])
                paths.extend(p for p in (target/'src/src/templates').rglob('*') if p.is_file())
                paths.extend(p for p in (target/'bin').glob('*') if p.is_file())
                if (target/'dependencies.json').is_file():paths.append(target/'dependencies.json')
                if (target/'runtime.json').is_file():
                    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8-sig'))
                    node=Path(runtime['node'])
                    if node.name.lower() not in {'node','node.exe'}:raise ValueError('unexpected Hygen runtime executable')
                    runtime_executables['node']=sha256(node)
            elif project=='rclone':
                paths.extend(p for p in (target/'src').rglob('*') if p.is_file())
                if (target/'toolchain/sdk.json').is_file():paths.append(target/'toolchain/sdk.json')
                if (target/'build.json').is_file():
                    build=json.loads((target/'build.json').read_text(encoding='utf-8-sig'))
                    binary=target/build['binary_relative_path']
                    binary.resolve(strict=True).relative_to(target.resolve())
                    if binary.is_symlink() or getattr(binary,'is_junction',lambda:False)():raise ValueError('linked Rclone binary')
                    paths.append(binary)
                if (target/'runtime.json').is_file():
                    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8-sig'))
                    compiler=Path(runtime['go'])
                    compiler.resolve(strict=True).relative_to(target.resolve())
                    if compiler.is_symlink() or getattr(compiler,'is_junction',lambda:False)():raise ValueError('linked Rclone compiler')
                    paths.append(compiler)
                    runtime_executables['go']=sha256(compiler)
            elif project in {'old-helix','old-broot','old-yazi'}:
                review_path=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration'/project.removeprefix('old-')/'source-review.json'
                review=json.loads(review_path.read_text(encoding='utf-8-sig'))
                paths.append(review_path)
                paths.extend(target/'src'/name for name in review['reviewed_inputs'])
                for name in ['dependency-fetch-review.json','dependencies.json','toolchain.json']:
                    if (target/name).is_file():paths.append(target/name)
                if (target/'runtime.json').is_file():
                    runtime=json.loads((target/'runtime.json').read_text())
                    for key,field in [('rustc','rustc_path'),('cargo','cargo_path')]:
                        tool=Path(runtime[field]);resolved=tool.resolve(strict=True)
                        if resolved.is_relative_to(ROOT):paths.append(tool)
                        elif runtime.get('read_only_installed_prerequisites') is not True:
                            raise ValueError('undeclared external Rust prerequisite')
                        runtime_executables[key]=sha256(tool)
                paths.extend(p for p in (target/'cargo-home/registry/cache').rglob('*.crate') if p.is_file())
                if project=='old-yazi':
                    receipt=next((target/name for name in ['dependencies.json','dependency-fetch-review.json']
                                  if (target/name).is_file()),None)
                    if receipt is not None:
                        dependencies=json.loads(receipt.read_text(encoding='utf-8-sig'))
                        for name,row in dependencies.get('git_dependency',{}).get('files',{}).items():
                            dependency=target/name
                            dependency.resolve(strict=True).relative_to(target.resolve(strict=True))
                            if dependency.is_symlink():
                                from readiness_old_yazi_git import license_link
                                checkout=target/dependencies['git_dependency']['checkouts'][0]['root']
                                payload=license_link(dependency,checkout)
                                if hashlib.sha256(payload).hexdigest()!=row['sha256']:
                                    raise ValueError('locked Yazi Git license link changed')
                                input_links[dependency.relative_to(ROOT).as_posix()]=dict(target='../LICENSE',sha256=row['sha256'])
                                continue
                            if sha256(dependency)!=row['sha256']:
                                raise ValueError('locked Yazi Git dependency source changed')
                            paths.append(dependency)
                binary_name={'old-helix':'hx','old-broot':'broot','old-yazi':'yazi'}[project]
                binary=target/'bin'/(binary_name+('.exe' if os.name=='nt' else ''))
                if binary.is_file():paths.append(binary)
                paths.extend(p for p in (target/'bin/runtime').rglob('*') if p.is_file())
            elif project=='old-nnn':
                review_path=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/nnn/source-review.json'
                review=json.loads(review_path.read_text(encoding='utf-8-sig'));paths.append(review_path)
                paths.extend(target/'src'/name for name in review['reviewed_inputs'])
                binary=target/'bin/nnn'
                if binary.is_file():paths.append(binary)
                if (target/'runtime.json').is_file():
                    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8-sig'))
                    for name,row in runtime['tools'].items():runtime_executables[name]=sha256(Path(row['path']))
            elif project=='old-ranger':
                review_path=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/ranger/source-review.json'
                review=json.loads(review_path.read_text(encoding='utf-8-sig'));paths.append(review_path)
                paths.extend(target/'src'/name for name in review['reviewed_inputs'])
                launcher=target/'bin/ranger'
                if launcher.is_file():paths.append(launcher)
                if (target/'runtime.json').is_file():
                    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8-sig'))
                    for name,field in [('python','python_path'),('curses','curses_path'),('curses-extension','curses_extension_path')]:
                        tool=Path(runtime[field]);resolved=tool.resolve(strict=True)
                        if name=='python':
                            resolved.relative_to(target.resolve(strict=True))
                            if tool.is_symlink():raise ValueError('linked private Ranger interpreter')
                            paths.append(tool)
                        runtime_executables[name]=sha256(tool)
            elif project in {'old-lf','old-superfile','old-glow'}:
                original_project=project.removeprefix('old-')
                review_path=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration'/original_project/'source-review.json'
                review=json.loads(review_path.read_text(encoding='utf-8-sig'))
                paths.append(review_path)
                paths.extend(target/'src'/name for name in review['reviewed_inputs'])
                for name in ['toolchain/sdk.json','build.json','runtime.json']:
                    if (target/name).is_file():paths.append(target/name)
                compiler=target/'toolchain/go/bin'/('go.exe' if os.name=='nt' else 'go')
                if compiler.is_file():
                    paths.append(compiler);runtime_executables['go']=sha256(compiler)
                binary=target/'bin'/(original_project+'.exe' if os.name=='nt' else original_project)
                if binary.is_file():paths.append(binary)
            elif project in {'old-cookiecutter','old-copier'}:
                original_project=project.removeprefix('old-')
                review_path=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration'/original_project/'source-review.json'
                review=json.loads(review_path.read_text(encoding='utf-8-sig'))
                paths.append(review_path)
                paths.extend(target/'src'/name for name in review['reviewed_inputs'])
                for name in ['wheels.json','runtime-requirements.txt']:
                    if (target/name).is_file():paths.append(target/name)
                python=target/'venv'/('Scripts/python.exe' if os.name=='nt' else 'bin/python')
                if python.is_file():
                    if python.is_symlink() or getattr(python,'is_junction',lambda:False)():raise ValueError('linked owned Python')
                    paths.append(python);runtime_executables['python']=sha256(python)
                launcher=python.parent/(original_project+'.exe' if os.name=='nt' else original_project)
                if launcher.is_file():paths.append(launcher)
                sites=([target/'venv/Lib/site-packages'] if os.name=='nt' else list((target/'venv/lib').glob('python*/site-packages')))
                for site in sites:
                    if site.exists():
                        paths.extend(p for p in site.rglob('*') if p.is_file() and
                            (p.suffix in {'.py','.pyc','.pth','.so','.pyd'} or p.name in {'METADATA','entry_points.txt','RECORD'}))
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
        if runtime_executables:identity['runtime_executables']=runtime_executables
        if input_links:identity['input_links']=input_links
        if self.catalog_project==project:
            # Hash all actual files above before interning any shared catalog.
            # The catalog is content-addressed evidence, never a hash cache.
            references=[]
            target_prefix=target.relative_to(ROOT).as_posix()+'/'
            for scope in ['core','target']:
                selected={n:h for n,h in identity['files'].items() if
                    (scope=='core' and (n.startswith(('scripts/','schema/')) or n in {'go.mod','go.sum'})) or
                    (scope=='target' and n.startswith(target_prefix))}
                if not selected:continue
                payload=(json.dumps(dict(schema_version=1,files=selected),sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
                catalog_hash=hashlib.sha256(payload).hexdigest()
                catalog=self.raw/'identities/catalogs'/(catalog_hash+'.json')
                try:
                    immutable_json(catalog,dict(schema_version=1,files=selected))
                except FileExistsError:
                    if catalog.read_bytes()!=payload:raise ValueError('identity catalog collision')
                references.append(dict(scope=scope,manifest=catalog.relative_to(self.raw).as_posix(),sha256=catalog_hash))
                for name in selected:del identity['files'][name]
            identity['schema_version']=2
            identity['file_catalogs']=references
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
