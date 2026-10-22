"""Reconcile all original migrations with actual frozen-archive report payloads."""
import hashlib
import json
import tarfile

from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load

DOC=ROOT/'docs/validation/runner-readiness-ten-project-pass'
PROJECTS=['cookiecutter','copier','lf','superfile','helix','glow','broot','yazi','ranger','nnn']


def report(value,version,host,total,failed=False,legacy=False):
    require(value['runner_version']==version and value['os']==('darwin' if host=='macos' else host)
        and value['arch']==('arm64' if host=='macos' else 'amd64'),'old migration actual binary platform/version differs')
    require(value['summary']==dict(total=total,passed=0 if failed else total,failed=total if failed else 0,cancelled=0,not_run=0)
        and len(value['results'])==total,'old migration actual outcome denominator differs')
    ids=set()
    for row in value['results']:
        require(row['workspace']['cleaned'] and row['cleanup']['confirmed_exited'],
            'old migration invocation/cleanup differs')
        if legacy:
            require(value['report_version']==2 and not any('state' in s for s in row['steps']),
                'legacy terminal-only calibration contains saved-state claim')
        else:
            require(value['report_version']==3 and row['invocation_id'] not in ids,'old migration missing/reused invocation')
            ids.add(row['invocation_id'])
        require(row['status']==('failed' if failed else 'passed'),'old migration row outcome differs')
        if failed:require(row['failure']['category']=='state_assertion_failure','old migration public wrong-file diagnosis differs')
        else:require(all(s['status']=='passed' for s in row['steps']),'old migration missing positive step')
        for step in row['steps']:
            if 'state' in step:require(step['state']['invocation_id']==row['invocation_id']
                and step['state']['workspace_id']==row['workspace']['id'],'old migration cross-execution state')


