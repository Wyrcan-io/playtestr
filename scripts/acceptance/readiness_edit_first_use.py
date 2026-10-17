"""Measure the documented public record/review/replay/save/test route."""
import asyncio
import base64
import json
import os

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256


async def main():
    root=RAW/'edit/first-use';root.mkdir(parents=True,exist_ok=False)
    fixture=root/'fixture';fixture.mkdir()
    (fixture/'note.txt').write_bytes(b'reviewed seed\n')
    (fixture/'sentinel.txt').write_bytes(b'preserve reviewed existing work\n')
    active=RAW/'active/edit';build=json.loads((active/'build.json').read_text())
    editor=active/build['binary_relative_path']
    runner=RAW/'runner-revisions/inherited-interrupt/playtestr.exe'
    if os.name!='nt':raise RuntimeError('initial agent first-use route declared on local Windows only')
    help_result=await execute([runner,'record','--help'],'edit','first-use-public-recorder-help',timeout=30,campaign=Campaign())
    spec=root/'normal-edit.json'
    controls=['/expect reviewed seed','/key End','/text " + tested"','/key CtrlS',
        '/expect reviewed seed + tested','/snapshot edited.txt','/key CtrlQ','/exit 0',
        '/file note.txt','/entries .','/review','/replay','/save']
    capture=await execute([runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture',
        '--temporary-home','--temporary-temp','--width','100','--height','28','--timeout-ms','10000',
        '--run-timeout-ms','120000','--inherit-env','SystemDrive','--',editor,'note.txt'],
        'edit','first-use-public-record-review-replay-save',input='\n'.join(controls)+'\n',timeout=150,campaign=Campaign())
    exported=json.loads(spec.read_text());states=[s['state'] for s in exported['steps'] if 'state' in s]
    file=next(s for s in states if s['path']=='note.txt')
    if base64.b64decode(file['bytes_base64'])!=b'reviewed seed + tested\n':raise RuntimeError('first-use saved bytes differ from independently declared edit')
    entries=next(s for s in states if s['path']=='.')
    if set(entries['entries'])!={'note.txt','sentinel.txt'}:raise RuntimeError('unexpected first-use working-directory side effect')
    report=root/'results.json'
    ordinary=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],
        'edit','first-use-ordinary-public-test',timeout=130,campaign=Campaign())
    outcome=json.loads(report.read_text())['results'][0]
    if outcome['status']!='passed' or not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
        raise RuntimeError('first-use ordinary run or cleanup unconfirmed')
    immutable_json(root/'measurement.json',dict(shell_invocations=3,recorder_controls=len(controls),handwritten_playtestr_json=False,
        help_attempt=help_result['id'],capture_attempt=capture['id'],ordinary_attempt=ordinary['id'],
        spec_sha256=sha256(spec),runner_sha256=sha256(runner),target_build_sha256=sha256(active/'build.json'),
        human_time='unmeasured',confounders=['agent familiarity','prepared synthetic fixture','runtime built before first-use measurement'],
        qualification='development first-use route only; not a project or archive admission'))
    print('Public first-use route passed with three commands and',len(controls),'recorder controls.')


if __name__=='__main__':asyncio.run(main())
