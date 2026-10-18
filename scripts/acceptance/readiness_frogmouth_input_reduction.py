"""Exercise the pinned Textual Win32 reader through a real public-runner PTY."""
import asyncio
import json
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json
from readiness_frogmouth_first_use import environment,runner


async def main():
    if os.name!='nt':raise RuntimeError('Windows-only diagnostic')
    root=RAW/'frogmouth/input-reduction'/uuid.uuid4().hex;root.mkdir(parents=True)
    (root/'fixture').mkdir()
    runtime=json.loads((RAW/'active/frogmouth/runtime.json').read_text(encoding='utf-8-sig'))
    spec=dict(version=3,name='Synthetic Win32 input diagnostic, zero qualification credit',command=[runtime['python'],'-u',str(ROOT/'scripts/acceptance/readiness_frogmouth_console_probe.py'),str(root/'console-records.json')],
        workspace=dict(fixture='fixture',cwd='.',home='temporary',temp='temporary'),
        width=100,height=28,timeout_ms=10000,run_timeout_ms=15000,max_output_bytes=100000,
        steps=[dict(expect='console diagnostic ready'),dict(text='/\x11'),dict(expect='synthetic slash received'),dict(exit=0)])
    immutable_json(root/'diagnostic.json',spec)
    await execute([runner(),'test','--report',root/'results.json',root/'diagnostic.json'],'frogmouth','synthetic-real-console-input-reduction',env=environment(),timeout=30,campaign=Campaign())
    print((root/'console-records.json').read_text(encoding='utf-8'))
    print('Synthetic native console read passed; no target scenario/compatibility credit.')


if __name__=='__main__':asyncio.run(main())
