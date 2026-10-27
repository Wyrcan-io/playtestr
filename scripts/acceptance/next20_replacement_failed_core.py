"""Retain an actual rejected replacement-core cell without rewriting its outcomes."""
import argparse
import asyncio
import hashlib
import json
import subprocess

from adversarial_process import execute
from next20_check import RAW,ROOT,NAME,NextCampaign,owned_environment
from readiness_compact_native import compact
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['linux','windows'],required=True)
    parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--missing-race-compiler',action='store_true');args=parser.parse_args()
    if args.missing_race_compiler and args.host!='windows':raise ValueError('race prerequisite refusal is Windows-only')
    run='40424475362' if args.missing_race_compiler else '40420820491'
    revision='354b837ece1de487c5ca1025b8225a843eaba56c' if args.missing_race_compiler else 'dbb4d13cafb5ed834410788121ef98ca85937ac7'
    root=RAW/'native'/run;artifact='next20-private-replacement-'+('Linux' if args.host=='linux' else 'Windows')
    packet=root/artifact
    if not packet.is_dir() or len(list(root.iterdir()))!=1:raise ValueError('requires exactly one retrieved host packet')
    provider=await execute(['gh','run','view',run,'--repo','Wyrcan-io/playtestr','--json','headSha,status,conclusion,jobs'],
        'core','rejected-replacement-core-provider-'+args.host,cwd=ROOT,env=owned_environment(),timeout=60,campaign=NextCampaign())
    metadata=json.loads(provider['output']);immutable_json(root/'run-metadata.json',metadata)
    name='ubuntu-24.04' if args.host=='linux' else 'windows-2025'
    jobs=[j for j in metadata['jobs'] if name in j['name']]
    if metadata['headSha']!=revision or len(jobs)!=1 or jobs[0]['conclusion']!='failure':raise ValueError('wrong provider cell')
    steps={s['name']:s['conclusion'] for s in jobs[0]['steps']}
    if steps.get('Build once and inspect distinct private archive')!='skipped':raise ValueError('an archive was unexpectedly built')
    rows={}
    for path in (packet/'events').glob('*.json'):
        value=json.loads(path.read_text());slot=rows.setdefault(value['id'],{})
        if value['event'] in slot or value['campaign']!=NAME:raise ValueError('rewritten/duplicate original event')
        slot[value['event']]=value
    labels={};observed=[]
    code=subprocess.check_output(['git','show',revision+':scripts/acceptance/next20_replacement_candidate.py'],cwd=ROOT,timeout=15)
    code_hashes={hashlib.sha256(code).hexdigest(),hashlib.sha256(code.replace(b'\n',b'\r\n')).hexdigest()}
    for eid,events in rows.items():
        if not {'started','finished'}<=events.keys():raise ValueError('missing original started/finished outcome')
        start=events['started'];finish=events['finished'];label=start['label']
        if start['ci_run_id']!=run or label in labels:raise ValueError('run/label identity mismatch')
        labels[label]=finish
        if sha256(packet/'core'/eid/'console.log')!=finish['console_sha256']:raise ValueError('original console changed')
        if 'identified' in events:
            reference=events['identified']['identity'];manifest=packet/reference['manifest']
            if sha256(manifest)!=reference['sha256']:raise ValueError('original identity changed')
            value=json.loads(manifest.read_text());files=value['files']
            if files.get('scripts/acceptance/next20_replacement_candidate.py') not in code_hashes:
                raise ValueError('actual wrapper source not bound')
        if label=='replacement-focused-native-status-controls' and args.host=='linux':
            if set(events)!={'started','finished'} or finish['category']!='harness_error' or finish['harness_cleanup']!='not_started':
                raise ValueError('first Linux focused-check refusal differs')
        elif set(events)!={'started','identified','launched','finished'} or finish['cleanup_errors'] or finish['harness_cleanup']!='harness_process_reaped':
            raise ValueError('executed original command cleanup incomplete')
        observed.append(dict(id=eid,label=label,events=sorted(events),category=finish['category'],exit_code=finish['exit_code'],
            harness_cleanup=finish['harness_cleanup'],console_sha256=finish['console_sha256']))
    if labels['replacement-native-source-core']['exit_code']!=1 or labels['replacement-owned-native-sdk']['exit_code']!=0:
        raise ValueError('original source wrapper outcomes differ')
    if args.host=='linux':
        if labels['replacement-all-go-tests']['category']!='passed':raise ValueError('Linux full Go suite was not positive')
        parent=next(o for o in observed if o['label']=='replacement-native-source-core')
        if 'File name too long' not in (packet/'core'/parent['id']/'console.log').read_text():raise ValueError('Linux root cause differs')
    if args.missing_race_compiler:
        for label in ['replacement-all-go-tests','replacement-focused-native-status-controls','replacement-go-vet']:
            if labels[label]['category']!='passed':raise ValueError('Windows source/focused/vet were not positive')
        if 'replacement-native-race-tests' in labels:raise ValueError('race command unexpectedly launched')
        parent=next(o for o in observed if o['label']=='replacement-native-source-core')
        if 'required read-only native race GCC prerequisite missing' not in (packet/'core'/parent['id']/'console.log').read_text():raise ValueError('Windows race prerequisite refusal differs')
    immutable_json(root/'rejected-core-audit.json',dict(schema_version=1,run=run,host=args.host,
        qualification_revision=revision,provider_job=jobs[0]['databaseId'],original_commands=observed,
        native_core_credits=0,archive_builds=0,project_credits=0,
        disposition='Original source-core rejection preserved. Individual successful commands are not a complete native-core qualification. Unlaunched identity failure remains a harness refusal, not a Go test result.'))
    (RAW/'replacement-candidate').mkdir(exist_ok=True)
    compact(RAW,'replacement-candidate',[run],16*1024**2,generation=args.generation)
    await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'scripts/acceptance/next20_remove_native.ps1',
        '-Project','replacement-candidate','-Generation',str(args.generation)],'core','remove-rejected-replacement-core-'+args.host,
        cwd=ROOT,env=owned_environment(),timeout=180,campaign=NextCampaign())
    print('Actual rejected native core retained and expansion checked-removed:',args.host,'zero core/archive credit')


if __name__=='__main__':asyncio.run(main())
