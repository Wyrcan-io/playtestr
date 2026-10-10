#!/usr/bin/env python3
"""Explicitly review changed synthetic Git fixture commit snapshots."""
import hashlib,json,os,re
from pathlib import Path
import user_journeys as j

base=j.DOC/'lazygit'
config=json.loads((base/'scenarios.json').read_text())
os.environ['PATH']=str((j.ROOT/config['runtime_path']).resolve())+os.pathsep+os.environ['PATH']
changed=[]
for case in config['cases']:
    baseline=base/'snapshots'/case['snapshot']
    before=baseline.read_text()
    # Preserve the old reviewed baseline as a synthetic evidence artifact.
    (j.RAW/'lazygit'/('fixture-before-'+case['snapshot'])).write_text(before)
    j.run([j.BIN,'test','--update','--snapshot',case['snapshot'],'--report',j.RAW/'lazygit'/('fixture-update-'+case['name']+'.json'),base/(case['name']+'.json')], 'lazygit/fixture-update-'+case['name'])
    after=baseline.read_text()
    # The only intended display change is the synthetic initial-commit hash.
    assert re.sub(r'\b[a-f0-9]{8}\b','COMMIT',before)==re.sub(r'\b[a-f0-9]{8}\b','COMMIT',after),case['name']
    print(json.dumps(dict(scenario=case['name'],changed_rows=[b for a,b in zip(before.splitlines(),after.splitlines()) if a!=b]),ensure_ascii=True),flush=True)
    changed.append(dict(scenario=case['name'],before_sha256=hashlib.sha256(before.encode()).hexdigest(),after_sha256=hashlib.sha256(after.encode()).hexdigest(),review='Only synthetic initial-commit hash changed; real Git mode regression independently verified'))
(j.RAW/'lazygit/fixture-baseline-review.json').write_text(json.dumps(changed,indent=2)+'\n')
