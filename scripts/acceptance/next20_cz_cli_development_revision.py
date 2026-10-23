"""Retain the first series and explicitly correct three contract assumptions."""
import json
import shutil

from next20_check import RAW,DOC,ROOT
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'cz-cli';series=RAW/'cz-cli/development/0d34272bfcb3437e9b5ef6974731c970'
    summary=json.loads((series/'summary.json').read_text(encoding='utf-8'))
    if summary['passed']!=17 or summary['failed']!=3:raise ValueError('Unexpected actual first-series denominator')
    original=series/'original-inputs';original.mkdir()
    declaration=json.loads((package/'scenarios.json').read_text(encoding='utf-8'))
    for name in ['scenarios.json',*[c['spec'] for c in declaration['cases']]]:shutil.copyfile(package/name,original/name)
    for name in ['fixture','fixtures','snapshots']:shutil.copytree(package/name,original/name)
    changes=[]
    for cid in ['E01','E02','E07']:
        case=next(c for c in declaration['cases'] if c['id']==cid);path=package/case['spec']
        spec=json.loads(path.read_text(encoding='utf-8'));before=sha256(path)
        report=json.loads((series/(cid+'.report.json')).read_text(encoding='utf-8'))['results'][0]
        screen=package/(case['spec']+'.actual.txt');shutil.copyfile(screen,original/screen.name)
        if cid in {'E01','E02'}:
            if report['target']['exit_code']!=1:raise ValueError('Actual interruption evidence differs')
            for step in spec['steps']:
                if 'exit' in step:
                    if step['exit']!=130:raise ValueError('Original predicted cancellation code differs')
                    step['exit']=1
            case['expected_exit']=1
            reason='Actual Windows Inquirer interruption exits1, not the predicted130. Preserve first failure. Require the exact observed nonzero1, prior positive prompt/input evidence, absent message and all unchanged fixture state. Unix planned130 follows Inquirer self-SIGINT and runner signal normalization; native execution must verify that path separately.'
        else:
            if report['failure']['category']!='assertion_timeout' or report['steps'][16]['status']!='failed':raise ValueError('Original resize failure differs')
            if spec['steps'][16]!={'expect':'open issues?'}:raise ValueError('Original last readiness anchor differs')
            spec['steps'][16]={'expect':'Does this change affect'}
            reason='Actual40-column final prompt wraps between open and issues. Use the intact unique Does this change affect label. Keep the exact input, correction, resize dimensions, exit and all saved-file/fixture oracles unchanged.'
        path.write_text(json.dumps(spec,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        case['spec_sha256']=sha256(path)
        changes.append(dict(case=cid,original_sha256=before,replacement_sha256=sha256(path),reason=reason,
            actual_report_sha256=sha256(series/(cid+'.report.json')),original_screen_sha256=sha256(original/screen.name)))
    declaration['development_revision']=2
    (package/'scenarios.json').write_text(json.dumps(declaration,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'first-development-disposition.json',dict(schema_version=1,initial_series=series.name,
        ordinary_development_attempts=20,passed=17,failed=3,final_ordinary_credit=0,runner_repairs=0,
        original_inputs=original.relative_to(ROOT).as_posix(),changes=changes,failed_attempts_preserved=True,
        target_observation='Windows self-interruption code1 is platform behavior; not a passing cancellation until exact code and absence/preservation checks actually pass.'))
    print('Retained first20 outcomes17pass/3fail and every original input/screen. Declared two Windows exit-code corrections and one intact readiness anchor.')


if __name__=='__main__':main()
