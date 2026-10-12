"""Bounded Windows target diagnostics; never grants application qualification."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import time
from adversarial_process import ROOT, DOC, RAW, run


def main():
    if os.name != 'nt':
        raise RuntimeError('This investigation is the native Windows input path')
    app=ROOT/'.cache/ten-new-project-apps/superfile'
    identity=json.loads((app/'runtime.json').read_text(encoding='utf-8'))
    diagnostic=app/('input-investigation-'+str(time.time_ns()))
    diagnostic.mkdir(exist_ok=False)
    package=DOC/'superfile'
    shutil.copytree(package/'fixtures',diagnostic/'fixtures')
    shutil.copytree(package/'snapshots',diagnostic/'snapshots')
    config=diagnostic/'fixtures/.configuration/config.toml'
    content=config.read_text(encoding='utf-8')
    content,count=re.subn(r'(?m)^debug\s*=\s*false\s*$', 'debug = true',content)
    if count!=1: raise RuntimeError('Diagnostic debug setting is not unique')
    config.write_text(content,encoding='utf-8')
    spec=json.loads((package/'normal-panel-copy.json').read_text(encoding='utf-8'))
    binary=app/'bin/superfile-race.exe'
    if not binary.is_file(): raise RuntimeError('Missing separately instrumented target')
    spec['command'][0]=str(binary)
    # A relative owned path avoids ThreadSanitizer treating a Windows drive
    # colon as an option delimiter; the target's cwd is the managed fixture.
    spec['env']['GORACE']='halt_on_error=0 exitcode=66 log_path=.diagnostic-race-log'
    path=diagnostic/'copy.json'
    path.write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    temporary=diagnostic/'temporary'
    temporary.mkdir()
    env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'],
             TEMP=str(temporary),TMP=str(temporary))
    records=[]
    for repetition in range(30):
        report=RAW/'superfile'/(diagnostic.name+'-'+str(repetition)+'.json')
        try:
            result=run([ROOT/'bin/playtestr.exe','test','--keep-workspace-on-failure',
                '--report',report,'--artifacts-dir',report.with_suffix(''),path],
                'superfile','diagnostic-race-input-'+str(repetition),env=env,load=True)
            records.append(dict(repetition=repetition,passed=True,evidence_id=result['id']))
        except RuntimeError as error:
            if not report.is_file(): raise
            data=json.loads(report.read_text(encoding='utf-8'))
            failed=data['results'][0]
            if failed['status']!='failed' or not failed['cleanup']['confirmed_exited']: raise
            retained=Path(failed['workspace']['retained_path']).resolve(strict=True)
            retained.relative_to(temporary.resolve())
            if retained.is_symlink() or retained.is_junction(): raise RuntimeError('Linked diagnostic workspace')
            logs=[]
            for race in retained.rglob('.diagnostic-race-log.*'):
                if race.is_symlink() or race.stat().st_size>4*1024*1024: raise RuntimeError('Unsafe race diagnostic log')
                output=report.with_suffix('.race-log.txt')
                output.write_bytes(race.read_bytes())
                logs.append(dict(path=str(output.relative_to(ROOT)),sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
            for log in retained.rglob('superfile.log'):
                if log.is_symlink() or log.stat().st_size>4*1024*1024: raise RuntimeError('Unsafe target diagnostic log')
                output=report.with_suffix('.target-log.txt')
                output.write_bytes(log.read_bytes())
                logs.append(dict(path=str(output.relative_to(ROOT)),sha256=hashlib.sha256(output.read_bytes()).hexdigest()))
            records.append(dict(repetition=repetition,passed=False,evidence_id=error.evidence_id,
                failure=failed['failure'],report=str(report.relative_to(ROOT)),target_logs=logs,
                retained_workspace=str(retained)))
            print(json.dumps(records[-1],indent=2),flush=True)
            break
        print('Race diagnostic copy',repetition,'passed',flush=True)
    (RAW/'superfile'/(diagnostic.name+'-result.json')).write_text(json.dumps(dict(
        phase='Diagnostic target race experiment; not qualification',records=records,
        pristine_target_sha256=identity['binary_sha256'],
        diagnostic_target_sha256=hashlib.sha256(binary.read_bytes()).hexdigest(),
        owned_diagnostic_root=str(diagnostic)),indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
