"""Bind two audited final native cells to complete retained packet inventories."""
import argparse
import json

from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True,
        choices=['plop','poetry','rubygems','edit','vis','frogmouth','papis'])
    parser.add_argument('--run',required=True);parser.add_argument('--generations',type=int,required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal() and 1<=args.generations<=100,'invalid retention scope')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass';project=docs/args.project
    hosts=['linux','windows'] if args.project in {'rubygems','edit','frogmouth','papis'} else ['linux','macos']
    audits={};values={}
    for host in hosts:
        path=project/('final-verified-'+host+'.json');value=load(path)
        require(value['run']==args.run and value['host']==host and value['ordinary_executions']==240
            and value['calibration_executions']==9,'incomplete independent native audit')
        audits[host]=sha256(path);values[host]=value
    review=load(project/'source-review.json');canonical=RAW/args.project/'retained-source'
    require(sha256(canonical/'source.tar.gz')==review['archive_sha256'],'canonical source archive changed')
    archives=[];inventories=[]
    for generation in range(1,args.generations+1):
        root=RAW/args.project/('retained-native-v'+str(generation));index=load(root/'index.json',maximum=4*1024**2)
        checked=load(root/'verified.json');removed=load(root/'expanded-removed.json')
        require(checked['index_sha256']==sha256(root/'index.json')==removed['index_sha256']
            and checked['archive_sha256']==index['archive_sha256']==removed['archive_sha256']
            and removed['all_expanded_removed'] and removed['removed_runs']==index['runs'],'retention/removal differs')
        verify(root/'packets.tar.gz',index['files'])
        for name in index['selected_restore']:
            require(sha256(root/'selected-restore'/name)==index['files'][name]['sha256'],'selected packet restore differs')
        archives.append(dict(generation=generation,index_sha256=sha256(root/'index.json'),archive_sha256=index['archive_sha256']))
        inventories.append(index)
    for host,value in values.items():
        suffix={'linux':'Linux','windows':'Windows','macos':'macOS'}[host]
        prefix='native/'+args.run+'/final-'+args.project+'-'+suffix+'/'
        for digest in [value['source_fault_summary_sha256'],value['cleanup_receipt_sha256']]:
            require(any(name.startswith(prefix) and record['sha256']==digest for index in inventories
                for name,record in index['files'].items()),'actual audited faults/cleanup not retained')
    path=project/'final-series-verification.json'
    immutable_json(path,dict(run=args.run,canonical_scenarios=20,audits=audits,retained_archives=archives,
        verified_ordinary_executions=480,verified_calibration_executions=18,verified_native_cells=2,
        final_archive_qualified_projects=0,paid_launch_admissions=0,
        scope='Both exact-archive native twelve-by-twenty series and actual source faults/restoration independently audited; complete historical and final packet inventories reverified, selected evidence restored, expanded packets removed. Overall final matrix/control gates remain separate.'))
    status_path=docs/'final-series-status.json';status=load(status_path)
    matches=[p for p in status['projects'] if p['project']==args.project]
    if matches:current=matches[0]
    else:
        current=dict(project=args.project,series=[]);status['projects'].append(current);status['attempted_projects']+=1
    require(not any(s['run']==args.run for s in current['series']),'final series already counted')
    current['series'].append(dict(run=args.run,status='independently-verified',ordinary_observed=480,ordinary_passed=480,
        receipt_sha256=sha256(path)))
    for key,amount in dict(observed_ordinary_executions=480,observed_ordinary_passed=480,
        observed_public_calibration_executions=18,verified_calibration_executions=18,
        verified_ordinary_executions=480,verified_series_cells=2,verified_series_projects=1).items():status[key]+=amount
    status_path.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print('Verified final native series and complete retention:',args.project,'; overall final admission remains separate.')


if __name__=='__main__':main()
