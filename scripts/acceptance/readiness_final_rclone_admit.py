"""Retain and bind independently audited Rclone final cells without launch credit."""
import json

from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load
from readiness_verify_reencoded_native import verify_retained


def require(value,message):
    if not value:raise RuntimeError(message)


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass';project=docs/'rclone'
    audits={};payloads={}
    for host in ['linux','windows']:
        path=project/('final-verified-'+host+'.json');value=load(path)
        require(value['run']=='39577934986' and value['host']==host and value['ordinary_executions']==240
            and value['calibration_executions']==9,'incomplete native audit')
        audits[host]=sha256(path);payloads[host]=[value['source_fault_summary_sha256'],value['cleanup_receipt_sha256']]
    archives=[]
    for generation in range(1,13):
        root=RAW/'rclone'/('retained-native-v'+str(generation))
        if generation<=10:
            index=verify_retained(root);encoding=load(root/'reencoded.json');archive_sha=encoding['replacement_archive_sha256']
        else:
            index=load(root/'index.json',maximum=4*1024**2);checked=load(root/'verified.json');removed=load(root/'expanded-removed.json')
            require(checked['index_sha256']==sha256(root/'index.json')==removed['index_sha256']
                and checked['archive_sha256']==index['archive_sha256']==removed['archive_sha256']
                and removed['all_expanded_removed'] and removed['removed_runs']==index['runs'],'retention/removal differs')
            verify(root/'packets.tar.gz',index['files']);archive_sha=index['archive_sha256']
            host='linux' if generation==11 else 'windows'
            require(index['runs']==['39577934986'] and all(any(row['sha256']==digest for row in index['files'].values())
                for digest in payloads[host]),'audited final faults/cleanup not retained')
            for name in index['selected_restore']:
                require(sha256(root/'selected-restore'/name)==index['files'][name]['sha256'],'selected evidence restore differs')
        archives.append(dict(generation=generation,index_sha256=sha256(root/'index.json'),archive_sha256=archive_sha,
            encoding='xz' if generation<=10 else 'gzip'))
    path=project/'final-series-verification.json'
    immutable_json(path,dict(run='39577934986',canonical_scenarios=20,audits=audits,retained_archives=archives,
        verified_ordinary_executions=480,verified_calibration_executions=18,verified_native_cells=2,
        final_archive_qualified_projects=0,paid_launch_admissions=0,
        scope='Both exact-archive native twelve-by-twenty series, actual compiled faults/restoration, explicit final phases, self-contained catalogs and cleanup independently audited. All twelve historical/final packet generations verified using their actual encoding. Overall final matrix/control gates are separate.'))
    status_path=docs/'final-series-status.json';status=load(status_path)
    require(not any(p['project']=='rclone' for p in status['projects']),'series already counted')
    status['projects'].append(dict(project='rclone',series=[dict(run='39577934986',status='independently-verified',
        ordinary_observed=480,ordinary_passed=480,receipt_sha256=sha256(path))]))
    for key,amount in dict(attempted_projects=1,observed_ordinary_executions=480,observed_ordinary_passed=480,
        observed_public_calibration_executions=18,verified_calibration_executions=18,
        verified_ordinary_executions=480,verified_series_cells=2,verified_series_projects=1).items():status[key]+=amount
    status_path.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print('Verified both final Rclone cells and twelve retained generations; overall final admission remains separate.')


if __name__=='__main__':main()
