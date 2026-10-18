"""Admit Frogmouth development evidence only after native and retained-byte checks."""
import json
import shutil

from readiness_compact_native import verify
from readiness_evidence import RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import packet_observations,read_json as load
from readiness_frogmouth_verify_first_use import PIN,ARCHIVE,require
from readiness_frogmouth_verify_native import SOURCE


def main():
    project=RAW/'frogmouth';docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/frogmouth'
    core=RAW/'native/39103715410/run-metadata.json';metadata=load(core)
    require(metadata['headSha']==SOURCE and metadata['status']=='completed' and metadata['conclusion']=='success','unqualified core source')
    require(len(metadata['jobs'])==3 and all(j['conclusion']=='success' for j in metadata['jobs']),'incomplete native core')
    controls=packet_observations('39103715410')
    for host in ['linux','macos']:
        require(sum(row['host']==host and
            ('github.com/Wyrcan-io/playtestr/internal/runner','TestPrimaryReplyRealPTYStartupAndExactExit') in row['whole']
            for row in controls)>=2,'ordinary/race real PTY controls missing')
    require(not (RAW/'active/frogmouth').exists(),'local active target remains')
    retained=project/'retained-source';removed=load(retained/'removed.json');source_index=load(retained/'verified-index.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/frogmouth' and removed['source_archive_sha256']==ARCHIVE==sha256(retained/'source.tar.gz'),'local removal/source identity differs')
    for name in source_index['selected_restore']:
        require(sha256(retained/'selected-restore'/name)==source_index['files'][name]['sha256'],'local selected restore differs')
    native_path=project/'native-development-verification.json';native=load(native_path);series=load(docs/'current-qualification-series.json');current=load(docs/'current-source-requalification.json')
    require(native['runner_source']==SOURCE and native['real_faults']==3 and len(native['cells'])==2 and native['evidence_repair_required'] is False,'native coverage differs or R3-11 evidence remains missing')
    require(native['original_current_source_heldout']==dict(run=series['native_run'],host='Linux',fault='F04'),'wrong original holdout')
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
        require(cell['run']==current['native_run'] and cell['scenarios']==20,'wrong qualification run/scenarios')
        prefix='native/'+cell['run']+'/'+cell['host']+'/'
        for key in ['report_sha256','source_fault_summary_sha256','maintenance_sha256','cleanup_receipt_sha256']:
            require(any(name.startswith(prefix) and record['sha256']==cell[key] for name,record in all_files.items()),'verified native payload absent from retained archive')
    original=docs/'original-source-faults/summary.json';faults=load(original)['faults']
    require({r['id'] for r in faults}=={'F01','F02','F04'} and [r['id'] for r in faults if r['held_out']]==['F04'] and all(r['restored_exact'] for r in faults),'original current-source faults incomplete')
    selection=load(original.parent/'selected-faults.json')
    require(selection['selection_revision']==2 and selection['frozen_contract_sha256']==sha256(docs/'reviewed-contract-freeze.json'),'original holdout belongs to another freeze')
    require(any(name.startswith('native/'+series['native_run']+'/playtestr-Linux/frogmouth/faults/') and record['sha256']==sha256(original) for name,record in all_files.items()),'original current-source summary absent from native archive')
    first_path=docs/('first-use-native-'+current['native_run']+'.json');first=load(first_path);require(first['source_revision']==SOURCE and len(first['cells'])==2,'native first use unqualified')
    observed=sum(p.stat().st_size for p in project.rglob('*') if p.is_file());require(observed<64*1024**2,'retained evidence cap exceeded')
    candidate_path=docs.parent/'candidates.json';before=candidate_path.read_bytes();candidates=load(candidate_path)
    require(candidates['project_admissions']==candidates['development_admissions']==7,'unexpected admission counter')
    row=next(r for r in candidates['rows'] if r['repository']=='Textualize/frogmouth')
    row.update(status='development-admitted',qualified_hosts=['linux-amd64','windows-amd64'],qualification='Twenty meaningful frozen browsing scenarios, three genuine source fault replicas/restorations, useful final failure frames, twelve-command maintenance and checked cleanup on both native hosts at '+SOURCE[:7]+', run '+current['native_run']+'. Only original Linux F04 at qualified prior source f46f240/run '+series['native_run']+' is heldout. Earlier weak breadth and invalid injection remain historical; final archives pending.')
    candidates['project_admissions']=candidates['development_admissions']=8
    record=dict(schema_version=1,project='Textualize/frogmouth',pin=PIN,status='development-admitted',normal_scenarios=8,edge_scenarios=12,real_faults=3,cells=native['cells'],runner_source=SOURCE,
        core_run='39103715410',core_metadata_sha256=sha256(core),native_verification_sha256=sha256(native_path),
        first_use_sha256=sha256(first_path),reviewed_freeze_sha256=sha256(docs/'reviewed-contract-freeze.json'),
        original_fault_summary_sha256=sha256(original),local_source_removal_receipt_sha256=sha256(retained/'removed.json'),native_packet_archives=archives,
        observed_project_retained_bytes=observed,archive_qualified=False,final_runner_admissions=0,human_usability='unmeasured',
        holdout='Only initial Linux F04 in '+series['native_run']+' is original, declared after meaningful twenty-case freeze b393fc1. Windows/later runs are replicas. Prior F03 was selected but never reached and has zero revised-freeze heldout credit.',
        limitations='Trusted offline local Markdown browsing only. Managed-home bookmark/history UI exercised, without a public structured-home-state claim. Earlier help/About-only breadth, focus failures and ineffective process-exit injection are preserved and excluded. Agent familiarity and warm prerequisites; human usability unmeasured. Final archives and actual generated CI remain open.')
    shutil.copyfile(native_path,docs/native_path.name)
    immutable_json(docs/'development-admission.json',record)
    data=(json.dumps(candidates,indent=2,ensure_ascii=True)+'\n').encode()
    if b'\r\n' in before:data=data.replace(b'\n',b'\r\n')
    candidate_path.write_bytes(data)
    print('Frogmouth development admitted: eight projects/sixteen native cells; final archive credit zero.')


if __name__=='__main__':main()
