"""Preserve the refused development window and narrowly repair harness-authored contracts."""
import copy
import json

from next20_check import DOC,RAW,ROOT
from next20_target_cleanup import invalid_spec_before_launch
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'peco';root=RAW/'peco/technical-contract-revision-v2';root.mkdir(exist_ok=False)
    original=json.loads((package/'scenarios.json').read_text());(root/'scenarios-v1.json').write_bytes((package/'scenarios.json').read_bytes())
    window=RAW/'peco/development/bc8cb2e61ffb41fab8f3181c28f26a7b';reports=[];invalid=[]
    for path in sorted(window.glob('*.report.json')):
        doc=json.loads(path.read_text());row=doc['results'][0]
        if row['failure']['category']=='invalid_spec' if row.get('failure') else False:
            if not invalid_spec_before_launch(doc,row):raise ValueError('refused spec has target-launch state')
            invalid.append(sha256(path))
        elif not row['cleanup']['confirmed_exited'] or not row['workspace']['cleaned']:raise ValueError('initial actual target cleanup incomplete')
        reports.append(dict(report=path.relative_to(RAW).as_posix(),sha256=sha256(path),status=row['status'],category=row.get('failure',{}).get('category'),target_launched=bool(row.get('invocation_id'))))
    if len(reports)!=9 or len(invalid)!=1:raise ValueError('initial partial development denominator differs')
    changes=[]
    for case in original['cases']:
        path=package/case['spec'];body=path.read_bytes();(root/path.name).write_bytes(body)
        if case['id']=='N01':continue
        value=json.loads(body);before=copy.deepcopy(value)
        if value['command'][5:7]!=['--','--']:raise ValueError('unexpected original capture argv')
        del value['command'][6]
        for step in value['steps']:
            if step.get('wait_for_redraw')=={} and set(step)=={'wait_for_redraw'}:step['wait_for_redraw']=True
        path.write_text(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        changes.append(dict(case=case['id'],original_sha256=case['spec_sha256'],revised_sha256=sha256(path),removed_one_duplicate_capture_terminator=True,redraw_schema_boolean=case['id'] in {'E01','E12'}));case['spec_sha256']=sha256(path)
    (package/'scenarios.json').write_text(json.dumps(original,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'technical-contract-revision-v2.json',dict(schema_version=1,original_development_wrapper='713b69c092784826a1b249ca7588a6d9',original_partial_reports=reports,
        actual_targets=8,actual_passed=1,actual_failed=7,unlaunched_invalid_spec_report_sha256=invalid,changes=changes,original_scenarios_sha256=sha256(root/'scenarios-v1.json'),revised_scenarios_sha256=sha256(package/'scenarios.json'),
        scope='First technical development stopped after9 runner reports:8 target executions plus1 invalid-spec prelaunch refusal. Harness builder duplicated the capture -- separator and used an object instead of required boolean for redraw. Original contracts,reports,frames and helper bytes retained. Narrow argv/schema repairs only; no target source,expected file bytes,meaningful input,deadline or oracle relaxation. Fresh whole20-case window required. Initial public route remains its separate positive3shell/16control observation.'))
    print('Preserved initial8target/1refusal window; narrowly revised19technical argv and2redraw schema values. Fresh complete development required.')


if __name__=='__main__':main()
