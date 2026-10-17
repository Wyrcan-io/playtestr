"""Public selected updates, suffix rerecord, relocation and workflow generation."""
import asyncio
import base64
import json
import os
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_papis_first_use import environment, fixture_files


def load(path):return json.loads(path.read_text(encoding='utf-8-sig'))


async def main():
    root=RAW/'papis'/('maintenance caf\u00e9 '+uuid.uuid4().hex[:10]);root.mkdir(parents=True)
    package=root/'package';shutil.copytree(RAW/'papis/host-contracts',package)
    runner=RAW/('bin/playtestr.exe' if os.name=='nt' else 'bin/playtestr');attempts=[]
    async def run(argv,label,expected=0,input=None):
        result=await execute(argv,'papis','maintenance-'+label,env=environment(),expected=expected,
            input=input,timeout=180,campaign=Campaign());attempts.append(dict(label=label,id=result['id']));return result
    async def test(spec,label,expected=0,extra=()):
        report=root/(label+'.json')
        await run([runner,'test',*extra,'--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(label+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],label,expected)
        outcome=load(report)['results'][0]
        if not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
            raise RuntimeError('maintenance cleanup unconfirmed')
        return report,outcome
    spec=package/'N01.json';original=load(spec);fixture=package/'fixtures/N01/sentinel.txt'
    fixture.write_bytes(b'reviewed sentinel revision two\n')
    report,outcome=await test(spec,'intended-file-change',1)
    if outcome['failure']['category']!='state_assertion_failure':raise RuntimeError('wrong saved-file diagnosis')
    await run([runner,'report','--input',report.relative_to(ROOT),'--evidence-root',root.relative_to(ROOT),
        '--output',(root/'diagnosis.html').relative_to(ROOT)],'offline-diagnosis')
    index=next(i for i,s in enumerate(original['steps']) if s.get('state',{}).get('path')=='sentinel.txt')
    await run([runner,'record','--edit',spec.relative_to(ROOT)],'selected-file-update',
        input=f'/update-state {index+1}\n/review\n/replay\n/save\n')
    changed=load(spec)
    if base64.b64decode(changed['steps'][index]['state']['bytes_base64'])!=fixture.read_bytes():
        raise RuntimeError('selected file update captured different bytes')
    comparison=load(spec);comparison['steps'][index]=original['steps'][index]
    if comparison!=original:raise RuntimeError('selected file update changed unrelated expectations')
    await test(spec,'selected-file-replay')
    snapshot=next(s['snapshot'] for s in changed['steps'] if 'snapshot' in s)
    previous=(package/'snapshots'/snapshot).read_bytes()
    header=('Reviewed <ansired>{doc.html_escape[title]}</ansired>\n'
        ' <ansigreen>{doc.html_escape[author]}</ansigreen>\n'
        '  <ansiblue>({doc.html_escape[year]})</ansiblue> [<ansiyellow>{doc.html_escape[tags]}</ansiyellow>]')
    command=changed['command'];position=command.index('export');command[position:position]=['--set','header-format',header]
    spec.write_text(json.dumps(changed,indent=2)+'\n',encoding='utf-8',newline='\n');approved=spec.read_bytes()
    _,outcome=await test(spec,'intended-screen-prefix-change',1)
    if outcome['failure']['category']!='snapshot_mismatch':raise RuntimeError('wrong intended screen diagnosis')
    await test(spec,'selected-screen-update',extra=['--update','--snapshot',snapshot])
    if spec.read_bytes()!=approved:raise RuntimeError('screen update changed spec or saved expectations')
    expected_screen=previous.replace(b'Alpha Book',b'Reviewed Alpha Book').replace(b'Beta Book',b'Reviewed Beta Book')
    if (package/'snapshots'/snapshot).read_bytes()!=expected_screen:
        raise RuntimeError('independent intended screen prefix differs')
    await test(spec,'selected-screen-replay')
    suffix=package/'rerecorded-suffix.json'
    controls=['/expect Alpha Book','/key Enter','/expect Exporting document','/exit 0','/rerecord 1',
        '/key ArrowDown','/expect 2/2','/key Enter','/expect Exporting document','/exit 0']
    expected=fixture_files();expected['sentinel.txt']=fixture.read_bytes()
    expected.update({'exported/info.yaml':expected['library/beta/info.yaml'],'exported/paper.txt':expected['library/beta/paper.txt']})
    controls += ['/file '+name for name in sorted(expected)]
    controls += ['/entries '+name for name in ['.','library','library/alpha','library/beta','exported']]
    controls += ['/review','/replay','/save']
    argv=[runner,'record','--output',suffix.relative_to(ROOT),'--fixture','fixtures/N01','--temporary-home',
        '--temporary-temp','--width','100','--height','28','--timeout-ms','15000','--run-timeout-ms','120000']
    for name,value in original['env'].items():argv+=['--env',name+'='+value]
    argv+=['--',*original['command']]
    await run(argv,'fresh-suffix-rerecord',input='\n'.join(controls)+'\n')
    exported=load(suffix)
    saved={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in exported['steps'] if s.get('state',{}).get('kind')=='file'}
    if saved!=expected:raise RuntimeError('suffix selected the wrong document or changed preserved bytes')
    if [s for s in exported['steps'] if s.get('key')=='Enter']!=[dict(key='Enter')]:
        raise RuntimeError('discarded wrong-document suffix remains')
    await test(suffix,'suffix-ordinary-replay')
    relocated=root/'relocated \u96ea route';shutil.copytree(package,relocated)
    for selected in [spec,suffix]:
        if sha256(relocated/selected.name)!=sha256(selected):raise RuntimeError('relocation changed a contract')
        await test(relocated/selected.name,'relocated-'+selected.stem)
    workflow=root/'generated-workflow.yml'
    await run([runner,'workflow','--source-revision',os.environ.get('SOURCE_REVISION','f46f2409985af077fd29723ab963d24792eabbbe'),
        '--os','linux,windows','--suite','artifacts/runner-readiness-ten-project-pass/papis/host-contracts',
        '--build','python scripts/acceptance/readiness_papis_native_prepare.py --target-only',
        '--output',workflow.relative_to(ROOT)],'generate-ordinary-workflow')
    immutable_json(root/'journey.json',dict(attempts=attempts,selected_file_controls=4,suffix_controls=len(controls),
        unrelated_steps_preserved=True,selected_screen_spec_bytes_preserved=True,maintained_spec_sha256=sha256(spec),
        relocated_spec_sha256=sha256(relocated/spec.name),generated_workflow_sha256=sha256(workflow),
        phase='development',human_time='unmeasured'))
    print('Public Papis maintenance, suffix, Unicode relocation and generated workflow passed:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
