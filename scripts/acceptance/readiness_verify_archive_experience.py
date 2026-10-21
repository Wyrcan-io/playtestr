"""Independently check the actual private native archive calibration evidence."""
import argparse
import base64
import ctypes
from pathlib import Path

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--id',required=True);parser.add_argument('--series',choices=['provisional-v1','migration-v2'],default='provisional-v1')
    parser.add_argument('--packet',type=Path);parser.add_argument('--check-only',action='store_true')
    parser.add_argument('--canonical-archive',type=Path);args=parser.parse_args()
    require(len(args.id)==32 and all(c in '0123456789abcdef' for c in args.id),'invalid calibration id')
    base=args.packet.resolve(strict=True) if args.packet else RAW
    base.relative_to(RAW.resolve(strict=True))
    root=base/'archive-experience'/args.id
    def key(path):return 'artifacts/runner-readiness-ten-project-pass/'+path.relative_to(base).as_posix()
    receipt=load(root/'experience.json');package=root/'relocated caf\u00e9 \u96ea'
    require(receipt.get('series','provisional-v1')==args.series,'archive experience candidate series differs')
    freeze_name='provisional-candidate-freeze.json' if args.series=='provisional-v1' else 'migration-candidate-freeze.json'
    freeze=load(ROOT/'docs/validation/runner-readiness-ten-project-pass'/freeze_name)
    host=receipt.get('host','windows');suffix='.exe' if host=='windows' else ''
    require(host in {'windows','linux','darwin'},'undeclared native archive host')
    cell=next(c for c in freeze['cells'] if c['host']==host)
    require(receipt['current_archive_sha256']==cell['archive_sha256']
            and receipt['installed_binary_sha256']['current']==cell['binary_sha256'],'different actual candidate')
    canonical=ROOT/cell['archive_local_only'];corrupt=root/'corrupt.zip'
    if args.canonical_archive:
        canonical=args.canonical_archive.resolve(strict=True)
        canonical.relative_to(RAW.resolve(strict=True))
    require(canonical.stat().st_size==cell['archive_bytes'] and sha256(canonical)==cell['archive_sha256']
            and corrupt.is_file() and corrupt.stat().st_size==cell['archive_bytes'],
            'canonical or corrupt checksum-control archive missing or changed')
    original_bytes=canonical.read_bytes();corrupt_bytes=corrupt.read_bytes()
    require(corrupt_bytes[0]==original_bytes[0]^1 and corrupt_bytes[1:]==original_bytes[1:],
            'checksum-control payload is not the declared single-bit corruption')
    require(sha256(root/'build/main.go')==receipt['fixture_source_sha256']
            ==sha256(ROOT/'scripts/acceptance/readiness_archive_fixture.go.txt'),
            'preserved fixture source differs')
    previous=next(c for c in load(ROOT/'release/e5-candidate-manifest.json')
                  if c['host']['runner_os']=={'windows':'Windows','linux':'Linux','darwin':'macOS'}[host])
    if receipt.get('previous_series','e5-rc2')=='provisional-v1':
        previous_freeze=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/provisional-candidate-freeze.json')
        previous_cell=next(c for c in previous_freeze['cells'] if c['host']==host and c['architecture']==cell['architecture'])
        previous=dict(archive_sha256=previous_cell['archive_sha256'],executable_sha256=previous_cell['binary_sha256'],version=previous_freeze['version'])
    else:require(receipt.get('previous_series','e5-rc2')=='e5-rc2','unknown previous archive generation')
    require(receipt['old_archive_sha256']==previous['archive_sha256'],'different rollback archive')
    installed={name:root/(folder+' caf\u00e9 \u96ea')/('playtestr'+suffix)
               for name,folder in [('previous','old'),('current','upgrade'),('rollback','rollback')]}
    expected_binaries={name:(cell['binary_sha256'] if name=='current' else previous['executable_sha256'])
                       for name in installed}
    for name,binary in installed.items():
        require(sha256(binary)==receipt['installed_binary_sha256'][name]==expected_binaries[name]
                and len(list(binary.parent.iterdir()))==4,'actual source-free installed package differs')
    expected_labels={name+'-'+action for name in installed for action in ['version','help']}
    expected_labels|={'fixture-build-'+mode for mode in ['good','screen','file']}
    expected_labels|={'record','current-clean','screen-changed','screen-restored','file-changed','file-restored',
                      'previous-v2','upgraded-v2','rollback-v2','current-reads-previous-report'}
    require(set(receipt['attempts'])==expected_labels,'missing or unexpected archive journey commands')
    manifests={}
    for label,identity in receipt['attempts'].items():
        require(len(identity)==32 and all(c in '0123456789abcdef' for c in identity),'unsafe command identity')
        event={kind:load(base/'events'/(identity+'-'+kind+'.json'))
               for kind in ['started','identified','launched','finished']}
        require(all(row['id']==identity and row['event']==kind and row['project']=='core'
                    and row['label']=='archive-experience-'+label for kind,row in event.items()),
                'actual command event identity differs')
        finished=event['finished']
        expected_exit=1 if label in {'screen-changed','file-changed'} else 0
        require(event['started']['expected_exit']==expected_exit and finished['exit_code']==expected_exit
                and finished['category']=='passed' and finished['harness_cleanup']=='harness_process_reaped'
                and not finished['cleanup_errors'],'calibration child outcome/cleanup differs')
        require(sha256(base/'core'/identity/'console.log')==finished['console_sha256'],'changed command output')
        reference=event['identified']['identity'];manifest=packet_file(base,reference['manifest'].replace('\\','/'),2*1024**2)
        require(sha256(manifest)==reference['sha256'],'changed prelaunch identity')
        manifests[label]=load(manifest)['files']
        if label.startswith('fixture-build-'):
            compiler='artifacts/runner-readiness-ten-project-pass/toolchain/go/bin/go'+suffix
            fixture_source=key(root/'build/main.go')
            require(manifests[label][compiler]==receipt['compiler_sha256']
                    and manifests[label][fixture_source]==receipt['fixture_source_sha256']
                    ==sha256(ROOT/'scripts/acceptance/readiness_archive_fixture.go.txt'),
                    'actual fixture compiler or reviewed source differs')
        else:
            selected='previous' if label.startswith('previous-') else 'rollback' if label.startswith('rollback-') else 'current'
            binary_key=key(installed[selected])
            require(manifests[label][binary_key]==expected_binaries[selected],'actual executed archive binary differs')
            if label.endswith('-version'):
                version=freeze['version'] if selected=='current' else previous['version']
                require((base/'core'/identity/'console.log').read_text(encoding='utf-8-sig').strip()=='playtestr '+version,
                        'actual archive version output differs')
    contract=load(package/'spec.json')
    require(sha256(package/'spec.json')==receipt['spec_sha256']
            and sha256(package/'snapshots/saved.txt')==receipt['baseline_sha256'],'approved contract changed')
    files={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in contract['steps']
           if s.get('state',{}).get('kind')=='file'}
    require(files=={'saved.txt':b'reviewed\n','seed.bin':b'preserve\x00\r\n'},'independent saved-byte oracle differs')
    target=key(package/('target'+suffix))
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
    source_free=receipt['source_free_path'].replace('\\','/')
    require(source_free==key(root/'empty-path'),'source-free PATH identity differs')
    if (root/'empty-path').exists():
        require(not any((root/'empty-path').iterdir()),'source-free PATH is no longer empty')
    else:
        require(args.packet is not None and receipt.get('artifact_empty_directories')==['empty-path']
                and receipt.get('source_free_directory_entries')==[],
                'missing source-free directory lacks an explicit empty-directory transfer declaration')
    require((package/'previous-report.html').is_file(),'previous report HTML was not generated')
    if not args.check_only:
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
