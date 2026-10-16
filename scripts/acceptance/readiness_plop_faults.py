"""Three real pinned-source Plop faults with unchanged contracts/restorations.

These are development controls. An open resize case and no archive/native
qualification prevent this packet from admitting the project.
"""
import asyncio
import argparse
import difflib
import json
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_plop_cases import PACKAGE, cases


async def main():
    global PACKAGE
    parser=argparse.ArgumentParser()
    parser.add_argument('--package',type=Path)
    args=parser.parse_args()
    if args.package:
        PACKAGE=args.package.resolve();PACKAGE.relative_to(ROOT)
    campaign=Campaign()
    source=RAW/'active/plop/src'
    folder=RAW/'plop'/'faults'/uuid.uuid4().hex
    folder.mkdir(parents=True)
    contracts={filename:sha256(PACKAGE/filename) for _,filename,_,_ in cases()}
    immutable_json(folder/'contracts-frozen-before-fault-selection.json',dict(
        contracts=contracts,ordinary_development_passes=19,open_case='E05 repeated Windows resize',
        status='contract freeze only; project not qualified',runner_sha256=sha256(RAW/'bin/playtestr.exe' if os.name=='nt' else RAW/'bin/playtestr')))
    # This selection happens after the immutable contract freeze above. No
    # expectation is added to detect the selected same-length corruption.
    definitions=[
      ('F01','packages/plop/src/plop.js','normal-version.json',
       '    runGeneratorByName(generatorName);','    runGeneratorByName(generatorNames[0]);',
       'Selected version generator incorrectly dispatches the first module generator',False),
      ('F02','packages/node-plop/src/generator-runner.js','edge-continue-after-error.json',
       '} catch (failure) {\n        if (actionCfg.abortOnFail !== false) {',
       '} catch (failure) {\n        if (true) {',
       'Action failure incorrectly aborts an explicitly nonfatal action sequence',False),
      ('F03','packages/node-plop/src/actions/_common-action-add-file.js','normal-artifact.json',
       'await fspp.writeFile(fileDestPath, transformedTemplate);',
       'await fspp.writeFile(fileDestPath, transformedTemplate.replace(/name=/g, "namo="));',
       'Success screen retained while same-length persisted payload is corrupted',True),
    ]
    immutable_json(folder/'selected-faults.json',dict(faults=[dict(id=d[0],source=d[1],spec=d[2],risk=d[5],held_out=d[6]) for d in definitions]))
    env=dict(os.environ);env['PATH']=str(RAW/'active/plop/bin')+os.pathsep+env['PATH']
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')

    async def test(identity,phase,spec,expected):
        if {filename:sha256(PACKAGE/filename) for filename in contracts}!=contracts:
            raise RuntimeError('frozen contracts changed')
        report=folder/(identity+'-'+phase+'.json')
        result=await execute([runner,'test','--artifacts-dir',str(folder/(identity+'-'+phase+'-screens')),
            '--report',str(report),str(PACKAGE/spec)],'plop','fault-'+identity+'-'+phase,
            env=env,timeout=120,expected=expected,campaign=campaign)
        observed=json.loads(report.read_text(encoding='utf-8'))['results'][0]
        if not observed['cleanup']['confirmed_exited'] or not observed['workspace']['cleaned']:
            raise RuntimeError('fault/control cleanup unconfirmed')
        return result,observed

    receipts=[]
    for identity,relative,spec,old,new,risk,heldout in definitions:
        baseline,baseline_report=await test(identity,'baseline',spec,0)
        if baseline_report['status']!='passed':raise RuntimeError('baseline did not pass')
        path=source/relative;original=path.read_bytes()
        text=original.decode('utf-8')
        if text.count(old)!=1:raise RuntimeError('pinned mutation anchor is not unique')
        changed=text.replace(old,new).encode('utf-8')
        (folder/(identity+'-original.js')).write_bytes(original)
        patch=''.join(difflib.unified_diff(text.splitlines(True),changed.decode().splitlines(True),
                      fromfile='a/'+relative,tofile='b/'+relative))
        patch_path=folder/(identity+'.patch');patch_path.write_text(patch,encoding='utf-8',newline='\n')
        immutable_json(folder/(identity+'-prepared.json'),dict(id=identity,risk=risk,held_out=heldout,
            source=relative,original_sha256=sha256(path),patch_sha256=sha256(patch_path),
            build='interpreted JavaScript source; fresh ordinary CLI loads patched pinned module, no compilation',
            license='MIT; upstream LICENSE.md retained with pinned source'))
        try:
            path.write_bytes(changed)
            mutated_sha=sha256(path)
            fault,observed=await test(identity,'mutated',spec,1)
            if observed['status']!='failed':raise RuntimeError('unchanged test missed fault')
            if identity=='F01':
                screen=Path(observed['evidence']['screen_path']).resolve()
                screen.relative_to(RAW)
                if screen.stat().st_size>65536 or 'Module name' not in screen.read_text(encoding='utf-8'):
                    raise RuntimeError('wrong-generator fault did not reach the actual wrong prompt')
            if identity=='F03':
                failed=[s for s in observed['steps'] if s['status']=='failed']
                if observed['failure']['category']!='state_assertion_failure' or len(failed)!=1:
                    raise RuntimeError('state corruption did not reach the public oracle')
                index=observed['steps'].index(failed[0])
                if any(s['status']!='passed' for s in observed['steps'][:index]):
                    raise RuntimeError('an earlier screen/exit/snapshot failed instead')
                if failed[0]['state']['workspace_id']!=observed['workspace']['id']:
                    raise RuntimeError('state rejection belongs to another workspace')
                if failed[0]['state']['invocation_id']!=observed['invocation_id']:
                    raise RuntimeError('state rejection belongs to another invocation')
        finally:
            path.write_bytes(original)
            if path.read_bytes()!=original:raise RuntimeError('exact source restoration failed')
        restored,restored_report=await test(identity,'restored',spec,0)
        if restored_report['status']!='passed':raise RuntimeError('unchanged test failed restoration')
        receipt=dict(id=identity,held_out=heldout,baseline=baseline['id'],mutated=fault['id'],
                     restored=restored['id'],source=relative,mutated_source_sha256=mutated_sha,
                     restored_source_sha256=sha256(path),spec_sha256=contracts[spec],
                     rejection=observed['failure']['category'],cleanup_confirmed=True)
        immutable_json(folder/(identity+'-receipt.json'),receipt);receipts.append(receipt)
        print(identity,'detected and exactly restored',flush=True)
    immutable_json(folder/'summary.json',dict(faults=receipts,project_admitted=False,phase='development'))
    print('Fault packet:',folder.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
