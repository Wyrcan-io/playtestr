"""Prove the old archive rejects v3 before a calibrated target side effect."""
import argparse
import asyncio
import os
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--experience',required=True);args=parser.parse_args()
    if len(args.experience)!=32 or any(c not in '0123456789abcdef' for c in args.experience):raise RuntimeError('invalid experience id')
    base=RAW/'archive-experience'/args.experience
    experience=load(base/'experience.json')
    previous=base/'old caf\u00e9 \u96ea/playtestr.exe';current=base/'upgrade caf\u00e9 \u96ea/playtestr.exe'
    if sha256(previous)!=experience['installed_binary_sha256']['previous'] or sha256(current)!=experience['installed_binary_sha256']['current']:
        raise RuntimeError('archive binaries changed')
    root=base/('version-rejection-'+uuid.uuid4().hex);root.mkdir()
    marker=root/'would-launch.html';report=base/'relocated caf\u00e9 \u96ea/previous-v2.json'
    env={k:os.environ[k] for k in ['SYSTEMROOT','WINDIR','COMSPEC','PATHEXT'] if k in os.environ}
    env.update(PATH=str(base/'empty-path'),TEMP=str(RAW/'tmp'),TMP=str(RAW/'tmp'))
    command=[str(current),'report','--input',str(report),'--evidence-root',str(report.parent),'--output',str(marker)]
    (root/'fixture').mkdir()
    control=dict(version=2,name='calibrated target launch',command=command,
        workspace=dict(fixture='fixture',cwd='.',home='temporary',temp='temporary'),
        timeout_ms=3000,run_timeout_ms=10000,steps=[dict(exit=0)])
    spec=root/'control-v2.json';immutable_json(spec,control)
    positive=await execute([previous,'test',spec],'core','archive-old-v2-target-side-effect-control',env=env,timeout=30,campaign=Campaign())
    if not marker.is_file() or marker.stat().st_size<100:raise RuntimeError('target side effect was not positively calibrated')
    preserved=root/'calibrated-target-output.html';marker.rename(preserved)
    rejected=root/'unsupported-v3.json';immutable_json(rejected,dict(control,version=3))
    negative=await execute([previous,'test',rejected],'core','archive-old-v3-prelaunch-rejection',env=env,expected=1,timeout=30,campaign=Campaign())
    if marker.exists() or 'unsupported' not in negative['output'].lower() or 'version' not in negative['output'].lower():
        raise RuntimeError('old archive did not clearly reject v3 before the calibrated launch effect')
    immutable_json(root/'verified.json',dict(positive_attempt=positive['id'],negative_attempt=negative['id'],
        previous_binary_sha256=sha256(previous),current_binary_sha256=sha256(current),calibrated_output_sha256=sha256(preserved),
        v2_spec_sha256=sha256(spec),v3_spec_sha256=sha256(rejected),target_side_effect_absent_after_rejection=True,
        final_archive_credit=0))
    print('Old private archive clearly rejected v3 before a positively calibrated target side effect:',root)


if __name__=='__main__':asyncio.run(main())
