"""Separate every retained old-migration report outcome by actual applicability."""
from collections import Counter
import hashlib
import json
import re
import tarfile

from readiness_closing_old_audit import DOC, PROJECTS
from readiness_evidence import RAW, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load


def main():
    reports={};counts=Counter();statuses=Counter()
    pattern=re.compile(r'old-migration/([^/]+)/(linux|macos|windows)/(runs/[a-f0-9]{32}/results|corruption/[a-f0-9]{32}/(?:legacy-terminal-false-green|public-state-corruption-rejected|public-state-corruption-restored))\.json$')
    def add(name,data,digest):
        match=pattern.search(name)
        if not match:return
        # The logical application report path contains a fresh per-run ID;
        # identical copies of that same report add no outcomes.
        identity=match.group(0)
        if identity in reports:
            require(reports[identity]['sha256']==digest,'conflicting old report copies');return
        value=json.loads(data.decode('utf-8-sig'));cal='/corruption/' in identity
        require(value['summary']['total']==len(value['results']),'old report selected denominator differs')
        for row in value['results']:
            category='calibration' if cal else ('prelaunch-invalid' if row.get('failure',{}).get('category')=='invalid_spec' else 'ordinary')
            counts[category]+=1;statuses[(category,row['status'])]+=1
        reports[identity]=dict(sha256=digest,total=value['summary']['total'])
    for project in PROJECTS:
        for folder in sorted((RAW/('old-'+project)).glob('retained-native-v*')):
            index=load(folder/'index.json',maximum=4*1024**2)
            with tarfile.open(folder/'packets.tar.gz','r:gz') as archive:
                for name,row in index['files'].items():
                    if not pattern.search(name):continue
                    require(row['bytes']<=4*1024**2,'old accounting report size bound')
                    data=archive.extractfile(row.get('member',name)).read(4*1024**2+1)
                    require(len(data)==row['bytes'] and hashlib.sha256(data).hexdigest()==row['sha256'],'old accounting actual payload changed')
                    add(name,data,row['sha256'])
        for path in (RAW/'old-migration'/project).rglob('*.json'):
            name=path.relative_to(RAW).as_posix()
            if pattern.search(name):add(name,path.read_bytes(),sha256(path))
    require(dict(counts)=={'ordinary':565,'calibration':108,'prelaunch-invalid':3},'all old attempted actual outcome accounting differs')
    immutable_json(DOC/'all-old-attempt-accounting.json',dict(reports=reports,counts=dict(counts),
        statuses=[dict(category=c,status=s,outcomes=n) for (c,s),n in sorted(statuses.items())],
        total_selected_outcomes=sum(counts.values()),original_mixed_legacy_counter=500,
        original_actual_ordinary=425,original_actual_calibration=72,original_prelaunch_invalid=3,
        six_fresh_primary=140,six_fresh_calibration=36,
        scope='Actual original and six fresh old-migration report rows, deduplicated by unique run-path identity. The old field named observed_ordinary_executions includes calibration and invalid-spec outcomes. Final qualified 274 primary/63 calibration is a subset and is not added to these all-attempt totals. Setup/authoring/build commands are in the separate command journal.'))
    print('All actual old report outcomes:',dict(counts),'; selected total:',sum(counts.values()))


if __name__=='__main__':main()
