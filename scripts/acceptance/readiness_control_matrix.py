"""Bind all 88 historical control declarations to current immutable native events."""
import argparse
import hashlib
import json
from pathlib import Path

from readiness_evidence import ROOT, RAW, immutable_json, sha256
from readiness_new_control_matrix import packet_file


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',default='38950594057')
    parser.add_argument('--output',type=Path,default=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-control-matrix.json')
    args=parser.parse_args()
    if not args.run.isascii() or not args.run.isdecimal():raise RuntimeError('invalid native core run')
    output=args.output.resolve();output.relative_to(ROOT/'docs/validation/runner-readiness-ten-project-pass')
    historical=ROOT/'docs/validation/ten-new-project-adversarial-pass/coverage-matrix.json'
    original=json.loads(historical.read_text())
    if len(original['controls'])!=88:raise RuntimeError('historical control scope changed')
    native=RAW/'native'/args.run
    metadata=json.loads((native/'run-metadata.json').read_text(encoding='utf-8-sig'))
    if metadata['status']!='completed' or metadata['conclusion']!='success' or len(metadata['jobs'])!=3 or any(j['status']!='completed' or j['conclusion']!='success' for j in metadata['jobs']):
        raise RuntimeError('three actually successful native core jobs required')
    evidence={}
    for host in (p for p in native.iterdir() if p.is_dir()):
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
            launched=json.loads((events/(attempt+'-launched.json')).read_text())
            if finished['category']!='passed' or finished['exit_code']!=0 or launched['id']!=attempt or finished['harness_cleanup']!='harness_process_reaped' or finished['cleanup_errors']:
                raise RuntimeError('failed or unconfirmed parent cannot qualify controls')
            if sha256(console)!=finished['console_sha256']:raise RuntimeError('native control console changed')
            manifest=packet_file(host,identified['identity']['manifest'].replace('\\','/'),2*1024**2)
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
                    run=args.run,attempt=observation['attempt'],console_sha256=observation['console_sha256'],
                    identity_sha256=observation['manifest_sha256'],actual_test_file_sha256=actual))
        actions={item['action'] for item in row['evidence']}
        row['status']='development-executed' if actions=={'pass'} else 'explicit-unqualified-skip'
        if old['id']=='windows-workspace-long-path':
            row['disposition']='Hosted filesystem did not expose a short temporary-path alias; actual skip retained. Existing compact-path and bounded installer controls do not substitute for this exact path. Unqualified capability, no alias/host setting changes.'
        controls.append(row)
    immutable_json(output,dict(schema_version=1,historical_matrix_sha256=sha256(historical),controls=controls,
        native_run=args.run,native_metadata_sha256=sha256(native/'run-metadata.json'),
        count=88,whole_controls_with_passing_applicable_evidence=sum(c['status']=='development-executed' for c in controls),
        claim='Current source development evidence only; one real short-alias skip remains unqualified. Final candidate controls must execute again.'))
    print('Preserved all 88 declarations:',sum(c['status']=='development-executed' for c in controls),'have passing applicable native evidence; explicit skips remain unqualified.')


if __name__=='__main__':main()
