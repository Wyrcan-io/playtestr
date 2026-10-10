#!/usr/bin/env python3
"""Sequential external-project evidence through public Playtestr commands.

Run on a native Unix host (including explicitly labelled local WSL). This tool
does not mutate upstreams, contact maintainers or silently accept old baselines.
Application acquisition/removal is separately verified by the operator.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import selectors
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BIN = ROOT / "bin" / ("playtestr-linux" if "microsoft" in platform.release().lower() else "playtestr")
DOC = ROOT / "docs/validation/ten-project-user-pass"
RAW = ROOT / "artifacts/ten-project-user-pass"


def preserve(path):
    """Keep every earlier attempt before replacing its convenient latest name."""
    if path.exists():
        history = path.parent / 'history'
        history.mkdir(exist_ok=True)
        path.rename(history / (str(time.time_ns()) + '-' + path.name))


class StateMismatch(RuntimeError):
    def __init__(self, actual, expected):
        super().__init__('independent exact-byte state oracle mismatch')
        self.actual_sha256=hashlib.sha256(actual).hexdigest()
        self.expected_sha256=hashlib.sha256(expected).hexdigest()


def probe_bytes(command, cwd):
    """Bound independent trusted state probes in time, output and process life."""
    proc=subprocess.Popen(command,cwd=cwd,stdout=subprocess.PIPE,start_new_session=True)
    selector=selectors.DefaultSelector();selector.register(proc.stdout,selectors.EVENT_READ)
    value=bytearray();deadline=time.monotonic()+10;completed=False
    try:
        while selector.get_map() or proc.poll() is None:
            if time.monotonic()>deadline:raise RuntimeError('independent state probe deadline')
            for key,_ in selector.select(timeout=0.05):
                block=os.read(key.fileobj.fileno(),16384)
                if not block:selector.unregister(key.fileobj);continue
                value.extend(block)
                if len(value)>4*1024*1024:raise RuntimeError('independent state probe output limit')
        if proc.wait(timeout=1)!=0:raise RuntimeError('independent state probe returned nonzero')
        completed=True
        return bytes(value)
    finally:
        if not completed:
            try:os.killpg(proc.pid,signal.SIGKILL)
            except ProcessLookupError:pass
        proc.wait(timeout=2)
        selector.close();proc.stdout.close()


def run(args, label, *, input=None, expected=0, env=None, timeout=150, load=False):
    out = RAW / label
    out.parent.mkdir(parents=True, exist_ok=True)
    preserve(out.with_suffix('.log'))
    worker=None
    if load:
        worker=subprocess.Popen([sys.executable,'-c',
            'import hashlib,time; b=b"x"*(8*1024*1024); end=time.monotonic()+2; '
            '\nwhile time.monotonic()<end: hashlib.sha256(b).digest()'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        p = subprocess.run(list(map(str, args)), cwd=ROOT, input=input,
                           text=True, encoding="utf-8", stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, env=env, timeout=timeout)
    finally:
        if worker:
            try: worker.wait(timeout=3)
            except subprocess.TimeoutExpired: worker.kill();worker.wait(timeout=3)
    out.with_suffix(".log").write_text(p.stdout, encoding="utf-8")
    if p.returncode != expected:
        raise RuntimeError(f"{label}: expected {expected}, got {p.returncode}; first failure retained\n{p.stdout[-5000:]}")
    return p


def controls(steps):
    lines = []
    names = {"expect": "expect", "expect_not": "absent", "key": "key", "snapshot": "snapshot", "exit": "exit"}
    for step in steps:
        k, v = next(iter(step.items()))
        if k == "text": lines.append("/text " + json.dumps(v, ensure_ascii=False))
        elif k == "resize": lines.append(f"/resize {v['width']} {v['height']}")
        elif k == "wait_for_redraw": lines.append("/redraw")
        elif k == "snapshot" and isinstance(v,dict): lines.append(f"/snapshot-rows {v['name']} {v['first']} {v['last']}")
        else: lines.append("/" + names[k] + " " + str(v))
    return "\n".join(lines) + "\n"


def probe(slug, command, anchor):
    output = ROOT / ".cache/ten-project-apps" / slug / "probe.json"
    p = run([BIN,"record","--output",output,"--timeout-ms","5000","--run-timeout-ms","15000","--",*command],
            slug+"/probe",input=f"/expect {anchor}\n/screen\n/quit\n",expected=130)
    print(p.stdout)


def hashes(paths):
    return {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}


def record(slug, case):
    directory = DOC / slug
    path = directory / (case['name'] + '.json')
    args = [BIN,'record','--output',path,'--name',case['purpose'],'--fixture','fixtures',
            '--temporary-home','--temporary-temp','--width','100','--height','30',
            '--timeout-ms',str(case.get('timeout_ms',5000)),'--run-timeout-ms','120000']
    for key,value in case.get('env',{}).items(): args += ['--env',key+'='+value]
    for key in case.get('inherit_env',[]): args += ['--inherit-env',key]
    args += ['--',*case['command']]
    sequence=controls(case['steps'])
    if case.get('rerecord'): sequence += '/rerecord 0\n'+controls(case['steps'])
    if case.get('replace'): sequence += '/replace '+str(case['replace']['number'])+' '+json.dumps(case['replace']['step'])+'\n'
    proc=subprocess.Popen(list(map(str,args)),cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    output=bytearray(); sel=selectors.DefaultSelector(); sel.register(proc.stdout,selectors.EVENT_READ)
    try:
        proc.stdin.write((sequence+'/review\n').encode('utf-8'));proc.stdin.flush()
        end=time.monotonic()+100
        while time.monotonic()<end:
            for key,_ in sel.select(timeout=0.1):
                chunk=os.read(key.fileobj.fileno(),16384)
                if not chunk: raise RuntimeError('recorder ended before reviewed candidate')
                output.extend(chunk)
                if len(output)>1024*1024: raise RuntimeError('recorder evidence limit')
            text=output.decode('utf-8',errors='replace')
            if 'Recorder:' in text:
                proc.stdin.write(b'/screen\n/quit\n');proc.stdin.flush()
                tail,_=proc.communicate(timeout=10);output.extend(tail)
                raise RuntimeError('recorder rejected a step; current screen and first failure retained')
            if 'Baseline '+case['snapshot']+':' in text and text.rstrip().endswith('record>'): break
        else: raise RuntimeError('review output deadline')
        if 'Recorder:' in text: raise RuntimeError('recorder rejected a step; inspect preserved log')
        if case.get('oracle'):
            matches=re.findall(r'working-directory=(".*")',text)
            if not matches: raise RuntimeError('missing resolved workspace')
            working=Path(json.loads(matches[-1]))
            if not working.parent.name.startswith('playtestr-workspace-'): raise RuntimeError('not owned workspace')
            checks=case['oracle'] if isinstance(case['oracle'],list) else [case['oracle']]
            for oracle in checks:
                if 'command' in oracle:
                    value=probe_bytes(oracle['command'],working)
                else:
                    file=(working/oracle['path']).resolve();file.relative_to(working.resolve())
                    with file.open('rb') as stream:value=stream.read(4*1024*1024+1)
                    if len(value)>4*1024*1024:raise RuntimeError('independent state file limit')
                if value!=oracle['text'].encode('utf-8'): raise StateMismatch(value,oracle['text'].encode('utf-8'))
        if case.get('check_only'):
            proc.stdin.write(b'/quit\n');proc.stdin.flush();proc.wait(timeout=7)
            output.extend(proc.stdout.read())
            if proc.returncode!=130: raise RuntimeError('state probe did not cleanly cancel')
            return None
        proc.stdin.write(b'/replay\n/save\n');proc.stdin.flush();proc.stdin.close()
        while proc.poll() is None:
            for key,_ in sel.select(timeout=0.1):
                chunk=os.read(key.fileobj.fileno(),16384)
                if chunk: output.extend(chunk)
            if time.monotonic()>end+40: raise RuntimeError('fresh replay/export deadline')
        rest=proc.stdout.read();output.extend(rest)
        if proc.returncode!=0 or not path.exists(): raise RuntimeError('review/replay/export failed')
        if b'Recorder:' in output: raise RuntimeError('recorder failure retained, not hidden by subsequent export')
    finally:
        if proc.poll() is None:
            try: proc.stdin.write(b'/quit\n');proc.stdin.flush();proc.wait(timeout=7)
            except (OSError,ValueError,subprocess.TimeoutExpired): proc.kill();proc.wait(timeout=5)
        sel.close()
        log=RAW/slug/(case['name']+'-record.log');log.parent.mkdir(parents=True,exist_ok=True);preserve(log);log.write_bytes(output)
    return path


def journey(slug, mode):
    config=json.loads((DOC/slug/'scenarios.json').read_text())
    if config.get('runtime_path'):
        runtime_path=(ROOT/config['runtime_path']).resolve()
        runtime_path.relative_to((ROOT/'.cache/ten-project-apps').resolve())
        os.environ['PATH']=str(runtime_path)+os.pathsep+os.environ['PATH']
    if mode=='inspect':
        case=config['cases'][0];p=DOC/slug/'inspection.json'
        result=run([BIN,'record','--output',p,'--fixture','fixtures','--temporary-home','--temporary-temp','--width','120','--height','40','--timeout-ms','5000','--run-timeout-ms','20000','--',*case['command']],slug+'/inspection',input=controls(case['steps'][:1])+'/screen\n/quit\n',expected=130)
        print(result.stdout[-6500:])
        return
    if mode in ('oracle-negative','oracle-positive'):
        case=dict(next(c for c in config['cases'] if c.get('oracle') and (not config.get('negative_oracle_case') or c['name']==config['negative_oracle_case'])))
        case['name']=mode
        case['check_only']=True
        try: record(slug,case)
        except StateMismatch as error:
            if mode!='oracle-negative': raise
            f=RAW/slug/'independent-state-negative.json'
            f.write_text(json.dumps(dict(category='independent_state_mismatch',detected=True,actual_sha256=error.actual_sha256,expected_sha256=error.expected_sha256,screen_success_did_not_prove_saved_state=True),indent=2)+'\n')
            print(slug,'actual saved-state corruption detected by unchanged independent oracle',flush=True)
            return
        if mode=='oracle-positive':
            print(slug,'exact saved state independently verified; capture canceled cleanly',flush=True)
            return
        raise RuntimeError('state corruption was not detected')
    if mode=='oracle-all':
        checked=[]
        for candidate in config['cases']:
            if not candidate.get('oracle'): continue
            case=dict(candidate);case['name']='oracle-'+candidate['name'];case['check_only']=True
            record(slug,case);checked.append(candidate['name'])
        result=RAW/slug/'oracle-all-summary.json';preserve(result)
        result.write_text(json.dumps(dict(project=slug,checked=checked,passed=True,cleanup='each recorder cleanly canceled after state check'),indent=2)+'\n')
        print(slug,'all independent state checks passed:',checked,flush=True);return
    rows=[]
    for case in config['cases']:
        path=DOC/slug/(case['name']+'.json')
        if mode=='record' and not path.exists(): record(slug,case)
        contracts=[path,DOC/slug/'snapshots'/case['snapshot']]
        before=hashes(contracts)
        counts=10 if mode in ('record','final') else 1
        for i in range(counts):
            report=RAW/slug/f'{case["name"]}-{mode}-{i}.json'
            preserve(report)
            run([BIN,'test','--report',report,'--artifacts-dir',report.with_suffix(''),path],
                slug+'/'+report.stem,expected=1 if mode=='defect' else 0,load=(mode=='final' and i>=5))
            d=json.loads(report.read_text()); result=d['results'][0]
            if not result['cleanup'].get('confirmed_exited'): raise RuntimeError('unconfirmed target cleanup')
            if mode=='defect':
                if not result.get('failure'): raise RuntimeError('missing actual negative evidence')
                break
        if hashes(contracts)!=before: raise RuntimeError('contracts changed during ordinary replay')
        rows.append(dict(scenario=case['name'],attempts=counts,passed=0 if mode=='defect' else counts,
                         failed=1 if mode=='defect' else 0,contract_hashes=before,
                         independent_state_oracle=case.get('oracle'),cleanup_confirmed=True))
        rows[-1]['load_variation']='five ordinary + five with a bounded 2-second, 8-MiB SHA256 CPU worker' if mode=='final' else 'fresh state repetition; no invented delay variation'
        print(slug,case['name'],mode,'complete',flush=True)
        if mode=='defect': break
    output=RAW/slug/(mode+'-summary.json');preserve(output);output.write_text(json.dumps(dict(host=platform.platform(),runner_sha256=hashlib.sha256(BIN.read_bytes()).hexdigest(),mode=mode,scenarios=rows),indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["probe","record","defect","recovery","final","check-process","oracle-negative","oracle-positive","oracle-all","inspect"])
    parser.add_argument("slug")
    parser.add_argument("anchor",nargs='?',default='')
    parser.add_argument("command",nargs=argparse.REMAINDER)
    args=parser.parse_args()
    if args.mode=='check-process':
        target=str((ROOT/'.cache/ten-project-apps'/args.slug).resolve())
        found=[]
        for item in Path('/proc').iterdir():
            if not item.name.isdigit() or int(item.name)==os.getpid(): continue
            try:
                exe=str((item/'exe').resolve());cwd=str((item/'cwd').resolve())
                argv=(item/'cmdline').read_bytes().decode('utf-8',errors='replace').split('\0')
                if exe.startswith(target+'/') or cwd.startswith(target+'/') or any(a.startswith(target+'/') for a in argv): found.append(item.name)
            except (OSError,PermissionError): pass
        if found: raise SystemExit('Task-owned target processes still live: '+str(found))
        print('No remaining target processes:',args.slug)
    elif args.mode=='probe': probe(args.slug,args.command,args.anchor)
    else: journey(args.slug,args.mode)


if __name__ == "__main__":
    main()
