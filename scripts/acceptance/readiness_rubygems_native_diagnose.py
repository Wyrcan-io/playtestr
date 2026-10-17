"""Declared public unsaved reviews of native failures; never exports baselines."""
import asyncio
import json
import os
import shutil
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
    # Separate diagnostic contracts preserve the approved originals. A Ruby
    # exit hook observes only this synthetic fixture's immediate names before
    # the runner performs its unchanged entry assertions.
    diagnostic=RAW/'rubygems/native-probes';diagnostic.mkdir()
    shutil.copytree(package/'fixture',diagnostic/'fixture')
    normal=json.loads(spec.read_text())
    # Use the pinned source executable directly, avoiding installed-gem lookup.
    normal['command']=['ruby','-EUTF-8','-e',
        'at_exit { puts "SELECTED_ROOT_ENTRIES=#{Dir.children(Dir.pwd).sort.inspect}" }; load ARGV.shift',
        str(RAW/'active/rubygems/src/exe/bundle'),*json.loads(spec.read_text())['command'][4:]]
    normal['workspace']['fixture']='fixture'
    normal['steps']=[s for s in normal['steps'] if 'snapshot' not in s]
    for name,value in [('root',normal),('interrupt',json.loads(interrupt.read_text()))]:
        value['workspace']['fixture']='fixture'
        if name=='interrupt':value['steps'][0]['expect']='rspec/minitest/test-unit/(none):'
        path=diagnostic/(name+'.json');path.write_text(json.dumps(value,indent=2)+'\n')
        report=diagnostic/(name+'-report.json')
        try:
            await execute([runner,'test','--artifacts-dir',(diagnostic/(name+'-evidence')).relative_to(ROOT),
                '--report',report.relative_to(ROOT),path.relative_to(ROOT)],
                'rubygems','native-'+name+'-reduced-diagnosis',expected=1,env=environment(),timeout=130,campaign=Campaign())
        except RuntimeError:
            # A diagnostic passing is useful evidence too. Its initial exit
            # mismatch remains in the immutable ledger; never retry it.
            result=json.loads(report.read_text())
            if result['summary']['passed']!=1 or result['summary']['failed']!=0:raise
            print(name+': unexpected diagnostic success retained; no qualification credit')
    immutable_json(RAW/'rubygems/native-diagnosis.json',dict(root_review_attempt=review['id'],
        interrupt_review_attempt=signal['id'],original_spec_unchanged=True,qualification='diagnosis only; no export or scenario admission'))
    print('Public root review and Ctrl-C/Enter discrimination retained without modifying approved specs.')


if __name__=='__main__':asyncio.run(main())
