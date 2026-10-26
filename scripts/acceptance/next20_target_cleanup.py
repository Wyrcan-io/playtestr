"""Retain bounded target provenance, verify source restoration, and prepare cleanup."""
import argparse
from datetime import datetime,timezone
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import uuid

from next20_check import NAME,RAW,ROOT
from readiness_evidence import immutable_json,sha256


def target_inventory(target, max_files=40000):
    if max_files not in (40000,60000):raise ValueError('unreviewed cleanup file bound')
    files={};links={};total=0;pending=[target]
    while pending:
        directory=pending.pop()
        for entry in directory.iterdir():
            relative=entry.relative_to(target).as_posix()
            if entry.is_symlink():
                value=os.readlink(entry)
                if entry.name!='lib64' or value!='lib' or entry.resolve()!=entry.parent/'lib':
                    raise ValueError('unreviewed cleanup source link')
                links[relative]=value
            elif getattr(entry,'is_junction',lambda:False)():raise ValueError('unreviewed cleanup reparse entry')
            elif entry.is_dir():pending.append(entry)
            elif entry.is_file():
                size=entry.stat().st_size;total+=size
                if len(files)>=max_files or size>128*1024**2 or total>1024**3:raise ValueError('cleanup inventory bound')
                files[relative]=dict(bytes=size,sha256=sha256(entry))
            else:raise ValueError('special cleanup payload')
    return dict(files=files,owned_links=links,total_bytes=total)


