"""Bind fresh original migration audits to verified self-contained retention."""
import argparse
import json

from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=['cookiecutter','copier','lf','superfile','helix','glow'],required=True)
    parser.add_argument('--run',required=True);parser.add_argument('--generations',type=int,required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal() and 1<=args.generations<=100,'invalid native retention scope')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass';project=docs/'old-migration'/args.project
    hosts=['linux','macos'] if args.project in {'superfile','glow'} else ['linux','windows']
    candidate=load(docs/'migration-candidate-freeze.json');audits={};values={}
    for host in hosts:
        path=project/('final-verified-'+host+'.json');value=load(path)
        cell=next(c for c in candidate['cells'] if c['host']==('darwin' if host=='macos' else host))
        require(value['project']==args.project and value['host']==host and value['run']==args.run
            and value['runner_sha256']==cell['binary_sha256'] and value['provisional_archive_sha256']==cell['archive_sha256'],
            'incomplete exact-archive final migration audit')
        audits[host]=sha256(path);values[host]=value
    require(len({v['scenarios'] for v in values.values()})==1,'native original case denominator differs')
    indices=[];archives=[];name='old-'+args.project
    for generation in range(1,args.generations+1):
        root=RAW/name/('retained-native-v'+str(generation));index=load(root/'index.json',maximum=4*1024**2)
        checked=load(root/'verified.json');removed=load(root/'expanded-removed.json')
        require(sha256(root/'index.json')==checked['index_sha256']==removed['index_sha256']
            and sha256(root/'packets.tar.gz')==index['archive_sha256']==checked['archive_sha256']==removed['archive_sha256']
            and removed['all_expanded_removed'] and removed['removed_runs']==index['runs'],'historical/final retention or removal differs')
        verify(root/'packets.tar.gz',index['files'])
        for selected in index['selected_restore']:require(sha256(root/'selected-restore'/selected)==index['files'][selected]['sha256'],'selected restore differs')
        indices.append(index);archives.append(dict(generation=generation,index_sha256=sha256(root/'index.json'),archive_sha256=index['archive_sha256']))
    for host,value in values.items():
        suffix={'linux':'Linux','windows':'Windows','macos':'macOS'}[host]
        prefix='native/'+args.run+'/'+name+'-'+suffix+'/'
        for key in ['full_suite_sha256','corruption_sha256','cleanup_sha256']:
            require(any(n.startswith(prefix) and r['sha256']==value[key] for index in indices for n,r in index['files'].items()),'audited actual final migration evidence not retained')
    receipt=dict(project=args.project,run=args.run,audits=audits,canonical_scenarios=next(iter(values.values()))['scenarios'],
        primary_executions=sum(v['scenarios'] for v in values.values()),calibration_executions=6,native_cells=2,retained_archives=archives,
        scope='Fresh exact rc.5 native original cases, actual saved corruption/legacy false-green/recovery and checked cleanup independently audited; complete historical/final packet inventories reverified and expanded packets removed. Previous migration counts are not incremented.',
        new_project_credit=0,final_runner_credit=0,paid_launch_admissions=0)
    path=project/'final-archive-verification.json';immutable_json(path,receipt)
    status_path=docs/'final-old-migration-status.json'
    status=load(status_path) if status_path.exists() else dict(projects=[],rechecked_projects=0,canonical_scenarios=0,primary_executions=0,calibration_executions=0,native_cells=0)
    require(not any(p['project']==args.project for p in status['projects']),'final old project already counted')
    status['projects'].append(dict(project=args.project,receipt_sha256=sha256(path)))
    status['rechecked_projects']+=1
    for key in ['canonical_scenarios','primary_executions','calibration_executions','native_cells']:status[key]+=receipt[key]
    status_path.write_text(json.dumps(status,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Verified exact archive original migration and complete retention:',args.project)


if __name__=='__main__':main()
