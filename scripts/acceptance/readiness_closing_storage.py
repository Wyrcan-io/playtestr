"""Observe every campaign/project cap and retain historical sampled high waters."""
from datetime import datetime, timezone

from readiness_closing_old_audit import DOC, PROJECTS
from readiness_evidence import RAW, immutable_json
from readiness_final_batch_verify import require
from readiness_final_matrix_audit import PROJECTS as NEW
from readiness_new_control_matrix import read_json as load
from readiness_storage import measure


def main():
    raw=measure(RAW);curated=measure(DOC)
    retained=sum(n for name,n in raw['top_level_bytes'].items() if name not in {'active','toolchain','go-cache','gopath','gh-cache','tmp'})
    active=list((RAW/'active').iterdir());require(not active,'owned application still active')
    projects=[]
    for name in [*NEW,*['old-'+p for p in PROJECTS]]:
        size=raw['top_level_bytes'].get(name,0);native=[]
        if name.startswith('old-'):
            folder=RAW/'old-migration'/name[4:]
            if folder.exists():size+=measure(folder)['total_bytes']
        for run in (RAW/'native').iterdir():
            if not run.is_dir():continue
            attributed=(any(run.glob('*/runner-readiness-ten-project-pass/'+name+'-native-runner.json'))
                or any(run.glob('*/'+name+'-native-runner.json')) or any(p.is_dir() for p in run.glob('*/'+name)))
            if not attributed:
                for path in run.glob('*/events/*-started.json'):
                    event=load(path,maximum=65536)
                    if event.get('project')==name or event.get('label','').startswith(name+'-native-'):attributed=True;break
            if attributed:size+=measure(run)['total_bytes'];native.append(run.name)
        cap=(32 if name.startswith('old-') else 64)*1024**2
        projects.append(dict(project=name,bytes=size,cap_bytes=cap,expanded_native_runs=native))
        require(size<=cap,'project retention cap exceeded: '+name)
    samples=[]
    for path in (RAW/'storage').glob('*.json'):
        value=load(path,maximum=4*1024**2)
        if all(k in value for k in ['raw','retained_bytes','curated']):samples.append(value)
    require(raw['total_bytes']<=6*1024**3 and retained<=2*1024**3 and curated['total_bytes']<=25*1024**2,'closing global storage cap exceeded')
    immutable_json(DOC/'closing-storage.json',dict(observed_at_utc=datetime.now(timezone.utc).isoformat(),
        raw_bytes=raw['total_bytes'],retained_bytes=retained,curated_bytes=curated['total_bytes'],raw_files=raw['files'],
        caps=dict(raw_bytes=6*1024**3,retained_bytes=2*1024**3,curated_bytes=25*1024**2),projects=projects,active_projects=[],
        prior_samples=len(samples),sampled_high_water=dict(raw_bytes=max([raw['total_bytes']]+[s['raw']['total_bytes'] for s in samples]),
            retained_bytes=max([retained]+[s['retained_bytes'] for s in samples]),curated_bytes=max([curated['total_bytes']]+[s['curated']['total_bytes'] for s in samples])),
        prior_project_cap_breach_observations=sum(s.get('selected_project_bytes',0)>s.get('selected_project_cap_bytes',2**63) for s in samples),
        unfollowed_links=raw['unfollowed_links'],
        scope='Logical bytes observed before writing this receipt, including retained evidence, candidate packages, owned prerequisites and caches. All twenty current project caps checked. Periodic samples are neither exact disk allocation/peak nor an OS quota. Earlier policy breaches remain in requirements/limitations. Shared prerequisites and verified evidence are intentionally retained; all qualified application active roots are absent.'))
    print('Closing storage bytes:',raw['total_bytes'],'raw,',retained,'retained,',curated['total_bytes'],'curated; all20project caps pass; active[]')


if __name__=='__main__':main()
