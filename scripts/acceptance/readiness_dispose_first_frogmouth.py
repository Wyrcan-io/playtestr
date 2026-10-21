"""Bind cancelled-series accounting to retained bytes and preserve denominators."""
import json

from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass';project=docs/'frogmouth'
    receipts={host:load(project/('final-first-series-'+host+'.json')) for host in ['linux','windows']}
    archives=[]
    for generation in [3,4]:
        root=RAW/'frogmouth'/('retained-native-v'+str(generation));index=load(root/'index.json',maximum=4*1024**2)
        removed=load(root/'expanded-removed.json');checked=load(root/'verified.json')
        require(removed['all_expanded_removed'] and removed['index_sha256']==checked['index_sha256']==sha256(root/'index.json')
            and removed['archive_sha256']==index['archive_sha256']==checked['archive_sha256'],'partial packet retention differs')
        verify(root/'packets.tar.gz',index['files'])
        archives.append(dict(generation=generation,archive_sha256=index['archive_sha256'],index_sha256=sha256(root/'index.json')))
    require(all(r['run']=='39680492184' and r['final_archive_credit']==0 for r in receipts.values()),'wrong original series')
    launches=sum(r['ordinary_runner_launches'] for r in receipts.values())
    passed=sum(r['ordinary_reported_statuses'].get('passed',0) for r in receipts.values())
    failed=sum(r['ordinary_reported_statuses'].get('failed',0) for r in receipts.values())
    cancelled=sum(r['ordinary_reported_statuses'].get('cancelled',0) for r in receipts.values())
    unreported=sum(r['ordinary_unreported_launches'] for r in receipts.values())
    require(launches==passed+failed+cancelled+unreported,'ordinary outcome denominator differs')
    calibration=sum(r['public_calibration_executions'] for r in receipts.values())
    path=project/'final-first-series-disposition.json'
    immutable_json(path,dict(run='39680492184',status='cancelled-harness-profile',ordinary_runner_launches=launches,
        ordinary_reported_passed=passed,ordinary_reported_failed=failed,ordinary_reported_cancelled=cancelled,
        ordinary_unreported_launches=unreported,public_calibration_executions=calibration,
        cell_receipts={h:sha256(project/('final-first-series-'+h+'.json')) for h in receipts},retained_archives=archives,
        probe_receipt_sha256=sha256(RAW/'windows-helper-ownership/verified.json'),final_archive_credit=0,
        source_runtime_removed={h:r['source_runtime_removed'] for h,r in receipts.items()},
        scope='Cancel/preserve original workflow after confirming helper-interpreter ownership hazard; exact ordinary reports and cancellation remain in denominators. Linux source/runtime removal confirmed; original Windows additional observer/removal unconfirmed. Replacement keeps helpers on bootstrap Python without weakening target/process checks or changing target correctness oracles. No stronger unlogged PID-cause claim.'))
    status_path=docs/'final-series-status.json';status=load(status_path)
    require(not any(p['project']=='frogmouth' for p in status['projects']),'original series already counted')
    status['projects'].append(dict(project='frogmouth',series=[dict(run='39680492184',status='cancelled-harness-profile',
        ordinary_observed=launches,ordinary_passed=passed,ordinary_failed=failed,ordinary_cancelled=cancelled,
        ordinary_unreported=unreported,receipt_sha256=sha256(path))]))
    status['attempted_projects']+=1
    for key,amount in dict(observed_ordinary_executions=launches,observed_ordinary_passed=passed,observed_ordinary_failed=failed,
        observed_ordinary_cancelled=cancelled,observed_ordinary_unreported=unreported,
        observed_public_calibration_executions=calibration).items():status[key]=status.get(key,0)+amount
    status_path.write_text(json.dumps(status,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Preserved original cancelled Frogmouth:',launches,'ordinary launches,',passed,'passes,',cancelled,'cancelled,',calibration,'calibration calls; zero qualification credit.')


if __name__=='__main__':main()
