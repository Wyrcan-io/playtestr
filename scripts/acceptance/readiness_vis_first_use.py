"""First vis recording uses only public CLI and independently reviewed exact bytes."""
import asyncio
import base64
import json
import os
import platform
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256


async def main():
    root=RAW/'vis/first-use'/uuid.uuid4().hex;root.mkdir(parents=True)
    fixture=root/'fixture';fixture.mkdir()
    (fixture/'note.txt').write_bytes(b'reviewed seed\n');(fixture/'sentinel.txt').write_bytes(b'preserve existing work\n')
    controls=['/expect reviewed seed','/text "A"','/expect INSERT','/text " + tested"',
        '/expect reviewed seed + tested','/key Escape','/absent INSERT','/snapshot edited.txt',
        '/text ":wq"','/key Enter','/exit 0','/file note.txt','/entries .','/review','/replay','/save']
    immutable_json(root/'intent.json',dict(start='Target and candidate already available; first public version check.',
        end='First independently reviewed ordinary public test.',expected_file_hex=b'reviewed seed + tested\n'.hex(),
        controls=controls,planned_shell_invocations=3,handwritten_playtestr_json=False))
    binary=RAW/'bin'/'playtestr';env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    env['PATH']=str(RAW/'active/vis/src')+os.pathsep+env['PATH'];attempts=[]
    async def run(argv,label,input=None):
        result=await execute(argv,'vis','first-use-'+label,input=input,env=env,timeout=180,campaign=Campaign())
        attempts.append(result['id']);return result
    await run([binary,'--version'],'version-check')
    spec=root/'spec.json'
    capture=await run([binary,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
        '--env','TERM=xterm-256color','--env','LC_ALL='+('en_US.UTF-8' if platform.system()=='Darwin' else 'C.UTF-8'),
        '--width','100','--height','28','--timeout-ms','10000','--run-timeout-ms','120000','--','vis','note.txt'],
        'public-author-review-replay-export',input='\n'.join(controls)+'\n')
    exported=json.loads(spec.read_text(encoding='utf-8-sig'))
    selected=next(s['state'] for s in exported['steps'] if s.get('state',{}).get('path')=='note.txt')
    if base64.b64decode(selected['bytes_base64'])!=b'reviewed seed + tested\n':raise RuntimeError('independent first-use byte review failed')
    entries=next(s['state'] for s in exported['steps'] if s.get('state',{}).get('kind')=='entries')
    if entries['entries']!=['note.txt','sentinel.txt']:raise RuntimeError('unreviewed first-use directory changes')
    report=root/'ordinary-results.json'
    ordinary=await run([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/'evidence').relative_to(ROOT),
        spec.relative_to(ROOT)],'ordinary-public-test')
    outcome=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
    if outcome['status']!='passed' or not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
        raise RuntimeError('first ordinary vis result/cleanup unconfirmed')
    immutable_json(root/'journey.json',dict(attempts=attempts,shell_invocations=len(attempts),recorder_controls=len(controls),
        capture_attempt=capture['id'],ordinary_attempt=ordinary['id'],spec_sha256=sha256(spec),runner_sha256=sha256(binary),
        target_build_sha256=sha256(RAW/'active/vis/build.json'),human_time='unmeasured',handwritten_playtestr_json=False,
        confounders=['prepared tiny synthetic fixture','agent/source familiarity','owned target and runner already built'],
        counting='This fresh route only; earlier failures remain separate. No new scenario/project credit.'))
    print('First public vis route passes:',len(attempts),'commands and',len(controls),'controls; human time unmeasured.')


if __name__=='__main__':asyncio.run(main())
