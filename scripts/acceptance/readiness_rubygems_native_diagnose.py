"""Declared public unsaved reviews of native failures; never exports baselines."""
import asyncio
import json
import os
import shutil
import uuid
from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_rubygems_cases import environment


async def main():
    diagnostic_id=uuid.uuid4().hex
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
    if os.name=='nt':
        retained=RAW/'experimental/native-root-diagnosis'/diagnostic_id;retained.mkdir(parents=True)
        report=retained/'results.json'
        try:
            await execute([runner,'test','--keep-workspace-on-failure','--report',report.relative_to(ROOT),
                '--artifacts-dir',(retained/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],
                'rubygems','native-exact-contract-retained-root',expected=1,timeout=130,campaign=Campaign())
        except RuntimeError:
            if json.loads(report.read_text())['summary']['passed']!=1:raise
        result=json.loads(report.read_text())['results'][0]
        if result['workspace']['retained']:
            from pathlib import Path
            path=Path(result['workspace']['retained_path']);path.resolve().relative_to((RAW/'tmp').resolve())
            fixture=path/'fixture'
            from itertools import islice
            names=sorted(p.name for p in islice(fixture.iterdir(),257))
            if len(names)>256:raise RuntimeError('diagnostic entry bound')
            immutable_json(retained/'root-names.json',dict(report_sha256=sha256(report),invocation=result['invocation_id'],names=names))
            await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                'scripts/acceptance/readiness_remove_diagnostic_workspace.ps1','-Report',report,
                '-MarkerSHA256',sha256(path/'.playtestr-owner')],
                'rubygems','native-retained-diagnostic-checked-removal',timeout=30,campaign=Campaign())
            immutable_json(retained/'removed.json',dict(report_sha256=sha256(report),workspace_removed=not path.exists()))
    # Separate diagnostic contracts preserve the approved originals. A Ruby
    # exit hook observes only this synthetic fixture's immediate names before
    # the runner performs its unchanged entry assertions.
    diagnostic=RAW/'rubygems/native-probes'/diagnostic_id;diagnostic.mkdir(parents=True)
    shutil.copytree(package/'fixture',diagnostic/'fixture')
    normal=json.loads(spec.read_text())
    # Use the pinned source executable directly, avoiding installed-gem lookup.
    normal['command']=['ruby','-EUTF-8','-e',
        'at_exit { puts "SELECTED_ROOT_ENTRIES=#{Dir.children(Dir.pwd).sort.inspect}" }; load ARGV.shift',
        str(RAW/'active/rubygems/src/exe/bundle'),*json.loads(spec.read_text())['command'][4:]]
    normal['workspace']['fixture']='fixture'
    normal['steps']=[s for s in normal['steps'] if 'snapshot' not in s]
    probes=[('root',normal),('interrupt',json.loads(interrupt.read_text()))]
    for name,code in [('ruby-gets','STDIN.gets'),('ruby-readline','require "readline"; Readline.readline("NATIVE-READLINE-READY>")')]:
        value=json.loads(interrupt.read_text())
        value['command']=['ruby','-e','STDOUT.sync=true; trap("INT") { exit 7 }; '+
            ('puts "NATIVE-RUBY-READY"; ' if name=='ruby-gets' else '')+code+'; exit 9']
        value['steps']=[{'expect':'NATIVE-RUBY-READY' if name=='ruby-gets' else 'NATIVE-READLINE-READY>'},
            {'key':'CtrlC'},{'exit':7}]
        probes.append((name,value))
    for name,value in probes:
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
    immutable_json(RAW/'rubygems'/('native-diagnosis-'+diagnostic_id+'.json'),dict(root_review_attempt=review['id'],
        interrupt_review_attempt=signal['id'],original_spec_unchanged=True,qualification='diagnosis only; no export or scenario admission'))
    print('Public root review and Ctrl-C/Enter discrimination retained without modifying approved specs.')


if __name__=='__main__':asyncio.run(main())
