"""Verify actual canonical-mode loss of the Backspace editing byte."""
import hashlib
import json
import re

from next20_check import RAW,DOC
from next20_native_packet_reader import read_packet
from readiness_evidence import immutable_json,sha256


def main():
    run='40753955125';revision='a5d19d3a60af784c8a053482bf8b2d55eab54919';generation=11;project='cargo-generate'
    retained=RAW/project/('retained-native-v'+str(generation));index,files=read_packet(project,generation)
    prefix='native/'+run+'/next20-cargo-native-input-diagnostic/';root=prefix+project+'/candidate-input-trace/v2-e02/'
    provider=json.loads((retained/'provider.json').read_text())
    if provider['headSha']!=revision or provider['conclusion']!='success' or provider['status']!='completed':raise ValueError('wrong actual edit diagnostic provider/source')
    summary=json.loads(files[root+'summary.json'])
    if summary['executions']!=2 or [r['status'] for r in summary['observations']]!=['passed','failed']:raise ValueError('original edit diagnostic first-failure boundary differs')
    for observation in summary['observations']:
        path=root+str(observation['number'])+'/report.json';report=json.loads(files[path]);row=report['results'][0]
        if hashlib.sha256(files[path]).hexdigest()!=observation['report_sha256'] or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('actual edit diagnostic report/cleanup changed')
    observation=summary['observations'][1];folder=root+'1/';rows=[]
    for name,expected in observation['traces'].items():
        data=files[folder+name]
        if len(data)!=expected['bytes'] or hashlib.sha256(data).hexdigest()!=expected['sha256']:raise ValueError('actual edit syscall stream changed')
        for line in data.decode('utf-8').splitlines():
            match=re.match(r'([0-9]+\.[0-9]+) (.*)',line)
            if match:rows.append(dict(time=match[1],stream=name,line=match[2]))
    rows.sort(key=lambda row:(float(row['time']),row['stream']))
    start=next(i for i,r in enumerate(rows) if 'write(' in r['line'] and '/dev/ptmx' in r['line'] and '"Adx", 3) = 3' in r['line'])
    backspace=next(i for i in range(start+1,len(rows)) if 'write(' in rows[i]['line'] and '/dev/ptmx' in rows[i]['line'] and '"\\177", 1) = 1' in rows[i]['line'])
    mode=next(i for i in range(backspace-1,start,-1) if 'TCSETSW' in rows[i]['line'] and '/dev/pts/' in rows[i]['line'])
    flags=re.search(r'c_lflag=([^,]+)',rows[mode]['line']).group(1).split('|')
    if not {'ICANON','ECHO','ECHOE'}<=set(flags):raise ValueError('actual Backspace did not arrive during canonical erase mode')
    enter=next(i for i in range(backspace+1,len(rows)) if 'write(' in rows[i]['line'] and '/dev/ptmx' in rows[i]['line'] and '"\\r", 1) = 1' in rows[i]['line'])
    target_read_x=next(i for i in range(backspace+1,len(rows)) if 'read(0</dev/pts/' in rows[i]['line'] and '"x", 1) = 1' in rows[i]['line'])
    target_read_a=next(i for i in range(target_read_x+1,len(rows)) if 'read(0</dev/pts/' in rows[i]['line'] and '"a", 1) = 1' in rows[i]['line'])
    if any('read(0</dev/pts/' in r['line'] and '"\\177", 1)' in r['line'] for r in rows[backspace:target_read_a+1]):raise ValueError('Backspace was delivered to target; proposed kernel-erase diagnosis differs')
    report=json.loads(files[folder+'report.json']);row=report['results'][0]
    if row['failure']['category']!='state_assertion_failure' or not all(s['status']=='passed' for s in row['steps'][:16]):raise ValueError('saved-state failure was masked by prior error')
    path=prefix+row['evidence']['screen_path'].removeprefix('artifacts/runner-readiness-next-twenty-project-pass/')
    if 'Project owner: Adxa' not in files[path].decode('utf-8'):raise ValueError('actual wrong owner screen missing')
    tool=json.loads(files[root+'tool-and-runtime.json'])
    receipt=dict(schema_version=1,run=run,revision=revision,retained_generation=generation,retained_index_sha256=sha256(retained/'index.json'),
        retained_archive_sha256=index['archive_sha256'],diagnostic_observations=2,passed=1,failed=1,
        actual_runner_sha256=tool['actual_runner_sha256'],actual_target_sha256=tool['actual_target_sha256'],
        causal_sequence=[rows[i] for i in sorted({start,mode,backspace,enter,target_read_x,target_read_a})],
        finding='Backspace reached the master with ICANON/ECHO/ECHOE enabled before the target finished consuming Adx. No DEL byte reached target stdin; x and then a did. Target rendered Adxa and the saved-state oracle correctly rejected it.',
        scope='Same pinned source built in the earlier canonical preflight, exact rc.6 archive, unchanged E02. This diagnostic build is not the newer window2 executable. Source-level input-mode behavior reproduced; no final-series credit or general no-flakiness claim.',
        proposed_remedy='Positive full-input checkpoints before editing/submitting and explicit disappearance plus remaining-text checkpoints after Backspace. Preserve actual key sequence, resize, reviewed saved bytes and all20 cases.',ordinary_credit=0,calibration_credit=0,project_admissions=0)
    immutable_json(DOC/project/'native-linux-backspace-trace-v1.json',receipt)
    print('Verified actual cooked-mode Backspace not delivered to target, subsequent Adxa and correct saved-state rejection; two diagnostic observations, zero final credit')


if __name__=='__main__':main()
