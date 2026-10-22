"""Independently inspect the first retime failure with an owned direct CLI control."""
import asyncio
import base64
import json
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


async def main():
    target=RAW/'active/jrnl';runtime=json.loads((target/'runtime.json').read_text())
    package=DOC/'jrnl';root=RAW/'jrnl/diagnostic-controls'/uuid.uuid4().hex;root.mkdir(parents=True)
    for name in ['config.yaml','journal.txt']:
        (root/name).write_bytes((package/'fixture'/name).read_bytes())
    before=(root/'journal.txt').read_bytes()
    result=await execute([runtime['python'],'-B','-m','jrnl','--config-file','config.yaml',
        '-contains','alpha','--change-time','2030-02-03 04:05'],'jrnl','direct-retime-order-diagnostic',
        cwd=root,env=environment(target),input='y\n',timeout=30,campaign=NextCampaign())
    actual=(root/'journal.txt').read_bytes()
    expected=(b'[2020-01-02 10:15] beta retained.\nSecond body.\n\n'
              b'[2030-02-03 04:05] alpha ready.\nFirst body.\n')
    input_order=(b'[2030-02-03 04:05] alpha ready.\nFirst body.\n\n'
                b'[2020-01-02 10:15] beta retained.\nSecond body.\n')
    if actual!=input_order:raise ValueError('reduced retime behavior differs; investigate without rebaselining')
    immutable_json(root/'diagnosis.json',dict(schema_version=1,attempt=result['id'],
        before_sha256=__import__('hashlib').sha256(before).hexdigest(),
        actual_bytes_base64=base64.b64encode(actual).decode(),
        expected_chronological_base64=base64.b64encode(expected).decode(),
        source_sha256=sha256(target/'src/jrnl/journals/Journal.py'),
        finding='Actual target retains pre-change in-memory order after retiming an entry across another entry. Journal.open sorts on read; change_date_entries and write do not resort before storage.',
        owner='upstream-target-behavior',runner_fault=False,project_admissions=0,
        scope='Direct CLI diagnostic with owned synthetic files, not PTY/scenario/final execution credit.'))
    print('Direct CLI confirms target storage-order limit; public same-execution file assertion correctly rejected it. Diagnostic retained:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
