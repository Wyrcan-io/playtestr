"""Require actual source-matched native tests before the migration repair package."""
import argparse
import hashlib
import json
import subprocess

from readiness_candidate_package import MIGRATION_SOURCE
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
    run=args.run
    if not run.isascii() or not run.isdecimal():raise RuntimeError('invalid native run')
    root=RAW/'native'/run
    metadata=load(root/'run-metadata.json')
    jobs=metadata['jobs']
    expected_jobs={'native-core (ubuntu-24.04)','native-core (macos-15)','native-core (windows-2025)'}
    if (metadata['status']!='completed'
            or metadata['conclusion']!='success' or len(jobs)!=3 or {j['name'] for j in jobs}!=expected_jobs
            or any(j['status']!='completed' or j['conclusion']!='success' for j in jobs)):
        raise RuntimeError('successful source-matched native core jobs required')
    tracked=subprocess.check_output(['git','ls-tree','-r','--name-only',MIGRATION_SOURCE],cwd=ROOT,text=True,timeout=15).splitlines()
    inputs={}
    for name in tracked:
        if name.endswith('.go') and name.startswith(('internal/','cmd/')):
            data=subprocess.check_output(['git','show',MIGRATION_SOURCE+':'+name],cwd=ROOT,timeout=15).replace(b'\r\n',b'\n')
            inputs[name]={hashlib.sha256(data).hexdigest(),hashlib.sha256(data.replace(b'\n',b'\r\n')).hexdigest()}
    required={'native-core-tests','native-vet','native-race','native-evidence-controls','native-ci-summary-controls','native-public-state-parent'}
    controls={'TestStateContractLargeManagedCheckpoint','TestStateLargeSameExecutionCheckpoint','TestStateContractRejectsBeforeLaunch'}
    cells=[]
    for os_name,host in [('ubuntu-24.04','linux'),('macos-15','macos'),('windows-2025','windows')]:
        packet=root/('runner-readiness-core-'+os_name)
        campaign=object.__new__(Campaign);campaign.raw=packet
        attempts=campaign.attempts();selected={}
        for attempt,row in attempts.items():
            label=row['started']['label']
            if label not in required:continue
            if label in selected:raise RuntimeError('duplicate native engineering check')
            finished=row['finished']
            if ('launched' not in row or row['started']['expected_exit']!=0 or finished['category']!='passed'
                    or finished['exit_code']!=0 or finished['cleanup_errors'] or finished['harness_cleanup']!='harness_process_reaped'):
                raise RuntimeError('native check failed or cleanup incomplete')
            reference=row['identified']['identity'];manifest=packet_file(packet,reference['manifest'],1024**2)
            if sha256(manifest)!=reference['sha256']:raise RuntimeError('native manifest changed')
            files=load(manifest)['files']
            console=packet_file(packet,'core/'+attempt+'/console.log',4*1024**2)
            if sha256(console)!=finished['console_sha256']:raise RuntimeError('native console changed')
            if label in {'native-core-tests','native-vet','native-race'}:
                if any(files.get(name) not in hashes for name,hashes in inputs.items()):
                    raise RuntimeError('actual native Go command has different source inputs')
            if label in {'native-core-tests','native-race'}:
                passed=set()
                for line in console.read_text(encoding='utf-8-sig').splitlines():
                    try:event=json.loads(line)
                    except ValueError:continue
                    if isinstance(event,dict) and event.get('Action')=='pass' and event.get('Package')=='github.com/Wyrcan-io/playtestr/internal/runner':
                        passed.add(event.get('Test'))
                if not controls<=passed:raise RuntimeError('large-checkpoint controls did not pass natively')
            selected[label]=dict(attempt=attempt,manifest_sha256=sha256(manifest),console_sha256=sha256(console))
        if set(selected)!=required:raise RuntimeError('missing actual native engineering checks')
        cells.append(dict(host=host,artifact=packet.name,checks=selected))
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/native-core-129b7a4.json',dict(
        schema_version=1,source_revision=MIGRATION_SOURCE,tooling_revision=metadata['headSha'],run=run,metadata_sha256=sha256(root/'run-metadata.json'),
        native_hosts=['linux','macos','windows'],cells=cells,verified_success=True,
        earlier_attempts=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha256(p)) for p in [
            RAW/'native/39443018782/run-metadata.json',root/'run-metadata-attempt-1.json'] if p.is_file()],
        scope='Actual native tests, vet, race, helper controls and public saved-state journey; expanded checkpoint controls positively observed in ordinary and race output. No project/final-archive credit.'))
    print('Three native core cells independently verified for migration repair.')


if __name__=='__main__':main()
