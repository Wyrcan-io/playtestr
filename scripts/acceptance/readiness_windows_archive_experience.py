"""Owned, source-free private archive upgrade/rollback calibration on declared native hosts."""
import argparse
import asyncio
import base64
import ctypes
import json
import os
import platform
import tarfile
from pathlib import Path
import shutil
import uuid
import zipfile

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


def extract(archive,expected,output):
    require(sha256(archive)==expected['archive_sha256'],'archive checksum mismatch before extraction')
    require(not output.exists(),'refuse existing private installation')
    windows_archive=archive.name.endswith('.zip')
    require(windows_archive or archive.name.endswith('.tar.gz'),'unsupported private archive format')
    suffix='.exe' if windows_archive else ''
    binary_name='playtestr'+suffix
    expected_names={binary_name,'LICENSE','README.md','THIRD_PARTY_NOTICES.md'}
    payloads={}
    if windows_archive:
        with zipfile.ZipFile(archive) as source:
            entries=source.infolist()
            require(len(entries)==4,'unexpected archive count')
            for member in entries:
                require(not member.is_dir() and member.file_size<=32*1024**2,'unsafe archive type/size')
                require(member.filename not in payloads,'duplicate archive member')
                payloads[member.filename]=source.read(member)
    else:
        with tarfile.open(archive,'r:gz') as source:
            entries=source.getmembers()
            require(len(entries)==4,'unexpected archive count')
            for member in entries:
                require(member.isfile() and member.size<=32*1024**2 and member.name not in payloads,'unsafe archive type/size')
                payloads[member.name]=source.extractfile(member).read(member.size+1)
    require(len({str(Path(n).parent) for n in payloads})==1 and {Path(n).name for n in payloads}==expected_names,'archive layout differs')
    output.mkdir(parents=True)
    for name,data in payloads.items():
        require('\\' not in name and ':' not in name and all(p not in {'','..','.'} for p in name.split('/')),'unsafe archive member')
        target=output/Path(name).name;target.write_bytes(data)
        if not windows_archive:target.chmod(0o755 if target.name==binary_name else 0o644)
    require(sha256(output/binary_name)==expected['binary_sha256'],'installed executable differs')
    return output/binary_name



