"""Admit Rclone only after native development and checked retention gates."""
import json

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_rclone_verify_first_use import require
from readiness_verify_reencoded_native import verify_retained


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone';target=RAW/'rclone'
    frozen=load(docs.parent/'provisional-candidate-freeze.json');review=load(docs/'source-review.json')
    native=load(docs/'native-development-verification.json');original=load(docs/'original-source-faults.json')
    require(native['runner_source']==frozen['source_revision'] and native['candidate_version']==frozen['version']
            and native['real_faults']==3 and len(native['cells'])==2 and {c['host'] for c in native['cells']}=={'linux','windows'},
            'complete native development qualification missing')
    require(native['original_fault_verification_sha256']==sha256(docs/'original-source-faults.json')
            and original['run']==native['original_heldout']['run'] and original['host']=='linux'
            and [r['id'] for r in original['faults'] if r['original_heldout']]==['F03'],'original heldout identity differs')
    require(not (RAW/'active/rclone').exists(),'local active target remains')
    retained=target/'retained-source';index=load(retained/'verified-index.json');removed=load(retained/'removed.json')
    require(removed['removed'] and removed['owned_relative_path']=='active/rclone'
            and removed['source_archive_sha256']==review['archive_sha256']==sha256(retained/'source.tar.gz'),
            'local source archive/removal differs')
    require({name:row['sha256'] for name,row in index['files'].items()}==review['reviewed_inputs'],'local original source catalog differs')
    for name in index['selected_restore']:
        require(sha256(retained/'selected-restore'/name)==index['files'][name]['sha256'],'local source restore differs')
    failed_setup=load(retained/'failed-setup.json')
    require(not failed_setup['native_cli_built'] and not failed_setup['native_cli_executed'],
            'local setup failure cannot become local CLI qualification')
    inventories=[];encodings=[]
    for root in sorted(target.glob('retained-native-v*')):
        inventory=verify_retained(root);inventories.append(inventory)
        encoding=load(root/'reencoded.json')
        encodings.append(dict(generation=inventory['generation'],index_sha256=sha256(root/'index.json'),
            archive_sha256=encoding['replacement_archive_sha256'],logical_payloads=len(inventory['files']),
            archive_bytes=(root/'packets.tar.xz').stat().st_size,runs=inventory['runs']))
    require(inventories,'native evidence not retained')
    def covered(run,host,digest):
        prefix='native/'+run+'/playtestr-'+('Linux' if host=='linux' else 'Windows')+'/'
        return any(name.startswith(prefix) and row['sha256']==digest for inventory in inventories for name,row in inventory['files'].items())
    require(covered(original['run'],'linux',original['summary_sha256'])
            and covered(original['run'],'linux',original['source_cleanup_sha256']),'original source fault payload/cleanup not retained')
    for cell in native['cells']:
        require(cell['scenarios']==20,'native scenario boundary differs')
        for key in ['full_suite_sha256','maintenance_sha256','source_cleanup_sha256']:
            require(covered(cell['run'],cell['host'],cell[key]),'audited native payload not retained')
        replica_path=docs/('replica-source-faults-'+cell['host']+'-'+cell['run']+'.json')
        require(sha256(replica_path)==cell['fault_verification_sha256'],'replica verification changed')
        replica=load(replica_path)
        require(covered(cell['run'],cell['host'],replica['summary_sha256']), 'replica source-fault summary not retained')
        for fault in replica['faults']:
            require(covered(cell['run'],cell['host'],fault['receipt_sha256']),'replica compiled fault receipt not retained')
    author=load(docs/'native-authoring-review.json')
    for cell in author['cells']:
        require(covered(author['run'],cell['host'],cell['report_sha256'])
                and covered(author['run'],cell['host'],cell['cleanup_sha256']),'original reviewed twenty-case packet not retained')
    first_path=docs/'first-use-native-39289806481.json';first=load(first_path)
    require(first['fresh_route_shell_commands']==3 and first['fresh_route_controls']==16 and len(first['cells'])==2,
            'actual first-use route differs')
    require(first['initial_windows_first_use_window']==dict(shell_commands=7,requested_controls=56),
            'initial failed first-use window was erased')
    for cell in first['cells']:
        for key in ['journey_sha256','spec_sha256','cleanup_sha256']:
            require(covered(first['run'],cell['host'],cell[key]),'actual first-use payload not retained')
    core=RAW/'native/39103715410/run-metadata.json';metadata=load(core)
    require(metadata['headSha']==frozen['source_revision'] and metadata['conclusion']=='success'
            and metadata['status']=='completed' and len(metadata['jobs'])==3
            and all(j['conclusion']=='success' for j in metadata['jobs']),'native runner source unqualified')
    observed=sum(p.stat().st_size for p in target.rglob('*') if p.is_file())
    require(observed<=64*1024**2,'project retained evidence exceeds cap')
    path=docs.parent/'candidates.json';before=path.read_bytes();ledger=load(path)
    require(ledger['project_admissions']==ledger['development_admissions']==9,'unexpected prior admission count')
    row=next(r for r in ledger['rows'] if r['repository']=='rclone/rclone')
    require(row['status']=='active-source-reviewed-build-in-progress','unexpected reserved Rclone stage')
    record=dict(schema_version=1,project='rclone/rclone',pin=review['pin'],status='development-admitted',
        runner_source=frozen['source_revision'],candidate_version=frozen['version'],normal_scenarios=8,edge_scenarios=12,
        real_faults=3,cells=native['cells'],native_verification_sha256=sha256(docs/'native-development-verification.json'),
        original_fault_verification_sha256=sha256(docs/'original-source-faults.json'),
        reviewed_freeze_sha256=sha256(docs/'reviewed-contract-freeze.json'),first_use_sha256=sha256(first_path),
        local_removal_sha256=sha256(retained/'removed.json'),local_setup_only=True,core_metadata_sha256=sha256(core),
        retained_encodings=encodings,observed_project_retained_bytes=observed,archive_qualified=False,final_runner_admissions=0,
        human_usability='unmeasured',original_heldout=native['original_heldout'],
        limitations='Synthetic local/alias configuration only; no cloud, authentication, encryption, mounts, servers or general terminal compatibility. Windows active post-resize character checkpoints require explicit ArrowRight; immediate echo remains an unproven cause. Initial Windows first-use totals 7 commands/56 controls, missing cumulative engineering targets; corrected fresh route is 3/16. Local full target builds timed out and grant no local CLI credit. Generated workflow execution and final archive repetitions remain open.')
    immutable_json(docs/'development-admission.json',record)
    row.update(status='development-admitted',qualified_hosts=['linux-amd64','windows-amd64'],
        qualification='Twenty frozen useful configuration workflows, three real compiled source faults with exact binary restoration, and thirteen-command public maintenance verified on native Linux/Windows private provisional archives. Original Linux F03 only is heldout; first failures and explicit resize/first-use limitations retained. Final archive matrix remains open.')
    ledger['project_admissions']=ledger['development_admissions']=10
    data=(json.dumps(ledger,indent=2,ensure_ascii=True)+'\n').encode()
    path.write_bytes(data.replace(b'\n',b'\r\n') if b'\r\n' in before else data)
    print('Rclone development admitted: ten projects/twenty native cells; final archive credit remains zero.')


if __name__=='__main__':main()
