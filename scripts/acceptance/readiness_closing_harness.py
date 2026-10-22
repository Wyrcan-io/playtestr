"""Audit one native closing harness packet before bounded retention/removal."""
import argparse
import re

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import packet_file, read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--source',required=True)
    parser.add_argument('--host',choices=['ubuntu-24.04','macos-15','windows-2025'],required=True);args=parser.parse_args()
    require(re.fullmatch('[0-9]{1,20}',args.run) and re.fullmatch('[a-f0-9]{40}',args.source),'unsafe harness selection')
    parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and metadata['headSha']==args.source
        and {j['name'] for j in metadata['jobs']}=={'native-harness ('+h+')' for h in ['ubuntu-24.04','macos-15','windows-2025']}
        and all(j['status']=='completed' and j['conclusion']=='success' for j in metadata['jobs']),
        'complete native harness matrix required')
    base=parent/('runner-readiness-harness-'+args.host);checks=[]
    for label in ['native-readiness-helper-syntax','native-harness-controls']:
        found=[p for p in (base/'events').glob('*-finished.json') if load(p)['label']==label]
        require(len(found)==1,'missing/duplicate native harness check')
        end=load(found[0]);identity=end['id'];start=load(base/'events'/(identity+'-started.json'))
        require(str(start['ci_run_id'])==args.run and end['exit_code']==0 and end['category']=='passed'
            and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'native harness actual completion differs')
        log=packet_file(base,'core/'+identity+'/console.log',4*1024**2);require(sha256(log)==end['console_sha256'],'native harness log changed')
        output=log.read_text(encoding='utf-8-sig');item=dict(label=label,attempt=identity,console_sha256=sha256(log))
        identified=load(base/'events'/(identity+'-identified.json'))['identity']
        manifest=packet_file(base,identified['manifest'].replace('\\','/'),2*1024**2)
        require(sha256(manifest)==identified['sha256'],'native harness manifest changed')
        if label=='native-harness-controls':
            match=re.search(r'Ran ([0-9]+) tests in ',output);require(match and int(match[1])==64,'unexpected native harness denominator')
            require(re.search(r'^OK(?: \(skipped=[0-9]+\))?\s*$',output,re.M),'native harness did not pass')
            skips=re.findall(r"^(.+?) \.\.\. skipped (.+)$",output,re.M)
            item.update(tests_discovered=64,platform_prerequisite_skips=[dict(test=t,reason=r) for t,r in skips],
                passed=64-len(skips),manifest_sha256=sha256(manifest))
            require('test_compiled_app_source_lock_compiler_and_binary_are_bound' in output,'native provenance regression absent')
        else:require(re.search(r'Parsed [0-9]+ readiness helpers',output),'missing native syntax evidence')
        checks.append(item)
    immutable_json(ROOT/('docs/validation/runner-readiness-ten-project-pass/closing-harness-'+args.host+'.json'),
        dict(run=args.run,source=args.source,host=args.host,metadata_sha256=sha256(parent/'run-metadata.json'),checks=checks,
            product_control_credit=0,scope='Actual native helper syntax and whole harness tests; each prerequisite skip is reported explicitly. No application scenario, new whole product control or archive invocation credit.'))
    print('Verified actual closing native harness:',args.host)


if __name__=='__main__':main()