def main():
    frozen=load(DOC/'migration-candidate-freeze.json');old_status=load(DOC/'old-migration-status.json')
    final_status=load(DOC/'final-old-migration-status.json')
    require({r['project'] for r in old_status['projects']}==set(PROJECTS)
        and {r['project'] for r in final_status['projects']}==set(PROJECTS[:6]),'missing/duplicate old migration project')
    output=[];primary=calibration=canonical=cells=0
    for project in PROJECTS:
        docs=DOC/'old-migration'/project;original=load(docs/'migration-admission.json')
        require(next(r for r in old_status['projects'] if r['project']==project)['receipt_sha256']==sha256(docs/'migration-admission.json'),
            'original migration receipt changed')
        if project in PROJECTS[:6]:
            final=load(docs/'final-archive-verification.json')
            require(next(r for r in final_status['projects'] if r['project']==project)['receipt_sha256']==sha256(docs/'final-archive-verification.json'),
                'fresh migration receipt changed')
            audited=[load(docs/('final-verified-'+h+'.json')) for h in final['audits']]
            require(all(sha256(docs/('final-verified-'+h+'.json'))==digest for h,digest in final['audits'].items()),'fresh cell audit changed')
            archives=final['retained_archives'];receipt=docs/'final-archive-verification.json'
        else:
            audited=original['cells'];archives=original['retained_archives'];receipt=docs/'migration-admission.json'
            require(all(load(docs/('verified-'+c['host']+'.json'))==c for c in audited),'original exact-archive cell audit changed')
        require(len(audited)==(3 if project=='yazi' else 2) and len({c['host'] for c in audited})==len(audited),'old migration native cells missing')
        inventory=[];retention=[]
        for declaration in archives:
            folder=RAW/('old-'+project)/('retained-native-v'+str(declaration['generation']))
            index=load(folder/'index.json',maximum=4*1024**2);checked=load(folder/'verified.json');removed=load(folder/'expanded-removed.json')
            require(sha256(folder/'index.json')==declaration['index_sha256']==checked['index_sha256']==removed['index_sha256']
                and sha256(folder/'packets.tar.gz')==declaration['archive_sha256']==index['archive_sha256']==checked['archive_sha256']==removed['archive_sha256']
                and removed['all_expanded_removed'] and removed['removed_runs']==index['runs'],
                'old migration retained payload/index/removal changed')
            verify(folder/'packets.tar.gz',index['files'])
            for selected in index['selected_restore']:require(sha256(folder/'selected-restore'/selected)==index['files'][selected]['sha256'],'old selected restore differs')
            inventory.append((folder,index));retention.append(dict(generation=declaration['generation'],index_sha256=sha256(folder/'index.json')))
        def payload(digest):
            for folder,index in reversed(inventory):
                match=next(((n,r) for n,r in index['files'].items() if r['sha256']==digest),None)
                if not match:continue
                name,row=match
                require(row['bytes']<=4*1024**2,'old selected payload size bound')
                with tarfile.open(folder/'packets.tar.gz','r:gz') as archive:data=archive.extractfile(row.get('member',name)).read(4*1024**2+1)
                require(hashlib.sha256(data).hexdigest()==digest,'actual old payload changed')
                return json.loads(data.decode('utf-8-sig'))
            # Yazi's original Windows cell ran natively on this workstation.
            if project=='yazi':
                removed=RAW/'old-yazi/retained-source/removed.json'
                if removed.is_file() and sha256(removed)==digest:return load(removed)
                for path in (RAW/'old-migration/yazi/windows').rglob('*.json'):
                    if path.stat().st_size<=4*1024**2 and sha256(path)==digest:return load(path)
            raise RuntimeError('actual old migration payload not retained: '+project+' '+digest)
        host_rows=[]
        for cell in audited:
            candidate=next(c for c in frozen['cells'] if c['host']==('darwin' if cell['host']=='macos' else cell['host']))
            require(cell['runner_sha256']==candidate['binary_sha256'] and cell['provisional_archive_sha256']==candidate['archive_sha256'],
                'stale old migration binary')
            suite=payload(cell['full_suite_sha256']);report(suite,frozen['version'],cell['host'],cell['scenarios'])
            corruption=payload(cell['corruption_sha256']);removed=payload(cell['cleanup_sha256'])
            require(corruption['restored_exact'] and corruption['approved_inputs_unchanged']
                and corruption['runner_sha256']==candidate['binary_sha256']
                and corruption['provisional_archive_sha256']==candidate['archive_sha256']
                and corruption['original_source_sha256']!=corruption['mutated_source_sha256']
                and removed['removed'] and removed['owned_relative_path']=='active/old-'+project,
                'old actual mutation/restoration/source removal differs')
            require(set(corruption['calls'])=={'legacy-terminal-false-green','public-state-corruption-rejected','public-state-corruption-restored'},
                'old actual three-way oracle calibration missing')
            for name,call in corruption['calls'].items():
                report(payload(call['report_sha256']),frozen['version'],cell['host'],1,
                    failed=name=='public-state-corruption-rejected',legacy=name=='legacy-terminal-false-green')
            host_rows.append(dict(host=cell['host'],run=cell['run'],scenarios=cell['scenarios'],
                full_suite_sha256=cell['full_suite_sha256'],corruption_sha256=cell['corruption_sha256'],cleanup_sha256=cell['cleanup_sha256']))
        require(not (RAW/'active'/('old-'+project)).exists(),'old target still active')
        primary+=sum(c['scenarios'] for c in audited);calibration+=len(audited)*3;cells+=len(audited);canonical+=original['canonical_scenarios']
        output.append(dict(project=project,receipt_sha256=sha256(receipt),original_migration_sha256=sha256(docs/'migration-admission.json'),cells=host_rows,retention=retention))
        print('Audited original exact-archive migration:',project,flush=True)
    require((canonical,primary,calibration,cells)==(130,274,63,21),'all-old final denominator differs')
    immutable_json(DOC/'closing-old-archive-audit.json',dict(projects=output,projects_verified=10,canonical_scenarios=canonical,
        primary_executions=primary,calibration_executions=calibration,native_cells=cells,
        original_status_sha256=sha256(DOC/'old-migration-status.json'),six_fresh_rechecks_sha256=sha256(DOC/'final-old-migration-status.json'),
        new_project_credit=0,scope='All ten original migrations reconciled to exact rc.5 actual full-suite and three-way public wrong-file calibration reports, restoration, native cells, original receipts and complete self-contained retention/removal. Fresh six replace prior rc.4 qualification; they do not duplicate canonical cases or old project credit. Broot is Linux/macOS; Yazi also includes actual local Windows.'))
    print('Verified all ten final-archive old migrations:',primary,'primary,',calibration,'calibration,',cells,'cells.')


if __name__=='__main__':main()