def report_documents(project_root):
    """Read report-shaped documents outside the declared fixture input trees."""
    for path in project_root.rglob('*.json'):
        if {'fixture','fixtures'} & set(path.relative_to(project_root).parts[:-1]):continue
        if path.stat().st_size>4*1024**2:continue
        data=json.loads(path.read_text(encoding='utf-8-sig'))
        if isinstance(data,dict) and 'runner_version' in data and isinstance(data.get('results'),list):yield path,data


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--max-files',type=int,choices=[40000,60000],default=40000)
    parser.add_argument('--unlaunched-report-sha256',action='append',default=[]);args=parser.parse_args()
    if len(args.unlaunched_report_sha256)>4 or len(set(args.unlaunched_report_sha256))!=len(args.unlaunched_report_sha256) or any(not re.fullmatch('[0-9a-f]{64}',v) for v in args.unlaunched_report_sha256):
        raise ValueError('Explicit unlaunched report digest bound')
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project):raise ValueError('unsafe target cleanup slug')
    target=RAW/'active'/args.project
    target.resolve(strict=True).relative_to(RAW/'active')
    for ancestor in [ROOT/'artifacts',RAW,RAW/'active',target]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('linked target cleanup ancestor')
    owner=json.loads((target/'task-owned.json').read_text())
    if owner['workspace']!=str(ROOT) or owner['campaign']!=NAME or owner['slug']!=args.project:raise ValueError('foreign target cleanup marker')
    acquisition=json.loads((target/'acquisition.json').read_text())
    source=target/'src'
    actual={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}
    if actual!=acquisition['source_files']:raise ValueError('target source not exactly restored; retain it for investigation')
    reports=0;unlaunched=[]
    for path,data in report_documents(RAW/args.project):
        for row in data['results']:
            if sha256(path) in args.unlaunched_report_sha256:
                if not (os.name=='nt' and len(data['results'])==1 and
                    row.get('failure')==dict(category='workspace_setup_failure',message='workspace setup failed: expand native workspace path: Access is denied.') and
                    row.get('target')==dict(exited=False) and not row.get('invocation_id') and
                    row.get('cleanup',{}).get('attempted') is False and
                    row.get('workspace',{}).get('prepared') is False and not row['workspace'].get('root') and not row['workspace'].get('id') and
                    row['workspace'].get('cleanup_attempted') is False and not row.get('evidence') and
                    all(s.get('status')=='not_run' for s in row['steps'])):
                    raise ValueError('Explicit unlaunched report contains launched/partially prepared state')
                unlaunched.append(dict(report=path.relative_to(ROOT).as_posix(),sha256=sha256(path),
                    category='workspace_setup_failure',target_launched=False,workspace_prepared=False,cleanup_credit=0))
                continue
            if not row.get('cleanup',{}).get('confirmed_exited') or not row.get('workspace',{}).get('cleaned'):
                raise ValueError('unconfirmed target/workspace report prevents source/runtime deletion')
            reports+=1
    if reports==0:raise ValueError('no actual target report cleanup proof')
    if {r['sha256'] for r in unlaunched}!=set(args.unlaunched_report_sha256):raise ValueError('Explicit unlaunched report not found exactly')
    if os.name=='nt':
        proof_path=RAW/args.project/'process-proof.json'
        proof=json.loads(proof_path.read_text(encoding='utf-8-sig'))
        if proof['owned_target']!=str(target) or not proof['confirmed_no_matching_live_processes'] or proof['matching_live_processes']:
            raise ValueError('native Windows target process proof missing/failed')
        if not args.prepare_only:raise ValueError('Windows removal must use native checked PowerShell after preparation')
    else:
        result=subprocess.run(['ps','-axo','pid=,lstart=,args='],capture_output=True,timeout=5,check=True)
        if len(result.stdout)>1024**2:raise ValueError('native process observer bound')
        matching=[line.split(None,1)[0].decode() for line in result.stdout.splitlines() if str(target).encode() in line]
        if matching:raise ValueError('owned target process path remains: '+','.join(matching))
        proof_path=RAW/args.project/'process-proof.json'
        immutable_json(proof_path,dict(owned_target=str(target),confirmed_no_matching_live_processes=True,
            matching_live_processes=[],scope='Bounded native process arguments and all runner descendant-cleanup reports; no global argument inventory persisted.'))
    retained=RAW/args.project/'retained-source';retained.mkdir()
    names=['source.tar.gz','task-owned.json','acquisition.json','runtime.json','build.json','wheels.json',
           'dependency-review.json','installed-inventory.json','install-approval.json','requirements.txt','constraints.txt','launch-runtime-catalog.json',
           'node-prerequisite.json','dependency-fetch.json','build-lock-derivation.json','build-planned.json']
    copied={}
    for name in names:
        source_file=target/name
        if source_file.is_file():
            destination=retained/name;shutil.copyfile(source_file,destination)
            if sha256(source_file)!=sha256(destination):raise ValueError('retained source provenance copy mismatch')
            copied[name]=sha256(destination)
    for name in ['dependency-review','linux-dependency-review','wheels','npm-cache','npm-installed-locks','dependency-research','npm-metadata-retention']:
        directory=target/name
        if directory.is_dir():
            destination=retained/name
            shutil.copytree(directory,destination)
            for path in destination.rglob('*'):
                if path.is_file():
                    relative=path.relative_to(retained).as_posix()
                    if sha256(target/relative)!=sha256(path):raise ValueError('retained dependency review/package changed')
                    copied[relative]=sha256(path)
    inventory=target_inventory(target,max_files=args.max_files)
    if args.max_files!=40000:inventory['max_files']=args.max_files
    immutable_json(retained/'cleanup-inventory.json',dict(schema_version=1,project=args.project,owned_target=str(target),
        owner_sha256=sha256(target/'task-owned.json'),process_proof_sha256=sha256(proof_path),
        actual_reports_with_confirmed_cleanup=reports,source_restored_exact=True,retained=copied,
        **(dict(unlaunched_setup_reports=unlaunched) if unlaunched else {}),**inventory))
    immutable_json(retained/'prepared.json',dict(schema_version=1,cleanup_inventory_sha256=sha256(retained/'cleanup-inventory.json'),
        process_proof_sha256=sha256(proof_path),source_archive_sha256=sha256(retained/'source.tar.gz'),
        source_restored_exact=True,removed=False))
    if not args.prepare_only:
        # One shell/process end-to-end, resolved owned root and complete checked
        # inventory above. Unlink only explicitly reviewed runtime aliases.
        for relative in inventory['owned_links']:(target/relative).unlink()
        shutil.rmtree(target)
        if target.exists():raise ValueError('owned source/runtime root remains')
        immutable_json(retained/'removed.json',dict(schema_version=1,removed=True,owned_relative_path='active/'+args.project,
            cleanup_inventory_sha256=sha256(retained/'cleanup-inventory.json'),source_restored_exact=True,
            checked_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Verified exact source restoration and',reports,'target/workspace cleanups; retained provenance;',
        'Windows native removal pending' if args.prepare_only else 'owned source/runtime removed')


if __name__=='__main__':main()
