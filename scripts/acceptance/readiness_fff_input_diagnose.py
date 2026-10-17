"""Bounded independent real-PTY input observations; never qualification credit."""
import asyncio
import fcntl
import json
import os
from pathlib import Path
import platform
import re
import select
import signal
import struct
import subprocess
import termios
import time
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


def probe(root, mode, repetition):
    folder = root/(mode+'-'+str(repetition))
    fixture = folder/'fixture'
    fixture.mkdir(parents=True)
    is_folder = mode.startswith('noop-')
    if is_folder:
        (fixture/'folder').mkdir()
        (fixture/'folder/note.txt').write_bytes(b'keep exact bytes\n')
    else:
        (fixture/'source.txt').write_bytes(b'keep exact bytes\n')
    env = dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin', LC_ALL='C', LANG='C', TERM='xterm-256color',
               FFF_LS_COLORS='0', FFF_CD_ON_EXIT='1')
    for name, directory in [('HOME','home'),('TMPDIR','tmp'),('TEMP','tmp'),('TMP','tmp')]:
        path = folder/directory
        path.mkdir(exist_ok=True)
        env[name] = str(path)
    env['FFF_TRASH'] = str(folder/'home/trash')
    script = RAW/'active/fff/src/fff'
    command = ['/bin/bash','--noprofile','--norc',str(script)]
    ledger = Campaign()
    identity = uuid.uuid4().hex
    common = dict(id=identity, project='fff', label='independent-pty-'+mode+'-'+str(repetition))
    ledger.append(dict(**common, event='started', command=command, expected_exit=0, timeout_seconds=12,
                       qualification_credit=False))
    manifest = ledger.identity('fff', [*command, *fixture.rglob('*.txt')])
    ledger.append(dict(**common, event='identified', identity=manifest))
    master, slave = os.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack('HHHH',28,100,0,0))
    raw = bytearray()
    trace = []
    child = None
    timed_out = None
    forced = False
    started = time.monotonic()

    def read_ready(predicate, label):
        deadline = min(started+12, time.monotonic()+2)
        while time.monotonic() < deadline:
            if predicate():
                return
            if select.select([master], [], [], min(.02, max(0,deadline-time.monotonic())))[0]:
                try:
                    block = os.read(master, 16384)
                except OSError:
                    block = b''
                if not block:
                    if predicate():return
                    if child is not None and child.poll() is not None:break
                    continue
                raw.extend(block)
                if len(raw)>128*1024:
                    raise RuntimeError('independent diagnostic PTY output bound')
        raise TimeoutError(label)

    def writing(data, label):
        flags = termios.tcgetattr(slave)[3]
        trace.append(dict(label=label, bytes_hex=data.hex(), canonical=bool(flags&termios.ICANON),
                          echo=bool(flags&termios.ECHO), elapsed_ms=round((time.monotonic()-started)*1000)))
        if os.write(master,data)!=len(data):
            raise RuntimeError('short independent PTY input write')

    def prompt():
        matches = re.findall(rb'\r\x1b\[Krename (?:source\.txt|folder): ([^\r\x1b]*)', raw)
        return matches[-1] if matches else None

    def input_ready(expected):
        return prompt()==expected and not termios.tcgetattr(slave)[3]&termios.ICANON

    def attach():
        os.setsid()
        fcntl.ioctl(slave, termios.TIOCSCTTY, 0)

    try:
        child = subprocess.Popen(command, cwd=fixture, env=env, stdin=slave, stdout=slave, stderr=slave,
                                 close_fds=True, preexec_fn=attach)
        ledger.append(dict(**common,event='launched',pid=child.pid))
        read_ready(lambda:b'folder/' in raw if is_folder else b'source.txt' in raw, 'initial rendered-name output')
        if is_folder:
            if mode=='noop-batched':
                writing(b'gr','one write containing no-op g and rename r')
            else:
                writing(b'g','no-op g')
                writing(b'r','rename r')
            read_ready(lambda:prompt() is not None, 'rename prompt after no-op')
            writing(b'renamed-folder','new folder name')
            read_ready(lambda:prompt()==b'renamed-folder', 'complete rename input')
        else:
            writing(b'r','rename r')
            read_ready(lambda:prompt()==b'', 'initial rename prompt')
            writing(b'draft','proposed rename')
            read_ready(lambda:prompt()==b'draft', 'complete proposed rename')
            if mode=='backspace-batched':
                writing(b'\x7f'*5,'one write containing five backspaces')
            else:
                for number in range(5):
                    if mode=='backspace-observed':
                        expected=b'draft'[:5-number]
                        read_ready(lambda:input_ready(expected), 'observed input-ready prompt before backspace')
                    writing(b'\x7f','backspace '+str(number+1))
                    if mode=='backspace-observed':
                        expected=b'draft'[:4-number]
                        read_ready(lambda:input_ready(expected), 'observed input-ready prompt after backspace')
        writing(b'\r','submit rename')
        offset = len(raw)
        read_ready(lambda:b'\x1b[2K\x1b[?25l\x1b8' in raw[offset:], 'prompt completion output')
        writing(b'q','quit')
        read_ready(lambda:child.poll() is not None, 'natural target exit')
    except TimeoutError as error:
        timed_out = str(error)
    finally:
        if child is not None and child.poll() is None:
            forced = True
            os.killpg(child.pid, signal.SIGKILL)
            child.wait(timeout=3)
        os.close(master)
        os.close(slave)
    (folder/'raw-pty.bin').write_bytes(raw)
    outcome = dict(mode=mode,repetition=repetition,attempt=identity,timed_out=timed_out,forced_shutdown=forced,
                   exit_code=child.returncode if child else None,trace=trace,
                   fixture_files={p.relative_to(fixture).as_posix():p.read_bytes().hex() for p in fixture.rglob('*') if p.is_file()},
                   interpreter_sha256=sha256(Path('/bin/bash').resolve()),source_sha256=sha256(script),
                   raw_output_sha256=sha256(folder/'raw-pty.bin'),qualification_credit=False)
    immutable_json(folder/'observation.json',outcome)
    ledger.append(dict(**common,event='finished',category='diagnostic_observation',exit_code=outcome['exit_code'],
                       harness_cleanup='harness_process_reaped',cleanup_errors=[],qualification_credit=False))
    return outcome


