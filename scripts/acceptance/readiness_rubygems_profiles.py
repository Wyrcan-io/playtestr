"""Declare native host contracts before running any ordinary target scenario."""
import base64
import json
import os
from pathlib import Path
import shutil
from readiness_evidence import RAW, immutable_json, sha256
from readiness_rubygems_cases import PACKAGE, rows
from readiness_rubygems_faults import contract_names

WINDOWS=os.name=='nt'


def main(target=None):
    target=Path(target).resolve() if target else RAW/'rubygems/host-contracts'
    target.resolve().relative_to((RAW/'rubygems').resolve())
    target.mkdir(parents=True,exist_ok=False)
    by_name={r[1]:r[0] for r in rows()}
    by_name.update({'normal-gem.json':'N01','normal-extension.json':'N02','normal-build-gem.json':'N03'})
    folders={'snapshots'}
    for name in contract_names():folders.add(json.loads((PACKAGE/name).read_text())['workspace']['fixture'])
    for folder in sorted(folders):shutil.copytree(PACKAGE/folder,target/folder)
    # Git does not store empty directories. This reviewed fixture precondition
    # was present during public N03 recording; recreate it before target launch.
    (target/'build-fixture/dist').mkdir(exist_ok=True)
    records=[]
    for name in contract_names():
        source=PACKAGE/name;spec=json.loads(source.read_text());identity=by_name[name];differences=[]
        if identity=='N06':
            spec['env']['BUNDLE_FORCE_RUBY_PLATFORM']='true'
            i=spec['command'].index('--remove-platform');del spec['command'][i:i+2]
            differences.append('documented portable Ruby platform locking; avoid observed native add/remove duplicate-platform defect')
        if WINDOWS:
            if 'SystemDrive' not in spec['inherit_env']:spec['inherit_env'].append('SystemDrive')
            differences.append('explicit SystemDrive required by the owned Windows Ruby runtime system directory expansion')
        else:
            spec['env']['GEMRC']=os.devnull;spec['env']['GIT_CONFIG_GLOBAL']=os.devnull
            spec['inherit_env']=[k for k in spec['inherit_env'] if k!='SystemDrive']
            differences.append('native null device and POSIX Ruby has no Windows SystemDrive prerequisite')
            runtime=json.loads((RAW/'active/rubygems/runtime.json').read_text())
            spec['command'][0]=runtime['installed_ruby_executable']
            differences.append('explicit resolved installed Ruby executable; context correctly refuses the symlink alias')
            if identity=='N01':
                spec['env']['NO_COLOR']='1'
                differences.append('explicit no-color prompt: native EditLine itself strips ESC and emits literal CSI suffixes')
            if identity in {'N04','N05'}:
                for step in spec['steps']:
                    selected=step.get('state',{})
                    if selected.get('path')=='.bundle/config':
                        selected['bytes_base64']=base64.b64encode(base64.b64decode(selected['bytes_base64']).replace(b'\r\n',b'\n')).decode()
                differences.append('new native YAML file uses LF, existing reviewed LF fixtures unchanged')
            for step in spec['steps']:
                selected=step.get('state',{})
                if selected.get('path')=='.bundle-user-config' and selected.get('kind')=='file':
                    selected['bytes_base64']=base64.b64encode(base64.b64decode(selected['bytes_base64']).replace(b'\r\n',b'\n')).decode()
                    differences.append('new selected Bundler preferences use native LF')
        (target/name).write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8',newline='\n')
        records.append(dict(id=identity,spec=name,source_sha256=sha256(source),authored_sha256=sha256(target/name),differences=differences))
    profile=target.parent/('host-profile.json' if target.name=='host-contracts' else target.name+'-profile.json')
    immutable_json(profile,dict(contracts=records,
        source_freeze_sha256=sha256(PACKAGE/'reviewed-contract-freeze.json'),
        resize='actual Git/less diff child; quiet collision resize remains excluded',qualification='authored; execution pending'))
    print('Prepared exactly twenty reviewed native Bundler contracts.')


if __name__=='__main__':main()
