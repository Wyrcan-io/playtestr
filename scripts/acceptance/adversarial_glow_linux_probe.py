"""Capture a bounded real-PTY startup diagnostic for the owned pristine target."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import pty
import select
import shutil
import signal
import struct
import termios
import time
from adversarial_process import DOC,RAW,ROOT


def main():
    app=Path('/var/tmp/playtestr-adversarial-glow')
    owner=json.loads((app/'task-owned.json').read_text())
    if owner['workspace']!=str(ROOT) or owner['project']!='glow' or app.is_symlink():
        raise RuntimeError('Unknown diagnostic target ownership')
    diagnostic=app/('startup-probe-'+str(time.time_ns()))
    diagnostic.mkdir()
    shutil.copytree(DOC/'glow/fixtures',diagnostic/'fixture')
    for folder in ['home','temporary']:(diagnostic/folder).mkdir()
    pid,master=pty.fork()
    if pid==0:
        os.chdir(diagnostic/'fixture')
        os.environ.update(HOME=str(diagnostic/'home'),XDG_CONFIG_HOME=str(diagnostic/'home'),
            TMPDIR=str(diagnostic/'temporary'),TERM='xterm-256color',GLAMOUR_STYLE='dark',GLOW_TEXT_SIZING='off')
        os.execv(str(app/'bin/glow'),['glow','--style','dark','--mouse=false'])
    fcntl.ioctl(master,termios.TIOCSWINSZ,struct.pack('HHHH',30,100,0,0))
    data=bytearray()
    started=time.monotonic()
    quit_sent=False
    reaped=False
    status=None
    try:
        while time.monotonic()-started<13:
            if not quit_sent and time.monotonic()-started>=8:
                if os.getpgid(pid)!=pid:raise RuntimeError('Unexpected diagnostic process group')
                os.killpg(pid,signal.SIGQUIT)
                quit_sent=True
            readable,_,_=select.select([master],[],[],0.1)
            if readable:
                try:chunk=os.read(master,65536)
                except OSError:break
                if not chunk:break
                data.extend(chunk)
                if len(data)>4*1024*1024:raise RuntimeError('Diagnostic capture limit')
            done,status=os.waitpid(pid,os.WNOHANG)
            if done:
                reaped=True
                break
    finally:
        if not reaped:
            try:os.killpg(pid,signal.SIGKILL)
            except ProcessLookupError:pass
            _,status=os.waitpid(pid,0)
            reaped=True
        os.close(master)
    output=RAW/'glow'/(diagnostic.name+'.txt')
    output.write_bytes(data)
    result=dict(scope='Pristine target direct real-PTY diagnostic; deliberate SIGQUIT is not a qualification run',
        raw_capture=output.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(data).hexdigest(),
        bytes=len(data),sigquit_sent=quit_sent,child_reaped=reaped,wait_status=status)
    output.with_suffix('.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
