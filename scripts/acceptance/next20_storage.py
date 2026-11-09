"""Observe declared combined campaign and current project storage ceilings."""
import argparse
from datetime import datetime, timezone
import json
import uuid

from next20_check import RAW, DOC, ROOT
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure
from next20_storage_baseline import prior_campaign_usage


def owned_short_cache(current):
    """Identify only Cargo's verified live short-path compiler cache as active."""
    target=RAW/'active/cargo-generate';cache=RAW/'r'
    for path in [RAW,RAW/'active',target,cache]:
        if not path.is_dir() or path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('live short-cache ownership root missing or linked')
    owner=json.loads((cache/'task-owned.json').read_text())
    reference=json.loads((target/'short-cache-reference.json').read_text())
    materialized=json.loads((cache/'materialized.json').read_text())
    catalog=sha256(target/'dependency-source-catalog.json')
    if (owner.get('workspace')!=str(ROOT) or owner.get('project')!='cargo-generate' or owner.get('source_target')!=str(target) or
        owner.get('catalog_sha256')!=catalog or reference.get('root')!=str(cache) or
        reference.get('owner_sha256')!=sha256(cache/'task-owned.json') or reference.get('materialized_sha256')!=sha256(cache/'materialized.json') or
        materialized.get('original_source_catalog_sha256')!=catalog):raise ValueError('live short compiler cache is not bound to actual owned target/source')
    size=current['top_level_bytes'].get('r',0)
    if not 0<size<=512*1024**2 or any(n=='r' or n.startswith('r/') for n in current['unfollowed_links']):raise ValueError('live short compiler cache size/link bound')
    return dict(path='r',project='cargo-generate',bytes=size,owner_sha256=sha256(cache/'task-owned.json'),
        materialized_sha256=sha256(cache/'materialized.json'),source_catalog_sha256=catalog,
        scope='Explicitly requested current owned compiler cache,not retained evidence. Still counted in raw and active-target bounds. Classification invalid once the owned target is absent; cache then must be removed or counted as retained.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--owned-short-cache-as-active',action='store_true');args=parser.parse_args()
    ledger=json.loads((DOC/'projects.json').read_text(encoding='utf-8'))
    # The ledger can add new rows without silently authorizing arbitrary paths.
    if '/' in args.project or '\\' in args.project or args.project in {'.','..'}:
        raise ValueError('unsafe storage project')
    if not (DOC/args.project/'source-provenance.json').is_file():raise ValueError('undeclared project storage scope')
    previous=prior_campaign_usage(DOC,ROOT)
    current=measure(RAW);curated=measure(DOC)
    caches={'active','toolchain','go-cache','gopath','gh-cache','tmp'}
    retained=lambda value,extra=():sum(v for k,v in value['top_level_bytes'].items() if k not in caches and k not in extra)
    short_cache=None
    if args.owned_short_cache_as_active:
        if args.project!='cargo-generate':raise ValueError('explicit live short-cache observation is Cargo-only')
        short_cache=owned_short_cache(current)
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
    active_root=RAW/'active'
    if active_root.exists():
        if active_root.is_symlink() or getattr(active_root,'is_junction',lambda:False)():
            raise ValueError('active target root is linked')
        for target in active_root.iterdir():
            if target.is_dir():active.append(dict(project=target.name,**measure(target)))
    if short_cache:
        if len(active)!=1 or active[0]['project']!='cargo-generate':raise ValueError('short compiler cache requires the single matching active target')
        active[0]['owned_short_cache_bytes']=short_cache['bytes'];active[0]['total_bytes']+=short_cache['bytes']
    caps=dict(new_raw=4*1024**3,combined_raw=6*1024**3,combined_retained=2*1024**3,
              project=64*1024**2,new_curated=25*1024**2,combined_curated=50*1024**2)
    actual=dict(new_raw=current['total_bytes'],combined_raw=current['total_bytes']+previous['raw'],
                combined_retained=retained(current,{'r'} if short_cache else ())+previous['retained'],project=size,new_curated=curated['total_bytes'],
                combined_curated=curated['total_bytes']+previous['curated'])
    failures=[k for k,v in actual.items() if v>caps[k]]
    if len(active)>1 or any(a['total_bytes']>min(4*1024**3,caps['combined_raw']-actual['combined_raw']+a['total_bytes']) for a in active):
        failures.append('active-target-bound')
    destination=RAW/'storage'/uuid.uuid4().hex
    immutable_json(destination/'observed.json',dict(schema_version=1,project=args.project,
        observed_at_utc=datetime.now(timezone.utc).isoformat(),caps=caps,actual=actual,
        active=active,expanded_native_artifacts=expanded,failed=failures,
        **(dict(explicit_live_short_cache_classification=short_cache) if short_cache else {}),
        scope='Observed logical bytes before this receipt; all project generations included. Historical campaign cache classification unchanged. Optional exact owned live Cargo cache classification is separately recorded; raw/active totals include it. No exact peak/allocation/quota claim.'))
    print('Observed campaign storage:',actual,'active:',[a['project'] for a in active],'failed:',failures)
    if failures:raise ValueError('Declared storage cap exceeded; preserve evidence and stop acquisition')


if __name__=='__main__':main()
