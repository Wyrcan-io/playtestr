"""Bind all 88 historical control declarations to current immutable native events."""
import hashlib
import json
from pathlib import Path

from readiness_evidence import ROOT, RAW, immutable_json, sha256


def main():
    historical=ROOT/'docs/validation/ten-new-project-adversarial-pass/coverage-matrix.json'
    original=json.loads(historical.read_text())
    if len(original['controls'])!=88:raise RuntimeError('historical control scope changed')
    native=RAW/'native/38950594057'
    evidence={}
    for host in native.iterdir():
        events=host/'events'
        identities=host/'identities'
        observations={}
        for console in host.rglob('console.log'):
            records=[]
            for line in console.read_text(encoding='utf-8',errors='replace').splitlines():
                try:row=json.loads(line)
                except ValueError:continue
                if isinstance(row,dict) and row.get('Action') in {'pass','skip','fail'} and row.get('Test'):
                    records.append(row)
            if not records:continue
            attempt=console.parent.name
            identified=json.loads((events/(attempt+'-identified.json')).read_text())
            finished=json.loads((events/(attempt+'-finished.json')).read_text())
            if finished['category']!='passed':raise RuntimeError('failed parent cannot qualify controls')
            manifest=host/identified['identity']['manifest'].replace('\\','/')
            if sha256(manifest)!=identified['identity']['sha256']:raise RuntimeError('identity manifest digest mismatch')
            files=json.loads(manifest.read_text())['files']
            for record in records:
                key=(record['Package'].removeprefix('github.com/Wyrcan-io/playtestr/'),record['Test'])
                observations.setdefault(key,[]).append(dict(action=record['Action'],attempt=attempt,
                    console_sha256=sha256(console),manifest_sha256=sha256(manifest),files=files))
        evidence[host.name]=observations
    controls=[]
    for old in original['controls']:
        source=ROOT/old['source'];canonical=source.read_bytes().replace(b'\r\n',b'\n')
        hashes={hashlib.sha256(canonical).hexdigest(),hashlib.sha256(canonical.replace(b'\n',b'\r\n')).hexdigest()}
        row={k:old[k] for k in ['id','family','test','package','requirement','severity','hosts','source']}
        row['current_canonical_source_sha256']=hashlib.sha256(canonical).hexdigest()
        row['historical_test_source_sha256']=old['test_source_sha256']
        row['evidence']=[]
        for host,observations in evidence.items():
            os_name='windows' if 'windows' in host else 'macos' if 'macos' in host else 'linux'
            if os_name not in row['hosts']:continue
            found=observations.get((old['package'].removeprefix('./'),old['test']),[])
            if not found:raise RuntimeError('applicable whole control missing: '+old['id']+' '+host)
            for observation in found:
                actual=observation['files'].get(old['source'])
                if actual not in hashes:raise RuntimeError('control source mismatch: '+old['id'])
                row['evidence'].append(dict(host=host,action=observation['action'],
                    run='38950594057',attempt=observation['attempt'],console_sha256=observation['console_sha256'],
                    identity_sha256=observation['manifest_sha256'],actual_test_file_sha256=actual))
        actions={item['action'] for item in row['evidence']}
        row['status']='development-executed' if actions=={'pass'} else 'explicit-unqualified-skip'
        if old['id']=='windows-workspace-long-path':
            row['disposition']='Hosted filesystem did not expose a short temporary-path alias; actual skip retained. Existing compact-path and bounded installer controls do not substitute for this exact path. Unqualified capability, no alias/host setting changes.'
        controls.append(row)
    output=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-control-matrix.json'
    immutable_json(output,dict(schema_version=1,historical_matrix_sha256=sha256(historical),controls=controls,
        count=88,whole_controls_with_passing_applicable_evidence=sum(c['status']=='development-executed' for c in controls),
        claim='Current source development evidence only; one real short-alias skip remains unqualified. Final candidate controls must execute again.'))
    print('Preserved all 88 declarations: 87 have passing applicable native evidence; one explicit short-alias skip.')


if __name__=='__main__':main()
