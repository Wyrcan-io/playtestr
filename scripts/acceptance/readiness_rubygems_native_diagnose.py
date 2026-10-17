"""Declared public unsaved reviews of native failures; never exports baselines."""
import asyncio
import json
import os
import shutil
import uuid
from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_rubygems_cases import environment


async def linux_diagnosis(package,runner):
    """Review selected lock bytes and distinguish target bytes from VT parsing."""
    import base64
    import errno
    import pty
    import select
    import signal
    import time
    root=RAW/'rubygems/linux-diagnosis'/uuid.uuid4().hex;root.mkdir(parents=True)
    spec=package/'normal-lock.json';before=sha256(spec)
    review=await execute([runner,'record','--edit',spec.relative_to(ROOT)],'rubygems','linux-unsaved-lock-byte-review',
        input='/update-state 3\n/review\n/quit\n',expected=130,env=environment(),timeout=130,campaign=Campaign())
    assert sha256(spec)==before
    runtime=json.loads((RAW/'active/rubygems/runtime.json').read_text())
    ruby=runtime['installed_ruby_executable']
    metadata=await execute([ruby,'-e','require "readline"; require "bundler"; puts RUBY_DESCRIPTION; puts Readline::VERSION; puts Gem::Platform.local; puts Bundler.local_platform; p Gem.platforms.map(&:to_s); p Gem::Platform.instance_method(:initialize).source_location'],
        'rubygems','linux-readline-and-platform-identity',env=environment(),timeout=30,campaign=Campaign())
    env={k:v for k,v in environment().items() if k in ['PATH','RUBYLIB','LANG','LC_ALL']}
    home=root/'home';home.mkdir();env.update(HOME=str(home),INPUTRC=os.devnull,TERM='xterm-256color',TMPDIR=str(root))
    code='require "readline"; STDOUT.sync=true; puts "\\e[31mDIRECT-READY\\e[0m"; Readline.readline("\\e[32mPROMPT>\\e[0m"); puts "COMPLETE"'
    pid,fd=pty.fork()
    if pid==0:
        os.chdir(root)
        os.execve(ruby,[ruby,'-e',code],env)
    data=bytearray();status=None;sent=False;deadline=time.monotonic()+5
    try:
        while time.monotonic()<deadline:
            if select.select([fd],[],[],0.05)[0]:
                try:block=os.read(fd,4096)
                except OSError as error:
                    if error.errno==errno.EIO:break
                    raise
                if not block:break
                data.extend(block)
                if len(data)>65536:raise RuntimeError('synthetic raw PTY byte cap')
                if b'PROMPT>' in data and not sent:os.write(fd,b'reviewed\n');sent=True
            if status is None:
                observed,status_value=os.waitpid(pid,os.WNOHANG)
                if observed:status=status_value
        while status is None and time.monotonic()<deadline:
            observed,status_value=os.waitpid(pid,os.WNOHANG)
            if observed:status=status_value
            else:time.sleep(0.01)
        if status is None:raise RuntimeError('synthetic Readline PTY deadline')
    finally:
        if status is None:
            if os.getpgid(pid)!=pid:raise RuntimeError('owned synthetic process group changed')
            os.killpg(pid,signal.SIGKILL);_,status=os.waitpid(pid,0)
        os.close(fd)
    immutable_json(root/'observation.json',dict(lock_review_attempt=review['id'],metadata_attempt=metadata['id'],
        synthetic_raw_bytes_base64=base64.b64encode(data).decode(),exit_code=os.waitstatus_to_exitcode(status),
        reaped=True,qualification='diagnosis only; no baseline export or project admission'))
    print('Selected lock bytes and bounded synthetic native Readline raw bytes retained.')


async def main():
    diagnostic_id=uuid.uuid4().hex
    package=RAW/'rubygems/host-contracts'
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    if os.name!='nt':
        await linux_diagnosis(package,runner)
        return
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
