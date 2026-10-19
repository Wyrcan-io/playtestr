"""Bounded logical-byte storage observation for this campaign's owned roots."""
import argparse
import json
from datetime import datetime,timezone
import os
import stat
from pathlib import Path
import uuid

from readiness_evidence import RAW,ROOT,immutable_json


def measure(root):
    root=Path(root)
    if root.is_symlink() or getattr(root,'is_junction',lambda:False)():raise RuntimeError('linked storage observation root')
    totals={};count=0;links=[];entries=0
    pending=[(str(root),None)]
    while pending:
        directory,top=pending.pop()
        with os.scandir(directory) as children:
            for entry in children:
                entries+=1
                if entries>500000:raise RuntimeError('storage directory entry bound')
                info=entry.stat(follow_symlinks=False)
                first=entry.name if top is None else top
                linked=(stat.S_ISLNK(info.st_mode) or getattr(info,'st_reparse_tag',0)==
                        getattr(stat,'IO_REPARSE_TAG_MOUNT_POINT',0xA0000003))
                if linked:
                    totals[first]=totals.get(first,0)+info.st_size
                    links.append(Path(entry.path).relative_to(root).as_posix())
                    if len(links)>1000:raise RuntimeError('storage link metadata bound')
                elif stat.S_ISDIR(info.st_mode):
                    pending.append((entry.path,first))
                elif stat.S_ISREG(info.st_mode):
                    count+=1
                    if count>250000:raise RuntimeError('storage observation count bound')
                    totals[first]=totals.get(first,0)+info.st_size
                else:raise RuntimeError('special storage observation entry')
    return dict(total_bytes=sum(totals.values()),files=count,top_level_bytes=totals,unfollowed_links=sorted(links))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);args=parser.parse_args()
    old=args.project.startswith('old-')
    old_names={p['project'] for p in json.loads((ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration-inventory.json').read_text())['projects']}
    if (old and args.project[4:] not in old_names or not old and
            args.project not in {'plop','poetry','rubygems','edit','vis','fff','papis','frogmouth','hygen','rclone'}):
        raise RuntimeError('undeclared project storage scope')
    raw=measure(RAW);curated=measure(ROOT/'docs/validation/runner-readiness-ten-project-pass')
    # Prerequisite/build caches count in the six-GiB campaign ceiling. Everything
    # else is conservatively counted as retained evidence/private packages.
    caches={'active','toolchain','go-cache','gopath','gh-cache','tmp'}
    retained=sum(size for name,size in raw['top_level_bytes'].items() if name not in caches)
    project_bytes=raw['top_level_bytes'].get(args.project,0)
    migration_bytes=0
    if old:
        migration=RAW/'old-migration'/args.project[4:]
        if migration.exists():migration_bytes=measure(migration)['total_bytes']
        project_bytes+=migration_bytes
    native_bytes=0;native_runs=[]
    for run in (RAW/'native').iterdir():
        if not run.is_dir():continue
        attributed=(any(run.glob('*/runner-readiness-ten-project-pass/'+args.project+'-native-runner.json'))
                    or any(run.glob('*/'+args.project+'-native-runner.json'))
                    or any(p.is_dir() for p in run.glob('*/'+args.project)))
        if not attributed:
            for event in run.glob('*/events/*-started.json'):
                if event.stat().st_size>65536:raise RuntimeError('storage attribution event byte bound')
                row=json.loads(event.read_text(encoding='utf-8-sig'))
                if row.get('project')==args.project or row.get('label','').startswith(args.project+'-native-'):
                    attributed=True
                    break
        if attributed:
            native_bytes+=measure(run)['total_bytes'];native_runs.append(run.name)
    project_bytes+=native_bytes
    record=dict(raw=raw,curated=curated,retained_bytes=retained,selected_project=args.project,
        selected_project_bytes=project_bytes,selected_project_cap_bytes=(32 if old else 64)*1024**2,
        old_migration_package_bytes=migration_bytes,attributed_expanded_native_bytes=native_bytes,native_runs=native_runs,
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        interpretation='Logical file bytes observed before writing this receipt; not allocation, exact peak or an OS quota.',
        active_projects=sorted(p.name for p in (RAW/'active').iterdir()))
    immutable_json(RAW/'storage'/(uuid.uuid4().hex+'.json'),record)
    if raw['total_bytes']>6*1024**3 or retained>2*1024**3 or curated['total_bytes']>25*1024**2 or project_bytes>record['selected_project_cap_bytes']:
        raise RuntimeError('declared campaign/retention/curated/project storage cap exceeded; preserve receipt and stop acquisition')
    print('Campaign bytes:',raw['total_bytes'],'retained:',retained,'curated:',curated['total_bytes'],
        'selected project:',project_bytes,'active:',record['active_projects'])


if __name__=='__main__':main()
