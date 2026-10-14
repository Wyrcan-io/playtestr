"""Bounded native command execution and append-only campaign attempts.

The harness is not a security sandbox. Only reviewed commands run here.
"""
import asyncio
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import platform
import signal
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/validation/ten-new-project-adversarial-pass'
RAW = ROOT / 'artifacts/ten-new-project-adversarial-pass'

@contextmanager
def ledger_lock():
    # Atomic directory creation is shared by native Windows and WSL/DrvFS;
    # flock and Windows byte locks would use different lock protocols here.
    RAW.mkdir(parents=True,exist_ok=True)
    lock=RAW/'.attempts-lock'
    deadline=time.monotonic()+10
    while True:
        try:
            lock.mkdir()
            break
        except (FileExistsError, PermissionError, FileNotFoundError) as error:
            # Windows can report ERROR_ACCESS_DENIED while another writer's
            # just-removed directory is still delete-pending. Retry acquisition
            # only within the same deadline; never remove or steal the lock.
            if isinstance(error,PermissionError) and not (
                    os.name=='nt' and getattr(error,'winerror',None)==5):
                raise
            # DrvFS can expose the same Windows delete-pending transition as
            # ENOENT. Retry only while the verified evidence parent still
            # exists; do not recreate a disappeared parent or steal a lock.
            if isinstance(error,FileNotFoundError) and not RAW.is_dir():
                raise
            if time.monotonic()>=deadline:
                raise RuntimeError('Campaign ledger lock deadline; inspect owned writers before removing a stale lock')
            time.sleep(0.01)
    try:
        yield
    finally:
        lock.rmdir()

