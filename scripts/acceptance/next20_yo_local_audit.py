"""Independently audit retained local yo reports, source copies and public journeys."""
import base64
import copy
import hashlib
import json
import tarfile
import uuid

from next20_check import RAW, ROOT, DOC, NAME
from next20_local_audit import LocalAudit
from next20_target_cleanup import report_documents
from next20_catalog_store import catalog_bytes
from next20_verify_node import tar_files, require
from next20_verify_yo import dependencies, assembly
from readiness_evidence import immutable_json, sha256


def main():
    audit=LocalAudit('yo');raw=RAW/'yo';package=DOC/'yo';retained=raw/'retained-source'
    provenance=audit.load(package/'source-provenance.json');freeze=audit.load(package/'development-test-freeze.json')
    cleanup=audit.load(retained/'cleanup-inventory.json');removed=audit.load(retained/'removed.json')
    require(removed['removed'] and removed['source_restored_exact'] and not (RAW/'active/yo').exists(),'local owned runtime still present')
    require(removed['cleanup_inventory_sha256']==sha256(retained/'cleanup-inventory.json'),'local cleanup inventory changed')
    source=tar_files((retained/'source.tar.gz').read_bytes());audit.subject(retained/'source.tar.gz')
    require({n:hashlib.sha256(v).hexdigest() for n,v in source.items()}==provenance['files'],'local canonical source bytes differ')
    require({n[4:]:v['sha256'] for n,v in cleanup['files'].items() if n.startswith('src/')}==provenance['files'],'actual source was not restored before cleanup')
    def path_for(relative):
        return retained/relative.removeprefix('yo/retained-source/') if relative.startswith('yo/retained-source/') else RAW/relative
    def get(relative):return audit.load(path_for(relative))
    def hash_of(relative):
        path=path_for(relative);audit.subject(path);return sha256(path)
    cache={'yo/retained-source/'+p.relative_to(retained).as_posix():p.read_bytes()
           for p in (retained/'npm-cache/_cacache/content-v2').rglob('*') if p.is_file()}
    for p in (retained/'npm-cache/_cacache/content-v2').rglob('*'):
        if p.is_file():audit.subject(p)
    def raw_bytes(relative):
        if relative is None:return cache
        path=path_for(relative);audit.subject(path);return path.read_bytes()
    dependencies(get,raw_bytes,hash_of,'windows',provenance)
    metadata_root=retained/'npm-metadata-retention';metadata=audit.load(metadata_root/'index.json')
    metadata_removed=audit.load(metadata_root/'removed.json');audit.subject(metadata_root/'packets.tar.gz')
    require(metadata_removed['exact_nonpackage_files_removed'] and metadata_removed['index_sha256']==sha256(metadata_root/'index.json') and metadata_removed['archive_sha256']==metadata['archive_sha256']==sha256(metadata_root/'packets.tar.gz'),'exact cache metadata retention changed')
    observed={}
    with tarfile.open(metadata_root/'packets.tar.gz','r|gz') as bundle:
        for member in bundle:
            require(member.name in metadata['files'] and member.name not in observed and member.isfile() and member.size<=16*1024**2,'unsafe/duplicate retained cache metadata member')
            data=bundle.extractfile(member).read(16*1024**2+1)
            observed[member.name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    require(observed==metadata['files'],'retained cache metadata member byte readback differs')
    inventory=audit.load(retained/'installed-inventory.json')['files']
    for name,value in inventory.items():require(cleanup['files']['runtime/'+name]['sha256']==value,'actual restored runtime changed before cleanup')
    for name,value in freeze['inputs'].items():require(sha256(package/name)==value,'local frozen contract/input changed')
    first=audit.load(package/'first-use.json');snapshot=audit.load(package/'snapshot-authoring.json')
    require(first['shell_invocations']==3 and first['recorder_controls']==16 and not first['handwritten_playtestr_json'],'first public route measurement differs')
    require(snapshot['shell_invocations']==3 and snapshot['recorder_controls']==19 and not snapshot['handwritten_playtestr_json'],'technical public route measurement differs')
    for eid in first['attempts']+snapshot['attempts']:audit.command(eid,source=provenance['files'])
    expected=json.loads((package/'normal-project.json').read_text())
    for file,key in [('output/project.json','independently_expected_project_sha256'),('output/README.md','independently_expected_readme_sha256')]:
        state=next(s['state'] for s in expected['steps'] if s.get('state',{}).get('path')==file)
        require(hashlib.sha256(base64.b64decode(state['bytes_base64'])).hexdigest()==first[key],'public recorder approved unintended output')
    development=[]
    original=raw/'development-inputs-v1';preserved=audit.load(original/'preserved.json')
    for name,value in preserved['files'].items():require(sha256(original/name)==value,'original development input/screen changed')
    for summary_path in sorted((raw/'development').glob('*/summary.json')):
        summary=audit.load(summary_path)
        require(len(summary['results'])==20 and summary['final_ordinary_credit']==0,'incomplete or relabeled local development')
        is_original=summary['declaration_sha256']==preserved['original_declaration_sha256']
        folder=original if is_original else package
        declaration=audit.load(folder/'scenarios.json')
        for observation in summary['results']:
            report=ROOT/observation['report'];row=json.loads(report.read_text())['results'][0]
            launch=audit.command(observation['attempt'],original_failure=row['status']=='failed',source=provenance['files'])
            require(observation['spec_sha256'] in launch['base']['files'].values() and sha256(report)==observation['report_sha256'],'local development launch/report binding differs')
            case=next(c for c in declaration['cases'] if c['id']==observation['case'])
            require(sha256(folder/case['spec'])==observation['spec_sha256'],'local original/replacement spec changed')
        development.append(dict(passed=summary['passed'],failed=summary['failed'],summary_sha256=sha256(summary_path)))
    require(sorted((r['passed'],r['failed']) for r in development)==[(18,2),(20,0)],'local original/replacement denominator differs')
    declaration=audit.load(package/'fault-declaration.json')
    require(declaration['selected_after_freeze_sha256']==sha256(package/'development-test-freeze.json'),'local mutations selected before freeze')
    matrices=list((raw/'faults').glob('*/summary.json'));require(len(matrices)==1,'ambiguous local calibration matrix')
    matrix=audit.load(matrices[0]);require(matrix['calibrations']==10 and matrix['real_faults']==3,'local source calibration denominator differs')
    for fault in matrix['faults']:
        declared=next(f for f in declaration['faults'] if f['id']==fault['id']);original_source=source[fault['source']]
        require(original_source.count(declared['before'].encode())==1 and hashlib.sha256(original_source.replace(declared['before'].encode(),declared['after'].encode())).hexdigest()==fault['mutated_sha256'],'actual local mutation differs from declaration')
        require(fault['original_sha256']==fault['restored_sha256']==provenance['files'][fault['source']] and fault['restored_exact'],'local fault not exactly restored')
        for outcome in fault['outcomes']:
            expected_source=dict(provenance['files'])
            if outcome['phase'] in {'mutated','terminal-only'}:expected_source[fault['source']]=fault['mutated_sha256']
            launch=audit.command(outcome['attempt'],source=expected_source)
            proof=outcome['source_assembly'];files=assembly(proof,get,raw_bytes,hash_of,expected_source,inventory)
            catalog=json.loads(catalog_bytes(ROOT/proof['catalog_path'],proof['catalog_sha256']))
            require(catalog['files']==files and launch['target']['files']['artifacts/'+NAME+'/active/yo/launch-runtime-catalog.json']==proof['catalog_sha256'],'local actual interpreted execution catalog differs')
            require(sha256(ROOT/outcome['report'])==outcome['report_sha256'],'local fault report changed')
            report=json.loads((ROOT/outcome['report']).read_text())['results'][0]
            require(report['status']==('failed' if outcome['phase']=='mutated' else 'passed'),'local source-fault outcome differs')
            if outcome['phase']=='mutated':
                require(report['failure']['category']==declared['category'],'local source fault rejected for wrong reason')
                if fault['id']=='F03':
                    first_state=next(i for i,s in enumerate(report['steps']) if s['action']=='state')
                    require(all(s['status']=='passed' for s in report['steps'][:first_state]),'local saved corruption failed before terminal/exit completion')
    journeys=list(raw.glob('maintenance-*/journey.json'));require(len(journeys)==1,'ambiguous local public maintenance')
    journey=audit.load(journeys[0]);root=journeys[0].parent
    require(journey['real_fault_diagnostic_public_commands']==2 and not journey['compiler_execution'],'local diagnosis measurement or interpreted mode differs')
    original_cli=source['lib/cli.js'];anchor=declaration['faults'][2]['before'].encode()
    allowed={hashlib.sha256(original_cli).hexdigest(),hashlib.sha256(original_cli.replace(anchor,declaration['faults'][2]['after'].encode())).hexdigest()}
    for suffix in ['\n','\n\n']:
        allowed.add(hashlib.sha256(original_cli.replace(anchor,anchor+b"\n      fs.appendFileSync(path.resolve('output/project.json'), "+json.dumps(suffix).encode()+b');')).hexdigest())
    catalogs={}
    for proof in journey['source_assemblies']:
        receipt=get(proof['assembly_receipt'].removeprefix('artifacts/'+NAME+'/'));expected_source=dict(provenance['files'])
        require(receipt['source_inputs']['lib/cli.js'] in allowed,'undeclared local maintenance source variant')
        expected_source['lib/cli.js']=receipt['source_inputs']['lib/cli.js']
        files=assembly(proof,get,raw_bytes,hash_of,expected_source,inventory)
        catalog=json.loads(catalog_bytes(ROOT/proof['catalog_path'],proof['catalog_sha256']))
        require(catalog['files']==files,'local maintenance actual runtime catalog differs')
        catalogs[proof['catalog_sha256']]=expected_source
    for attempt in journey['attempts']:
        launch=audit.command(attempt['id']);require(launch['label']==attempt['label'],'local public maintenance attempt differs')
        actual_catalog=launch['target']['files']['artifacts/'+NAME+'/active/yo/launch-runtime-catalog.json']
        require(actual_catalog in catalogs,'local public maintenance launched an undeclared runtime catalog')
        actual_source={n.split('/src/',1)[1]:v for n,v in launch['target']['files'].items() if '/active/yo/src/' in n}
        require(actual_source==catalogs[actual_catalog],'local public maintenance actual source differs from declared variant')
    approved=audit.load(package/'normal-javascript.json');changed=audit.load(root/'reviewed route/maintained.json')
    approved['command'][0]=changed['command'][0];comparison=copy.deepcopy(changed);index=journey['selected_state_number']-1
    comparison['steps'][index]=approved['steps'][index]
    require(comparison==approved,'selected maintenance changed unrelated approvals')
    require(base64.b64decode(changed['steps'][index]['state']['bytes_base64'])==base64.b64decode(approved['steps'][index]['state']['bytes_base64'])+b'\n','selected update captured wrong JSON')
    require(sha256(root/'reviewed route/snapshots/javascript-complete.txt')==journey['snapshot_sha256']==sha256(package/'snapshots/javascript-complete.txt'),'maintenance changed unrelated snapshot')
    for name,key in [('maintained.json','maintained_spec_sha256'),('suffix.json','suffix_spec_sha256')]:
        require(sha256(root/'reviewed route'/name)==journey[key]==sha256(root/'relocated café 雪'/name),'relocation changed reviewed contract')
    suffix=audit.load(root/'reviewed route/suffix.json')
    require(any(s.get('key')=='CtrlC' for s in suffix['steps']) and not any(s.get('key')=='Enter' or 'snapshot' in s for s in suffix['steps']),'discarded completion suffix survived')
    require(not (root/'reviewed route/snapshots/discarded-before-cancel.txt').exists(),'discarded snapshot survived')
    unlaunched=audit.load(package/'sandbox-prelaunch-disposition.json')
    require(len(cleanup['unlaunched_setup_reports'])==1 and cleanup['unlaunched_setup_reports'][0]['sha256']==unlaunched['report_sha256'],'unlaunched report not explicitly separated at cleanup')
    total=0
    for path,report in report_documents(raw):
        if sha256(path)==unlaunched['report_sha256']:continue
        row=report['results'][0]
        audit.report(path,row['status'],row.get('failure',{}).get('category'));total+=1
    require(total==cleanup['actual_reports_with_confirmed_cleanup']==60,'local actual report/cleanup coverage differs')
    destination=raw/'local-audits'/uuid.uuid4().hex;destination.mkdir(parents=True)
    immutable_json(destination/'verified.json',dict(schema_version=1,project='yo',all_local_reports=total,
        separately_accounted_unlaunched_reports=1,development=development,local_real_faults=3,
        local_calibrations=10,source_runtime_removed=True,subjects=audit.subjects,
        ordinary_qualification_credit=0,new_project_admissions=0))
    print('Independently audited all60 local reports, separate unlaunched denial, actual source-copy faults, public maintenance and exact checked cleanup; no native admission credit.')


if __name__=='__main__':main()
