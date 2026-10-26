"""Account for the exact sandbox-denied prelaunch report without cleanup credit."""
import json

from next20_check import RAW, ROOT, DOC
from next20_local_audit import LocalAudit
from readiness_evidence import immutable_json, sha256


def main():
    matches=[]
    for path in (RAW/'yo/development').glob('*/N01.report.json'):
        report=json.loads(path.read_text());row=report['results'][0]
        if row.get('failure',{}).get('category')=='workspace_setup_failure':matches.append((path,report,row))
    if len(matches)!=1:raise ValueError('Exactly one original unlaunched report required')
    path,report,row=matches[0]
    if row['failure']['message']!='workspace setup failed: expand native workspace path: Access is denied.':
        raise ValueError('Original sandbox denial differs')
    if row['workspace']['prepared'] or row['workspace'].get('root') or row.get('invocation_id') or row['cleanup']['attempted'] or row['target']!={'exited':False} or row.get('evidence'):
        raise ValueError('Report contains launched or prepared target state')
    if any(step['status']!='not_run' for step in row['steps']):raise ValueError('Prelaunch report executed a step')
    observation=json.loads((path.parent/'N01.observation.json').read_text())
    if observation['report_sha256']!=sha256(path):raise ValueError('Original unlaunched report changed')
    audit=LocalAudit('yo');provenance=json.loads((DOC/'yo/source-provenance.json').read_text())
    audit.command(observation['attempt'],original_failure=True,source=provenance['files'])
    immutable_json(DOC/'yo/sandbox-prelaunch-disposition.json',dict(schema_version=1,report=path.relative_to(ROOT).as_posix(),
        report_sha256=sha256(path),attempt=observation['attempt'],target_launched=False,workspace_prepared=False,
        executed_steps=0,confirmed_target_cleanup=False,cleanup_credit=0,ordinary_credit=0,
        reason=row['failure']['message'],all_original_events_and_report_preserved=True,
        source_runtime_cleanup='Separate native PID/birth proof and checked exact owned-root retention/removal required.',
        subjects=audit.subjects))
    print('Exact unlaunched report digest for explicit cleanup disposition:',sha256(path))


if __name__=='__main__':main()
