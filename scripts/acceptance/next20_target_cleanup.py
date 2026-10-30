"""Retain bounded target provenance, verify source restoration, and prepare cleanup."""
import argparse
import hashlib
from datetime import datetime,timezone
import json
import os
import re
from pathlib import Path
import shutil
import stat
import subprocess
import uuid

from next20_check import NAME,RAW,ROOT
from readiness_evidence import immutable_json,sha256


def prepare_native_directory_permissions(target,boundary):
    """Make checked, owned Unix directories removable without changing files."""
    if os.name=='nt':raise ValueError('native Unix directory preparation required')
    target=Path(target);boundary=Path(boundary).resolve(strict=True)
    resolved=target.resolve(strict=True);resolved.relative_to(boundary)
    if resolved==boundary or target.is_symlink():raise ValueError('unsafe owned permission root')
    count=0;changed=0;pending=[target]
    while pending:
        directory=pending.pop();count+=1
        directory.resolve(strict=True).relative_to(resolved)
        if count>60000 or directory.is_symlink():raise ValueError('owned directory permission boundary')
        mode=stat.S_IMODE(directory.stat().st_mode)
        if mode & (stat.S_IWUSR|stat.S_IXUSR)!=(stat.S_IWUSR|stat.S_IXUSR):
            directory.chmod(mode|stat.S_IWUSR|stat.S_IXUSR);changed+=1
        for entry in directory.iterdir():
            if entry.is_symlink():raise ValueError('unreviewed link during owned permission preparation')
            if entry.is_dir():pending.append(entry)
    return changed


def target_inventory(target, max_files=40000, max_bytes=1024**3):
    if max_files not in (40000,60000):raise ValueError('unreviewed cleanup file bound')
    if max_bytes not in (1024**3,2*1024**3):raise ValueError('unreviewed cleanup byte bound')
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
                if len(files)>=max_files or size>128*1024**2 or total>max_bytes:raise ValueError('cleanup inventory bound')
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


def cleanup_reports(project_root,closed_packets=()):
    """Include explicit fully retained closed windows without recounting copies."""
    seen=set()
    for path,data in report_documents(project_root):
        seen.add(path.relative_to(RAW).as_posix())
        yield path,data,sha256(path)
    if len(closed_packets)>4 or len(set(closed_packets))!=len(closed_packets):raise ValueError('closed report packet count/duplicates')
    for packet in closed_packets:
        if not re.fullmatch(r'retained-(?:failed|complete)-final-v[1-9][0-9]{0,2}',packet):raise ValueError('unsafe closed report packet')
        from next20_local_records import read_packet
        index,payloads=read_packet(project_root.name,packet=packet)
        root=project_root/packet;removed=json.loads((root/'expanded-removed.json').read_text(encoding='utf-8-sig'))
        if not removed['all_expanded_removed'] or removed['index_sha256']!=sha256(root/'index.json') or removed['archive_sha256']!=index['archive_sha256']:
            raise ValueError('closed report packet lacks matching complete retention/removal proof')
        for name,raw in payloads.items():
            if not name.endswith('.json') or {'fixture','fixtures'} & set(name.split('/')[:-1]):continue
            if len(raw)>4*1024**2:continue
            value=json.loads(raw.decode('utf-8-sig'))
            if not isinstance(value,dict) or 'runner_version' not in value or not isinstance(value.get('results'),list):continue
            if name in seen:raise ValueError('closed report has a duplicate physical or retained source')
            seen.add(name);yield RAW/name,value,hashlib.sha256(raw).hexdigest()


