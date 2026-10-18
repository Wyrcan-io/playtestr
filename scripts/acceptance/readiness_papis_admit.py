"""Admit Papis development evidence only after native and retained-byte checks."""
import json
import shutil

from readiness_compact_native import verify
from readiness_evidence import RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import packet_observations,read_json as load
from readiness_papis_verify_first_use import PIN,ARCHIVE,require
from readiness_papis_verify_native import SOURCE


def main():
    project=RAW/'papis';docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/papis'
    core=RAW/'native/39067447993/run-metadata.json';metadata=load(core)
    require(metadata['headSha']==SOURCE and metadata['status']=='completed' and metadata['conclusion']=='success','unqualified core source')
    require(len(metadata['jobs'])==3 and all(j['conclusion']=='success' for j in metadata['jobs']),'incomplete native core')
    controls=packet_observations('39067447993')
    for host in ['linux','macos']:
        require(sum(row['host']==host and
            ('github.com/Wyrcan-io/playtestr/internal/runner','TestPrimaryReplyRealPTYStartupAndExactExit') in row['whole']
            for row in controls)>=2,'ordinary/race real PTY controls missing')
    require(not (RAW/'active/papis').exists(),'local active target remains')
    retained=project/'retained-source';removed=load(retained/'removed.json');source_index=load(retained/'verified-index.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/papis' and removed['source_archive_sha256']==ARCHIVE==sha256(retained/'source.tar.gz'),'local removal/source identity differs')
    for name in source_index['selected_restore']:
        require(sha256(retained/'selected-restore'/name)==source_index['files'][name]['sha256'],'local selected restore differs')
    native_path=project/'native-fresh-development-verification.json';native=load(native_path)
    require(native['runner_source']==SOURCE and native['real_faults']==4 and len(native['cells'])==2,'native coverage differs')
    require(native['original_current_source_heldout']==dict(run='39099744836',host='Linux',fault='F04'),'wrong original holdout')
    archives=[];all_files={}
    for generation in [1,2]:
        directory=project/('retained-native-v'+str(generation));index=load(directory/'index.json',4*1024**2);verified=load(directory/'verified.json');expanded=load(directory/'expanded-removed.json')
        require(sha256(directory/'index.json')==verified['index_sha256'] and sha256(directory/'packets.tar.gz')==index['archive_sha256']==verified['archive_sha256'],'native retained identity differs')
        require(len(index['files'])<=40000 and index['expanded_bytes']<=128*1024**2,'archive coverage exceeds bounds')
        verify(directory/'packets.tar.gz',index['files'])
        require(expanded['all_expanded_removed'] and expanded['archive_sha256']==index['archive_sha256'] and set(expanded['removed_runs'])==set(index['runs']),'expanded removal incomplete')
        require(all(not (RAW/'native'/run).exists() for run in index['runs']),'expanded packet remains')
        require(not (all_files.keys() & index['files'].keys()),'native archive runs overlap')
        all_files.update(index['files'])
        archives.append(dict(generation=generation,archive_sha256=index['archive_sha256'],index_sha256=sha256(directory/'index.json'),logical_files=verified['members_verified'],selected_restores=verified['selected_restore_verified']))
    for cell in native['cells']:
        require(cell['run']=='39099744836' and cell['scenarios']==20,'wrong qualification run/scenarios')
        prefix='native/'+cell['run']+'/'+cell['host']+'/'
        for key in ['report_sha256','source_fault_summary_sha256','maintenance_sha256','cleanup_receipt_sha256']:
            require(any(name.startswith(prefix) and record['sha256']==cell[key] for name,record in all_files.items()),'verified native payload absent from retained archive')
    original=docs/'original-current-source-faults/summary.json';faults=load(original)['faults']
    require({r['id'] for r in faults}=={'F01','F02','F03','F04'} and [r['id'] for r in faults if r['held_out']]==['F04'] and all(r['restored_exact'] for r in faults),'original current-source faults incomplete')
    selection=load(original.parent/'selected-faults.json')
    require(selection['selection_revision']==2 and selection['frozen_contract_sha256']==sha256(docs/'reviewed-contract-freeze.json'),'original holdout belongs to another freeze')
    require(any(name.startswith('native/39099744836/playtestr-Linux/papis/faults/') and record['sha256']==sha256(original) for name,record in all_files.items()),'original current-source summary absent from native archive')
    historical=load(docs/'local-original-verification.json');require(historical['current_source_fault_credit']==0,'dev runner evidence acquired qualification credit')
    first=load(docs/'first-use-native-39072664569.json');require(first['source_revision']==SOURCE and len(first['cells'])==2,'native first use unqualified')
    observed=sum(p.stat().st_size for p in project.rglob('*') if p.is_file());require(observed<64*1024**2,'retained evidence cap exceeded')
    candidate_path=docs.parent/'candidates.json';before=candidate_path.read_bytes();candidates=load(candidate_path)
    require(candidates['project_admissions']==candidates['development_admissions']==6,'unexpected admission counter')
    row=next(r for r in candidates['rows'] if r['repository']=='papis/papis')
    row.update(status='development-admitted',qualified_hosts=['linux-amd64','windows-amd64'],qualification='Twenty frozen scenarios, four actual interpreted-source faults with exact restorations, twelve-command maintenance and checked cleanup on both native hosts at '+SOURCE[:7]+', run 39099744836. Only initial Linux F04 is current-source heldout. Local dev evidence excluded; final archives pending.')
    candidates['project_admissions']=candidates['development_admissions']=7
    record=dict(schema_version=1,project='papis/papis',pin=PIN,status='development-admitted',normal_scenarios=8,edge_scenarios=12,real_faults=4,cells=native['cells'],runner_source=SOURCE,
        core_run='39067447993',core_metadata_sha256=sha256(core),native_verification_sha256=sha256(native_path),
        first_use_sha256=sha256(docs/'first-use-native-39072664569.json'),reviewed_freeze_sha256=sha256(docs/'reviewed-contract-freeze.json'),
        original_fault_summary_sha256=sha256(original),local_source_removal_receipt_sha256=sha256(retained/'removed.json'),native_packet_archives=archives,
        observed_project_retained_bytes=observed,archive_qualified=False,final_runner_admissions=0,human_usability='unmeasured',
        holdout='F04 initial Linux execution in 39099744836, after committed freeze a9a6a25 and declaration d3edbe9. Windows and subsequent repetitions are replicas. Earlier local dev F03 remains historical with zero current-source credit.',
        limitations='Trusted local offline library/picker/export workflows only. Agent familiarity and warm prerequisites; human usability unmeasured. Local dev-runner explorations excluded. First Windows cleanup refusal and empty-directory transfer failure preserved; successful native qualification is fresh. Final archive and actual generated CI gates remain open.')
    shutil.copyfile(native_path,docs/native_path.name)
    immutable_json(docs/'development-admission.json',record)
    data=(json.dumps(candidates,indent=2,ensure_ascii=True)+'\n').encode()
    if b'\r\n' in before:data=data.replace(b'\n',b'\r\n')
    candidate_path.write_bytes(data)
    print('Papis development admitted: seven projects/fourteen native cells; final archive credit zero.')


if __name__=='__main__':main()
