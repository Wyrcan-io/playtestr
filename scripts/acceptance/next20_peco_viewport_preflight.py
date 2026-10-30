"""Validate the independently derived wider snapshot before final freezing."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_batch_snapshots import apply
from next20_candidate import executable
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json, sha256


async def main():
    package=DOC/'peco';target=RAW/'active/peco';canonical=RAW/'peco/host-contracts'
    root=RAW/'peco'/('viewport-preflight-'+uuid.uuid4().hex);contracts=root/'contracts';shutil.copytree(canonical,contracts)
    declaration=json.loads((package/'viewport-snapshot-declaration-v1.json').read_text())
    profiles={'4':{'snapshots/normal-selection.txt':dict(original_sha256=declaration['original_snapshot_sha256'],reviewed_input=declaration['reviewed_input'],reviewed_sha256=declaration['reviewed_sha256'])}}
    changes=apply(contracts,package,profiles,4)
    runtime=json.loads((target/'runtime.json').read_text());build=json.loads((target/'build.json').read_text());runner=executable('native-exit-v1')
    spec=contracts/'normal-selection.json';value=json.loads(spec.read_text());value.update(width=110,height=26)
    value['command'][0]=os.path.relpath(runtime['native'],contracts).replace('\\','/')
    spec.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    def verify():
        for name,hashed in build['compiled_files'].items():
            if sha256(Path(runtime['native']).parent/name)!=hashed:raise ValueError('actual viewport app/capture bytes changed')
        for name,hashed in json.loads((package/'source-provenance.json').read_text())['files'].items():
            if sha256(target/'src'/name)!=hashed:raise ValueError('viewport source is not pristine')
    verify();immutable_json(root/'planned.json',dict(schema_version=1,source_declaration_sha256=sha256(package/'viewport-snapshot-declaration-v1.json'),
        spec_sha256=sha256(spec),snapshot_changes=changes,runner_sha256=sha256(runner),app_sha256=build['actual_target_sha256'],capture_sha256=build['binary_sha256'],final_ordinary_credit=0))
    report=root/'viewport.report.json'
    result=await execute([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],
        'peco','independently-declared-width110-native-preflight',cwd=ROOT,env=environment(target),timeout=140,campaign=NextCampaign())
    row=json.loads(report.read_text())['results'][0]
    if row['status']!='passed' or any(s['status']!='passed' for s in row['steps']) or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('viewport preflight/cleanup incomplete')
    verify();immutable_json(root/'summary.json',dict(schema_version=1,attempt=result['id'],report_sha256=sha256(report),spec_sha256=sha256(spec),snapshot_sha256=sha256(contracts/'snapshots/normal-selection.txt'),
        independent_expectation_exact=True,selected_stdout_and_preserved_files_exact=True,source_and_binaries_unchanged=True,final_ordinary_credit=0,project_admissions=0))
    print('Actual width110 snapshot matches independent pinned-layout derivation; selected bytes and all preserved files exact. No final credit.')


if __name__=='__main__':asyncio.run(main())
