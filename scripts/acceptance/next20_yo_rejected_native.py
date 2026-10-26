"""Audit retained first native failures without granting any qualification."""
import argparse
import json

from next20_check import RAW
from next20_verify_jrnl import json_payloads, require
from readiness_compact_native import verify
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--host',choices=['linux','windows'],required=True)
    parser.add_argument('--generation',type=int,choices=[1,2],required=True);args=parser.parse_args()
    retained=RAW/'yo'/('retained-native-v'+str(args.generation));index=json.loads((retained/'index.json').read_text())
    require(index['project']=='yo' and index['runs']==['40301653366'] and sha256(retained/'packets.tar.gz')==index['archive_sha256'],'wrong rejected native packet')
    verify(retained/'packets.tar.gz',index['files']);data=json_payloads(retained,index)
    provider=data['native/40301653366/run-metadata.json']
    require(provider['headSha']=='1199115ba469506034e27177a80face43eb192b2' and provider['status']=='completed' and provider['conclusion']=='cancelled','first native provider identity differs')
    os_name='Linux' if args.host=='linux' else 'Windows';prefix='native/40301653366/next20-yo-'+os_name+'/'
    jobs=[j for j in provider['jobs'] if ('ubuntu-24.04' if args.host=='linux' else 'windows-2025') in j['name']]
    require(len(jobs)==1 and jobs[0]['conclusion']==('failure' if args.host=='linux' else 'cancelled'),'wrong first native job disposition')
    reports={n:v for n,v in data.items() if n.startswith(prefix+'yo/final-series/') and n.endswith('.report.json')}
    require(bool(reports),'no actual first native reports retained')
    passed=failed=confirmed=0;invocations=set()
    for name,report in reports.items():
        require(report['report_version']==3 and report['runner_version']=='v0.4.0-rc.5' and report['os']==args.host and len(report['results'])==1,'wrong original native report')
        row=report['results'][0]
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations,'duplicate first native invocation')
        invocations.add(row['invocation_id']);passed+=row['status']=='passed';failed+=row['status']=='failed'
        confirmed+=bool(row.get('cleanup',{}).get('confirmed_exited') and row.get('workspace',{}).get('cleaned'))
    if args.host=='linux':
        require(len(reports)==11 and passed==10 and failed==1 and confirmed==11,'unexpected original Linux denominator')
        failed_name=prefix+'yo/final-series/0/E03.report.json';row=reports[failed_name]['results'][0]
        require(row['target']['exit_code']==1 and row['failure']['category']=='unexpected_exit','original native cancellation differs')
        require(row['steps'][0]['status']==row['steps'][1]['status']=='passed' and row['steps'][2]['status']=='failed','original cancellation did not reach prompt/key/exit boundary')
        contract=data[prefix+'yo/final-series/0/contracts/e03.json']
        require(next(s['exit'] for s in contract['steps'] if 'exit' in s)==130,'first predicted Linux exit changed')
    immutable_json(retained/'rejected-audit.json',dict(schema_version=1,run='40301653366',host=args.host,
        archive_sha256=index['archive_sha256'],index_sha256=sha256(retained/'index.json'),
        original_reports=len(reports),passed=passed,failed=failed,confirmed_individual_cleanups=confirmed,
        native_cells=0,ordinary_qualification_credit=0,calibration_credit=0,new_project_admissions=0,
        scope='Rejected first series. Linux predicted130 disproved by actual1; fixture/report discovery also failed. Windows cancelled to avoid further work on rejected source. No complete target source/runtime cleanup claim; individual report cleanup remains separately counted.'))
    print('Audited rejected',args.host,'packet:',len(reports),'reports,',passed,'passed,',failed,'failed; zero qualification credit.')


if __name__=='__main__':main()
