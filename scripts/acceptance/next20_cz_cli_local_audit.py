"""Audit actual cz-cli public authoring, first failures, faults and maintenance."""
import base64
import copy
import hashlib
import json
import uuid

from next20_check import RAW, ROOT, DOC, NAME
from next20_catalog_store import catalog_bytes
from next20_local_audit import LocalAudit
from next20_verify_jrnl import require
from next20_verify_node import dependencies, compiled_payloads, tar_files
from readiness_evidence import immutable_json, sha256


def main():
    audit=LocalAudit('cz-cli');raw=RAW/'cz-cli';package=DOC/'cz-cli';retained=raw/'retained-source'
    provenance=audit.load(package/'source-provenance.json');freeze=audit.load(package/'development-test-freeze.json')
    acquisition=audit.load(retained/'acquisition.json');build=audit.load(retained/'build.json')
    runtime=audit.load(retained/'runtime.json');inventory=audit.load(retained/'installed-inventory.json')
    require(acquisition['source_files']==provenance['files'] and sha256(retained/'source.tar.gz')==acquisition['archive_sha256'],'canonical local source archive differs')
    source=tar_files((retained/'source.tar.gz').read_bytes())
    require({n:hashlib.sha256(v).hexdigest() for n,v in source.items()}==provenance['files'],'actual local canonical source bytes differ')
    def get(relative):return audit.load(retained/relative.removeprefix('cz-cli/retained-source/'))
    cache={n.relative_to(ROOT).as_posix():n.read_bytes() for n in (retained/'npm-cache/_cacache/content-v2').rglob('*') if n.is_file()}
    def registry_raw(relative):return cache if relative is None else (retained/relative.removeprefix('cz-cli/retained-source/')).read_bytes()
    dependencies(get,registry_raw,lambda r:sha256(retained/r.removeprefix('cz-cli/retained-source/')),'windows',provenance)
    supplement=audit.load(raw/'compiled-byte-supplement.json')
    require(supplement['original_build_sha256']==sha256(retained/'build.json') and supplement['source_restored'] and supplement['compiled_original_restored'],'compiled byte supplement is not bound to original actual build')
    def code_raw(relative):
        path=RAW/relative;audit.subject(path);return path.read_bytes()
    compiled_payloads(dict(compiled_files=build['compiled_files'],compiled_payloads=supplement['original_payloads']),code_raw,build['compiled_files'])
    cleanup=audit.load(retained/'cleanup-inventory.json')
    require(cleanup['source_restored_exact'] and not cleanup['owned_links'],'unsafe local restored target inventory')
    require({n.removeprefix('src/'):r['sha256'] for n,r in cleanup['files'].items() if n.startswith('src/')}==provenance['files'],'local actual source not restored')
    for name,digest in {**inventory['files'],**build['compiled_files']}.items():
        require(cleanup['files'][runtime['app_relative_path']+'/'+name]['sha256']==digest,'local actual executed module changed before retention')
    for receipt,spec_name,report_name,controls in [('first-use.json','normal-message.json','first-ordinary-report.json',20),('snapshot-authoring.json','normal-fix.json','snapshot-ordinary-report.json',22)]:
        first=audit.load(package/receipt);spec=audit.load(package/spec_name)
        require(first['shell_invocations']==3 and len(first['attempts'])==3 and first['recorder_controls']==controls and not first['handwritten_playtestr_json'],'public authoring denominator differs')
        for eid in first['attempts']:audit.command(eid,source=provenance['files'])
        require(sha256(package/spec_name)==first['spec_sha256'] and sha256(raw/report_name)==first['report_sha256'],'public authoring contract/report changed')
        saved=next(s['state'] for s in spec['steps'] if s.get('state',{}).get('kind')=='file')
        require(hashlib.sha256(base64.b64decode(saved['bytes_base64'])).hexdigest()==first['independent_expected_file_sha256'],'independent first-use saved bytes differ')
        audit.report(raw/report_name,contract=spec)
    development=[]
    for series,passed,failed in [('0d34272bfcb3437e9b5ef6974731c970',17,3),('563b46e7d2a1459c8d5f7c262da12527',20,0)]:
        summary=audit.load(raw/'development'/series/'summary.json')
        require(summary['phase']=='development' and summary['final_ordinary_credit']==0 and len(summary['results'])==20,'local development relabeled or incomplete')
        statuses=[]
        for result in summary['results']:
            path=ROOT/result['report'];require(sha256(path)==result['report_sha256'],'first development report changed')
            row=audit.report(path,result['status'],result['category'])
            launch=audit.command(result['attempt'],original_failure=row['status']=='failed',source=provenance['files'])
            require(result['spec_sha256'] in launch['base']['files'].values(),'development actual contract hash not bound before launch')
            statuses.append(row['status'])
        require(statuses.count('passed')==passed and statuses.count('failed')==failed,'first development denominator changed')
        development.append(dict(series=series,passed=passed,failed=failed))
    disposition=audit.load(package/'first-development-disposition.json')
    originals=ROOT/disposition['original_inputs']
    for change in disposition['changes']:
        case=next(c for c in audit.load(package/'scenarios.json')['cases'] if c['id']==change['case'])
        require(sha256(originals/case['spec'])==change['original_sha256'] and sha256(package/case['spec'])==change['replacement_sha256'],'first failure original/replacement contract changed')
    faults_path=raw/'faults/3bdec96f6f2346b494c2a629ca4bfeb5/summary.json'
    summary=audit.load(faults_path);declaration=audit.load(package/'fault-declaration.json')
    require(declaration['selected_after_freeze_sha256']==sha256(package/'development-test-freeze.json') and summary['calibrations']==10,'local source faults not selected after canonical freeze')
    for fault in summary['faults']:
        declared=next(f for f in declaration['faults'] if f['id']==fault['id'])
        before=declared['before'].encode();original=source[fault['source']]
        require(original.count(before)==1 and hashlib.sha256(original.replace(before,declared['after'].encode())).hexdigest()==fault['mutated_sha256'],'local source mutation differs from declaration')
        require(fault['original_sha256']==fault['restored_sha256']==provenance['files'][fault['source']] and fault['restored_exact'],'local source fault not restored')
        late=next(r for r in supplement['supplements'] if r['fault']==fault['id'])
        require(late['original_summary_sha256']==sha256(faults_path),'late compiled payload supplement bound to another calibration')
        late_proof=late['rebuilt'];compiled_payloads(late_proof,code_raw,build['compiled_files'])
        for outcome in fault['outcomes']:
            mutated=outcome['phase'] in {'mutated','terminal-only'}
            expected_source=dict(provenance['files'])
            if mutated:expected_source[fault['source']]=fault['mutated_sha256']
            launch=audit.command(outcome['attempt'],source=expected_source)
            proof=outcome['compiled_build'];receipt=audit.load(ROOT/proof['compiled_receipt'])
            require(sha256(ROOT/proof['compiled_receipt'])==proof['compiled_receipt_sha256'] and receipt['source_inputs']==expected_source,'local actual compiler source/receipt differs')
            audit.command(proof['attempt'],runner=False,source=expected_source)
            require(receipt['compiled_files']==proof['compiled_files']==(late_proof['compiled_files'] if mutated else build['compiled_files']),'actual local compiled mutation/restoration bytes differ')
            catalog_path=raw/'faults/3bdec96f6f2346b494c2a629ca4bfeb5'/(fault['id']+'-'+outcome['phase']+'-runtime-catalog.json')
            catalog=json.loads(catalog_bytes(catalog_path,outcome['actual_runtime_catalog_sha256']))
            require(catalog['files']=={**inventory['files'],**proof['compiled_files']},'local actual calibration catalog differs from exact executed compiled variant')
            require(launch['target']['files']['artifacts/'+NAME+'/active/cz-cli/launch-runtime-catalog.json']==outcome['actual_runtime_catalog_sha256'],'actual compiled calibration catalog not bound at launch')
            report_path=ROOT/outcome['report'];require(sha256(report_path)==outcome['report_sha256'],'local calibration report changed')
            row=audit.report(report_path,'failed' if outcome['phase']=='mutated' else 'passed',declared['category'] if outcome['phase']=='mutated' else None)
            if fault['id']=='F03' and outcome['phase']=='mutated':
                state=next(i for i,s in enumerate(row['steps']) if s['action']=='state')
                require(all(s['status']=='passed' for s in row['steps'][:state]),'saved corruption failed before terminal/exit completion')
    root=raw/'maintenance-a040aa77eed640b59f8366b42434a2fa';journey=audit.load(root/'journey.json')
    require(journey['real_fault_diagnostic_public_commands']==2 and journey['selected_state_number']==18,'public diagnosis or selected update measurement differs')
    for attempt in journey['attempts']:require(audit.command(attempt['id'])['label']==attempt['label'],'public maintenance command mismatch')
    for path in root.glob('*.json'):
        data=json.loads(path.read_text(encoding='utf-8-sig'))
        if 'runner_version' not in data:continue
        failed=path.stem in {'diagnosis-real-saved-message-corruption','maintenance-intended-newline-change'}
        audit.report(path,'failed' if failed else 'passed','state_assertion_failure' if failed else None)
    approved=audit.load(package/'normal-fix.json');changed=audit.load(root/'reviewed route/maintained.json')
    approved['command'][0]=changed['command'][0];comparison=copy.deepcopy(changed);index=journey['selected_state_number']-1
    comparison['steps'][index]=approved['steps'][index]
    require(comparison==approved,'selected maintenance altered unrelated approvals')
    require(base64.b64decode(changed['steps'][index]['state']['bytes_base64'])==base64.b64decode(approved['steps'][index]['state']['bytes_base64'])+b'\n','maintenance intended newline bytes differ')
    require(sha256(root/'reviewed route/snapshots/normal-fix.txt')==journey['snapshot_sha256']==sha256(package/'snapshots/normal-fix.txt'),'unrelated approved snapshot changed')
    for name,key in [('maintained.json','maintained_spec_sha256'),('suffix.json','suffix_spec_sha256')]:
        require(sha256(root/'reviewed route'/name)==journey[key]==sha256(root/'relocated caf\u00e9 \u96ea'/name),'relocation edited approved contract bytes')
    suffix=audit.load(root/'reviewed route/suffix.json')
    require(any(s.get('key')=='CtrlC' for s in suffix['steps']) and not any(s.get('key')=='Enter' or 'snapshot' in s for s in suffix['steps']),'discarded successful suffix survived cancellation')
    require(not (root/'reviewed route/snapshots/discarded-before-cancel.txt').exists(),'discarded suffix snapshot survived')
    first_maintenance=audit.load(package/'maintenance-first-disposition.json')
    original=root.parent/first_maintenance['partial_root']/'maintenance-intended-newline-change.json'
    require(sha256(original)==first_maintenance['actual_report_sha256'],'ineffective original maintenance variant report changed')
    audit.report(original)
    partial=root.parent/first_maintenance['partial_root']
    partial_labels={'diagnosis-real-saved-message-corruption','diagnosis-restored-recovery','maintenance-intended-newline-change'}
    for path in partial.glob('*.json'):
        data=json.loads(path.read_text(encoding='utf-8-sig'))
        if 'runner_version' not in data or path==original:continue
        failed=path.stem=='diagnosis-real-saved-message-corruption'
        audit.report(path,'failed' if failed else 'passed','state_assertion_failure' if failed else None)
    partial_commands=[]
    for eid,label in [('0767317535834f348821b82bd254b364','diagnosis-real-saved-message-corruption'),
                      ('5de18f1e55584e53bca8e67f24ba6c62','diagnosis-restored-recovery'),
                      ('dfdf8b948ceb42f8872ac249a8982444','maintenance-intended-newline-change')]:
        launch=audit.command(eid,mismatch=(1,0) if label=='maintenance-intended-newline-change' else None)
        require(launch['label']==label,'first partial maintenance command label differs')
        report=audit.load(partial/(label+'.json'))
        spec_path=ROOT/report['results'][0]['spec_path'];spec_path.resolve(strict=True).relative_to(ROOT)
        require(launch['base']['files'].get(spec_path.relative_to(ROOT).as_posix())==sha256(spec_path),'first partial maintenance actual contract not bound')
        partial_commands.append(label)
    require(len(partial_commands)==3 and set(partial_commands)==partial_labels,'partial first maintenance actual commands missing/ambiguous')
    require(len(audit.seen)==cleanup['actual_reports_with_confirmed_cleanup'],'local public/first-failure/calibration report denominator incomplete')
    destination=raw/'local-audits'/uuid.uuid4().hex
    immutable_json(destination/'verified.json',dict(schema_version=1,project='cz-cli',development=development,
        first_use_commands=3,first_use_controls=20,technical_snapshot_controls=22,local_calibrations=10,
        diagnosis_commands=2,maintenance_suffix_relocation=True,individual_reports=len(audit.seen),
        subjects=audit.subjects,source_runtime_removal_pending=True,new_project_admissions=0,
        scope='Actual local public workflow evidence, preserved first failures, source/compiled/catalog identities and retained canonical package payload reconstruction. Older local helpers retain their recorded hash epochs; no claim their bodies equal later committed native helpers. Native matrix and checked local removal remain separate.'))
    print('Independently audited local cz-cli public journeys, both complete development series, ten compiled calibrations and maintenance; no project admission.')
    return destination


if __name__=='__main__':main()
