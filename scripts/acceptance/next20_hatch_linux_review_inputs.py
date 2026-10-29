"""Fetch native Linux review inputs; never install or execute downloaded code."""
import asyncio
import argparse
from email.parser import BytesParser
import hashlib
import json
import re
import urllib.request
import zipfile

from adversarial_process import execute
from next20_check import RAW,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


def primary(url):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:data=response.read(4*1024**2+1)
    if len(data)>4*1024**2:raise ValueError('primary metadata bound')
    return data


async def main(resume):
    target=RAW/'active/hatch';root=target/'linux-review-inputs'
    if resume:
        if not root.is_dir() or (root/'index.json').exists():raise ValueError('only interrupted native review inputs may resume')
    else:root.mkdir(exist_ok=False)
    def retained(name,url):
        path=root/name
        if path.exists():
            if not resume or path.stat().st_size>4*1024**2:raise ValueError('preserve unexpected existing primary body')
            return path.read_bytes()
        data=primary(url)
        with path.open('xb') as stream:stream.write(data)
        return data
    common=json.loads((target/'wheel-review-inputs/index-v2.json').read_text())['wheels']
    normalize=lambda name:re.sub(r'[-_.]+','-',name.lower())
    versions={normalize(r['name']):r['version'] for r in common}
    selected={};bodies={}
    for name in ['distro','secretstorage','jeepney','cryptography','cffi','pycparser']:
        data=retained(name+'-latest.json','https://pypi.org/pypi/'+name+'/json');value=json.loads(data);version=value['info']['version']
        release=retained(name+'-'+version+'.json','https://pypi.org/pypi/'+name+'/'+version+'/json')
        selected[name]=version;bodies[name]=json.loads(release)
    for name in ['uv','backports-zstd']:
        version=versions[name];data=retained(name+'-'+version+'.json','https://pypi.org/pypi/'+name+'/'+version+'/json')
        selected[name]=version;bodies[name]=json.loads(data)
    immutable_json(root/'planned.json',dict(schema_version=1,versions=selected,
        inputs_scope='Wheel-only inputs for exact Linux-only dependencies and two platform-dependent common wheels. Existing43-wheel Windows inputs retained. No target/native executable or startup hook is installed or executed.',
        compressed_forecast_bytes=48*1024**2,max_single_wheel_bytes=32*1024**2,max_expanded_single_wheel_bytes=128*1024**2,
        host='ubuntu-24.04 linux x86_64 Python3.12; manylinux2.28/2014 compatible tags'))
    wheels=root/'wheels';wheels.mkdir()
    command=[target/'venv/Scripts/python.exe','-B','-m','pip','download','--only-binary=:all:','--no-deps',
        '--platform','manylinux_2_28_x86_64','--platform','manylinux2014_x86_64','--platform','linux_x86_64',
        '--python-version','3.12','--implementation','cp','--abi','cp312','--dest',wheels,
        *[name+'=='+version for name,version in sorted(selected.items())]]
    await execute(command,'hatch','linux-wheel-only-native-review-input-fetch',cwd=target,env=environment(target),timeout=300,campaign=NextCampaign())
    rows=[];total=0
    for path in sorted(wheels.iterdir()):
        total+=path.stat().st_size
        if path.suffix!='.whl' or path.stat().st_size>32*1024**2 or total>48*1024**2:raise ValueError('native review input storage bound')
        with zipfile.ZipFile(path) as archive:
            infos=archive.infolist()
            if len(infos)>10000 or sum(i.file_size for i in infos)>128*1024**2:raise ValueError('expanded native wheel review bound')
            names=[i.filename for i in infos if i.filename.endswith('.dist-info/METADATA') and len(i.filename.split('/'))==2]
            if len(names)!=1:raise ValueError('native wheel top-level metadata identity')
            metadata=archive.read(names[0]);info=BytesParser().parsebytes(metadata);name=normalize(info['Name'])
            if selected.get(name)!=info['Version']:raise ValueError('unselected native dependency version')
            matches=[r for r in bodies[name]['urls'] if r['filename']==path.name and r['digests']['sha256']==sha256(path) and r['size']==path.stat().st_size]
            if len(matches)!=1:raise ValueError('native wheel absent from exact primary release')
            hooks={i.filename:hashlib.sha256(archive.read(i)).hexdigest() for i in infos if i.filename.endswith('.pth') or '.data/scripts/' in i.filename}
            licenses={i.filename:hashlib.sha256(archive.read(i)).hexdigest() for i in infos if 'license' in i.filename.lower() or 'copying' in i.filename.lower()}
            with (root/(path.name+'.metadata.txt')).open('xb') as stream:stream.write(metadata)
            rows.append(dict(name=name,version=info['Version'],wheel=path.name,sha256=sha256(path),bytes=path.stat().st_size,
                hooks=hooks,license=info.get('License-Expression') or info.get('License'),license_members=licenses,
                requires_dist=info.get_all('Requires-Dist',[]),requires_python=info.get('Requires-Python'),
                primary_metadata_sha256=sha256(root/(name+'-'+info['Version']+'.json'))))
    if len(rows)!=8 or {r['name'] for r in rows}!=set(selected):raise ValueError('native review wheel closure differs')
    immutable_json(root/'index.json',dict(schema_version=1,wheels=rows,selected_versions=selected,compressed_bytes=total,
        approved_for_install=False,target_code_executed=False,scope='Primary-bound review inputs only; inspect all requirements/licenses/hooks before native preparation approval.'))
    print('Fetched and primary-verified8 native Linux review wheels;',total,'compressed bytes; no installation or target execution.')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true');args=parser.parse_args();asyncio.run(main(args.resume))
