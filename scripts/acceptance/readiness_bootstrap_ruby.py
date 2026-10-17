"""Verify and unpack the official portable Windows Ruby; never run an installer."""
import asyncio
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import urllib.request

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args()
    if os.name!='nt':raise RuntimeError('use a reviewed installed native Ruby on POSIX')
    target=RAW/'active/rubygems'
    owner=json.loads((target/'task-owned.json').read_text())
    if owner['workspace']!=str(ROOT) or owner['project']!='ruby/rubygems':raise RuntimeError('unowned Ruby runtime root')
    archive=target/'ruby-portable.7z'
    expected='7a9be96d3448ecbd9a81eccae1f619131dfcc761f2c98dded03ece6c05d0474f'
    url='https://github.com/oneclick/rubyinstaller2/releases/download/RubyInstaller-4.0.7-1/rubyinstaller-4.0.7-1-x64.7z'
    if args.resume:
        if not archive.is_file() or (target/'runtime').exists() or (target/'ruby-portable-inventory.json').exists():
            raise RuntimeError('resume requires the verified archive before runtime extraction')
        data=archive.read_bytes()
    else:
        if archive.exists():raise RuntimeError('preserve existing runtime acquisition')
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:
            data=response.read(17742012+1)
    if len(data)!=17742012 or hashlib.sha256(data).hexdigest()!=expected:
        raise RuntimeError('official portable Ruby size/digest mismatch')
    if not args.resume:
        with archive.open('xb') as stream:stream.write(data)
    tool=Path(r'C:\Program Files\7-Zip\7z.exe')
    if not tool.is_file():raise RuntimeError('reviewed installed 7-Zip unavailable; no global installation')
    env={k:os.environ[k] for k in ['PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC'] if k in os.environ}
    for key,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),
                       ('LOCALAPPDATA','home/localappdata'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp')]:
        path=target/folder;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
    listing=await execute([tool,'l','-slt','-ba','-sccUTF-8',archive],'rubygems','portable-ruby-member-inventory',
                          env=env,timeout=60,output_cap=16*1024**2,campaign=Campaign())
    entries=[];expanded=0;names=set()
    for block in listing['output'].replace('\r','').split('\n\n'):
        fields=dict(line.split(' = ',1) for line in block.splitlines() if ' = ' in line)
        if not fields.get('Path') or 'Type' in fields:continue
        name=fields['Path'].replace('\\','/');parts=PurePosixPath(name).parts
        if (not parts or PurePosixPath(name).is_absolute() or
            any(p in {'..','.'} or ':' in p or p.endswith((' ','.')) for p in parts) or
            fields.get('Symbolic Link') or fields.get('Hard Link') or fields.get('Encrypted','-')!='-'):
            raise RuntimeError('unsafe portable Ruby member')
        if name.casefold() in names:raise RuntimeError('portable Ruby member collision')
        names.add(name.casefold());size=int(fields.get('Size','0'));expanded+=size
        if len(names)>40000 or size<0 or size>32*1024**2 or expanded>288*1024**2:
            raise RuntimeError('portable Ruby extraction bounds exceeded')
        entries.append(dict(path=name,bytes=size,folder='D' in fields.get('Attributes','')))
    if not entries:raise RuntimeError('portable runtime inventory missing')
    immutable_json(target/'ruby-portable-inventory.json',dict(archive_sha256=expected,entries=entries,
        expanded_bytes=expanded,extractor_sha256=sha256(tool),source_url=url))
    runtime=target/'runtime';runtime.mkdir(exist_ok=False)
    await execute([tool,'x','-y','-sccUTF-8','-o'+str(runtime),archive],'rubygems','portable-ruby-owned-extraction',
                  env=env,timeout=120,campaign=Campaign())
    for entry in entries:
        path=runtime/entry['path']
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise RuntimeError('unexpected extracted runtime link')
        if entry['folder']:
            if not path.is_dir():raise RuntimeError('runtime directory missing')
        elif not path.is_file() or path.stat().st_size!=entry['bytes']:
            raise RuntimeError('runtime member size/type mismatch')
    binaries=list(runtime.rglob('bin/ruby.exe'))
    if len(binaries)!=1:raise RuntimeError('ambiguous portable Ruby executable')
    ruby=binaries[0]
    env['PATH']=str(target/'src/exe')+os.pathsep+str(ruby.parent)+os.pathsep+env['PATH']
    env['RUBYLIB']=str(target/'src/lib')
    env['GEMRC']=os.devnull
    env['GIT_CONFIG_NOSYSTEM']='1';env['GIT_CONFIG_GLOBAL']=os.devnull
    version=await execute([ruby,'-v'],'rubygems','portable-ruby-version',env=env,timeout=30,campaign=Campaign())
    built=await execute([ruby,'-S','bundle','--version'],'rubygems','pinned-bundler-source-version',
                        env=env,timeout=30,campaign=Campaign())
    if '4.1.0.beta2' not in built['output']:raise RuntimeError('wrong Bundler source loaded')
    immutable_json(target/'runtime.json',dict(ruby_relative_path=ruby.relative_to(target).as_posix(),
        ruby_sha256=sha256(ruby),ruby_version=version['output'].strip(),ruby_version_attempt=version['id'],
        archive_sha256=expected,source_url=url,installed_globally=False,expanded_runtime_bytes=expanded))
    immutable_json(target/'build.json',dict(pin=owner['pin'],source_runtime_interpreted=True,
        bundled_cli_version=built['output'].strip(),version_attempt=built['id'],
        license_sha256=sha256(target/'src/MIT.txt'),runtime_sha256=sha256(target/'runtime.json'),
        build_hooks_executed=False,dependency_installation=False))
    print('Official portable Ruby and pinned Bundler source verified:',built['output'].strip())


if __name__=='__main__':asyncio.run(main())
