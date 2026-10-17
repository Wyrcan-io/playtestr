"""Public first-use picker/export recording, with independently specified bytes."""
import asyncio
import base64
import json
import os
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


def environment():
    runtime=json.loads((RAW/'active/papis/runtime.json').read_text(encoding='utf-8-sig'))
    from pathlib import Path
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8')
    env['PATH']=str(Path(runtime['python']).parent)+os.pathsep+env['PATH']
    return env


def fixture_files():
    def info(title,author,ref):
        return ('author: '+author+'\nfiles:\n- paper.txt\npapis_id: '+ref+'\nref: '+ref+
                '\ntags:\n- reviewed\ntitle: '+title+'\ntype: book\nyear: 2024\n').encode()
    return {'config.ini':b'[settings]\npicktool = prompt_toolkit\ndatabase-backend = papis\nuse-git = false\n',
        'library/alpha/info.yaml':info('Alpha Book','Ada Alpha','alpha'),
        'library/alpha/paper.txt':b'alpha reviewed paper\n',
        'library/beta/info.yaml':info('Beta Book','Ada Beta','beta'),
        'library/beta/paper.txt':b'beta reviewed paper\r\n',
        'sentinel.txt':b'preserve independent existing work\n'}


async def main():
    root=RAW/'papis/first-use'/uuid.uuid4().hex;fixture=root/'fixture';fixture.mkdir(parents=True)
    original=fixture_files()
    for name,value in original.items():
        path=fixture/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)
    expected={'exported/info.yaml':original['library/beta/info.yaml'],
        'exported/paper.txt':original['library/beta/paper.txt'],
        'library/alpha/info.yaml':original['library/alpha/info.yaml'],
        'library/beta/info.yaml':original['library/beta/info.yaml'],'sentinel.txt':original['sentinel.txt']}
    controls=['/expect Alpha Book','/key ArrowDown','/expect 2/2','/snapshot selected.txt','/key Enter',
        '/expect Exporting document', '/exit 0',
        *['/file '+name for name in expected],'/entries exported','/review','/replay','/save']
    immutable_json(root/'intent.json',dict(expected_files={n:b.hex() for n,b in expected.items()},
        controls=controls,planned_shell_invocations=3,hand_written_playtestr_spec=False,
        target='Select the second synthetic bibliography entry and export its exact metadata/CRLF attachment.'))
    runner=RAW/('bin/playtestr.exe' if os.name=='nt' else 'bin/playtestr');attempts=[]
    async def run(argv,label,input=None):
        result=await execute(argv,'papis','first-use-'+label,env=environment(),input=input,
            timeout=180,campaign=Campaign());attempts.append(result['id']);return result
    await run([runner,'--version'],'version')
    spec=root/'spec.json'
    capture=await run([runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture',
        '--temporary-home','--temporary-temp','--width','100','--height','28','--timeout-ms','15000',
        '--run-timeout-ms','120000','--env','TERM=xterm-256color','--env','PYTHONDONTWRITEBYTECODE=1',
        '--env','PYTHONIOENCODING=utf-8','--','papis','--config','config.ini','--lib','library','--np','1',
        '--color','no','export','--folder','--out','exported','--sort','title'],
        'public-record-review-replay-export','\n'.join(controls)+'\n')
    value=json.loads(spec.read_text(encoding='utf-8-sig'))
    actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in value['steps']
        if s.get('state',{}).get('kind')=='file'}
    if actual!=expected:raise RuntimeError('independent first-use exact bytes differ')
    entries=next(s['state']['entries'] for s in value['steps'] if s.get('state',{}).get('kind')=='entries')
    if sorted(entries)!=['info.yaml','paper.txt']:raise RuntimeError('export contains unexpected entries')
    report=root/'ordinary-results.json'
    ordinary=await run([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
        (root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],'ordinary-test')
    result=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
    if result['status']!='passed' or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
        raise RuntimeError('first-use outcome or cleanup unconfirmed')
    immutable_json(root/'journey.json',dict(attempts=attempts,capture_attempt=capture['id'],ordinary_attempt=ordinary['id'],
        shell_invocations=len(attempts),recorder_controls=len(controls),spec_sha256=sha256(spec),
        runner_sha256=sha256(runner),target_build_sha256=sha256(RAW/'active/papis/build.json'),
        handwritten_playtestr_json=False,human_time='unmeasured',confounders=['synthetic prepared fixture',
        'agent/source familiarity','warm owned prerequisite venv'],
        claim='First useful route only; no twenty-scenario, fault or admission credit.'))
    print('First public Papis route:',len(attempts),'commands,',len(controls),'recorder controls; human time unmeasured.')


if __name__=='__main__':asyncio.run(main())
