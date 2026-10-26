"""Admit the compiled Node project only from complete actual audited evidence."""
import copy
import hashlib
import json

from next20_check import RAW,ROOT,DOC
from next20_cz_cli_local_audit import main as audit_local
from next20_partial_readback import readback
from next20_project_audit_controls import encoded
from next20_verify_jrnl import build_model,validate,json_payloads,require
from readiness_compact_native import verify
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def main():
    project='cz-cli';raw=RAW/project;package=DOC/project;subjects={}
    def load(path):
        path.resolve(strict=True).relative_to(ROOT);subjects[path.relative_to(ROOT).as_posix()]=sha256(path)
        return json.loads(path.read_text(encoding='utf-8-sig'))
    require(not (RAW/'active'/project).exists(),'local source/runtime still active')
    cleanup=load(raw/'retained-source/cleanup-inventory.json');removed=load(raw/'retained-source/removed.json')
    require(removed['removed'] and removed['cleanup_inventory_sha256']==sha256(raw/'retained-source/cleanup-inventory.json'),'local native checked removal missing/changed')
    process=load(raw/'process-proof.json')
    require(process['confirmed_no_matching_live_processes'] and not process['matching_live_processes'] and cleanup['process_proof_sha256']==sha256(raw/'process-proof.json'),'local process proof missing/changed')
    local=audit_local();local_receipt=load(local/'verified.json')
    require(local_receipt['individual_reports']==cleanup['actual_reports_with_confirmed_cleanup']==63,'local all-report denominator differs')
    models={};cells=[]
    for host,generation in [('linux',3),('windows',4)]:
        retained=raw/('retained-native-v'+str(generation))
        model,index=build_model(retained,'40026867471',host,project);counts=validate(model);models[host]=model
        require(load(retained/'expanded-removed.json')['all_expanded_removed'],'complete native packet expansion still present')
        load(retained/'index.json');load(retained/'verified.json')
        payloads=json_payloads(retained,index)
        prefix='native/40026867471/next20-cz-cli-'+('Windows' if host=='windows' else 'Linux')+'/'
        prerequisite=payloads[prefix+'cz-cli/retained-source/node-prerequisite.json']
        cells.append(dict(host=host,run='40026867471',generation=generation,**counts,
            archive_sha256=index['archive_sha256'],archive_bytes=index['archive_bytes'],
            actual_node_version=prerequisite['version'],actual_node_sha256=prerequisite['node_sha256'],actual_npm_version=prerequisite['npm_version']))
    controls=list((raw/'audit-controls').glob('*/results.json'))
    require(len(controls)==1,'missing/ambiguous actual native cell-model challenges')
    negatives=load(controls[0])['controls'];require(len(negatives)==24 and len({(c['host'],c['control']) for c in negatives})==24,'incomplete/duplicate cell-model challenges')
    for control in negatives:
        require(control['rejected'] and control.get('positive_model_root')=='campaign','nonqualifying actual model challenge')
        positive=RAW/control['positive_model'];positive.resolve(strict=True).relative_to(raw/'audits')
        require(sha256(positive)==control['positive_model_sha256'] and load(positive)==models[control['host']],'challenged model is not the actual complete cell')
        altered=copy.deepcopy(models[control['host']]);patch=control['mutation'];parent=altered
        for key in patch['path'][:-1]:parent=parent[key]
        key=patch['path'][-1]
        if patch['operation']=='truncate':parent[key]=parent[key][:patch['length']]
        else:
            require(patch['operation']=='replace','unknown actual model mutation');parent[key]=patch['value']
        require(hashlib.sha256(encoded(altered)).hexdigest()==control['altered_canonical_json_sha256'],'reconstructed challenged bytes differ')
        try:validate(altered)
        except ValueError as error:require(str(error)==control['reason'],'actual model rejection reason changed')
        else:raise ValueError('altered actual cell accepted at admission')
    for generation in [1,2]:
        retained=raw/('retained-native-v'+str(generation));index=load(retained/'index.json')
        verify(retained/'packets.tar.gz',index['files'])
        require(index['archive_sha256']==sha256(retained/'packets.tar.gz') and load(retained/'expanded-removed.json')['all_expanded_removed'],'first failed setup evidence not preserved/closed')
        payloads=json_payloads(retained,index)
        metadata=payloads['native/40025853402/run-metadata.json']
        require(metadata['conclusion']=='failure' and metadata['headSha']=='3643f67b1b89e7de46fd15cec3dd71e4e9ced84c','original native setup refusal relabeled')
        require(not any(isinstance(v,dict) and 'runner_version' in v for v in payloads.values()),'first refused setup unexpectedly contains application reports')
    readback()
    for name in ['subset-verified.json','partial-payload-removed.json','read-back-verified.json']:
        load(raw/'compaction-attempts/linux-limit16-first'/name)
    aliases=load(raw/'retained-catalogs-v1/duplicate-aliases.json');alias_removed=load(raw/'retained-catalogs-v1/duplicate-aliases-removed.json')
    require(alias_removed['all_exact_duplicates_removed'] and alias_removed['aliases_sha256']==sha256(raw/'retained-catalogs-v1/duplicate-aliases.json'),'catalog duplicate alias removal unbound')
    from next20_catalog_store import catalog_bytes
    for logical,canonical in aliases['aliases'].items():
        digest=aliases['files'][logical]['sha256']
        require(catalog_bytes(RAW/logical,digest)==catalog_bytes(RAW/canonical,digest),'original logical catalog exact readback failed')
    for name in ['source-provenance.json','source-review.json','setup-declaration.json','build-lock-derivation.json',
                 'development-test-freeze.json','first-development-disposition.json','maintenance-first-disposition.json',
                 'fault-declaration.json','first-native-setup-disposition.json','final-series-declaration-v1.json',
                 'final-series-declaration.json','native-runtime-lock.json']:
        load(package/name)
    subjects[(package/'generated-ci.yml').relative_to(ROOT).as_posix()]=sha256(package/'generated-ci.yml')
    cases=load(package/'scenarios.json')['cases']
    require(len(cases)==20 and sum(c['kind']=='normal' for c in cases)==8 and sum(c['kind']=='edge' for c in cases)==12,'canonical scenario denominator differs')
    size=measure(raw)['total_bytes'];require(size<=64*1024**2,'project retained evidence exceeds64MiB')
    immutable_json(package/'admission.json',dict(schema_version=1,project=project,repository='commitizen/cz-cli',
        pin=load(package/'source-provenance.json')['pin'],admitted=True,candidate='v0.4.0-rc.5',
        native_cells=cells,canonical_scenarios=20,normal=8,edge=12,ordinary=480,real_source_faults=3,
        calibrations=18,additional_terminal_only_probes=2,development=local_receipt['development'],
        first_use_commands=3,first_use_controls=20,diagnosis_commands=2,maintenance_suffix_relocation=True,
        all_local_reports=63,cell_model_negative_controls=24,local_target_absent=True,
        retained_bytes=size,subjects=subjects,human_participants=0,human_usability='unmeasured',paid_admissions=0,
        generated_ci='Public template prepared/linted only; no delivered execution credit for this project. The required two different-category delivered triplets are independently admitted jrnl and Python Commitizen.',
        scope='One engineering admission from actual two-host compiled Node source/package/payload/runtime/report proofs. Original setup refusals, development failures, ineffective maintenance variant, incomplete transfer and compaction attempts remain separately accounted. Whole next-twenty/global closure remains incomplete.'))
    print('Admitted cz-cli:480 ordinary,18 mandatory calibrations,2 separate terminal-only probes; all63 local reports audited. Full campaign incomplete.')


if __name__=='__main__':main()
