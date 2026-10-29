"""Close only Hatch's exact two-host private-candidate qualification."""
import hashlib
import json

from next20_check import DOC,RAW,ROOT
from next20_local_records import read_packet as local_packet
from next20_native_packet_reader import read_packet as native_packet
from next20_packet_archive import archive_path
from next20_review_input_packet import read as review_packet
from readiness_evidence import immutable_json,sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    package=DOC/'hatch';root=RAW/'hatch';subjects={}
    require(not (RAW/'active/hatch').exists(),'owned Hatch source/runtime remains')
    local_index,local=local_packet('hatch');closed_index,closed=local_packet('hatch',packet='retained-complete-final-v1')
    require(not set(local)&set(closed),'duplicate local/complete-window source records')
    records={**local,**closed}
    def raw(name):
        path=RAW/name
        body=path.read_bytes() if path.is_file() else records[name]
        subjects['artifacts/'+RAW.name+'/'+name]=hashlib.sha256(body).hexdigest()
        return body
    def value(name):return json.loads(raw(name).decode('utf-8-sig'))
    for packet in ['retained-local-v1','retained-complete-final-v1']:
        proof=value('hatch/'+packet+'/expanded-removed.json')
        require(proof['all_expanded_removed'],'unremoved retained evidence duplicate')
        for name in ['index.json','packets.tar.xz','prepared.json']:raw('hatch/'+packet+'/'+name)
    owner=value('hatch/retained-source/task-owned.json');removed=value('hatch/retained-source/removed.json')
    cleanup=value('hatch/retained-source/cleanup-inventory.json');process=value('hatch/process-proof.json')
    require(removed['removed'] and removed['source_restored_exact'] and removed['cleanup_inventory_sha256']==hashlib.sha256(raw('hatch/retained-source/cleanup-inventory.json')).hexdigest(),'source/runtime removal proof differs')
    require(cleanup['source_restored_exact'] and cleanup['actual_reports_with_confirmed_cleanup']==328 and process['confirmed_no_matching_live_processes'] and not process['matching_live_processes'],'historical report/process cleanup incomplete')
    primary=json.loads((package/'source-provenance.json').read_text());require(owner['pin']==primary['pin'],'wrong owned target pin')
    metadata=review_packet(root/'retained-source');refs=value('hatch/retained-source/canonical-native-references.json')
    require(len(refs['files'])==49 and len(metadata)>50,'source/dependency review retention incomplete')
    for name in ['review-inputs-index.json','review-inputs.tar.xz']:raw('hatch/retained-source/'+name)
    for generation in [1,2]:
        index,payloads=native_packet('hatch',generation);native_root=root/('retained-native-v'+str(generation))
        for path in [native_root/'index.json',archive_path(native_root,index),native_root/'verified.json']:
            subjects[path.relative_to(ROOT).as_posix()]=sha256(path)
        if generation==2:require(len(payloads)==3547 and len(index['external_exact_payloads'])==972,'native final logical packet coverage differs')
    results=max((root/'audit-controls').glob('*/results.json'),key=lambda p:p.stat().st_mtime_ns)
    controls=json.loads(results.read_text());require(controls['semantic_corruptions_rejected']==32,'missing actual semantic corruption challenges')
    subjects[results.relative_to(ROOT).as_posix()]=sha256(results)
    cells=[]
    for host in ['windows','linux']:
        readbacks=[p for p in (root/'cell-readbacks').glob(host+'-*.json') if json.loads(p.read_text())['source_runtime_removed']]
        require(readbacks,'missing post-cleanup actual cell readback');path=max(readbacks,key=lambda p:p.stat().st_mtime_ns);audit=json.loads(path.read_text())
        require(audit['ordinary_readbacks']==240 and audit['calibration_readbacks']==9 and audit['actual_attempts_verified']==249 and audit['helper_source_revision']=='010940a5db4e166d72f78641a46334e5ef49f5e7','wrong actual cell count/source')
        require(audit['reviewed_dependency_wheels']==(43 if host=='windows' else 48) and audit['reviewed_primary_release_bodies']==51 and audit['verified_runtime_roots']==3,'uncovered actual dependency payloads/primary bodies/runtime copies')
        require(len([f for f in audit['calibrations'] if f['actual_failure_frame_sha256']])==3,'missing actual source-fault failure frames')
        model=next(c for c in controls['cells'] if c['host']==host);require(len(model['controls'])==16 and all(c['rejected'] for c in model['controls']),'incomplete negative controls')
        subjects[path.relative_to(ROOT).as_posix()]=sha256(path);subjects['artifacts/'+RAW.name+'/'+model['model']]=sha256(RAW/model['model'])
        cells.append(dict(host=host,run=audit['provider_run'],source_revision=audit['helper_source_revision'],ordinary=240,calibrations=9,
            runner_sha256=audit['runner_sha256'],candidate_archive_sha256=audit['archive_sha256'],actual_readback=path.relative_to(RAW).as_posix(),
            actual_readback_sha256=sha256(path),actual_model=model['model'],actual_model_sha256=model['model_sha256'],source_runtime_removed=True))
    history=json.loads((package/'all-attempt-evidence.json').read_text());require(len(history['original_failed_report_frames'])==9 and history['initial_twenty_control_target_met'] is False,'original failure history omitted')
    for row in history['original_failed_report_frames']:require(hashlib.sha256(raw(row['frame'])).hexdigest()==row['frame_sha256'],'original failed screen changed/missing')
    journey=value('hatch/maintenance-0ef5b48894dc4483a5f1d9a29170a63c/journey.json')
    require(journey,'missing actual public maintenance journey')
    for path in package.rglob('*'):
        if path.is_file() and path.name!='admission.json':subjects[path.relative_to(ROOT).as_posix()]=sha256(path)
    size=sum(p.stat().st_size for p in root.rglob('*') if p.is_file());require(size<=64*1024**2,'Hatch retained project cap exceeded')
    immutable_json(package/'admission.json',dict(schema_version=1,admitted=True,project='hatch',repository='pypa/hatch',pin=primary['pin'],candidate='v0.4.0-rc.6',
        canonical_scenarios=20,normal=8,edge=12,ordinary=480,calibrations=18,real_source_faults=3,native_cells=cells,
        cell_model_negative_controls=32,local_target_absent=True,maintenance_suffix_relocation=True,initial_usability_target_met=False,
        generated_workflow=True,delivered_ci_observations=0,human_participants=0,human_usability='unmeasured',paid_admissions=0,
        retained_bytes=size,subjects=subjects,
        limitations=['Private engineering qualification of exact rc.6 archives; no stable/public or paid readiness claim.',
            'Prepared-agent initial sparse-init authoring failed the complete state oracle; cumulative28 recorder controls missed the original20-control target. A separate existing-table repair passed. Zero unfamiliar-human observations.',
            'The additional library route first omitted the required subcommand interaction flag; original failed console and helper bytes remain retained. The repaired route passed separately.',
            'Development includes one rejected exact config-byte expectation, then an explicitly declared blank-line correction and fresh complete passing window. No zero-flake or untouched-source claim.',
            'Template license/cache inputs are exact Apache-2.0/SPDX3.27.0 data; generated code and CI workflows were inspected as data, not executed. Environment creation, downloads, publishing and external plugins/templates remain excluded.',
            'Mandatory standalone native-v1 is required by final-native and local exact references; retained source/wheel/metadata readers reject missing or changed payloads. Full Python SDK/bootstrap are identified prerequisites, not a retained SDK or isolation.',
            'Generated workflow was linted but not dispatched; no delivered-CI observation credit. Original-ten and four prior current-candidate requalification and campaign-wide closure remain open.'],
        scope='One independently audited new project on exact private rc.6: two full native cells,480ordinary/18fresh calibrations,three real source faults,all actual code/runtime/primary metadata bytes,public authoring and maintenance,32semantic corruption challenges,complete failed-frame retention and checked source/runtime/evidence cleanup. Historical rc.5 and campaign-wide gates remain separate.'))
    print('Admitted Hatch on exact private rc.6:480 ordinary,18 calibrations,2 cells,3 real faults; original authoring miss retained. Campaign remains incomplete.')


if __name__=='__main__':main()
