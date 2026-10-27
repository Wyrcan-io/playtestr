"""Bounded real-PTY input/termios diagnosis; no Playtestr qualification credit."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import time

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign,owned_environment
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


def probe(mode,number):
    import errno
    import fcntl
    import pty
    import select
    import signal
    import struct
    import subprocess
    import termios
    target=RAW/'active/cargo-generate';binary=target/'bin/cargo-generate';root=RAW/'cargo-generate/input-diagnostic/v1'/f'{mode}-{number}'
    root.mkdir(parents=True,exist_ok=False);fixture=root/'fixture';shutil.copytree(DOC/'cargo-generate/fixture',fixture)
    approved=json.loads((DOC/'cargo-generate/native-linux-preflight-reviewed-audit.json').read_text())
    if sha256(binary)!=approved['target_binary_sha256']:raise ValueError('diagnostic target differs from exact retained reviewed native build')
    env=environment(target);env.update(TERM='xterm-256color',LANG='C.UTF-8',LC_ALL='C.UTF-8',USER='synthetic',USERNAME='synthetic',GIT_CONFIG_GLOBAL='/dev/null',GIT_CONFIG_NOSYSTEM='1')
    command=[str(binary),'generate','--path','template','--vcs','none','--no-workspace']
    immutable_json(root/'planned.json',dict(schema_version=1,mode=mode,number=number,binary_sha256=sha256(binary),command=command,
        fixture_files={p.relative_to(fixture).as_posix():sha256(p) for p in fixture.rglob('*') if p.is_file()},timeout_seconds=5,output_limit=65536,qualification_credit=0))
    master,slave=pty.openpty();fcntl.ioctl(slave,termios.TIOCSWINSZ,struct.pack('HHHH',24,120,0,0))
    def child_setup():os.setsid();fcntl.ioctl(0,termios.TIOCSCTTY,0)
    process=subprocess.Popen(command,cwd=fixture,env=env,stdin=slave,stdout=slave,stderr=slave,preexec_fn=child_setup,close_fds=True)
    os.close(slave);deadline=time.monotonic()+5;raw=bytearray();writes=[];error=None;forced=False
    def receive():
        remaining=deadline-time.monotonic()
        if remaining<=0:raise TimeoutError('diagnostic target deadline')
        ready,_,_=select.select([master],[],[],min(.01,remaining))
        if ready:
            try:block=os.read(master,4096)
            except OSError as exc:
                if exc.errno==errno.EIO:return False
                raise
            if not block:return False
            raw.extend(block)
            if len(raw)>65536:raise ValueError('diagnostic raw output bound')
        return True
    def until(text):
        while text not in raw:
            if not receive():raise ValueError('target exited before positive diagnostic checkpoint')
    def send(value):
        flags=termios.tcgetattr(master)[3]
        writes.append(dict(input_base64=base64.b64encode(value).decode(),offset=len(raw),echo=bool(flags&termios.ECHO),canonical=bool(flags&termios.ICANON),elapsed_seconds=5-(deadline-time.monotonic())))
        if os.write(master,value)!=len(value):raise ValueError('partial diagnostic PTY input')
    try:
        for prompt,value in [(b'Project Name',b'synthetic-notes'),(b'Project owner',b'Ada')]:
            until(prompt);send(value)
            if mode!='immediate':until(value)
            if mode=='observe-text-and-raw':
                while termios.tcgetattr(master)[3]&termios.ECHO:receive()
            send(b'\r')
        until(b'Project mode');send(b'\r');until(b'Include documentation');send(b'\r')
        while process.poll() is None:receive()
        while receive():pass
    except Exception as exc:error=str(exc)
    finally:
        if process.poll() is None:
            forced=True;os.killpg(process.pid,signal.SIGKILL)
        status=process.wait(timeout=2);os.close(master)
    try:os.killpg(process.pid,0)
    except ProcessLookupError:group_absent=True
    else:group_absent=False
    state={p.relative_to(fixture).as_posix():sha256(p) for p in fixture.rglob('*') if p.is_file()}
    immutable_json(root/'observed.json',dict(schema_version=1,mode=mode,number=number,writes=writes,
        raw_base64=base64.b64encode(raw).decode(),raw_sha256=__import__('hashlib').sha256(raw).hexdigest(),
        raw_bytes=len(raw),target_exit=status,forced=forced,error=error,confirmed_process_group_absent=group_absent,
        final_files=state,ordinary_credits=0,calibration_credits=0))
    if error or status!=0 or not group_absent:raise ValueError('diagnostic probe incomplete: '+str(error))
    print(mode,number,'real target exited0; raw bytes',len(raw),'writes',[(w['echo'],w['canonical']) for w in writes],flush=True)


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--probe',choices=['immediate','observe-text','observe-text-and-raw']);parser.add_argument('--number',type=int)
    parser.add_argument('--packet',type=Path);args=parser.parse_args()
    if args.probe:
        if args.number not in range(6):raise ValueError('diagnostic repetition bound')
        probe(args.probe,args.number);return
    if args.packet is None or os.name=='nt':raise ValueError('native Linux packet required')
    packet=args.packet.resolve(strict=True);packet.relative_to(RAW.resolve(strict=True))
    target=RAW/'active/cargo-generate'
    if target.exists():raise ValueError('preserve any active target')
    target.mkdir(parents=True)
    source=packet/'active/cargo-generate';packed=packet/'cargo-generate/native-preflight/linux'
    index=json.loads((packed/'compiled-binary-index.json').read_text());archive=packed/'compiled-binary.tar.xz'
    if sha256(archive)!=index['archive_sha256']:raise ValueError('original built native archive changed')
    for name in ['build.json','runtime.json','installed-inventory.json','task-owned.json','acquisition.json','source.tar.gz','dependency-source-catalog.json','dependency-fetch-review.json']:
        shutil.copyfile(source/name,target/name)
    binary=target/'bin/cargo-generate';binary.parent.mkdir()
    with tarfile.open(archive,'r:xz') as stream:
        member=stream.getmember('cargo-generate')
        if not member.isfile() or member.size>64*1024**2:raise ValueError('diagnostic executable bound')
        binary.write_bytes(stream.extractfile(member).read(64*1024**2+1));binary.chmod(0o755)
    if sha256(binary)!=index['files']['cargo-generate']['sha256']:raise ValueError('actual reused native executable differs')
    diagnostic_root=RAW/'cargo-generate/input-diagnostic/v1';diagnostic_root.mkdir(parents=True)
    immutable_json(diagnostic_root/'runtime-reference.json',dict(schema_version=1,original_run='40467049451',
        actual_binary_sha256=sha256(binary),original_binary_archive_sha256=sha256(archive),original_binary_index_sha256=sha256(packed/'compiled-binary-index.json'),
        original_build_sha256=sha256(target/'build.json'),new_compile=False,new_qualification_credit=0))
    campaign=NextCampaign(phase='development')
    for mode in ['immediate','observe-text','observe-text-and-raw']:
        for number in range(6):
            await execute([sys.executable,'-B',Path(__file__).resolve(),'--probe',mode,'--number',str(number)],'cargo-generate',
                'native-input-termios-diagnostic-'+mode+'-'+str(number),cwd=ROOT,env=owned_environment(),timeout=15,campaign=campaign)
    observed=[json.loads(path.read_text()) for path in diagnostic_root.glob('*/observed.json')]
    if len(observed)!=18 or not all(row['confirmed_process_group_absent'] and row['target_exit']==0 and not row['error'] for row in observed):raise ValueError('incomplete diagnostic target cleanup')
    inventory={};total=0
    for path in target.rglob('*'):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('unreviewed diagnostic target link')
        if path.is_file():
            total+=path.stat().st_size
            if len(inventory)>=1000 or total>80*1024**2:raise ValueError('diagnostic disposal inventory bound')
            inventory[path.relative_to(target).as_posix()]=dict(bytes=path.stat().st_size,sha256=sha256(path))
    if json.loads((target/'task-owned.json').read_text())['workspace']!=str(ROOT):raise ValueError('diagnostic target owner differs')
    immutable_json(diagnostic_root/'cleanup-inventory.json',dict(schema_version=1,owned_target=str(target),files=inventory,bytes=total,confirmed_all18_process_groups_absent=True))
    for name,row in inventory.items():
        if sha256(target/name)!=row['sha256']:raise ValueError('diagnostic owned payload changed before disposal')
    shutil.rmtree(target)
    if target.exists():raise ValueError('diagnostic target remains')
    immutable_json(diagnostic_root/'cleanup-removed.json',dict(schema_version=1,owned_target_removed=True,inventory_sha256=sha256(diagnostic_root/'cleanup-inventory.json'),qualification_credit=0))
    print('Eighteen bounded real-PTY diagnostic executions complete; actual target payload checked-removed; zero ordinary/calibration qualification credit')


if __name__=='__main__':asyncio.run(main())
