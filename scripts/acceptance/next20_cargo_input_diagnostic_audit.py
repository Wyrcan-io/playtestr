"""Read actual raw diagnostic captures; retain their deliberately limited scope."""
import asyncio
import base64
import hashlib
import json

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign,owned_environment
from readiness_evidence import immutable_json,sha256
from readiness_compact_native import compact


async def main():
    run='40480783047';revision='0a17989d52214aa83f2efd8c41d6e862e40bddc7';root=RAW/'native'/run;packet=root/'next20-cargo-native-input-diagnostic'
    project='cargo-generate';diagnostic=packet/project/'input-diagnostic/v1'
    observed=await execute(['gh','run','view',run,'--repo','Wyrcan-io/playtestr','--json','headSha,status,conclusion,jobs'],
        'core','cargo-raw-input-diagnostic-provider',cwd=ROOT,env=owned_environment(),timeout=60,campaign=NextCampaign())
    provider=json.loads(observed['output'])
    if provider['headSha']!=revision or provider['status']!='completed' or provider['conclusion']!='success':raise ValueError('wrong actual native diagnostic provider/source')
    runtime=json.loads((diagnostic/'runtime-reference.json').read_text());approved=json.loads((DOC/project/'native-linux-preflight-reviewed-audit.json').read_text())
    if runtime['actual_binary_sha256']!=approved['target_binary_sha256'] or runtime['new_compile']:raise ValueError('diagnostic native source-built runtime differs')
    rows=[]
    for mode in ['immediate','observe-text','observe-text-and-raw']:
        for number in range(6):
            folder=diagnostic/(mode+'-'+str(number));path=folder/'observed.json';value=json.loads(path.read_text());plan=json.loads((folder/'planned.json').read_text())
            raw=base64.b64decode(value['raw_base64'],validate=True)
            if len(raw)>65536 or len(raw)!=value['raw_bytes'] or hashlib.sha256(raw).hexdigest()!=value['raw_sha256']:raise ValueError('actual raw capture changed/bound')
            inputs=[base64.b64decode(w['input_base64'],validate=True) for w in value['writes']]
            if inputs!=[b'synthetic-notes',b'\r',b'Ada',b'\r',b'\r',b'\r'] or not all(isinstance(w['echo'],bool) and isinstance(w['canonical'],bool) for w in value['writes']):raise ValueError('actual input schedule/termios capture differs')
            if plan['binary_sha256']!=runtime['actual_binary_sha256'] or value['mode']!=mode or value['number']!=number or value['target_exit']!=0 or value['error'] or not value['confirmed_process_group_absent']:raise ValueError('incomplete/wrong real diagnostic target outcome')
            if b'New project created' not in raw or not any(name.endswith('synthetic-notes/profile.txt') for name in value['final_files']):raise ValueError('missing actual completion/output-file observation')
            rows.append(dict(mode=mode,number=number,report_sha256=sha256(path),raw_sha256=value['raw_sha256'],
                echo_flags_before_writes=[w['echo'] for w in value['writes']]))
    removed=json.loads((diagnostic/'cleanup-removed.json').read_text())
    if not removed['owned_target_removed'] or removed['inventory_sha256']!=sha256(diagnostic/'cleanup-inventory.json'):raise ValueError('diagnostic payload cleanup record differs')
    receipt=dict(schema_version=1,run=run,revision=revision,observations=rows,actual_raw_target_observations=18,
        ordinary_credit=0,calibration_credit=0,project_admissions=0,
        finding='All18 direct PTY runs completed; first four writes consistently observed ECHO/ICANON disabled, later menu transitions sometimes enabled. Original partial-line failure not reproduced or explained by these observations alone.',
        limitations='The diagnostic source checks process-group absence after wait; raw target PID/birth was not separately persisted. These are diagnostic raw captures, not native qualification or an independent full lifecycle audit. No general input-readiness fix or target-library root-cause claim follows.')
    immutable_json(root/'run-metadata.json',provider);immutable_json(root/'diagnostic-audit.json',receipt)
    immutable_json(DOC/project/'native-linux-raw-input-diagnostic-v1.json',receipt)
    compact(RAW,project,[run],16*1024**2,generation=4)
    await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',ROOT/'scripts/acceptance/next20_remove_native.ps1','-Project',project,'-Generation','4'],
        'core','cargo-raw-input-diagnostic-expansion-removal',cwd=ROOT,env=owned_environment(),timeout=180,campaign=NextCampaign())
    print('Retained18 actual limited raw-input diagnostics and checked-removed packet expansion; no root-cause or qualification claim')


if __name__=='__main__':asyncio.run(main())
