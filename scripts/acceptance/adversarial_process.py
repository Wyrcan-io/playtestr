"""Bounded native command execution and append-only campaign attempts.

The harness is not a security sandbox. Only reviewed commands run here.
"""
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/validation/ten-new-project-adversarial-pass'
RAW = ROOT / 'artifacts/ten-new-project-adversarial-pass'

def append(record):
    DOC.mkdir(parents=True, exist_ok=True)
    with (DOC/'attempts.jsonl').open('a',encoding='utf-8') as stream:
        stream.write(json.dumps(record,ensure_ascii=True)+'\n')
        stream.flush()
        os.fsync(stream.fileno())

def contract_identity(project, argv):
    """Capture current bytes before execution, without reading ambient secrets."""
    package=DOC/project
    contracts={}
    if package.is_dir():
        for path in sorted(package.rglob('*')):
            if path.is_file() and not path.is_symlink() and (
                    path.parent==package and path.suffix=='.json' or
                    'snapshots' in path.relative_to(package).parts or
                    'fixtures' in path.relative_to(package).parts):
                if path.stat().st_size>4*1024*1024:
                    raise RuntimeError('Contract identity file exceeds independent bound')
                contracts[path.relative_to(package).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    runner=Path(str(argv[0]))
    identity={'contracts':contracts}
    inputs={}
    for argument in argv[1:]:
        path=Path(str(argument))
        if not path.is_absolute():
            path=ROOT/path
        if path.suffix=='.json' and path.is_file() and path.stat().st_size<=4*1024*1024:
            inputs[str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
    identity['existing_json_inputs']=inputs
    if runner.is_file() and runner.name.startswith('playtestr'):
        identity['runner_sha256']=hashlib.sha256(runner.read_bytes()).hexdigest()
    runtime=ROOT/'.cache/ten-new-project-apps'/project/'runtime.json'
    if not runtime.is_file() and os.name!='nt':
        runtime=Path('/var/tmp')/('playtestr-adversarial-'+project)/'runtime.json'
    if runtime.is_file():
        marker=json.loads((runtime.parent/'task-owned.json').read_text(encoding='utf-8'))
        if marker.get('workspace')!=str(ROOT) or marker.get('project')!=project:
            raise RuntimeError('Unowned runtime identity')
        data=json.loads(runtime.read_text(encoding='utf-8'))
        identity['target_revision']=data.get('source')
        identity['runtime_sha256']=hashlib.sha256(runtime.read_bytes()).hexdigest()
        target_source=Path(data['source_path']).resolve()
        target_source.relative_to(runtime.parent.resolve())
        source_files={}
        for path in sorted(target_source.rglob('*')):
            if path.is_file() and not path.is_symlink() and path.suffix in {'.py','.go','.rs','.c','.h','.toml'} and '.git' not in path.relative_to(target_source).parts:
                if path.stat().st_size>4*1024*1024:
                    raise RuntimeError('Target source identity file bound')
                source_files[path.relative_to(target_source).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        identity['target_source_files']=source_files
    # Stable inventories are stored once. Thousands of repetitions retain an
    # exact reference without multiplying the same approved fixture manifest.
    encoded=(json.dumps(identity,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode('utf-8')
    digest=hashlib.sha256(encoded).hexdigest()
    directory=DOC/'identities'
    directory.mkdir(parents=True,exist_ok=True)
    manifest=directory/(digest+'.json')
    if manifest.exists():
        if manifest.read_bytes()!=encoded:
            raise RuntimeError('Existing identity manifest differs from its digest')
    else:
        try:
            with manifest.open('xb') as stream:
                stream.write(encoded)
        except FileExistsError:
            if manifest.read_bytes()!=encoded:
                raise RuntimeError('Concurrent identity manifest mismatch')
    return {'manifest':manifest.relative_to(DOC).as_posix(),'sha256':digest,
            'runner_sha256':identity.get('runner_sha256'),'target_revision':identity.get('target_revision')}

async def stop(proc):
    if os.name=='nt':
        if proc.returncode is not None:
            return
        killer=await asyncio.create_subprocess_exec('taskkill','/PID',str(proc.pid),'/T','/F',
            stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL)
        await asyncio.wait_for(killer.wait(),timeout=5)
    else:
        try:
            os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:
            pass
    # Waiting before draining a full PIPE can deadlock asyncio's transport.
    # The caller drains bounded output first, then reaps the process.

async def execute(argv,project,label,*,cwd=ROOT,env=None,input=None,timeout=120,
                  output_cap=4*1024*1024,expected=0,on_output=None,load=False):
    run_id=uuid.uuid4().hex
    directory=RAW/project/run_id
    directory.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    record=dict(id=run_id,event='started',project=project,label=label,
                utc=datetime.now(timezone.utc).isoformat(),host=platform.platform(),
                timeout_seconds=timeout,output_cap=output_cap,
                variation='owned 2-second 8-MiB SHA256 CPU worker' if load else 'ordinary',
                expected_exit=expected,evidence=str(directory.relative_to(ROOT)))
    record['identity']=contract_identity(project,argv)
    append(record)
    output=bytearray()
    proc=None
    category='harness_error'
    result=None
    worker=None
    original_error=None
    try:
        if load:
            worker=await asyncio.create_subprocess_exec(sys.executable,'-c',
                'import hashlib,time; b=b"x"*(8*1024*1024); end=time.monotonic()+2; '
                '\nwhile time.monotonic()<end: hashlib.sha256(b).digest()',
                stdin=asyncio.subprocess.DEVNULL,stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL)
        proc=await asyncio.create_subprocess_exec(*map(str,argv),cwd=cwd,env=env,
            stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,start_new_session=os.name!='nt')
        append(dict(id=run_id,event='launched',project=project,label=label,pid=proc.pid))
        async def interact():
            if input is not None:
                proc.stdin.write(input.encode('utf-8'))
                await proc.stdin.drain()
            if on_output is None:
                proc.stdin.close()
            while True:
                block=await proc.stdout.read(16384)
                if not block:
                    break
                remaining=output_cap-len(output)
                output.extend(block[:remaining])
                if len(block)>remaining:
                    raise RuntimeError('independent harness output cap')
                if on_output is not None:
                    await on_output(proc,output,directory)
            return await proc.wait()
        result=await asyncio.wait_for(interact(),timeout=timeout)
        category='passed' if result==expected else 'exit_mismatch'
        if result!=expected:
            raise RuntimeError(f'{label}: expected exit {expected}, got {result}; {directory}')
        return dict(id=run_id,output=output.decode('utf-8',errors='replace'),directory=directory,
                    returncode=result,seconds=time.monotonic()-start)
    except asyncio.TimeoutError as error:
        original_error=error
        error.evidence_id=run_id
        error.evidence_directory=str(directory)
        category='harness_timeout'
        (directory/'harness-error.json').write_text(json.dumps(dict(
            type=type(error).__name__,message='independent deadline exceeded'),indent=2)+'\n',encoding='utf-8')
        raise
    except Exception as error:
        original_error=error
        error.evidence_id=run_id
        error.evidence_directory=str(directory)
        if str(error)=='independent harness output cap':
            category='harness_output_limit'
        (directory/'harness-error.json').write_text(json.dumps(dict(
            type=type(error).__name__,message=str(error)[:4096]),indent=2)+'\n',encoding='utf-8')
        raise
    finally:
        cleanup_errors=[]
        async def clean(operation,awaitable):
            try:
                return await awaitable
            except Exception as error:
                cleanup_errors.append(operation+': '+type(error).__name__+': '+str(error)[:1024])
        if worker is not None:
            try:
                await asyncio.wait_for(worker.wait(),timeout=3)
            except asyncio.TimeoutError:
                worker.kill()
                await clean('reap load worker',asyncio.wait_for(worker.wait(),timeout=2))
        cleanup='not_started'
        if proc is not None:
            if on_output is not None and proc.returncode is None and not proc.stdin.is_closing():
                try:
                    proc.stdin.write(b'/quit\n')
                    await proc.stdin.drain()
                    proc.stdin.close()
                    async def finish_capture():
                        while block:=await proc.stdout.read(16384):
                            remaining=output_cap-len(output)
                            output.extend(block[:max(0,remaining)])
                        await proc.wait()
                    await asyncio.wait_for(finish_capture(),timeout=5)
                    cleanup='recorder_gracefully_cancelled'
                except (OSError,RuntimeError,asyncio.TimeoutError):
                    cleanup='forced_harness_cleanup'
            await clean('terminate owned command',stop(proc))
            if not proc.stdin.is_closing():
                proc.stdin.close()
            try:
                await asyncio.wait_for(proc.stdin.wait_closed(),timeout=1)
            except (OSError,asyncio.TimeoutError):
                pass
            # Reap pipe transports before closing a Windows Proactor loop.
            # Independently bound even this final drain after process exit.
            async def drain_stopped():
                drained=0
                while block:=await proc.stdout.read(16384):
                    drained+=len(block)
                    remaining=output_cap-len(output)
                    output.extend(block[:max(0,remaining)])
                    if drained>4*1024*1024:
                        raise RuntimeError('stopped process pipe-drain bound')
            await clean('drain stopped command',asyncio.wait_for(drain_stopped(),timeout=2))
            await clean('reap owned command',asyncio.wait_for(proc.wait(),timeout=5))
            if cleanup=='not_started':
                cleanup='harness_process_reaped'
        (directory/'console.log').write_bytes(output)
        if cleanup_errors:
            cleanup='harness_cleanup_unconfirmed'
            if original_error is None:
                category='harness_cleanup_error'
            (directory/'cleanup-errors.json').write_text(json.dumps(cleanup_errors,indent=2)+'\n',encoding='utf-8')
        append(dict(id=run_id,event='finished',project=project,label=label,
                    category=category,exit_code=result,seconds=round(time.monotonic()-start,4),
                    console_sha256=hashlib.sha256(output).hexdigest(),
                    harness_cleanup=cleanup,cleanup_errors=cleanup_errors,output_bytes=len(output)))
        if cleanup_errors:
            if original_error is not None:
                original_error.add_note('Separate cleanup failures: '+'; '.join(cleanup_errors))
            else:
                raise RuntimeError('Separate cleanup failures: '+'; '.join(cleanup_errors))

def run(*args,**kwargs):
    return asyncio.run(execute(*args,**kwargs))
