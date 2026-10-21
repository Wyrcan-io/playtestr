"""Exact current Windows archive rejects unsupported spec before target launch."""
import asyncio
import base64
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


async def main():
    if os.name!='nt':
        raise RuntimeError('this current-archive control declares native Windows only')
    root=RAW/'current-format-refusal'/uuid.uuid4().hex
    root.mkdir(parents=True)
    (root/'fixture').mkdir()
    (root/'empty-path').mkdir()
    home=root/'home';home.mkdir()
    marker=root/'target-started.txt'
    powershell=Path(shutil.which('powershell.exe')).resolve(strict=True)
    quoted="'"+str(marker).replace("'","''")+"'"
    script="[IO.File]::WriteAllText("+quoted+",'target-started'); [Console]::WriteLine('format-control-ready'); exit 0"
    encoded=base64.b64encode(script.encode('utf-16-le')).decode('ascii')
    good=dict(version=3,name='Current archive format launch control',
        command=[str(powershell),'-NoLogo','-NoProfile','-NonInteractive','-EncodedCommand',encoded],
        workspace=dict(fixture='fixture',cwd='.',home='temporary',temp='temporary'),
        width=80,height=24,timeout_ms=30000,run_timeout_ms=60000,
        steps=[dict(expect='format-control-ready'),dict(exit=0)])
    bad=dict(good,version=999)
    immutable_json(root/'supported.json',good)
    immutable_json(root/'unsupported.json',bad)
    binary,frozen,cell=runner('migration-v2')
    immutable_json(root/'declared.json',dict(runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],
        valid_spec_sha256=sha256(root/'supported.json'),unsupported_spec_sha256=sha256(root/'unsupported.json'),
        only_change='version3 to999; exact same real target command and fixture',
        schedule=['positive target launch','remove only its owned marker','unsupported version refusal without marker','same valid contract recovery'],
        target_powershell_sha256=sha256(powershell),step_deadline_seconds=30,parent_command_seconds=75,
        scope='A marker outside the managed fixture but inside this owned workspace witnesses actual target entry. Zero project/scenario credit.'))
    env={k:v for k,v in os.environ.items() if k.upper() in {'SYSTEMROOT','WINDIR','COMSPEC','PATHEXT'}}
    env.update(PATH=str(root/'empty-path'),HOME=str(home),USERPROFILE=str(home),APPDATA=str(home),LOCALAPPDATA=str(home),
        TEMP=str(RAW/'tmp'),TMP=str(RAW/'tmp'),TMPDIR=str(RAW/'tmp'))
    rows=[]
    for label,spec,expected in [('supported-before','supported.json',0),('unsupported-refused','unsupported.json',1),
                                ('supported-after','supported.json',0)]:
        if marker.exists():
            if marker.is_symlink() or marker.read_bytes()!=b'target-started':
                raise RuntimeError('owned launch marker changed')
            marker.unlink()
        report=root/(label+'.json')
        attempt=await execute([binary,'test','--report',report,'--artifacts-dir',root/(label+'-evidence'),root/spec],
            'core','current-archive-'+label,env=env,timeout=75,expected=expected,campaign=Campaign(phase='final-archive'))
        value=load(report);row=value['results'][0]
        if expected:
            if (marker.exists() or row['failure']['category']!='invalid_spec' or row.get('invocation_id')
                    or row['cleanup']['attempted'] or row.get('workspace') or row['target']['exited']):
                raise RuntimeError('unsupported version did not refuse before actual target launch')
        elif (row['status']!='passed' or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']
                or not marker.is_file() or marker.read_bytes()!=b'target-started'):
            raise RuntimeError('valid contract launch/recovery lacked actual target marker or cleanup')
        if value['runner_version']!=frozen['version']:
            raise RuntimeError('control used another private archive')
        rows.append(dict(label=label,attempt=attempt['id'],report_sha256=sha256(report),
            target_marker_observed=marker.exists(),status=row['status']))
    immutable_json(root/'verified.json',dict(runner_sha256=cell['binary_sha256'],archive_sha256=cell['archive_sha256'],
        declared_sha256=sha256(root/'declared.json'),observations=rows,
        scope='Actual version999 refusal before target entry, bracketed by two real successful launches of the identical target command under version3.',final_archive_credit=0))
    print('Verified current exact Windows archive unsupported-version prelaunch refusal and real launch/recovery:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
