"""Audit actual native helper events, tested source and five named test outcomes."""
import argparse
import ast
import hashlib
import json
import subprocess

from next20_check import DOC,RAW,NAME
from readiness_evidence import immutable_json,sha256
from readiness_compact_native import compact


def main():
    parser=argparse.ArgumentParser();parser.add_argument('host',choices=['ubuntu-24.04','macos-15','windows-2025'])
    parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--run',default='39789582365')
    parser.add_argument('--revision',default='406169061ffb022c0fd0a4b1f99309836b6a96b1')
    args=parser.parse_args();run=args.run;revision=args.revision
    if not run.isascii() or not run.isdecimal() or len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('invalid explicit native run/source revision')
    test_source=subprocess.check_output(['git','show',revision+':scripts/acceptance/test_next20_campaign.py'])
    test_names=[node.name for node in ast.walk(ast.parse(test_source.decode('utf-8'))) if isinstance(node,ast.FunctionDef) and node.name.startswith('test_')]
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
            skipped=[];passed=[]
            for test in test_names:
                lines=[line for line in output.splitlines() if line.startswith(test+' ')]
                if len(lines)!=1:raise ValueError('missing/duplicated named native test outcome')
                if lines[0].endswith(' ... ok'):passed.append(test)
                elif (args.host!='windows-2025' and test=='test_native_target_removal_refuses_changed_payload_then_removes_exact_owned_fixture'
                      and lines[0].endswith(" ... skipped 'native Windows checked target removal control'")):
                    skipped.append(dict(test=test,reason='native Windows checked target removal control'))
                else:raise ValueError('unexpected native failure/skip')
            normalized=output.replace('\r\n','\n')
            if f'Ran {len(test_names)} tests' not in output or not any(line=='OK' or line==f'OK (skipped={len(skipped)})' for line in normalized.splitlines()):
                raise ValueError('partial/skipped native controls')
        else:
            if started['label']!='native-next20-syntax' or 'Parsed' not in output:raise ValueError('missing native syntax check')
        checks.append(dict(label=started['label'],attempt=eid,console_sha256=sha256(console),
                           identity_sha256=sha256(manifest),source_bindings=source_bindings))
    (RAW/'harness').mkdir(exist_ok=True)
    retained=compact(RAW,'harness',[run],generation=args.generation)
    if args.host=='windows-2025' and 'test_native_target_removal_refuses_changed_payload_then_removes_exact_owned_fixture' in test_names:
        matches=[]
        expected_blob=subprocess.check_output(['git','show',revision+':scripts/acceptance/next20_remove_target.ps1'])
        expected_hashes={hashlib.sha256(expected_blob).hexdigest(),hashlib.sha256(expected_blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n')).hexdigest()}
        for path in (root/'control-tests').rglob('*-identified.json'):
            event=json.loads(path.read_text());events=path.parent;eid=event['id']
            started=json.loads((events/(eid+'-started.json')).read_text())
            if not started['label'].startswith('native-removal-'):continue
            control_root=events.parent;manifest=control_root/event['identity']['manifest']
            if sha256(manifest)!=event['identity']['sha256']:raise ValueError('changed actual native removal identity')
            value=json.loads(manifest.read_text())
            sources=[h for n,h in value['files'].items() if n.endswith('fixture-workspace/scripts/acceptance/next20_remove_target.ps1')]
            if len(sources)!=1 or sources[0] not in expected_hashes:raise ValueError('stale native checked-removal subprocess source')
            finished=json.loads((events/(eid+'-finished.json')).read_text())
            if finished['category']!='passed' or finished['harness_cleanup']!='harness_process_reaped':raise ValueError('incomplete actual native guard command')
            matches.append(dict(label=started['label'],source_sha256=sources[0],attempt=eid))
        if len(matches)!=2:raise ValueError('missing real changed-payload refusal and exact removal executions')
    else:matches=[]
    receipt=dict(schema_version=1,run=run,host=args.host,tooling_revision=revision,checks=checks,
        named_controls_passed=len(passed),tests_discovered=len(test_names),skips=skipped,native_removal_commands=matches,
        source_syntax_scope='Only helpers present at recorded tested revision',
        archive_sha256=sha256(retained/'packets.tar.gz'),index_sha256=sha256(retained/'index.json'),
        retained_generation=args.generation,expanded_removal_confirmed=False,new_project_credit=0,
        scope='Actual source/event/positive-console proof for five new helper controls. No application or archive-product-control reexecution credit.')
    name=('harness-'+args.host+'.json') if run=='39789582365' else ('harness-'+run+'-'+args.host+'.json')
    immutable_json(DOC/name,receipt)
    print('Verified actual',args.host,'native helper controls and retained packet; checked expanded removal still required.')


if __name__=='__main__':main()
