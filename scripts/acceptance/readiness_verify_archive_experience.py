"""Independently check the actual private native archive calibration evidence."""
import argparse
import base64
import ctypes

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--id',required=True);parser.add_argument('--series',choices=['provisional-v1','migration-v2'],default='provisional-v1');args=parser.parse_args()
    require(len(args.id)==32 and all(c in '0123456789abcdef' for c in args.id),'invalid calibration id')
    root=RAW/'archive-experience'/args.id
    receipt=load(root/'experience.json');package=root/'relocated caf\u00e9 \u96ea'
    require(receipt.get('series','provisional-v1')==args.series,'archive experience candidate series differs')
    freeze_name='provisional-candidate-freeze.json' if args.series=='provisional-v1' else 'migration-candidate-freeze.json'
    freeze=load(ROOT/'docs/validation/runner-readiness-ten-project-pass'/freeze_name)
    host=receipt.get('host','windows');suffix='.exe' if host=='windows' else ''
    require(host in {'windows','linux','darwin'},'undeclared native archive host')
    cell=next(c for c in freeze['cells'] if c['host']==host)
    require(receipt['current_archive_sha256']==cell['archive_sha256']
            and receipt['installed_binary_sha256']['current']==cell['binary_sha256'],'different actual candidate')
    manifests={}
    for label,identity in receipt['attempts'].items():
        event={kind:load(RAW/'events'/(identity+'-'+kind+'.json'))
               for kind in ['started','identified','launched','finished']}
        require(all(row['id']==identity and row['event']==kind and row['project']=='core'
                    and row['label']=='archive-experience-'+label for kind,row in event.items()),
                'actual command event identity differs')
        finished=event['finished']
        require(finished['category']=='passed' and finished['harness_cleanup']=='harness_process_reaped'
                and not finished['cleanup_errors'],'calibration child outcome/cleanup differs')
        require(sha256(RAW/'core'/identity/'console.log')==finished['console_sha256'],'changed command output')
        reference=event['identified']['identity'];manifest=RAW/reference['manifest']
        require(sha256(manifest)==reference['sha256'],'changed prelaunch identity')
        manifests[label]=load(manifest)['files']
    contract=load(package/'spec.json')
    require(sha256(package/'spec.json')==receipt['spec_sha256']
            and sha256(package/'snapshots/saved.txt')==receipt['baseline_sha256'],'approved contract changed')
    files={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in contract['steps']
           if s.get('state',{}).get('kind')=='file'}
    require(files=={'saved.txt':b'reviewed\n','seed.bin':b'preserve\x00\r\n'},'independent saved-byte oracle differs')
    target=(package/('target'+suffix)).relative_to(ROOT).as_posix()
    cells=[]
    for label,digest in receipt['reports'].items():
        path=package/(label+'.json');report=load(path)
        require(sha256(path)==digest,'report bytes changed')
        result=report['results'][0];failed=label in {'screen-changed','file-changed'}
        require(report['summary']==dict(total=1,passed=int(not failed),failed=int(failed),cancelled=0,not_run=0)
                and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'wrong outcome or cleanup')
        mode='screen' if label=='screen-changed' else 'file' if label=='file-changed' else 'good'
        require(manifests[label][target]==sha256(root/'build'/(mode+suffix)),'actual launched fixture identity differs')
        if failed:
            require(result['failure']['category']==('assertion_timeout' if mode=='screen' else 'state_assertion_failure'),
                    'failure did not detect intended behavior')
        for step in result['steps']:
            if 'state' in step:
                require(step['state']['invocation_id']==result['invocation_id']
                        and step['state']['workspace_id']==result['workspace']['id'],'cross-execution state proof')
        cells.append(dict(label=label,report_sha256=digest,fixture_binary_sha256=sha256(root/'build'/(mode+suffix)),
            runner_version=report['runner_version'],status=result['status']))
    require(not (root/'rejected').exists() and receipt['corrupt_archive_rejected_before_extraction'],'corrupt archive extracted')
    require(not any((ROOT/receipt['source_free_path']).iterdir()),'source-free PATH is no longer empty')
    require((package/'previous-report.html').is_file(),'previous report HTML was not generated')
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/archive-experience'/(host+('-provisional.json' if args.series=='provisional-v1' else '-migration-v2.json')),
        dict(experience=args.id,receipt_sha256=sha256(root/'experience.json'),cells=cells,
        current_archive_sha256=cell['archive_sha256'],current_binary_sha256=cell['binary_sha256'],
        old_archive_sha256=receipt['old_archive_sha256'],actual_commands=len(receipt['attempts']),
        privileged_role_enabled_at_execution=receipt.get('privileged_role_enabled','unmeasured in historical receipt'),
        source_free_execution='Empty PATH and standalone archive package; fixture compiler preparation was separate.',
        historical_failure='dba0c6e85c8d4f17a5f149617d71f07f: helper created its shared owned temp directory twice, corrected before fixture build.',
        scope='Private native archive calibration: Unicode relocation, checksums, screen/file failure and recovery, v2 upgrade/rollback and older report rendering.',
        limits='No enforced offline-network proof, real-project fault credit or final-archive qualification. Native coverage is confined to this receipt host.',
        final_archive_credit=0))
    print('Independently verified',len(cells),'archive-driven ordinary outcomes and all actual command identities.')


if __name__=='__main__':main()
