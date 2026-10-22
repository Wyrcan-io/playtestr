"""Audit actual native helper events, tested source and five named test outcomes."""
import argparse
import hashlib
import json
import subprocess

from next20_check import DOC,RAW,NAME
from readiness_evidence import immutable_json,sha256
from readiness_compact_native import compact


def main():
    parser=argparse.ArgumentParser();parser.add_argument('host',choices=['ubuntu-24.04','macos-15','windows-2025'])
    parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    run='39789582365';revision='406169061ffb022c0fd0a4b1f99309836b6a96b1'
    root=RAW/'native'/run/('next20-harness-'+args.host)
    attempts={}
    for path in (root/'events').glob('*.json'):
        value=json.loads(path.read_text());attempts.setdefault(value['id'],{})[value['event']]=value
    if len(attempts)!=2:raise ValueError('missing/extra native top-level checks')
    checks=[]
    for eid,events in attempts.items():
        if set(events)!={'started','identified','launched','finished'}:raise ValueError('incomplete native command')
        if any(e['campaign']!=NAME for e in events.values()):raise ValueError('cross-campaign native event')
        started=events['started'];finish=events['finished']
        if started['ci_run_id']!=run or finish['category']!='passed' or finish['exit_code']!=0 or finish['harness_cleanup']!='harness_process_reaped':
            raise ValueError('nonqualifying native outcome/cleanup')
        console=root/'core'/eid/'console.log'
        if sha256(console)!=finish['console_sha256']:raise ValueError('changed actual native console')
        manifest=root/events['identified']['identity']['manifest']
        if sha256(manifest)!=events['identified']['identity']['sha256']:raise ValueError('native identity mismatch')
        identity=json.loads(manifest.read_text());source_bindings={}
        for name in ['scripts/acceptance/test_next20_campaign.py','scripts/acceptance/next20_check.py',
                     'scripts/acceptance/readiness_evidence.py','scripts/acceptance/adversarial_process.py']:
            blob=subprocess.check_output(['git','show',revision+':'+name])
            hashes={hashlib.sha256(blob).hexdigest(),hashlib.sha256(blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()}
            if identity['files'].get(name) not in hashes:raise ValueError('native tested source changed: '+name)
            source_bindings[name]=identity['files'][name]
        output=console.read_text(encoding='utf-8')
        if started['label']=='native-next20-command-controls':
            tests=['test_actual_success_and_expected_nonzero_keep_distinct_execution_ids',
                'test_actual_target_source_change_gets_new_prelaunch_identity',
                'test_actual_timeout_is_failed_and_process_is_reaped',
                'test_exclusive_events_have_new_campaign_without_changing_historical_default',
                'test_rejects_cross_campaign_destination']
            if any(not any(line.startswith(test+' ') and line.endswith(' ... ok') for line in output.splitlines()) for test in tests):
                raise ValueError('missing named native positive test')
            if 'Ran 5 tests' not in output or '\nOK\n' not in output.replace('\r\n','\n') or 'skipped' in output:
                raise ValueError('partial/skipped native controls')
        else:
            if started['label']!='native-next20-syntax' or 'Parsed' not in output:raise ValueError('missing native syntax check')
        checks.append(dict(label=started['label'],attempt=eid,console_sha256=sha256(console),
                           identity_sha256=sha256(manifest),source_bindings=source_bindings))
    (RAW/'harness').mkdir(exist_ok=True)
    retained=compact(RAW,'harness',[run],generation=args.generation)
    receipt=dict(schema_version=1,run=run,host=args.host,tooling_revision=revision,checks=checks,
        named_controls_passed=5,source_syntax_scope='Only helpers present at recorded tested revision',
        archive_sha256=sha256(retained/'packets.tar.gz'),index_sha256=sha256(retained/'index.json'),
        retained_generation=args.generation,expanded_removal_confirmed=False,new_project_credit=0,
        scope='Actual source/event/positive-console proof for five new helper controls. No application or archive-product-control reexecution credit.')
    immutable_json(DOC/('harness-'+args.host+'.json'),receipt)
    print('Verified actual',args.host,'native helper controls and retained packet; checked expanded removal still required.')


if __name__=='__main__':main()
