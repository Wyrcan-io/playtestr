"""Classify the two original parser refusals without inventing target cleanup."""
import json

from next20_check import RAW,ROOT,DOC
from next20_target_cleanup import invalid_spec_before_launch
from readiness_evidence import immutable_json,sha256


def main():
    rows=[]
    for series,case,attempt,reason in [
        ('7df7b5002e034415a28e82bc6ca8b116','N02','e742eb13d0b14e549e9ce6fdf802951f','Original author used unknown Down key spelling; corrected to public ArrowDown with original contract retained.'),
        ('992501310db14c729f1ac369160a5518','E03','004ea7bfbf684677986bf939772d984b','rc.5 rejected the real native Windows cancellation status above255. General specv3 native-status repair and replacement candidate required; cancellation case retained.')]:
        report=RAW/'cargo-generate/development'/series/(case+'.report.json')
        data=json.loads(report.read_text());row=data['results'][0]
        if data['runner_version']!='v0.4.0-rc.5' or not invalid_spec_before_launch(data,row):raise ValueError('original parser refusal differs')
        events={event:json.loads((RAW/'events'/(attempt+'-'+event+'.json')).read_text()) for event in ['started','identified','launched','finished']}
        finish=events['finished']
        if events['started']['project']!='cargo-generate' or finish['exit_code']!=1 or finish['harness_cleanup']!='harness_process_reaped' or finish['cleanup_errors']:
            raise ValueError('original runner process was not reaped')
        rows.append(dict(case=case,report=report.relative_to(ROOT).as_posix(),report_sha256=sha256(report),runner_attempt=attempt,
            category='invalid_spec',runner_process_executed=True,runner_process_reaped=True,target_launched=False,
            workspace_prepared=False,target_cleanup_credit=0,ordinary_execution_credit=0,reason=reason))
    immutable_json(DOC/'cargo-generate/invalid-spec-refusal-disposition.json',dict(schema_version=1,reports=rows,
        cleanup_policy='Only these exact explicitly supplied report hashes may use parser-refusal classification. Any invocation, workspace, executed step, evidence or attempted cleanup rejects that classification. They remain failed authoring/runner attempts with zero target execution/cleanup credit.'))
    print('Read back two original parser refusals and reaped runner processes; zero target execution/cleanup credit.')


if __name__=='__main__':main()
