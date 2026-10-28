"""Independently verify the exact-candidate syscall cause of the extra row."""
import asyncio
import json
import re

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign,owned_environment
from readiness_evidence import immutable_json,sha256
from readiness_compact_native import compact


async def main():
    run='40744103927';revision='3c18553cf7c650ae947bcaee333c24a40e54caad';project='cargo-generate'
    root=RAW/'native'/run;packet=root/'next20-cargo-native-input-diagnostic';trace=packet/project/'candidate-input-trace/v1'
    provider_result=await execute(['gh','run','view',run,'--repo','Wyrcan-io/playtestr','--json','status,conclusion,headSha,jobs'],
        'core','cargo-candidate-trace-provider-readback',cwd=ROOT,env=owned_environment(),timeout=60,campaign=NextCampaign())
    provider=json.loads(provider_result['output'])
    if provider['status']!='completed' or provider['conclusion']!='success' or provider['headSha']!=revision:raise ValueError('wrong actual trace provider/source')
    summary=json.loads((trace/'summary.json').read_text());observation=summary['observations'][0]
    if summary['executions']!=1 or len(summary['observations'])!=1 or observation['status']!='failed' or observation['category']!='snapshot_mismatch':raise ValueError('original diagnostic first failure differs')
    folder=trace/'0';report=folder/'report.json';data=json.loads(report.read_text());row=data['results'][0]
    if sha256(report)!=observation['report_sha256'] or row['failure']['category']!='snapshot_mismatch' or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('trace target failure/cleanup differs')
    tools=json.loads((trace/'tool-and-runtime.json').read_text());candidate=next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']=='linux')
    if tools['actual_runner_sha256']!=candidate['binary_sha256'] or tools['actual_target_sha256']!=json.loads((DOC/project/'native-linux-preflight-reviewed-audit.json').read_text())['target_binary_sha256']:raise ValueError('wrong actual private archive/source-built target')
    rows=[]
    for name,record in observation['traces'].items():
        path=folder/name
        if path.stat().st_size!=record['bytes'] or sha256(path)!=record['sha256']:raise ValueError('actual syscall trace changed')
        for line in path.read_text(encoding='utf-8').splitlines():
            match=re.match(r'([0-9]+\.[0-9]+) (.*)',line)
            if match:rows.append(dict(time=match[1],stream=name,line=match[2]))
    rows.sort(key=lambda item:(float(item['time']),item['stream']))
    ada=next(i for i,r in enumerate(rows) if 'write(' in r['line'] and '/dev/ptmx' in r['line'] and '"Ada", 3) = 3' in r['line'])
    enter=next(i for i in range(ada+1,len(rows)) if 'write(' in rows[i]['line'] and '/dev/ptmx' in rows[i]['line'] and '"\\r", 1) = 1' in rows[i]['line'])
    terminal_modes=[i for i in range(ada,enter) if '/dev/pts/' in rows[i]['line'] and 'TCSETSW' in rows[i]['line']]
    if not terminal_modes:raise ValueError('missing actual slave terminal-mode evidence')
    mode=terminal_modes[-1]
    flags=re.search(r'c_lflag=([^,]+)',rows[mode]['line']).group(1).split('|')
    if not {'ECHO','ICANON'}<=set(flags):raise ValueError('Enter did not arrive during actual canonical/echo mode')
    written_d=next(i for i in range(ada,enter) if 'write(2</dev/pts/' in rows[i]['line'] and '"d", 1) = 1' in rows[i]['line'])
    kernel_newline=next(i for i in range(enter+1,len(rows)) if 'read(' in rows[i]['line'] and '/dev/ptmx' in rows[i]['line'] and '"\\r\\n", 8192) = 2' in rows[i]['line'])
    written_a=next(i for i in range(enter+1,len(rows)) if 'write(2</dev/pts/' in rows[i]['line'] and '"a", 1) = 1' in rows[i]['line'])
    if kernel_newline>=written_a or any('write(2</dev/pts/' in r['line'] and '"\\n", 1)' in r['line'] for r in rows[enter:kernel_newline]):raise ValueError('newline is not isolated before final target-rendered character')
    prefix='artifacts/runner-readiness-next-twenty-project-pass/'
    screen=packet/row['evidence']['screen_path'].removeprefix(prefix);text=screen.read_text(encoding='utf-8')
    if 'Project owner: Ad\n' not in text or 'Project owner: Ada\n' not in text:raise ValueError('actual screen does not preserve the observed split line')
    proof=dict(schema_version=1,run=run,revision=revision,source_target_sha256=tools['actual_target_sha256'],runner_sha256=tools['actual_runner_sha256'],
        report_sha256=sha256(report),screen_sha256=sha256(screen),trace_files=observation['traces'],
        causal_sequence=[rows[i] for i in sorted({ada,mode,written_d,enter,kernel_newline,written_a})],
        finding='The target restored ECHO/ICANON between input characters. Runner Enter reached the PTY in that interval; master read a kernel-produced CRLF before the target wrote final a. The rendered Ad row is actual terminal output, not VT parser invention.',
        remedy='Add positive full-input rendered checkpoints before Enter for Linux N01, preserving exact snapshot and all saved-state oracles; requalify complete Linux window. No runner/PTY/spec change, byte filtering, row removal or general no-flakiness claim.',
        qualification_credit=0)
    immutable_json(root/'run-metadata.json',provider);immutable_json(root/'trace-audit.json',proof)
    immutable_json(DOC/project/'native-linux-input-echo-trace-v1.json',proof)
    compact(RAW,project,[run],16*1024**2,generation=5)
    await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'scripts/acceptance/next20_remove_native.ps1','-Project',project,'-Generation','5'],
        'core','cargo-candidate-syscall-trace-expansion-removal',cwd=ROOT,env=owned_environment(),timeout=180,campaign=NextCampaign())
    print('Verified actual canonical/echo Enter and kernel newline before final a; retained exact trace and original mismatch, zero qualification credit')


if __name__=='__main__':asyncio.run(main())
