"""Independently audit one successful native replacement packet before retention."""
import argparse
import asyncio
import hashlib
import io
import json
import subprocess
import tarfile
import zipfile

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NAME,NextCampaign,owned_environment
from readiness_evidence import immutable_json,sha256
from readiness_compact_native import compact


def blob(revision,name):
    return subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT,timeout=30)


def hashes(data):
    normalized=data.replace(b'\r\n',b'\n')
    return {hashlib.sha256(normalized).hexdigest(),hashlib.sha256(normalized.replace(b'\n',b'\r\n')).hexdigest()}


def audit(packet,provider,host,revision,source,run):
    arch='arm64' if host=='darwin' else 'amd64'
    native=packet/'replacement-candidate/native-exit-v1'/(host+'-'+arch)
    candidate=json.loads((native/'candidate.json').read_text())
    core=json.loads((native/'native-core.json').read_text())
    sdk=json.loads((packet/'toolchain/sdk.json').read_text())
    os_name={'darwin':'macos-15','linux':'ubuntu-24.04','windows':'windows-2025'}[host]
    jobs=[j for j in provider['jobs'] if os_name in j['name']]
    if provider['headSha']!=revision or provider['status']!='completed' or len(jobs)!=1 or jobs[0]['conclusion']!='success':
        raise ValueError('provider native success/source mismatch')
    for value in [candidate,core]:
        if (value['source_revision'],value['qualification_revision'],value['host'],value['architecture'],value['version'])!=(source,revision,host,arch,'v0.4.0-rc.6'):
            raise ValueError('native receipt source/version/host mismatch')
    if core['source_inputs']!=candidate['source_inputs'] or sha256(native/'native-core.json')!=candidate['native_core_sha256']:
        raise ValueError('core/candidate source mismatch')
    if sdk['version']!='go1.25.0' or sdk['host']!=host or sdk['architecture']!=arch or sha256(packet/'toolchain/sdk.json')!=core['sdk_sha256']:
        raise ValueError('native official SDK identity mismatch')
    names=subprocess.check_output(['git','ls-tree','-r','--name-only',source],cwd=ROOT,timeout=30).decode().splitlines()
    selected={n for n in names if n.endswith('.go') or n.startswith('schema/') and n.endswith('.json') or n in {'go.mod','go.sum','README.md','LICENSE','THIRD_PARTY_NOTICES.md'}}
    if selected!=set(core['source_inputs']):raise ValueError('incomplete native production/source test inventory')
    # One bounded Git archive proves exact historical source bytes without a checkout.
    source_archive=subprocess.check_output(['git','archive',source,*sorted(selected)],cwd=ROOT,timeout=60)
    if len(source_archive)>64*1024**2:raise ValueError('source archive bound')
    with tarfile.open(fileobj=io.BytesIO(source_archive)) as stream:
        for member in stream:
            if member.isfile() and core['source_inputs'][member.name] not in hashes(stream.extractfile(member).read()):
                raise ValueError('historical source input mismatch: '+member.name)
    events={}
    for path in (packet/'events').glob('*.json'):
        row=json.loads(path.read_text());eid=row['id']
        if row['campaign']!=NAME or row['event'] in events.setdefault(eid,{}):raise ValueError('wrong/duplicate original event')
        events[eid][row['event']]=row
    expected={'replacement-'+label for label in ['owned-native-sdk','native-source-core','native-private-package',
        'native-sdk-settings','all-go-tests','focused-native-status-controls','go-vet','native-race-tests',
        'native-build-once','native-package','extracted-version','extracted-help']}
    rows={}
    for eid,items in events.items():
        if set(items)!={'started','identified','launched','finished'}:raise ValueError('incomplete command evidence')
        start=items['started'];finish=items['finished'];label=start['label']
        if label in rows or start['ci_run_id']!=run:raise ValueError('duplicate/wrong original execution')
        if finish['category']!='passed' or finish['exit_code']!=0 or finish['cleanup_errors'] or finish['harness_cleanup']!='harness_process_reaped':
            raise ValueError('command not a successful reaped execution')
        console=packet/'core'/eid/'console.log'
        if sha256(console)!=finish['console_sha256']:raise ValueError('console changed')
        ref=items['identified']['identity'];manifest=packet/ref['manifest']
        if sha256(manifest)!=ref['sha256']:raise ValueError('identity manifest changed')
        identity=json.loads(manifest.read_text());files=identity['files']
        if files.get('scripts/acceptance/next20_replacement_candidate.py') not in hashes(blob(revision,'scripts/acceptance/next20_replacement_candidate.py')):
            raise ValueError('actual executing helper not bound')
        if label not in {'replacement-owned-native-sdk','replacement-native-source-core','replacement-native-private-package'}:
            if any(files.get('.candidate-source/'+n)!=h for n,h in core['source_inputs'].items()):
                raise ValueError('command did not bind exact complete production/test inputs')
        rows[label]={'id':eid,'console_sha256':sha256(console),'seconds':finish['seconds'],'identity_sha256':ref['sha256']}
    if set(rows)!=expected:raise ValueError('native command coverage mismatch')
    for declared in core['attempts']+candidate['attempts']:
        if rows['replacement-'+declared['label']]['id']!=declared['id']:raise ValueError('declared command differs from execution')
    def output(label):return (packet/'core'/rows['replacement-'+label]['id']/'console.log').read_text()
    focused=output('focused-native-status-controls')
    for family in ['TestExitStatusBoundsBySpecVersion','TestHTMLPreservesNativeWindowsExitStatus','TestNativeExitSchemaRangesPreserveOlderSpecBounds']:
        if '--- PASS: '+family not in focused:raise ValueError('common focused family did not pass: '+family)
    applicable=['TestNativeWindowsWideExitStatusAndSameRunState','TestRecorderExportsAndReplaysNativeWindowsExit'] if host=='windows' else ['TestNativeSignalExitStatusAndSameRunState']
    for family in applicable:
        if '--- PASS: '+family not in focused:raise ValueError('native focused family did not pass: '+family)
    if output('extracted-version').strip()!='playtestr v0.4.0-rc.6' or 'Usage' not in output('extracted-help'):
        raise ValueError('actual extracted executable version/help mismatch')
    archive=packet/candidate['archive'].split(NAME+'/',1)[1]
    if sha256(archive)!=candidate['archive_sha256'] or archive.stat().st_size!=candidate['archive_bytes']:
        raise ValueError('archive bytes differ')
    if archive.with_name(archive.name+'.sha256').read_text().strip()!=candidate['archive_sha256']+'  '+archive.name:
        raise ValueError('sidecar differs')
    actual={}
    if host=='windows':
        with zipfile.ZipFile(archive) as stream:
            for m in stream.infolist():
                if m.is_dir() or m.file_size>16*1024**2 or m.filename in actual:raise ValueError('unsafe/duplicate member')
                actual[m.filename]=stream.read(m)
    else:
        with tarfile.open(archive,'r:gz') as stream:
            for m in stream:
                if not m.isfile() or m.size>16*1024**2 or m.name in actual:raise ValueError('unsafe/duplicate member')
                actual[m.name]=stream.extractfile(m).read(m.size+1)
    if len(actual)!=4 or set(actual)!=set(candidate['archive_members']):raise ValueError('archive member coverage mismatch')
    binary='playtestr.exe' if host=='windows' else 'playtestr'
    for name,data in actual.items():
        digest=hashlib.sha256(data).hexdigest()
        if candidate['archive_members'][name]!={'bytes':len(data),'sha256':digest}:raise ValueError('archive member changed')
        leaf=name.split('/')
        if len(leaf)!=2 or leaf[0]!=archive.name.removesuffix('.tar.gz').removesuffix('.zip'):raise ValueError('archive member path mismatch')
        if digest!=(candidate['binary_sha256'] if leaf[1]==binary else core['source_inputs'][leaf[1]]):raise ValueError('binary/document source mismatch')
    return dict(schema_version=1,host=host,architecture=arch,source_revision=source,qualification_revision=revision,
        run=run,provider_job=jobs[0]['databaseId'],commands=rows,archive_sha256=sha256(archive),
        binary_sha256=candidate['binary_sha256'],archive_bytes=archive.stat().st_size,project_credits=0,
        publication=False),archive


