"""Bounded logical-byte storage observation for this campaign's owned roots."""
import argparse
from datetime import datetime,timezone
import os
from pathlib import Path
import uuid

from readiness_evidence import RAW,ROOT,immutable_json


def measure(root):
    totals={};count=0;links=[]
    for directory,dirs,files in os.walk(root,followlinks=False):
        linked=set()
        for name in dirs+files:
            path=Path(directory)/name
            if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
                linked.add(name);relative=path.relative_to(root)
                size=path.lstat().st_size
                totals[relative.parts[0]]=totals.get(relative.parts[0],0)+size
                links.append(relative.as_posix())
                if len(links)>1000:raise RuntimeError('storage link metadata bound')
        # Retained synthetic link controls are metadata, never traversal roots.
        # Inventorying them does not authorize their removal or follow targets.
        dirs[:]=[name for name in dirs if name not in linked]
        for name in files:
            if name in linked:continue
            path=Path(directory)/name;count+=1
            if count>250000:raise RuntimeError('storage observation count bound')
            if not path.is_file():raise RuntimeError('special storage observation entry')
            first=path.relative_to(root).parts[0]
            totals[first]=totals.get(first,0)+path.stat().st_size
    return dict(total_bytes=sum(totals.values()),files=count,top_level_bytes=totals,unfollowed_links=links)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True);args=parser.parse_args()
    if args.project not in {'plop','poetry','rubygems','edit','vis','fff','papis','frogmouth','hygen','rclone'}:
        raise RuntimeError('undeclared project storage scope')
    raw=measure(RAW);curated=measure(ROOT/'docs/validation/runner-readiness-ten-project-pass')
    # Prerequisite/build caches count in the six-GiB campaign ceiling. Everything
    # else is conservatively counted as retained evidence/private packages.
    caches={'active','toolchain','go-cache','gopath','gh-cache','tmp'}
    retained=sum(size for name,size in raw['top_level_bytes'].items() if name not in caches)
    project_bytes=raw['top_level_bytes'].get(args.project,0)
    native_bytes=0;native_runs=[]
    for run in (RAW/'native').iterdir():
        if run.is_dir() and any(run.glob('*/runner-readiness-ten-project-pass/'+args.project+'-native-runner.json')):
            native_bytes+=measure(run)['total_bytes'];native_runs.append(run.name)
    project_bytes+=native_bytes
    record=dict(raw=raw,curated=curated,retained_bytes=retained,selected_project=args.project,
        selected_project_bytes=project_bytes,attributed_expanded_native_bytes=native_bytes,native_runs=native_runs,
        checked_at_utc=datetime.now(timezone.utc).isoformat(),
        interpretation='Logical file bytes observed before writing this receipt; not allocation, exact peak or an OS quota.',
        active_projects=sorted(p.name for p in (RAW/'active').iterdir()))
    immutable_json(RAW/'storage'/(uuid.uuid4().hex+'.json'),record)
    if raw['total_bytes']>6*1024**3 or retained>2*1024**3 or curated['total_bytes']>25*1024**2 or project_bytes>64*1024**2:
        raise RuntimeError('declared campaign/retention/curated/project storage cap exceeded; preserve receipt and stop acquisition')
    print('Campaign bytes:',raw['total_bytes'],'retained:',retained,'curated:',curated['total_bytes'],
        'selected project:',project_bytes,'active:',record['active_projects'])


if __name__=='__main__':main()