def append(record):
    DOC.mkdir(parents=True, exist_ok=True)
    with ledger_lock():
        # Epoch 1 remains byte-for-byte frozen after a diagnosed concurrent
        # writer collision. New writes never rewrite or repair its raw bytes.
        with (DOC/'attempts-v2.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(record,ensure_ascii=True)+'\n')
            stream.flush()
            os.fsync(stream.fileno())

def read_ledger(path):
    quarantine=DOC/'core/ledger-quarantine.json'
    known=json.loads(quarantine.read_text(encoding='utf-8')) if quarantine.exists() else {}
    fragments={r['sha256'] for r in known.get('fragments',[])}
    data=path.read_bytes()
    records=[]
    for line in data.splitlines():
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            if hashlib.sha256(line).hexdigest() not in fragments or hashlib.sha256(data).hexdigest()!=known.get('frozen_sha256'):
                raise RuntimeError('Unknown campaign ledger damage: '+str(path))
            # This exact damaged fragment remains retained in the frozen file
            # and quarantine manifest. It is never treated as a passing event.
    return records

def read_attempts():
    with ledger_lock():
        return [row for name in ['attempts.jsonl','attempts-v2.jsonl']
                if (DOC/name).exists() for row in read_ledger(DOC/name)]

def contract_identity(project, argv):
    """Capture current bytes before execution, without reading ambient secrets."""
    package=DOC/project
    contracts={}
    fixture_names={'fixtures'}
    scenarios=package/'scenarios.json'
    if scenarios.is_file():
        configuration=json.loads(scenarios.read_text(encoding='utf-8'))
        fixture_names.add(configuration.get('fixture','fixtures'))
        fixture_names.update(case.get('fixture',configuration.get('fixture','fixtures')) for case in configuration.get('cases',[]))
    fixture_roots=[]
    for name in fixture_names:
        path=(package/name).resolve()
        path.relative_to(package.resolve())
        fixture_roots.append(path)
    if package.is_dir():
        for path in sorted(package.rglob('*')):
            if path.is_file() and not path.is_symlink() and (
                    path.parent==package and path.suffix=='.json' or
                    'snapshots' in path.relative_to(package).parts or
                    'fixtures' in path.relative_to(package).parts or
                    any(path.is_relative_to(root) for root in fixture_roots)):
                if path.stat().st_size>4*1024*1024:
                    raise RuntimeError('Contract identity file exceeds independent bound')
                contracts[path.relative_to(package).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
    runner=Path(str(argv[0]))
    fixture_directories=[]
    for root in fixture_roots:
        if root.is_dir():
            fixture_directories.extend(path.relative_to(package).as_posix()
                for path in [root,*root.rglob('*')] if path.is_dir() and not path.is_symlink()
                and not getattr(path,'is_junction',lambda:False)())
    identity={'contracts':contracts,'fixture_directories':sorted(set(fixture_directories))}
    if Path(str(argv[0])).name in {'go','go.exe'}:
        source_files={}
        for directory in [ROOT/'internal',ROOT/'cmd']:
            for path in sorted(directory.rglob('*.go')):
                source_files[path.relative_to(ROOT).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
        for name in ['go.mod','go.sum']:
            source_files[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        identity['product_source_files']=source_files
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
    if runtime.is_file() and os.name!='nt':
        owner=json.loads((runtime.parent/'task-owned.json').read_text(encoding='utf-8'))
        foreign=PureWindowsPath(owner.get('workspace',''))
        mapped=('/mnt/'+foreign.drive[0].lower()+'/'+('/'.join(foreign.parts[1:]))) if foreign.drive else ''
        if owner.get('project')==project and mapped==ROOT.as_posix():
            runtime=Path('/var/tmp')/('playtestr-adversarial-'+project)/'runtime.json'
    if not runtime.is_file() and os.name!='nt':
        runtime=Path('/var/tmp')/('playtestr-adversarial-'+project)/'runtime.json'
    if runtime.is_file():
        marker=json.loads((runtime.parent/'task-owned.json').read_text(encoding='utf-8'))
        if marker.get('workspace')!=str(ROOT) or marker.get('project')!=project:
            raise RuntimeError('Unowned runtime identity')
        data=json.loads(runtime.read_text(encoding='utf-8'))
        identity['target_revision']=data.get('source')
        identity['runtime_sha256']=hashlib.sha256(runtime.read_bytes()).hexdigest()
        if data.get('binary'):
            target_binary=Path(data['binary']).resolve(strict=True)
            target_binary.relative_to(runtime.parent.resolve())
            if target_binary.stat().st_size>128*1024*1024:
                raise RuntimeError('Target executable identity size bound')
            identity['target_binary_sha256']=hashlib.sha256(target_binary.read_bytes()).hexdigest()
        target_source=Path(data['source_path']).resolve()
        target_source.relative_to(runtime.parent.resolve())
        source_files={}
        for path in sorted(target_source.rglob('*')):
            if path.is_file() and not path.is_symlink() and (path.suffix in {'.py','.go','.rs','.c','.h','.toml'} or path.name in {'go.mod','go.sum','Cargo.lock'}) and '.git' not in path.relative_to(target_source).parts:
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

async def unix_process_inventory():
    """Read bounded PID/parent/birth identities without commands or environment."""
    inspector=await asyncio.create_subprocess_exec('ps','-axo','pid=,ppid=,lstart=',
        stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.DEVNULL,
        env=dict(os.environ,LC_ALL='C'))
    try:
        async def read_inventory():
            data=bytearray()
            while block:=await inspector.stdout.read(16384):
                if len(data)+len(block)>1024*1024:
                    raise RuntimeError('Owned process inventory output bound')
                data.extend(block)
            return data
        data=await asyncio.wait_for(read_inventory(),timeout=3)
        if await asyncio.wait_for(inspector.wait(),timeout=1)!=0:
            raise RuntimeError('Owned process inventory failed')
        rows={}
        for line in data.decode('utf-8',errors='strict').splitlines():
            values=line.split(None,2)
            if len(values)!=3:raise RuntimeError('Malformed native process identity')
            rows[int(values[0])]=(int(values[1]),values[2])
        return rows
    finally:
        if inspector.returncode is None:
            inspector.kill()
            await asyncio.wait_for(inspector.wait(),timeout=2)
        await close_transport(inspector)


def owned_descendants(rows,pid):
    owned={pid} if pid in rows else set()
    for _ in range(32):
        added={child for child,(parent,_) in rows.items() if parent in owned and child not in owned}
        if not added:break
        owned.update(added)
    else:raise RuntimeError('Owned process tree depth bound')
    if len(owned)>4096:raise RuntimeError('Owned process tree count bound')
    return {child:rows[child] for child in owned}


async def stop(proc):
    if os.name=='nt':
        if proc.returncode is not None:
            return
        killer=await asyncio.create_subprocess_exec('taskkill','/PID',str(proc.pid),'/T','/F',
            stdout=asyncio.subprocess.DEVNULL,stderr=asyncio.subprocess.DEVNULL)
        try:
            await asyncio.wait_for(killer.wait(),timeout=5)
        finally:
            if killer.returncode is None:
                killer.kill()
                await asyncio.wait_for(killer.wait(),timeout=2)
            await close_transport(killer)
    else:
        termination_errors=[]
        before=await unix_process_inventory()
        owned=owned_descendants(before,proc.pid)
        try:
            os.killpg(proc.pid,signal.SIGINT)
        except ProcessLookupError:
            pass
        except OSError as error:
            termination_errors.append('interrupt owned group: '+str(error))
        # Python asyncio helpers and the public CLI handle Interrupt. Give
        # their finally/context cleanup a bounded chance before forced shutdown.
        # PIPE backpressure can prevent wait completion; force after this bound.
        if proc.returncode is None:
            try:await asyncio.wait_for(asyncio.shield(proc.wait()),timeout=5)
            except asyncio.TimeoutError:pass
        current=await unix_process_inventory()
        if current.get(proc.pid)==before.get(proc.pid) and proc.pid in current:
            owned.update(owned_descendants(current,proc.pid))
        for pid,identity in owned.items():
            # Birth identity guards against reuse after graceful parent exit.
            if pid not in current or current[pid][1]!=identity[1]:continue
            try:os.kill(pid,signal.SIGKILL)
            except ProcessLookupError:pass
            except OSError as error:
                termination_errors.append('terminate captured owned PID '+str(pid)+': '+str(error))
        try:os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError:pass
        except OSError as error:
            termination_errors.append('terminate owned group: '+str(error))
        if termination_errors:
            raise RuntimeError('Separate owned termination failures: '+'; '.join(termination_errors))
    # Waiting before draining a full PIPE can deadlock asyncio's transport.
    # The caller drains bounded output first, then reaps the process.

async def close_transport(proc):
    # The pinned CPython 3.12 asyncio Process API has no public close operation.
    # Explicitly release its transport after bounded drain/reaping, while the
    # Proactor loop is still live. This is harness plumbing, not runner evidence.
    transport=getattr(proc,'_transport',None)
    if transport is not None:
        transport.close()
        await asyncio.sleep(0)

async def execute(argv,project,label,*,cwd=ROOT,env=None,input=None,timeout=120,
                  output_cap=4*1024*1024,expected=0,on_output=None,on_complete=None,load=False):
    run_id=uuid.uuid4().hex
    directory=RAW/project/run_id
    directory.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    record=dict(id=run_id,event='started',project=project,label=label,
                utc=datetime.now(timezone.utc).isoformat(),host=platform.platform(),
                timeout_seconds=timeout,output_cap=output_cap,
                variation='owned 2-second 8-MiB SHA256 CPU worker' if load else 'ordinary',
                expected_exit=expected,evidence=str(directory.relative_to(ROOT)))
    append(record)
    output=bytearray()
    proc=None
    category='harness_error'
    result=None
    worker=None
    original_error=None
    try:
        # Register even provenance/setup rejection before any subprocess starts.
        # The separate identity event must precede launch, and captures current
        # bytes without rewriting a previously fsynced started record.
        identity=contract_identity(project,argv)
        append(dict(id=run_id,event='identified',project=project,label=label,identity=identity))
        if time.monotonic()-start>=timeout:
            raise asyncio.TimeoutError()
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
        remaining=timeout-(time.monotonic()-start)
        if remaining<=0:
            raise asyncio.TimeoutError()
        result=await asyncio.wait_for(interact(),timeout=remaining)
        if on_complete is not None:
            on_complete(result,output,directory)
        if time.monotonic()-start>=timeout:
            raise asyncio.TimeoutError()
        category='passed' if result==expected else 'exit_mismatch'
        if result!=expected:
            raise RuntimeError(f'{label}: expected exit {expected}, got {result}; {directory}')
        return dict(id=run_id,output=output.decode('utf-8',errors='replace'),directory=directory,
                    returncode=result,seconds=time.monotonic()-start)
    except asyncio.CancelledError as error:
        original_error=error
        error.evidence_id=run_id
        error.evidence_directory=str(directory)
        category='harness_cancelled'
        (directory/'harness-error.json').write_text(json.dumps(dict(
            type=type(error).__name__,message='independent command cancelled'),indent=2)+'\n',encoding='utf-8')
        raise
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
            await clean('close load worker transport',close_transport(worker))
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
            await clean('close owned command transport',close_transport(proc))
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
    if os.name=='nt' and len(args)>=2 and args[1]=='yazi':
        from adversarial_windows_state import target_state
        with target_state(args[1],args[0]):
            return asyncio.run(execute(*args,**kwargs))
    return asyncio.run(execute(*args,**kwargs))
