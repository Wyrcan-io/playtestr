"""Real target control for a file-only transfer losing an empty fixture directory."""
import asyncio
import json
import os
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256
from readiness_papis_first_use import environment


async def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/papis'
    profile=docs/'native-profiles/windows' if os.name=='nt' else docs
    root=RAW/'papis/transfer-controls'/uuid.uuid4().hex;package=root/'package';package.mkdir(parents=True)
    for source in (profile/'contracts').rglob('*'):
        if source.is_file():
            destination=package/source.relative_to(profile/'contracts')
            destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,destination)
    spec=package/'E10.json';before={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}
    directory=package/'fixtures/E10/library'
    if directory.exists():raise RuntimeError('file-only transfer unexpectedly preserved empty fixture directory')
    runner=RAW/('bin/playtestr.exe' if os.name=='nt' else 'bin/playtestr');records=[]
    for phase,expected in [('before',1),('after',0)]:
        if phase=='after':directory.mkdir()
        report=root/(phase+'.json')
        attempt=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(phase+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],'papis','file-only-transfer-'+phase,
            env=environment(),expected=expected,timeout=90,campaign=Campaign())
        outcome=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
        if outcome['status']!=('failed' if expected else 'passed') or not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
            raise RuntimeError('transfer control outcome or cleanup differs')
        if expected and outcome['failure']['category']!='unexpected_exit':raise RuntimeError('different transfer failure')
        records.append(dict(phase=phase,attempt=attempt['id'],report_sha256=sha256(report)))
    after={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}
    if after!=before:raise RuntimeError('fixture setup changed frozen file bytes')
    immutable_json(root/'verified.json',dict(records=records,contract_sha256=sha256(spec),
        changed_files=[],created_directory='fixtures/E10/library',new_scenario_credit=0,
        claim='Real unchanged E10 fails after file-only transfer and passes after only its declared empty fixture directory is restored.'))
    print('Unchanged real Papis E10 fails before explicit empty-directory setup and passes afterward; all package files unchanged.')


if __name__=='__main__':asyncio.run(main())
