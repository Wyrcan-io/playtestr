"""Public local-document first use with exact source preservation and fresh replay."""
import asyncio
import base64
import json
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256

SOURCE='f46f2409985af077fd29723ab963d24792eabbbe'
PIN='15c3e85a6e84b2e4a6845723acf12beb54c81eb2'


def runner():
    if os.environ.get('GITHUB_ACTIONS')=='true':
        manifest=json.loads((RAW/'frogmouth-native-runner.json').read_text(encoding='utf-8-sig'))
        binary=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
        if manifest['source_revision']!=SOURCE or sha256(binary)!=manifest['copied_sha256']:raise RuntimeError('wrong native candidate')
    else:
        folder=RAW/'development-candidates'/SOURCE
        manifest=json.loads((folder/'candidate.json').read_text(encoding='utf-8-sig'));binary=ROOT/manifest['binary']
        if manifest['source_revision']!=SOURCE or sha256(binary)!=manifest['binary_sha256']:raise RuntimeError('wrong local candidate')
    return binary


def environment():
    runtime=json.loads((RAW/'active/frogmouth/runtime.json').read_text(encoding='utf-8-sig'))
    env={k:os.environ[k] for k in ['PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','LANG','LC_ALL'] if k in os.environ}
    env.update(PATH=str(Path(runtime['python']).parent)+os.pathsep+env.get('PATH',''),PYTHONDONTWRITEBYTECODE='1',PYTHONNOUSERSITE='1',PYTHONIOENCODING='utf-8')
    for name in ['TEMP','TMP','TMPDIR']:env[name]=str(RAW/'tmp')
    return env


def fixture_files():
    return {'alpha.md':b'# Alpha guide\n\nAlpha body independent source.\n\n## First section\n\nReviewed alpha instructions.\n',
        'beta.md':b'# Beta guide\n\nBeta body independent source.\n\n## Second section\n\nReviewed beta instructions.\n',
        'sentinel.bin':b'preserve\x00existing\r\n'}


def command(text):
    return ['/text "/"','/key End','/text '+json.dumps('\x15'+text),'/key Enter']


async def main():
    root=RAW/'frogmouth/first-use'/uuid.uuid4().hex;fixture=root/'fixture';fixture.mkdir(parents=True)
    expected=fixture_files()
    for name,value in expected.items():(fixture/name).write_bytes(value)
    controls=['/expect Alpha body independent source.',*command('beta.md'),'/screen','/expect Beta body independent source.',
        '/snapshot-rows selected.rows.json 4 26','/text "\\u0011"','/exit 0',
        *['/file '+name for name in expected],'/entries .','/review','/replay','/save']
    immutable_json(root/'intent.json',dict(expected_files={name:value.hex() for name,value in expected.items()},controls=controls,handwritten_spec=False,scope='Read-only synthetic local Markdown, second document selection; explicit snapshot rows exclude absolute path omnibox.'))
    binary=runner();attempts=[]
    async def run(argv,label,input=None):
        result=await execute(argv,'frogmouth','first-use-'+label,env=environment(),input=input,timeout=180,campaign=Campaign());attempts.append(result['id']);return result
    version=await run([binary,'--version'],'version')
    if version['output'].strip()!='playtestr source-'+SOURCE:raise RuntimeError('wrong first-use candidate')
    spec=root/'spec.json'
    capture=await run([binary,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
        '--width','100','--height','28','--timeout-ms','15000','--run-timeout-ms','120000','--env','TERM=xterm-256color',
        '--env','PYTHONDONTWRITEBYTECODE=1','--env','PYTHONIOENCODING=utf-8','--','frogmouth','alpha.md'],'public-record-review-replay-save','\n'.join(controls)+'\n')
    value=json.loads(spec.read_text(encoding='utf-8-sig'))
    actual={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in value['steps'] if s.get('state',{}).get('kind')=='file'}
    if actual!=expected:raise RuntimeError('first-use source preservation differs')
    report=root/'ordinary-results.json'
    ordinary=await run([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],'ordinary-test')
    result=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
    if result['status']!='passed' or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:raise RuntimeError('first-use result or cleanup unconfirmed')
    immutable_json(root/'journey.json',dict(attempts=attempts,capture_attempt=capture['id'],ordinary_attempt=ordinary['id'],shell_invocations=len(attempts),recorder_controls=len(controls),
        spec_sha256=sha256(spec),runner_sha256=sha256(binary),target_build_sha256=sha256(RAW/'active/frogmouth/build.json'),handwritten_playtestr_json=False,human_time='unmeasured',
        confounders=['synthetic prepared fixture','agent/source familiarity','warm prerequisite venv'],claim='First useful route only; no scenario/fault/admission credit.'))
    print('Frogmouth public first use:',len(attempts),'commands;',len(controls),'controls; human time unmeasured.')


if __name__=='__main__':asyncio.run(main())
