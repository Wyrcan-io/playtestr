"""Refuse starting the all-project freeze with an incomplete reviewed corpus."""
import argparse
import hashlib
import json
from pathlib import Path
from adversarial_process import DOC
from adversarial_journey import host_case_name

PROJECTS=['cookiecutter','copier','lf','superfile','helix','glow','broot','yazi','ranger','nnn']


def inspect(*,require_development=False):
    candidates=json.loads((DOC/'candidates.json').read_text(encoding='utf-8'))
    records=[];missing=[];pairs=[]
    for project in PROJECTS:
        candidate=next(c for c in candidates if c['repo'].split('/')[-1]==project)
        package=DOC/project;path=package/'scenarios.json'
        if not path.is_file():
            missing.append(project+': reviewed scenario corpus missing')
            continue
        config=json.loads(path.read_text(encoding='utf-8'));cases=config['cases']
        names=[c['name'] for c in cases]
        if len(names)!=len(set(names)):missing.append(project+': duplicate scenario names')
        normal=sum(c['kind']=='normal' for c in cases);edges=sum(c['kind']=='edge' for c in cases)
        if normal<5 or edges<5:missing.append(project+': needs five normal and five edge scenarios')
        contracts={}
        for case in cases:
            if case['kind'] not in ['normal','edge']:missing.append(project+': exploration cannot receive final credit')
            for host in candidate['planned_hosts']:
                spec=package/(host_case_name(case,config,{'linux':'Linux','macos':'Darwin','windows':'Windows'}[host])+'.json')
                if not spec.is_file():
                    missing.append(project+': missing '+spec.name+' for '+host)
                    continue
                data=json.loads(spec.read_text(encoding='utf-8'))
                contracts[spec.name]=hashlib.sha256(spec.read_bytes()).hexdigest()
                for step in data['steps']:
                    if 'snapshot' not in step:continue
                    baseline=package/'snapshots'/step['snapshot']
                    baseline.resolve().relative_to((package/'snapshots').resolve())
                    if not baseline.is_file():missing.append(project+': missing baseline '+baseline.name)
                    else:contracts['snapshots/'+baseline.name]=hashlib.sha256(baseline.read_bytes()).hexdigest()
        pairs.extend((project,host) for host in candidate['planned_hosts'])
        if require_development:
            for host in candidate['planned_hosts']:
                system={'linux':'Linux','macos':'Darwin','windows':'Windows'}[host]
                qualified=False
                for report in (DOC/'native').glob('*/adversarial-'+project+'-*/native-'+project+'-'+system+'.json'):
                    receipt=report.parent/('cleanup-'+system+'.json')
                    if not receipt.is_file():continue
                    actual=json.loads(report.read_text(encoding='utf-8'))
                    cleanup=json.loads(receipt.read_text(encoding='utf-8'))
                    if (actual.get('scenarios')==len(cases)
                        and actual.get('terminal_repetitions')==10*len(cases)
                        and actual.get('state_probe_repetitions')==10*len(cases)
                        and cleanup.get('removed') is True
                        and cleanup.get('source')==actual.get('source')):
                        qualified=True;break
                if not qualified:missing.append(project+': complete retained development evidence/cleanup missing on '+host)
        records.append(dict(project=project,source_pin=candidate['sha'],normal=normal,edges=edges,
                            contracts_sha256=contracts,planned_hosts=candidate['planned_hosts']))
    total=sum(r['normal']+r['edges'] for r in records)
    if total<100:missing.append('Needs at least 100 distinct reviewed scenarios')
    for host,required in [('linux',10),('windows',5),('macos',5)]:
        if sum(h==host for _,h in pairs)<required:missing.append('Insufficient '+host+' project assignments')
    return dict(ready=not missing,missing=missing,projects=records,distinct_scenarios=total,
                planned_project_host_pairs=len(pairs),scope='Corpus readiness only; no execution or platform qualification implied')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--inspect',action='store_true')
    parser.add_argument('--require-development',action='store_true')
    args=parser.parse_args();result=inspect(require_development=args.require_development)
    print(json.dumps(result,indent=2))
    if not args.inspect and not result['ready']:raise SystemExit('Final freeze refused: reviewed corpus is incomplete')


if __name__=='__main__':main()
