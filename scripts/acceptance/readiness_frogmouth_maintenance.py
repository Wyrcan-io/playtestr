"""Public selected maintenance, suffix reconstruction and Unicode relocation."""
import asyncio
import base64
import json
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_frogmouth_first_use import ADDRESS_FOCUS_BORDER,SOURCE,command,environment,fixture_files,runner


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))


def rendered_content(text):
    """Review a deliberate width-only baseline change; saved baselines stay exact."""
    return ''.join(c for c in text if not c.isspace() and not '\u2500'<=c<='\u259f')


async def main():
    root=RAW/'frogmouth'/('maintenance caf\u00e9 '+uuid.uuid4().hex[:10]);root.mkdir(parents=True)
    package=root/'package';shutil.copytree(RAW/'frogmouth/host-contracts',package)
    binary=runner();attempts=[]
    async def run(argv,label,expected=0,input=None):
        result=await execute(argv,'frogmouth','maintenance-'+label,env=environment(),expected=expected,input=input,timeout=180,campaign=Campaign())
        attempts.append(dict(label=label,id=result['id']));return result
    async def test(spec,label,expected=0,extra=()):
        report=root/(label+'.json')
        await run([binary,'test',*extra,'--report',report.relative_to(ROOT),'--artifacts-dir',(root/(label+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],label,expected)
        evidence=load(report);result=evidence['results'][0]
        if evidence['runner_version']!='source-'+SOURCE or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:raise RuntimeError('maintenance runner/cleanup differs')
        return report,result
    spec=package/'N01.json';original=load(spec);fixture=package/'fixtures/N01/sentinel.bin'
    fixture.write_bytes(b'reviewed sentinel revision two\x00\r\n')
    report,result=await test(spec,'intended-file-change',1)
    if result['failure']['category']!='state_assertion_failure':raise RuntimeError('wrong file mismatch diagnosis')
    await run([binary,'report','--input',report.relative_to(ROOT),'--evidence-root',root.relative_to(ROOT),'--output',(root/'diagnosis.html').relative_to(ROOT)],'offline-diagnosis')
    index=next(i for i,s in enumerate(original['steps']) if s.get('state',{}).get('path')=='sentinel.bin')
    await run([binary,'record','--edit',spec.relative_to(ROOT)],'selected-file-update',input=f'/update-state {index+1}\n/review\n/replay\n/save\n')
    changed=load(spec)
    if base64.b64decode(changed['steps'][index]['state']['bytes_base64'])!=fixture.read_bytes():raise RuntimeError('selected byte update differs')
    comparison=load(spec);comparison['steps'][index]=original['steps'][index]
    if comparison!=original:raise RuntimeError('selected state maintenance changed unrelated data')
    await test(spec,'selected-file-replay')
    snapshot=next(s['snapshot'] for s in changed['steps'] if 'snapshot' in s);previous=load(package/'snapshots'/snapshot)
    changed['width']=104
    focus=next(i for i,s in enumerate(changed['steps']) if s.get('expect')==ADDRESS_FOCUS_BORDER)
    changed['steps'][focus]['expect']='\u250f'+'\u2501'*102+'\u2513'
    spec.write_text(json.dumps(changed,indent=2)+'\n',encoding='utf-8',newline='\n');approved=spec.read_bytes()
    _,result=await test(spec,'intended-width-change',1)
    if result['failure']['category']!='snapshot_mismatch':raise RuntimeError('wrong deliberate width diagnosis')
    await test(spec,'selected-screen-update',extra=['--update','--snapshot',snapshot])
    if spec.read_bytes()!=approved:raise RuntimeError('snapshot update changed specification bytes')
    current=load(package/'snapshots'/snapshot)
    if (current['first_row'],current['last_row'])!=(4,26) or current['text']==previous['text']:raise RuntimeError('selected width baseline not changed as declared')
    if rendered_content(current['text'])!=rendered_content(previous['text']) or current['text'].count('Beta body independent source.')!=1:raise RuntimeError('width update changed document content')
    immutable_json(root/'selected-screen-review.json',dict(original=previous,updated=current,original_width=100,updated_width=104,scope='Explicit width/focus-border change only; independent content order/identity check. Actual snapshots retain every exact glyph/space; no product normalization.'))
    await test(spec,'selected-screen-replay')
    suffix_fixture=package/'suffix-fixture';shutil.copytree(package/'fixtures/N01',suffix_fixture)
    gamma=b'# Gamma guide\n\nGamma corrected suffix destination.\n'
    (suffix_fixture/'gamma.md').write_bytes(gamma)
    suffix=package/'rerecorded-suffix.json'
    prefix=['/expect Alpha body independent source.','/text "\\u000e"','/expect Contents']
    controls=[*prefix,*command('beta.md'),'/expect Beta body independent source.','/rerecord 3',
        *command('gamma.md'),'/expect Gamma corrected suffix destination.','/text "\\u0011"','/exit 0']
    expected={**fixture_files(),'sentinel.bin':fixture.read_bytes(),'gamma.md':gamma}
    controls += ['/file '+name for name in sorted(expected)]+['/entries .','/review','/replay','/save']
    argv=[binary,'record','--output',suffix.relative_to(ROOT),'--fixture','suffix-fixture','--temporary-home','--temporary-temp','--width','100','--height','28','--timeout-ms','15000','--run-timeout-ms','120000']
    for name,value in original['env'].items():argv+=['--env',name+'='+value]
    argv+=['--',*original['command']]
    await run(argv,'fresh-suffix-rerecord',input='\n'.join(controls)+'\n')
    exported=load(suffix)
    saved={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in exported['steps'] if s.get('state',{}).get('kind')=='file'}
    if saved!=expected or any(s.get('text')=='beta.md' for s in exported['steps']) or sum(s.get('key')=='Enter' for s in exported['steps'])!=1:raise RuntimeError('discarded wrong document input survived suffix reconstruction')
    await test(suffix,'suffix-ordinary-replay')
    relocated=root/'relocated \u96ea route';shutil.copytree(package,relocated)
    for selected in [spec,suffix]:
        if sha256(relocated/selected.name)!=sha256(selected):raise RuntimeError('relocation changed contract bytes')
        await test(relocated/selected.name,'relocated-'+selected.stem)
    workflow=root/'generated-workflow.yml'
    await run([binary,'workflow','--source-revision',SOURCE,'--os','linux,windows','--suite','artifacts/runner-readiness-ten-project-pass/frogmouth/host-contracts',
        '--build','python scripts/acceptance/readiness_frogmouth_native_prepare.py --target-only','--output',workflow.relative_to(ROOT)],'generate-ordinary-workflow')
    immutable_json(root/'journey.json',dict(attempts=attempts,selected_file_controls=4,suffix_controls=len(controls),unrelated_steps_preserved=True,selected_screen_spec_bytes_preserved=True,
        maintained_spec_sha256=sha256(spec),relocated_spec_sha256=sha256(relocated/spec.name),generated_workflow_sha256=sha256(workflow),phase='development',human_time='unmeasured',generated_workflow_execution=False))
    print('Frogmouth selected maintenance, suffix reconstruction and relocation passed; generated CI remains preparation only.')


if __name__=='__main__':asyncio.run(main())
