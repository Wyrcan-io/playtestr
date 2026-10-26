"""Close yo only from actual complete native cells and exact retained local bytes."""
import argparse
import copy
import hashlib
import json

from next20_check import RAW, ROOT, DOC
from next20_packet_archive import archive_path,verify
from next20_project_audit_controls import encoded
from next20_verify_jrnl import build_model,validate,json_payloads,require
from next20_yo_local_packet import read_bytes,verified_packet
from next20_yo_registry_reference import canonical_payloads
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--windows-run');parser.add_argument('--preflight',action='store_true')
    parser.add_argument('--verify-existing',action='store_true');args=parser.parse_args()
    require(not (args.preflight and args.verify_existing),'choose one readback mode')
    raw=RAW/'yo';package=DOC/'yo';subjects={}
    def data(path):
        path.resolve().relative_to(ROOT)
        value=read_bytes(path) if path.is_relative_to(raw) else path.read_bytes()
        subjects[path.relative_to(ROOT).as_posix()]=hashlib.sha256(value).hexdigest()
        return value
    def load(path):return json.loads(data(path).decode('utf-8-sig'))
    def digest(path):return hashlib.sha256(data(path)).hexdigest()
    require(not (RAW/'active/yo').exists(),'local yo target remains active')
    declaration=load(package/'final-series-declaration.json');require(declaration['revision']==3,'expected explicit Windows-only replacement')
    provenance=load(package/'source-provenance.json');scenarios=load(package/'scenarios.json')
    require(len(scenarios['cases'])==20 and sum(c['kind']=='normal' for c in scenarios['cases'])==8 and sum(c['kind']=='edge' for c in scenarios['cases'])==12,'canonical case boundary differs')
    require(sum(bool(c['combined_risks']) for c in scenarios['cases'])>=4,'combined risk boundary incomplete')
    frozen=load(package/'development-test-freeze.json')
    for name,value in frozen['inputs'].items():require(digest(package/name)==value,'canonical input/oracle changed')
    cleanup=load(raw/'retained-source/cleanup-inventory.json');removed=load(raw/'retained-source/removed.json')
    process=load(raw/'process-proof.json')
    require(removed['removed'] and removed['source_restored_exact'] and removed['cleanup_inventory_sha256']==digest(raw/'retained-source/cleanup-inventory.json'),'checked local source/runtime removal missing')
    require(process['confirmed_no_matching_live_processes'] and not process['matching_live_processes'] and cleanup['process_proof_sha256']==digest(raw/'process-proof.json'),'local native PID proof missing')
    require(cleanup['actual_reports_with_confirmed_cleanup']==60 and len(cleanup['unlaunched_setup_reports'])==1,'local report/cleanup accounting differs')
    # Every old local path remains byte-exact in the separately typed XZ packet.
    packet_index,packet_files=verified_packet()
    for name in ['index.json','verified.json','expanded-removed.json','packets.tar.xz','selected-restore.bin']:data(raw/'retained-local-v1'/name)
    packet_removed=load(raw/'retained-local-v1/expanded-removed.json')
    require(packet_removed['all_expanded_removed'] and packet_removed['index_sha256']==digest(raw/'retained-local-v1/index.json'),'local XZ expansion removal unbound')
    checked=list((raw/'retained-local-v1/audits').glob('*/checked.json'))
    require(bool(checked),'no genuine restored full local audit')
    for path in checked:
        row=load(path)
        require(row['actual_local_audit_passed'] and row['all_restored_duplicates_removed'] and row['exact_records_restored']==len(packet_files) and row['index_sha256']==digest(raw/'retained-local-v1/index.json'),'restored local audit did not complete exactly')
    require(not any((RAW/name).exists() for name in packet_files),'temporary local record duplicates remain')
    local_paths=list((raw/'local-audits').glob('*/verified.json'))
    require(bool(local_paths),'missing current independent local audit receipt')
    local=load(max(local_paths,key=lambda p:p.stat().st_mtime_ns))
    require(local['all_local_reports']==60 and local['separately_accounted_unlaunched_reports']==1 and local['local_real_faults']==3 and local['local_calibrations']==10 and local['source_runtime_removed'],'local audit incomplete')
    for logical,value in local['subjects'].items():require(digest(ROOT/logical)==value,'local audit subject changed or unavailable: '+logical)
    registry=load(package/'registry-payloads.json')
    require(registry['source_pin']==provenance['pin'] and registry['framework_lock_sha256']==digest(package/'generator-package-lock.json'),'canonical registry source identity differs')
    for logical,value in canonical_payloads().items():
        require(data(RAW/logical)==value,'mandatory canonical package source missing/changed')
    for generation in [1,2,4]:
        retained=raw/('retained-native-v'+str(generation));index=load(retained/'index.json')
        data(archive_path(retained,index));verify(archive_path(retained,index),index['files'])
        require(load(retained/'expanded-removed.json')['all_expanded_removed'],'earlier failed/partial native expansion remains')
        audit=load(retained/('startup-audit.json' if generation==4 else 'rejected-audit.json'))
        require(audit['archive_sha256']==index['archive_sha256'] and audit['index_sha256']==digest(retained/'index.json'),'earlier native failure evidence changed')
        require(audit.get('qualification_credit',audit.get('ordinary_qualification_credit'))==0,'partial native evidence relabeled qualified')
    for name in ['index.json','verified.json','expanded-removed.json','packets.tar.gz','duplicate-aliases.json','duplicate-aliases-removed.json']:
        data(raw/'retained-catalogs-v1'/name)
    from next20_catalog_store import catalog_bytes
    aliases=load(raw/'retained-catalogs-v1/duplicate-aliases.json')
    alias_removed=load(raw/'retained-catalogs-v1/duplicate-aliases-removed.json')
    require(alias_removed['all_exact_duplicates_removed'] and alias_removed['aliases_sha256']==digest(raw/'retained-catalogs-v1/duplicate-aliases.json'),'local catalog alias removal changed')
    for logical,canonical in aliases['aliases'].items():
        expected=aliases['files'][logical]['sha256']
        require(catalog_bytes(RAW/logical,expected)==catalog_bytes(RAW/canonical,expected),'local catalog logical source bytes unavailable')
    for name in ['source-provenance.json','source-review.json','setup-declaration.json','first-use.json','snapshot-authoring.json',
                 'first-development-disposition.json','development-revision.json','first-use-wrapper-disposition.json',
                 'sandbox-prelaunch-disposition.json','fault-declaration.json','first-native-disposition.json',
                 'windows-startup-disposition.json','final-series-declaration-v1.json','final-series-declaration-v2.json']:
        load(package/name)
    cells=[];models={};linux_run=declaration['accepted_prior_cells']['linux']['run']
    for host,generation,run in [('linux',3,linux_run),('windows',5,args.windows_run)]:
        if args.preflight and host=='windows':continue
        require(bool(run) and len(str(run))<=20 and str(run).isascii() and str(run).isdecimal(),'actual Windows replacement run required')
        retained=raw/('retained-native-v'+str(generation))
        model,index=build_model(retained,str(run),host,'yo');counts=validate(model);models[host]=model
        require(load(retained/'expanded-removed.json')['all_expanded_removed'],'qualified native expansion still present')
        load(retained/'index.json');load(retained/'verified.json');data(archive_path(retained,index))
        matches=[p for p in (raw/'audits').glob('*/actual-model.json') if load(p)==model]
        require(len(matches)==1,'complete actual native cell lacks one original independently audited model')
        payloads=json_payloads(retained,index);prefix='native/'+str(run)+'/next20-yo-'+('Windows' if host=='windows' else 'Linux')+'/'
        prerequisite=payloads[prefix+'yo/retained-source/node-prerequisite.json']
        cells.append(dict(host=host,run=str(run),source_revision=model['revision'],generation=generation,**counts,
            compression=index.get('compression','tar.gz'),archive_sha256=index['archive_sha256'],archive_bytes=index['archive_bytes'],
            model_sha256=digest(matches[0]),actual_node_version=prerequisite['version'],actual_node_sha256=prerequisite['node_sha256'],actual_npm_version=prerequisite['npm_version']))
    if args.preflight:
        require('linux' in models and 'windows' not in models,'preflight must not invent pending Windows evidence')
        print('Existing yo closure verified:60local reports, exact XZ recovery, canonical registry source, all original failures, complete carried Linux cell. Windows full replacement/audit/controls still required; no admission.')
        return
    controls=list((raw/'audit-controls').glob('*/results.json'));require(len(controls)==1,'native cell-model challenges missing/ambiguous')
    negatives=load(controls[0])['controls']
    require(len(negatives)==24 and len({(c['host'],c['control']) for c in negatives})==24,'incomplete actual native model challenges')
    for control in negatives:
        require(control['rejected'] and control.get('positive_model_root')=='campaign','nonqualifying native model challenge')
        positive=RAW/control['positive_model'];positive.resolve(strict=True).relative_to(raw/'audits')
        require(digest(positive)==control['positive_model_sha256'] and load(positive)==models[control['host']],'challenged model differs from actual complete cell')
        altered=copy.deepcopy(models[control['host']]);patch=control['mutation'];parent=altered
        for key in patch['path'][:-1]:parent=parent[key]
        key=patch['path'][-1]
        if patch['operation']=='truncate':parent[key]=parent[key][:patch['length']]
        else:require(patch['operation']=='replace','unknown native model mutation');parent[key]=patch['value']
        require(hashlib.sha256(encoded(altered)).hexdigest()==control['altered_canonical_json_sha256'],'native model corruption bytes differ')
        try:validate(altered)
        except ValueError:pass
        else:raise ValueError('Corrupted complete native cell accepted')
    size=measure(raw)['total_bytes'];require(size<=64*1024**2,'yo all-generation retained evidence exceeds64MiB')
    if args.verify_existing:
        existing=json.loads((package/'admission.json').read_text())
        require(existing['admitted'] and existing['project']=='yo' and existing['pin']==provenance['pin'] and
            existing['native_cells']==cells and existing['ordinary']==480 and existing['calibrations']==18 and
            existing['additional_terminal_only_probes']==2 and existing['all_local_reports']==60,'original admission differs from current actual closure')
        for logical,value in existing['subjects'].items():require(digest(ROOT/logical)==value,'original admission subject changed: '+logical)
        print('Original yo admission reproduced from complete actual native/local/negative evidence and exact physical or indexed subject bytes; immutable receipt unchanged.')
        return
    immutable_json(package/'admission.json',dict(schema_version=1,project='yo',repository='yeoman/yo',pin=provenance['pin'],
        admitted=True,candidate='v0.4.0-rc.5',native_cells=cells,canonical_scenarios=20,normal=8,edge=12,
        ordinary=480,real_source_faults=3,calibrations=18,additional_terminal_only_probes=2,
        development=local['development'],first_use_commands=3,first_use_controls=16,diagnosis_commands=2,
        maintenance_suffix_relocation=True,all_local_reports=60,separately_accounted_unlaunched_reports=1,
        cell_model_negative_controls=24,local_target_absent=True,retained_bytes=size,subjects=subjects,
        human_participants=0,human_usability='unmeasured',paid_admissions=0,
        startup_scope='Exact carried Linux2s variant; complete fresh Windows5s variant. Earlier Windows2s startup failure retained and excluded; no2s Windows claim.',
        source_scope='Actual pinned interpreted yo modules and official locked Generator APIs. Canonical SRI package source retained once and mandatory for each full native packet audit; no compiler or sandbox claim.',
        scope='One engineering admission from complete actual native cells on independently recorded source/run identities, with all original failures retained. Whole next-twenty campaign remains incomplete.'))
    print('Admitted yo:480ordinary,18mandatory calibrations+2separate probes;60local reports and all rejected attempts preserved. Full campaign incomplete.')


if __name__=='__main__':main()