async def main():
    p=argparse.ArgumentParser();p.add_argument('--run',required=True);p.add_argument('--revision',required=True)
    p.add_argument('--source',required=True);p.add_argument('--host',choices=['darwin','linux','windows'],required=True)
    p.add_argument('--generation',type=int,required=True);args=p.parse_args()
    import re
    if not re.fullmatch(r'[0-9]{1,20}',args.run) or any(not re.fullmatch('[0-9a-f]{40}',v) for v in [args.revision,args.source]) or not 1<=args.generation<=1000:raise ValueError('invalid exact scope')
    root=RAW/'native'/args.run;artifact='next20-private-replacement-'+{'darwin':'macOS','linux':'Linux','windows':'Windows'}[args.host]
    if len(list((RAW/'native').iterdir()))!=1 or len(list(root.iterdir()))!=1:raise ValueError('audit exactly one retrieved host packet')
    packet=root/artifact
    result=await execute(['gh','run','view',args.run,'--repo','Wyrcan-io/playtestr','--json','headSha,status,conclusion,jobs'],
        'core','replacement-success-provider-'+args.host,cwd=ROOT,env=owned_environment(),timeout=60,campaign=NextCampaign())
    provider=json.loads(result['output'])
    receipt,archive=audit(packet,provider,args.host,args.revision,args.source,args.run)
    destination=RAW/'replacement-archives/native-exit-v1'/archive.name;destination.parent.mkdir(parents=True,exist_ok=True)
    # Preserve exact downloaded release bytes separately before removing expansion.
    with destination.open('xb') as stream:stream.write(archive.read_bytes())
    if sha256(destination)!=receipt['archive_sha256']:raise ValueError('preserved archive copy mismatch')
    receipt['archive_local_only']=destination.relative_to(ROOT).as_posix()
    immutable_json(root/'run-metadata.json',provider);immutable_json(root/'native-candidate-audit.json',receipt)
    immutable_json(DOC/('replacement-native-'+args.host+'-'+args.run+'.json'),receipt)
    compact(RAW,'replacement-candidate',[args.run],16*1024**2,generation=args.generation)
    await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'scripts/acceptance/next20_remove_native.ps1',
        '-Project','replacement-candidate','-Generation',str(args.generation)],'core','remove-audited-replacement-'+args.host,
        cwd=ROOT,env=owned_environment(),timeout=180,campaign=NextCampaign())
    print('Independently audited native commands/source/archive, preserved exact archive and retained packet:',args.host)


if __name__=='__main__':asyncio.run(main())
