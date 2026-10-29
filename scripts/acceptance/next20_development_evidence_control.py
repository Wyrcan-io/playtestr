"""Real archive proof that development evidence must use invocation directories."""
import asyncio
import json
import sys
import uuid

from adversarial_process import execute
from next20_check import RAW,ROOT,NextCampaign,owned_environment
from next20_candidate import executable
from readiness_evidence import immutable_json,sha256


async def main():
    root=RAW/'control-tests/development-evidence'/uuid.uuid4().hex;fixture=root/'fixture';fixture.mkdir(parents=True)
    spec=root/'same-spec.json';runner=executable('native-exit-v1');campaign=NextCampaign();env=owned_environment()
    immutable_json(spec,dict(version=3,name='Bounded synthetic failure evidence control',command=[sys.executable,'-B','-c',
        'from pathlib import Path;print(Path("frame.txt").read_text(encoding="utf-8"),end="")'],
        workspace=dict(fixture='fixture',home='temporary',temp='temporary'),env=dict(PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8'),
        width=80,height=12,timeout_ms=1000,run_timeout_ms=5000,max_output_bytes=65536,steps=[dict(expect='intentionally missing assertion')]))
    observations=[]
    for mode in ['legacy-adjacent','isolated-artifacts']:
        previous=None
        for label in ['first-frame','second-frame']:
            (fixture/'frame.txt').write_text(label+'\n',encoding='utf-8',newline='\n')
            report=root/(mode+'-'+label+'.report.json');argv=[runner,'test','--report',report.relative_to(ROOT)]
            if mode=='isolated-artifacts':argv+=['--artifacts-dir',(root/'evidence').relative_to(ROOT)]
            argv.append(spec.relative_to(ROOT))
            result=await execute(argv,'core','actual-development-evidence-'+mode+'-'+label,cwd=ROOT,env=env,timeout=30,expected=1,campaign=campaign)
            row=json.loads(report.read_text())['results'][0]
            if row['status']!='failed' or row['failure']['category']!='unexpected_exit' or not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('actual synthetic failure/cleanup differs')
            path=ROOT/row['evidence']['screen_path'];path.resolve(strict=True).relative_to(root.resolve(strict=True));payload=path.read_bytes()
            if label.encode() not in payload:raise ValueError('actual selected frame evidence missing')
            retained=root/(mode+'-'+label+'.retained-original-screen.txt');retained.write_bytes(payload)
            if sha256(retained)!=sha256(path):raise ValueError('actual original frame backup differs')
            if previous:
                if mode=='legacy-adjacent' and (path!=previous['path'] or previous['payload']==path.read_bytes()):raise ValueError('legacy collision was not reproduced')
                if mode=='isolated-artifacts' and (path==previous['path'] or previous['path'].read_bytes()!=previous['payload']):raise ValueError('isolated first frame was overwritten')
            observations.append(dict(mode=mode,label=label,attempt=result['id'],invocation=row['invocation_id'],report_sha256=sha256(report),
                reported_screen=path.relative_to(ROOT).as_posix(),exact_original_backup=retained.relative_to(ROOT).as_posix(),original_screen_sha256=sha256(retained)))
            previous=dict(path=path,payload=payload)
    immutable_json(root/'verified.json',dict(schema_version=1,runner_sha256=sha256(runner),trusted_python_sha256=sha256(sys.executable),observations=observations,
        original_legacy_frames_backed_up_before_overwrite=True,legacy_collision_reproduced=True,fixed_distinct_frames_preserved=True,
        public_archive_invocations=4,application_scenario_credit=0,new_unique_whole_control_credit=0,
        scope='Actual real-PTY failures through exact rc.6 archive. Legacy default output deliberately reproduced only after first frame backup; per-invocation artifacts preserve both distinct originals. Development harness fix,not a product binary change.'))
    print('Actual archive evidence regression:legacy collision reproduced with originals backed up; isolated directories preserve both frames; all4 targets/workspaces cleaned')


if __name__=='__main__':asyncio.run(main())