def invalid_spec_before_launch(data,row):
    """Recognize an explicit parser refusal, with zero process/cleanup credit."""
    return (len(data.get('results',[]))==1 and row.get('status')=='failed' and
        row.get('failure')==dict(category='invalid_spec',message='test specification is invalid') and
        row.get('target')==dict(exited=False) and row.get('duration_ms')==0 and
        row.get('viewport')==dict(width=0,height=0) and
        row.get('cleanup')==dict(attempted=False,graceful=False,forced=False,confirmed_exited=False) and
        not row.get('workspace') and not row.get('invocation_id') and not row.get('evidence') and
        not row.get('steps'))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True)
    parser.add_argument('--prepare-only',action='store_true')
    parser.add_argument('--resume-preparation',action='store_true')
    parser.add_argument('--generated-source-manifest',type=Path)
    parser.add_argument('--closed-report-packet',action='append',default=[])
    parser.add_argument('--canonical-native-generation',type=int)
    parser.add_argument('--retain-review-directory',action='append',choices=['wheel-review-inputs','linux-review-inputs'],default=[])
    parser.add_argument('--compress-review-metadata',action='store_true')
    parser.add_argument('--retain-all-provenance-json',action='store_true')
    parser.add_argument('--max-files',type=int,choices=[40000,60000],default=40000)
    parser.add_argument('--max-bytes',type=int,choices=[1024**3,2*1024**3],default=1024**3)
    parser.add_argument('--unlaunched-report-sha256',action='append',default=[])
    parser.add_argument('--invalid-spec-report-sha256',action='append',default=[]);args=parser.parse_args()
    if len(args.invalid_spec_report_sha256)>4 or len(set(args.invalid_spec_report_sha256))!=len(args.invalid_spec_report_sha256) or any(not re.fullmatch('[0-9a-f]{64}',v) for v in args.invalid_spec_report_sha256):
        raise ValueError('Explicit invalid-spec report digest bound')
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
    expected=acquisition['source_files'];generated={};generated_manifest=None
    if args.generated_source_manifest:
        generated_manifest=args.generated_source_manifest.resolve(strict=True);generated_manifest.relative_to(ROOT)
        value=json.loads(generated_manifest.read_text())
        provenance=ROOT/'docs/validation'/NAME/args.project/'source-provenance.json'
        if value['primary_source_provenance_sha256']!=sha256(provenance) or json.loads(provenance.read_text())['files']!=expected:
            raise ValueError('generated-source declaration does not bind original primary inputs')
        generated=value['generated_files']
        from next20_generated_source import restored_source_inventory
        expected=restored_source_inventory(expected,generated)
    if actual!=expected:raise ValueError('target source not exactly restored; retain it for investigation')
    reports=0;unlaunched=[]
    for path,data,report_digest in cleanup_reports(RAW/args.project,args.closed_report_packet):
        for row in data['results']:
            if report_digest in args.invalid_spec_report_sha256:
                if not invalid_spec_before_launch(data,row):raise ValueError('Explicit invalid-spec report contains launch/cleanup state')
                unlaunched.append(dict(report=path.relative_to(ROOT).as_posix(),sha256=report_digest,
                    category='invalid_spec',target_launched=False,workspace_prepared=False,cleanup_credit=0))
                continue
            if report_digest in args.unlaunched_report_sha256:
                if not (os.name=='nt' and len(data['results'])==1 and
                    row.get('failure')==dict(category='workspace_setup_failure',message='workspace setup failed: expand native workspace path: Access is denied.') and
                    row.get('target')==dict(exited=False) and not row.get('invocation_id') and
                    row.get('cleanup',{}).get('attempted') is False and
                    row.get('workspace',{}).get('prepared') is False and not row['workspace'].get('root') and not row['workspace'].get('id') and
                    row['workspace'].get('cleanup_attempted') is False and not row.get('evidence') and
                    all(s.get('status')=='not_run' for s in row['steps'])):
                    raise ValueError('Explicit unlaunched report contains launched/partially prepared state')
                unlaunched.append(dict(report=path.relative_to(ROOT).as_posix(),sha256=report_digest,
                    category='workspace_setup_failure',target_launched=False,workspace_prepared=False,cleanup_credit=0))
                continue
            if not row.get('cleanup',{}).get('confirmed_exited') or not row.get('workspace',{}).get('cleaned'):
                raise ValueError('unconfirmed target/workspace report prevents source/runtime deletion')
            reports+=1
    if reports==0:raise ValueError('no actual target report cleanup proof')
    if {r['sha256'] for r in unlaunched}!=set(args.unlaunched_report_sha256+args.invalid_spec_report_sha256):raise ValueError('Explicit unlaunched report not found exactly')
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
    retained=RAW/args.project/'retained-source'
    if args.resume_preparation:
        if not args.prepare_only or not retained.is_dir() or (retained/'prepared.json').exists() or (retained/'cleanup-inventory.json').exists():raise ValueError('only interrupted pre-inventory preparation may resume explicitly')
    else:retained.mkdir()
    names=['source.tar.gz','task-owned.json','acquisition.json','runtime.json','build.json','wheels.json',
           'dependency-review.json','installed-inventory.json','install-approval.json','requirements.txt','constraints.txt','launch-runtime-catalog.json',
           'node-prerequisite.json','dependency-fetch.json','build-lock-derivation.json','build-planned.json',
           'dependency-fetch-review.json','dependency-source-catalog.json','native-hook-review.json',
           'native-c-compiler.json','required-source-dictionary.json','version-check.json','short-cache-reference.json',
           'post-build-dependency-readback.json','frozen-wheel-download.json']
    copied={};references={};canonical_records=None;canonical_identity=None;review_payloads={}
    if args.canonical_native_generation is not None:
        if not 1<=args.canonical_native_generation<=9999 or args.resume_preparation:raise ValueError('explicit canonical reference generation/resume bound')
        from next20_local_native_references import canonical,reference_for
        canonical_identity,canonical_records=canonical(args.project,args.canonical_native_generation)
    def retain_file(source_file,destination,name):
        if canonical_records is not None:
            row=reference_for(name,source_file.read_bytes(),canonical_records)
            if row is not None:
                references[name]=row;copied[name]=row['sha256'];return
        if args.compress_review_metadata and (name.split('/')[0] in {'dependency-review','linux-dependency-review',*args.retain_review_directory} or ('/' not in name and name not in names)):
            if name.endswith(('.whl','.gz','.xz')):raise ValueError('unreferenced binary in metadata compression input')
            review_payloads[name]=source_file.read_bytes();copied[name]=sha256(source_file);return
        destination.parent.mkdir(parents=True,exist_ok=True)
        if destination.exists():
            if not args.resume_preparation or destination.is_symlink() or sha256(destination)!=sha256(source_file):raise ValueError('existing retained provenance differs; preserve it')
        else:shutil.copyfile(source_file,destination)
        if sha256(source_file)!=sha256(destination):raise ValueError('retained source provenance copy mismatch')
        copied[name]=sha256(destination)
    if generated_manifest:
        destination=retained/'generated-source-manifest.json';shutil.copyfile(generated_manifest,destination)
        copied[destination.name]=sha256(destination)
        for name,row in generated.items():
            destination=retained/'generated-source'/name;destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source/name,destination)
            if sha256(destination)!=row['sha256']:raise ValueError('generated source retention differs')
            copied[destination.relative_to(retained).as_posix()]=sha256(destination)
    for name in names:
        source_file=target/name
        if source_file.is_file():
            destination=retained/name
            retain_file(source_file,destination,name)
    if args.retain_review_directory or args.retain_all_provenance_json:
        for path in sorted(target.glob('*.json')):
            if path.name not in copied:retain_file(path,retained/path.name,path.name)
    for name in ['dependency-review','linux-dependency-review','wheels','npm-cache','npm-installed-locks','dependency-research','npm-metadata-retention',*args.retain_review_directory]:
        directory=target/name
        if directory.is_dir():
            destination=retained/name
            if destination.exists():raise ValueError('preserve existing retained directory')
            for path in directory.rglob('*'):
                if path.is_file():
                    relative=path.relative_to(target).as_posix()
                    retain_file(path,retained/relative,relative)
    if references:
        immutable_json(retained/'canonical-native-references.json',dict(schema_version=1,project=args.project,required_canonical_packet=canonical_identity,files=references,
            scope='Every source archive/wheel reference was compared byte-exact with its original local payload and standalone mandatory retained native packet before cleanup. No remote lookup or reference chain.'))
        copied['canonical-native-references.json']=sha256(retained/'canonical-native-references.json')
    if review_payloads:
        from next20_review_input_packet import write
        write(retained,review_payloads)
        for name in ['review-inputs.tar.xz','review-inputs-index.json']:copied[name]=sha256(retained/name)
    if args.resume_preparation and {p.relative_to(retained).as_posix() for p in retained.rglob('*') if p.is_file()}!=set(copied):raise ValueError('unknown interrupted retention payload')
    inventory=target_inventory(target,max_files=args.max_files,max_bytes=args.max_bytes)
    if args.max_files!=40000:inventory['max_files']=args.max_files
    if args.max_bytes!=1024**3:inventory['max_bytes']=args.max_bytes
    immutable_json(retained/'cleanup-inventory.json',dict(schema_version=1,project=args.project,owned_target=str(target),
        owner_sha256=sha256(target/'task-owned.json'),process_proof_sha256=sha256(proof_path),
        actual_reports_with_confirmed_cleanup=reports,source_restored_exact=True,retained=copied,
        **(dict(closed_report_packets={name:sha256(RAW/args.project/name/'index.json') for name in args.closed_report_packet}) if args.closed_report_packet else {}),
        **(dict(unlaunched_setup_reports=unlaunched) if unlaunched else {}),**inventory))
    immutable_json(retained/'prepared.json',dict(schema_version=1,cleanup_inventory_sha256=sha256(retained/'cleanup-inventory.json'),
        process_proof_sha256=sha256(proof_path),source_archive_sha256=sha256(target/'source.tar.gz'),
        source_restored_exact=True,removed=False))
    if not args.prepare_only:
        # One shell/process end-to-end, resolved owned root and complete checked
        # inventory above. Unlink only explicitly reviewed runtime aliases.
        for relative in inventory['owned_links']:(target/relative).unlink()
        prepared_directories=prepare_native_directory_permissions(target,RAW/'active')
        shutil.rmtree(target)
        if target.exists():raise ValueError('owned source/runtime root remains')
        immutable_json(retained/'removed.json',dict(schema_version=1,removed=True,owned_relative_path='active/'+args.project,
            cleanup_inventory_sha256=sha256(retained/'cleanup-inventory.json'),source_restored_exact=True,
            native_directory_permissions_prepared=prepared_directories,
            checked_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Verified exact source restoration and',reports,'target/workspace cleanups; retained provenance;',
        'Windows native removal pending' if args.prepare_only else 'owned source/runtime removed')


if __name__=='__main__':main()
