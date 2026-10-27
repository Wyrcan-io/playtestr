"""Audit and retain one failed/cancelled engineering host packet without app credit."""
import argparse
import asyncio
import json
import re
import subprocess
import sys

from adversarial_process import execute
from next20_check import RAW,ROOT,NextCampaign,owned_environment,NAME
from readiness_compact_native import compact
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--kind',choices=['replacement-failed','legacy-cancelled'],required=True)
    parser.add_argument('--host',choices=['linux','darwin','windows'],required=True)
    parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    failed=args.kind=='replacement-failed'
    if not 1<=args.generation<=1000 or not failed and args.host=='windows':raise ValueError('invalid auxiliary host/generation')
    run='40419143483' if failed else '40418274509'
    revision='4a23e5044f121b8759287030aa62c399b081b9ff' if failed else 'a51d64ff9dc71185b7fc259712e5d9f06632065d'
    project='replacement-candidate' if failed else 'legacy-core-cancelled'
    os_name={'linux':'Linux','darwin':'macOS','windows':'Windows'}[args.host]
    host_name={'linux':'ubuntu-24.04','darwin':'macos-15','windows':'windows-2025'}[args.host]
    artifact='next20-private-replacement-'+os_name if failed else 'runner-readiness-core-'+host_name
    if any((RAW/'native').iterdir()):raise ValueError('retain/remove current host packet before another retrieval')
    retained=RAW/project/('retained-native-v'+str(args.generation))
    if retained.exists():raise ValueError('preserve existing retained generation')
    root=RAW/'native'/run;packet=root/artifact;campaign=NextCampaign()
    async def command(argv,label):
        return await execute(argv,'core',label,cwd=ROOT,env=owned_environment(),timeout=180,campaign=campaign)
    await command(['gh','run','download',run,'--repo','Wyrcan-io/playtestr','--name',artifact,'--dir',packet],
        'auxiliary-fetch-'+run+'-'+args.host)
    observed=await command(['gh','run','view',run,'--repo','Wyrcan-io/playtestr','--json','headSha,status,conclusion,jobs'],
        'auxiliary-provider-'+run+'-'+args.host)
    provider=json.loads(observed['output']);immutable_json(root/'run-metadata.json',provider)
    expected='failure' if failed else 'cancelled'
    jobs=[j for j in provider['jobs'] if host_name in j['name']]
    if provider['headSha']!=revision or provider['status']!='completed' or provider['conclusion']!=expected or len(jobs)!=1:
        raise ValueError('auxiliary provider/source mismatch')
    job=jobs[0]
    if job['conclusion']!=expected:raise ValueError('wrong original auxiliary job outcome')
    upload=[s for s in job['steps'] if 'upload-artifact' in s['name']]
    if len(upload)!=1 or upload[0]['conclusion']!='success':raise ValueError('original packet upload not confirmed')
    events={}
    for path in (packet/'events').glob('*.json'):
        value=json.loads(path.read_text(encoding='utf-8-sig'))
        if not re.fullmatch('[0-9a-f]{32}',value['id']):raise ValueError('invalid original attempt identity')
        if value['event'] in events.setdefault(value['id'],{}):raise ValueError('duplicate original event')
        events[value['id']][value['event']]=value
    if not events:raise ValueError('missing original auxiliary commands')
    summary=[]
    for eid,rows in events.items():
        started=rows.get('started')
        if started is None or started['ci_run_id']!=run:raise ValueError('original run binding missing')
        namespace=NAME if failed else 'runner-readiness-ten-project-pass'
        if any(r['campaign']!=namespace for r in rows.values()):raise ValueError('original namespace rewritten/mixed')
        original=packet/'core'/eid
        identity=rows.get('identified')
        if identity:
            reference=identity['identity'];manifest=packet/reference['manifest']
            if sha256(manifest)!=reference['sha256']:raise ValueError('original identity manifest changed')
            if failed:
                bound=json.loads(manifest.read_text())['files']
                helper='scripts/acceptance/next20_replacement_candidate.py'
                blob=subprocess.check_output(['git','show',revision+':'+helper],cwd=ROOT,timeout=15)
                import hashlib
                allowed={hashlib.sha256(blob).hexdigest(),hashlib.sha256(blob.replace(b'\n',b'\r\n')).hexdigest()}
                if bound.get(helper) not in allowed:raise ValueError('failed helper lacks exact original source binding')
        finish=rows.get('finished')
        if finish:
            if sha256(original/'console.log')!=finish['console_sha256']:raise ValueError('original console changed')
        if failed:
            if set(rows)!={'started','identified','launched','finished'}:raise ValueError('failed setup command incomplete')
            label=started['label'];category,code=('passed',0) if label=='replacement-owned-native-sdk' else ('exit_mismatch',1)
            if label not in {'replacement-owned-native-sdk','replacement-native-source-core'}:
                raise ValueError('unexpected target/native command in phase-refused packet')
            if finish['category']!=category or finish['exit_code']!=code or finish['cleanup_errors'] or finish['harness_cleanup']!='harness_process_reaped':
                raise ValueError('original helper outcome/cleanup differs')
            if code and 'undeclared evidence phase' not in (original/'console.log').read_text(encoding='utf-8'):
                raise ValueError('original native setup failure differs')
        summary.append(dict(id=eid,label=started['label'],events=sorted(rows),
            missing_events=sorted({'started','identified','launched','finished'}-set(rows)),
            category=finish.get('category') if finish else None,
            harness_cleanup=finish.get('harness_cleanup') if finish else None))
    if failed:
        sdk=json.loads((packet/'toolchain/sdk.json').read_text())
        if len(events)!=2 or sdk['version']!='go1.25.0' or sdk['host']!=args.host:
            raise ValueError('failed original SDK/command coverage differs')
        steps={s['name']:s['conclusion'] for s in job['steps']}
        if steps.get('Build once and inspect distinct private archive')!='skipped':raise ValueError('unexpected original archive build')
    immutable_json(root/'auxiliary-audit.json',dict(schema_version=1,kind=args.kind,run=run,host=args.host,
        qualification_revision=revision,provider_attempt=observed['id'],provider_job=job['databaseId'],
        source_namespace_preserved=True,original_commands=summary,project_credits=0,native_core_credits=0,
        archive_builds=0,scope='Actual failed/cancelled engineering evidence only. Original incomplete streams and cleanup dispositions are preserved, not turned into passes.'))
    (RAW/project).mkdir(exist_ok=True)
    compact(RAW,project,[run],16*1024**2,generation=args.generation,max_archive_bytes=16*1024**2)
    await command(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        ROOT/'scripts/acceptance/next20_remove_native.ps1','-Project',project,'-Generation',str(args.generation)],
        'auxiliary-remove-expansion-'+run+'-'+args.host)
    print('Audited/retained original auxiliary host packet and checked-removed expansion:',args.kind,args.host,'zero qualification credit')


if __name__=='__main__':asyncio.run(main())
