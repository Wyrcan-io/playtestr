"""Bind both independently audited fff cells to fully verified retained packets."""
from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def require(value, message):
    if not value:raise RuntimeError(message)


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    audits={}
    for host in ['linux','macos']:
        path=docs/'fff'/('final-v2-verified-'+host+'-r2.json');value=load(path)
        require(value['run']=='39575015155' and value['host']==host and value['auditor_revision']==2
            and value['ordinary_executions']==240 and value['calibration_executions']==9,'incomplete independent native audit')
        audits[host]=sha256(path)
    archives=[]
    for generation in range(1,9):
        root=RAW/'fff'/('retained-native-v'+str(generation));index=load(root/'index.json',maximum=4*1024**2)
        checked=load(root/'verified.json');removed=load(root/'expanded-removed.json')
        require(checked['index_sha256']==sha256(root/'index.json')==removed['index_sha256']
            and checked['archive_sha256']==index['archive_sha256']==removed['archive_sha256']
            and removed['all_expanded_removed'] and removed['removed_runs']==index['runs'],'retention/removal receipts disagree')
        verify(root/'packets.tar.gz',index['files'])
        for name in index['selected_restore']:
            require(sha256(root/'selected-restore'/name)==index['files'][name]['sha256'],'selected evidence restore changed')
        archives.append(dict(generation=generation,index_sha256=sha256(root/'index.json'),archive_sha256=index['archive_sha256']))
    path=docs/'fff/final-series-verification.json'
    immutable_json(path,dict(revision=2,run='39575015155',canonical_scenarios=20,audits=audits,retained_archives=archives,
        verified_ordinary_executions=480,verified_calibration_executions=18,verified_native_cells=2,
        final_archive_qualified_projects=0,paid_launch_admissions=0,
        scope='Both exact-archive native twelve-by-twenty series and real source faults/restoration independently audited; all historical packets retained and verified. Printable-field segmentation preserves qualified command/control groups. Original Linux quit timeouts remain unexplained. Overall final matrix and negative controls are separate gates.'))
    status_path=docs/'final-series-status.json';status=load(status_path)
    project=next(p for p in status['projects'] if p['project']=='fff')
    require(not any(s['run']=='39575015155' for s in project['series']),'series already counted')
    project['series'].append(dict(run='39575015155',status='independently-verified',ordinary_observed=480,
        ordinary_passed=480,receipt_sha256=sha256(path)))
    for key,amount in dict(observed_ordinary_executions=480,observed_ordinary_passed=480,
        observed_public_calibration_executions=18,verified_calibration_executions=18,
        verified_ordinary_executions=480,verified_series_cells=2,verified_series_projects=1).items():status[key]+=amount
    import json
    status_path.write_text(json.dumps(status,indent=2,sort_keys=True)+'\n',encoding='utf-8',newline='\n')
    print('Verified both final fff cells and all eight retained native archives; global admission remains separate.')


if __name__=='__main__':main()
