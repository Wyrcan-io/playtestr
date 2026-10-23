"""Observe declared combined campaign and current project storage ceilings."""
import argparse
from datetime import datetime, timezone
import json
import uuid

from next20_check import RAW, DOC, ROOT
from readiness_evidence import immutable_json
from readiness_storage import measure


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    ledger=json.loads((DOC/'projects.json').read_text(encoding='utf-8'))
    # The ledger can add new rows without silently authorizing arbitrary paths.
    if '/' in args.project or '\\' in args.project or args.project in {'.','..'}:
        raise ValueError('unsafe storage project')
    if not (DOC/args.project/'source-provenance.json').is_file():raise ValueError('undeclared project storage scope')
    old_raw=ROOT/'artifacts/runner-readiness-ten-project-pass'
    old_doc=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    current=measure(RAW);old=measure(old_raw);curated=measure(DOC);prior_curated=measure(old_doc)
    caches={'active','toolchain','go-cache','gopath','gh-cache','tmp'}
    retained=lambda value:sum(v for k,v in value['top_level_bytes'].items() if k not in caches)
    size=current['top_level_bytes'].get(args.project,0)
    expanded=[]
    native=RAW/'native'
    if native.is_dir():
        for run in native.iterdir():
            if not run.is_dir():continue
            for artifact in run.iterdir():
                if artifact.is_dir() and (artifact/args.project).is_dir():
                    observation=measure(artifact);size+=observation['total_bytes']
                    expanded.append(artifact.relative_to(RAW).as_posix())
    active=[]
    for target in (RAW/'active').iterdir():
        if target.is_dir():active.append(dict(project=target.name,**measure(target)))
    caps=dict(new_raw=4*1024**3,combined_raw=6*1024**3,combined_retained=2*1024**3,
              project=64*1024**2,new_curated=25*1024**2,combined_curated=50*1024**2)
    actual=dict(new_raw=current['total_bytes'],combined_raw=current['total_bytes']+old['total_bytes'],
                combined_retained=retained(current)+retained(old),project=size,new_curated=curated['total_bytes'],
                combined_curated=curated['total_bytes']+prior_curated['total_bytes'])
    failures=[k for k,v in actual.items() if v>caps[k]]
    if len(active)>1 or any(a['total_bytes']>min(4*1024**3,caps['combined_raw']-actual['combined_raw']+a['total_bytes']) for a in active):
        failures.append('active-target-bound')
    destination=RAW/'storage'/uuid.uuid4().hex
    immutable_json(destination/'observed.json',dict(schema_version=1,project=args.project,
        observed_at_utc=datetime.now(timezone.utc).isoformat(),caps=caps,actual=actual,
        active=active,expanded_native_artifacts=expanded,failed=failures,
        scope='Observed logical bytes before this receipt; all project generations included. Shared cache classification preserves the first-campaign closing definition. No exact peak/allocation/quota claim.'))
    print('Observed campaign storage:',actual,'active:',[a['project'] for a in active],'failed:',failures)
    if failures:raise ValueError('Declared storage cap exceeded; preserve evidence and stop acquisition')


if __name__=='__main__':main()
