"""Declared public unsaved reviews of native failures; never exports baselines."""
import asyncio
import json
import os
from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_rubygems_cases import environment


async def main():
    package=RAW/'rubygems/host-contracts'
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    spec=package/'normal-gem.json';original=sha256(spec)
    steps=json.loads(spec.read_text())['steps']
    selected=next(i+1 for i,s in enumerate(steps) if s.get('state',{}).get('path')=='.')
    review=await execute([runner,'record','--edit',spec.relative_to(ROOT)],'rubygems','native-unsaved-root-entry-review',
        input=f'/update-state {selected}\n/review\n/quit\n',expected=130,env=environment(),timeout=130,campaign=Campaign())
    assert sha256(spec)==original
    interrupt=package/'edge-interrupt.json';before=sha256(interrupt)
    # The original test already delivered Ctrl-C and timed out. Here review that
    # same public prefix, then use one Enter to distinguish a queued line byte
    # from a delivered interrupt. No export, no admitted scenario or retry credit.
    signal=await execute([runner,'record','--edit',interrupt.relative_to(ROOT)],'rubygems','native-interrupt-line-diagnosis',
        input='/rerecord 2\n/screen\n/key Enter\n/screen\n/exit 1\n/quit\n',expected=130,
        env=environment(),timeout=60,campaign=Campaign())
    assert sha256(interrupt)==before
    immutable_json(RAW/'rubygems/native-diagnosis.json',dict(root_review_attempt=review['id'],
        interrupt_review_attempt=signal['id'],original_spec_unchanged=True,qualification='diagnosis only; no export or scenario admission'))
    print('Public root review and Ctrl-C/Enter discrimination retained without modifying approved specs.')


if __name__=='__main__':asyncio.run(main())