async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--series',choices=['provisional-v1','migration-v2'],default='provisional-v1')
    parser.add_argument('--archive',type=Path);parser.add_argument('--previous-archive',type=Path);args=parser.parse_args()
    host={'Windows':'windows','Linux':'linux','Darwin':'darwin'}.get(platform.system())
    require(host is not None,'undeclared native archive host')
    suffix='.exe' if os.name=='nt' else ''
    root=RAW/'archive-experience'/uuid.uuid4().hex
    root.mkdir(parents=True)
    empty=root/'empty-path';empty.mkdir()
    env={k:os.environ[k] for k in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT'] if k in os.environ}
    env.update(PATH=str(empty),TEMP=str(RAW/'tmp'),TMP=str(RAW/'tmp'))
    freeze_name='provisional-candidate-freeze.json' if args.series=='provisional-v1' else 'migration-candidate-freeze.json'
    freeze=load(ROOT/'docs/validation/runner-readiness-ten-project-pass'/freeze_name)
    current=next(c for c in freeze['cells'] if c['host']==host)
    manifest=load(ROOT/'release/e5-candidate-manifest.json')
    old=next(c for c in manifest if c['host']['runner_os']=={'windows':'Windows','linux':'Linux','darwin':'macOS'}[host])
    previous=dict(archive_sha256=old['archive_sha256'],binary_sha256=old['executable_sha256'])
    old_archive=ROOT/'artifacts/e5-candidate-36329978517'/('playtestr-'+host+'-'+('arm64' if host=='darwin' else 'amd64'))/old['archive']
    current_archive=ROOT/current['archive_local_only']
    for option,name in [(args.archive,'current'),(args.previous_archive,'previous')]:
        if option is None:continue
        path=option if option.is_absolute() else ROOT/option
        require('..' not in path.parts,'archive override traversal')
        path.relative_to(RAW)
        path.resolve(strict=True).relative_to(RAW.resolve(strict=True))
        cursor=path
        while cursor!=RAW:
            require(not cursor.is_symlink() and not getattr(cursor,'is_junction',lambda:False)(),'linked archive override')
            cursor=cursor.parent
        if name=='current':current_archive=path
        else:old_archive=path
    installed={
        'previous':extract(old_archive,previous,root/'old caf\u00e9 \u96ea'),
        'current':extract(current_archive,current,root/'upgrade caf\u00e9 \u96ea'),
        'rollback':extract(old_archive,previous,root/'rollback caf\u00e9 \u96ea'),
    }
    attempts={}
    async def call(label,argv,expected=0,cwd=None,stdin=None,build_env=None):
        result=await execute(argv,'core','archive-experience-'+label,env=build_env or env,
            cwd=cwd or root,input=stdin,expected=expected,timeout=90,campaign=Campaign())
        attempts[label]=result['id']
        return result
    for name,binary in installed.items():
        result=await call(name+'-version',[binary,'--version'],cwd=binary.parent)
        require(result['output'].strip()=='playtestr '+(freeze['version'] if name=='current' else old['version']), 'wrong installed version')
        await call(name+'-help',[binary,'--help'],cwd=binary.parent)
        require(len(list(binary.parent.iterdir()))==4,'source-free installation gained unexpected files')
    corrupt=root/'corrupt.zip'
    shutil.copyfile(current_archive,corrupt)
    with corrupt.open('r+b') as stream:
        byte=stream.read(1);stream.seek(0);stream.write(bytes([byte[0]^1]))
    rejected=root/'rejected'
    try:extract(corrupt,current,rejected)
    except RuntimeError as error:require('checksum' in str(error),'wrong corruption rejection')
    else:raise RuntimeError('corrupt archive accepted')
    require(not rejected.exists(),'checksum rejection extracted payloads')
    build=root/'build';build.mkdir()
    source=build/'main.go'
    source.write_bytes((ROOT/'scripts/acceptance/readiness_archive_fixture.go.txt').read_bytes())
    (build/'go.mod').write_text('module archive-calibration\n\ngo 1.25\n',encoding='utf-8')
    build_env=dict(os.environ)
    for key,folder in [('TEMP','tmp'),('TMP','tmp'),('GOTMPDIR','tmp'),('GOCACHE','cache'),('GOPATH','gopath'),('GOMODCACHE','modules')]:
        path=build/folder;path.mkdir(exist_ok=True);build_env[key]=str(path)
    build_env.update(GOTOOLCHAIN='local',GOWORK='off',GOENV='off',GOTELEMETRY='off',GOPROXY='off',CGO_ENABLED='0')
    compiler=RAW/'toolchain/go/bin'/('go'+suffix)
    for mode in ['good','screen','file']:
        await call('fixture-build-'+mode,[compiler,'build','-trimpath','-ldflags','-s -w -X main.mode='+mode,
            '-o',build/(mode+suffix),source],cwd=build,build_env=build_env)
    package=root/'relocated caf\u00e9 \u96ea';package.mkdir()
    fixture=package/'fixture';fixture.mkdir()
    (fixture/'seed.bin').write_bytes(b'preserve\x00\r\n')
    target=package/('target'+suffix);shutil.copyfile(build/('good'+suffix),target)
    if os.name!='nt':target.chmod(0o755)
    spec=package/'spec.json'
    controls=['/expect Value>','/text '+json.dumps('reviewed\r'),'/expect Saved','/snapshot saved.txt',
        '/expect Quit>','/text '+json.dumps('q\r'),'/exit 0','/file saved.txt','/file seed.bin','/entries .','/review','/replay','/save']
    binary=installed['current']
    await call('record',[binary,'record','--output',spec,'--fixture','fixture','--temporary-home','--temporary-temp',
        '--timeout-ms','3000','--run-timeout-ms','15000','--','./target'+suffix],stdin='\n'.join(controls)+'\n')
    contract=load(spec)
    files={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in contract['steps']
           if s.get('state',{}).get('kind')=='file'}
    require(files=={'saved.txt':b'reviewed\n','seed.bin':b'preserve\x00\r\n'},'independent fixture byte oracle differs')
    approved=sha256(spec);baseline=sha256(package/'snapshots/saved.txt')
    reports={}
    async def test(label,runner,contract_path,expected):
        report=package/(label+'.json');evidence=package/(label+'-evidence')
        await call(label,[runner,'test','--report',report,'--artifacts-dir',evidence,contract_path],expected)
        result=load(report)
        require(result['summary']['passed']==(1 if expected==0 else 0) and result['summary']['failed']==expected,'wrong public outcome')
        row=result['results'][0]
        require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'unconfirmed archive calibration cleanup')
        reports[label]=sha256(report)
        return report
    await test('current-clean',binary,spec,0)
    for mode in ['screen','file']:
        shutil.copyfile(build/(mode+suffix),target)
        await test(mode+'-changed',binary,spec,1)
        shutil.copyfile(build/('good'+suffix),target)
        await test(mode+'-restored',binary,spec,0)
        require(sha256(spec)==approved and sha256(package/'snapshots/saved.txt')==baseline,'calibration changed approved expectations')
    legacy=dict(contract,version=2,steps=[s for s in contract['steps'] if 'state' not in s])
    legacy_path=package/'legacy.json';immutable_json(legacy_path,legacy)
    old_report=await test('previous-v2',installed['previous'],legacy_path,0)
    await test('upgraded-v2',binary,legacy_path,0)
    await test('rollback-v2',installed['rollback'],legacy_path,0)
    await call('current-reads-previous-report',[binary,'report','--input',old_report,'--evidence-root',package,
        '--output',package/'previous-report.html'])
    immutable_json(root/'experience.json',dict(series=args.series,host=host,architecture=current['architecture'],privileged_role_enabled=(bool(ctypes.windll.shell32.IsUserAnAdmin()) if os.name=='nt' else os.geteuid()==0),attempts=attempts,reports=reports,source_free_path=str(empty.relative_to(ROOT)),
        installed_binary_sha256={n:sha256(p) for n,p in installed.items()},current_archive_sha256=sha256(current_archive),
        old_archive_sha256=sha256(old_archive),fixture_source_sha256=sha256(source),compiler_sha256=sha256(compiler),
        spec_sha256=approved,baseline_sha256=baseline,corrupt_archive_rejected_before_extraction=True,
        scope='Private native archive calibration; source-free execution has an empty PATH and only installed files in the initial package. Fixture builds are separate engineering preparation.',
        limits='No OS network isolation claim, real-project fault credit, final-archive qualification, paid launch or human-usability credit. Explicit side-by-side private upgrade/rollback; no global installation.',
        final_archive_credit=0))
    print('Private native source-free version/help, Unicode relocation, corruption rejection, controlled failure/recovery and v2 upgrade/rollback calibrated:',root)


if __name__=='__main__':asyncio.run(main())
