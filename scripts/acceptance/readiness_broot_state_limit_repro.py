"""Record the actual public prelaunch limit without running Broot on Windows."""
import asyncio
import base64
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


async def main():
    source=RAW/'old-migration/broot/linux/contracts'
    spec_source=source/'edge-large-tree-content-search.json';contract=load(spec_source)
    states=[s['state'] for s in contract['steps'] if 'state' in s]
    root=RAW/'old-broot/limit-calibration'/uuid.uuid4().hex;root.mkdir(parents=True)
    package=root/'contracts';shutil.copytree(source,package)
    sentinel=root/'must-not-launch.exe'
    if sentinel.exists():raise RuntimeError('prelaunch sentinel unexpectedly exists')
    contract['command']=[str(sentinel)]
    spec=package/spec_source.name;immutable_json(root/'declared.json',dict(
        original_spec_sha256=sha256(spec_source),state_actions=len(states),
        expected_file_bytes=sum(len(base64.b64decode(s['bytes_base64'],validate=True)) for s in states if s['kind']=='file'),
        change='Only replace command with an absent owned absolute sentinel. All original actions, state expectations, fixtures and snapshots retained. No Broot program can execute.',
        old_project_credit=0,final_archive_credit=0))
    import json
    spec.write_text(json.dumps(contract,indent=2)+'\n',encoding='utf-8',newline='\n')
    binary,candidate,cell=runner();report=root/'rejection.json'
    result=await execute([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
        (root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],'core','broot-original-state-limit-public-rejection',
        expected=1,timeout=120,campaign=Campaign())
    row=load(report)['results'][0]
    if (row['failure']['category']!='invalid_spec' or 'state assertions exceed count or aggregate byte limit' not in result['output']
            or row.get('workspace',{}).get('prepared',False)):
        raise RuntimeError('public rejection did not prove the state validation limit before launch')
    immutable_json(root/'verified.json',dict(attempt=result['id'],report_sha256=sha256(report),
        original_spec_sha256=sha256(spec_source),state_actions=len(states),runner_sha256=cell['binary_sha256'],
        scope='Actual public candidate rejects the original 527-check contract before workspace/target launch. Listing alone is not validation evidence.',
        old_project_credit=0,final_archive_credit=0))
    print('Public frozen candidate rejected',len(states),'same-run state checks before launch; source/fixtures unchanged.')


if __name__=='__main__':asyncio.run(main())