async def main():
    if os.name=='nt':
        raise RuntimeError('independent diagnostic requires a native Unix PTY')
    root = RAW/'fff/input-diagnostics'/uuid.uuid4().hex
    root.mkdir(parents=True)
    modes=['noop-separated','noop-batched','backspace-separated','backspace-batched','backspace-observed']
    immutable_json(root/'intent.json',dict(modes=modes,repetitions_per_mode=4,maximum_seconds_per_probe=12,
                   purpose='Independent raw-PTY input timing observation with exact owned filesystem inspection. No rendered-screen assertion or qualification credit.',
                   differences_from_original='Reduced fixture has one initial selected item and task-owned trash outside the fixture; observed mode additionally waits for the actual noncanonical input mode.'))
    observations=[]
    for mode in modes:
        for number in range(4):
            observation=probe(root,mode,number)
            observations.append(observation)
            print(mode,number,'timeout='+str(observation['timed_out']),'files='+str(list(observation['fixture_files'])),flush=True)
    public=[]
    if platform.system()=='Linux':
        for number in range(10):
            report=root/('public-E03-'+str(number)+'.json')
            try:
                await execute([RAW/'bin/playtestr','test','--report',report.relative_to(ROOT),'--artifacts-dir',
                               (root/('public-evidence-'+str(number))).relative_to(ROOT),
                               'docs/validation/runner-readiness-ten-project-pass/fff/diagnostic-E03/spec.json'],
                              'fff','bounded-unchanged-public-E03-'+str(number),timeout=130,campaign=Campaign())
            except RuntimeError:
                if not report.is_file():
                    raise
            result=json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
            if not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
                raise RuntimeError('unconfirmed public diagnostic cleanup')
            public.append(dict(number=number,status=result['status'],failure=result.get('failure'),report_sha256=sha256(report)))
    immutable_json(root/'summary.json',dict(observations=observations,public_E03_repetitions=public,
                   qualification_credit=False,claim='Bounded diagnostic observations only; green repetitions do not erase original failures or establish cause.'))
    print('Retained bounded independent PTY and unchanged public-input observations:',root.relative_to(ROOT))


if __name__=='__main__':
    asyncio.run(main())
