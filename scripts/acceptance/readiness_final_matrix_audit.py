"""Stream actual retained ten-project reports and challenge the global matrix."""
import copy
import hashlib
import json
import re
import tarfile

from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load

PROJECTS=['fff','hygen','rclone','plop','poetry','rubygems','edit','frogmouth','papis','vis']
WINDOWS={'rclone','rubygems','edit','frogmouth','papis'}
DOC=ROOT/'docs/validation/runner-readiness-ten-project-pass'


def selected_payloads(root,index,names):
    """Read bounded selected logical members from one self-contained archive."""
    wanted={}
    for name in names:
        record=index['files'][name];wanted.setdefault(record.get('member',name),[]).append(name)
    output={}
    with tarfile.open(root/'packets.tar.gz','r|gz') as archive:
        for member in archive:
            if member.name not in wanted:continue
            require(member.isfile() and member.size<=4*1024**2,'unsafe selected global audit payload')
            payload=archive.extractfile(member).read(4*1024**2+1)
            for name in wanted[member.name]:
                record=index['files'][name]
                require(len(payload)==record['bytes'] and hashlib.sha256(payload).hexdigest()==record['sha256'],'changed actual global audit payload')
                output[name]=json.loads(payload.decode('utf-8-sig'))
    require(set(output)==set(names),'global audit payload missing')
    return output


def report_model(value):
    require(len(value['results'])==1,'global audit requires individual public invocation reports')
    row=value['results'][0]
    return dict(version=value['runner_version'],invocation=row['invocation_id'],workspace=row['workspace']['id'],
        cleaned=row['workspace']['cleaned'],confirmed_exited=row['cleanup']['confirmed_exited'],status=row['status'],
        steps=[dict(status=s['status'],action=s['action'],state=s.get('state')) for s in row['steps']],
        category=row.get('failure',{}).get('category'))


def build_model():
    model=dict(projects=[],first_failures={})
    for project in PROJECTS:
        docs=DOC/project;series=load(docs/'final-series-verification.json');run=series['run']
        hosts=['linux','windows'] if project in WINDOWS else ['linux','macos']
        row=dict(project=project,run=run,cells=[])
        for host in hosts:
            matching=[p for p in docs.glob('final*.json') if sha256(p)==series['audits'][host]]
            require(len(matching)==1,'missing or ambiguous independent final cell audit')
            audit=load(matching[0]);suffix={'linux':'Linux','macos':'macOS','windows':'Windows'}[host]
            prefix='native/'+run+'/final-'+project+'-'+suffix+'/'
            chosen=[]
            for archive in series['retained_archives']:
                root=RAW/project/('retained-native-v'+str(archive['generation']))
                require(sha256(root/'index.json')==archive['index_sha256'],'changed retained index')
                index=load(root/'index.json',maximum=4*1024**2)
                if any(n.startswith(prefix) for n in index['files']):chosen.append((root,index,archive))
            require(len(chosen)==1,'missing or duplicated final native packet')
            root,index,archive=chosen[0];removed=load(root/'expanded-removed.json')
            require(sha256(root/'packets.tar.gz')==archive['archive_sha256']==index['archive_sha256']
                and removed['index_sha256']==archive['index_sha256'] and removed['all_expanded_removed']
                and all(not (RAW/'native'/r).exists() for r in index['runs']),'unsafe/incomplete native packet retention/removal')
            verify(root/'packets.tar.gz',index['files'])
            def inside(name):return name.startswith(prefix)
            names=[n for n,v in index['files'].items() if inside(n) and (
                '/final-series/' in n and n.endswith(('.report.json','.planned.json','/prepared.json'))
                or re.search(r'/faults/[0-9a-f]{32}/F[0-9]{2}-(?:baseline|mutated|restored)\.json$',n)
                or v['sha256'] in {audit['source_fault_summary_sha256'],audit['cleanup_receipt_sha256']})]
            payloads=selected_payloads(root,index,names)
            fault_paths=[n for n in names if index['files'][n]['sha256']==audit['source_fault_summary_sha256']]
            cleanup_paths=[n for n in names if index['files'][n]['sha256']==audit['cleanup_receipt_sha256']]
            require(len(fault_paths)==len(cleanup_paths)==1,'missing actual source faults/cleanup')
            faults=payloads[fault_paths[0]];cleanup=payloads[cleanup_paths[0]]
            ordinary=[];seen_reports=set()
            for observation in audit['observations']:
                matches=[n for n in names if n.endswith('.report.json') and index['files'][n]['sha256']==observation['report_sha256']]
                require(len(matches)==1 and matches[0] not in seen_reports,'missing or duplicated actual ordinary report')
                name=matches[0];seen_reports.add(name);base=name.removesuffix('.report.json');planned=payloads[base+'.planned.json']
                batch_root=base.rsplit('/',1)[0];prepared=payloads[batch_root+'/prepared.json'];spec=observation['spec']
                contract_path=batch_root+'/'+prepared['batch']['package_directory']+'/'+spec
                require(contract_path in index['files'],'actual executed contract missing')
                result=report_model(payloads[name]);require(result['invocation']==observation['invocation_id'],'changed actual invocation')
                result.update(spec=spec,batch=planned['batch'],contract_actual_sha256=index['files'][contract_path]['sha256'],
                    contract_planned_sha256=planned['spec_sha256'],runner_sha256=planned['runner_sha256'],archive_sha256=planned['archive_sha256'])
                ordinary.append(result)
            calibration=[];normalized_faults=[]
            for fault in faults['faults']:
                category=fault.get('category',fault.get('rejection'))
                if category is None:
                    require(project in {'poetry','rubygems'},'unknown historical fault receipt schema')
                    # Historical receipts omit category: changed prompt,
                    # wrong exit branch, then wrong saved bytes respectively.
                    category={'F01':'assertion_timeout','F02':'unexpected_exit','F03':'state_assertion_failure'}[fault['id']]
                restored=fault.get('restored_exact')
                if project=='plop':
                    review=load(docs/'source-review.json')
                    restored=fault['cleanup_confirmed'] and fault['restored_source_sha256']==review['reviewed_inputs'][fault['source']]
                normalized_faults.append(dict(id=fault['id'],restored_exact=restored))
                for phase in ['baseline','mutated','restored']:
                    name=fault_paths[0].removesuffix('summary.json')+fault['id']+'-'+phase+'.json'
                    require(name in payloads,'missing actual fault/restoration report')
                    result=report_model(payloads[name]);result.update(fault=fault['id'],phase=phase,expected_category=category)
                    calibration.append(result)
            row['cells'].append(dict(host=host,runner_sha256=audit['runner_sha256'],archive_sha256=audit['archive_sha256'],
                ordinary=ordinary,calibration=calibration,faults=normalized_faults,
                cleanup=cleanup,audit_sha256=series['audits'][host],archive_index_sha256=archive['index_sha256']))
        model['projects'].append(row)
        print('Streamed actual complete final matrix evidence:',project,flush=True)
    for project,name in [('fff','final-first-series-rejected.json'),('hygen','final-first-series-disposition.json'),('frogmouth','final-first-series-disposition.json')]:
        path=DOC/project/name
        require(path.is_file(),'missing original failed/unqualified series disposition')
        model['first_failures'][project]=dict(path=path.relative_to(ROOT).as_posix(),sha256=sha256(path))
    return model


def validate(model,candidate):
    projects=model['projects']
    require(len(projects)==10 and {p['project'] for p in projects}==set(PROJECTS),'duplicated/missing global project')
    require(set(model['first_failures'])=={'fff','hygen','frogmouth'},'missing original first failure')
    for record in model['first_failures'].values():require(sha256(ROOT/record['path'])==record['sha256'],'changed original first failure')
    invocations=set();ordinary_total=calibration_total=0
    def outcome(row,expected):
        require(row['version']==candidate['version'],'wrong final report binary version')
        require(row['status']==expected and row['cleaned'] and row['confirmed_exited'],'incomplete/unsafe actual cleanup')
        require(row['invocation']==row['workspace'] and row['invocation'] not in invocations,'duplicated/cross-execution invocation')
        invocations.add(row['invocation'])
        if expected=='passed':require(all(s['status']=='passed' for s in row['steps']),'missing positive step')
        for step in row['steps']:
            if step['state']:require(step['state']['invocation_id']==row['invocation'] and step['state']['workspace_id']==row['workspace'],'state from another invocation')
    for project in projects:
        require(project['run'].isascii() and project['run'].isdecimal(),'missing actual native run')
        hosts={'linux','windows'} if project['project'] in WINDOWS else {'linux','macos'}
        require(len(project['cells'])==2 and {c['host'] for c in project['cells']}==hosts,'missing required native host')
        expected_faults=4 if project['project']=='papis' else 3
        for cell in project['cells']:
            candidate_cell=next(c for c in candidate['cells'] if c['host']==('darwin' if cell['host']=='macos' else cell['host']))
            require(cell['runner_sha256']==candidate_cell['binary_sha256'] and cell['archive_sha256']==candidate_cell['archive_sha256'],'wrong final archive/binary')
            cleanup=cell['cleanup'];require(cleanup['removed'] and cleanup['owned_relative_path']=='active/'+project['project'],'unsafe native source/runtime cleanup')
            require(len(cell['ordinary'])==240 and {r['batch'] for r in cell['ordinary']}==set(range(12)),'partial ordinary host series')
            cases={r['spec'] for r in cell['ordinary']};require(len(cases)==20,'missing canonical scenario')
            for batch in range(12):require(len([r for r in cell['ordinary'] if r['batch']==batch])==20
                and {r['spec'] for r in cell['ordinary'] if r['batch']==batch}==cases,'partial scenario repetition')
            for row in cell['ordinary']:
                require(row['runner_sha256']==cell['runner_sha256'] and row['archive_sha256']==cell['archive_sha256'],'wrong actual planned runner')
                require(row['contract_actual_sha256']==row['contract_planned_sha256'],'mismatched executed contract')
                outcome(row,'passed')
            require(len(cell['faults'])==expected_faults and all(f['restored_exact'] for f in cell['faults']),'absent fault restoration')
            require(len(cell['calibration'])==expected_faults*3,'missing public source-fault calibration')
            for fault in cell['faults']:
                rows=[r for r in cell['calibration'] if r['fault']==fault['id']]
                require(len(rows)==3 and {r['phase'] for r in rows}=={'baseline','mutated','restored'},'missing fault baseline/mutation/restoration')
                for row in rows:
                    outcome(row,'failed' if row['phase']=='mutated' else 'passed')
                    if row['phase']=='mutated':require(row['category']==row['expected_category'],
                        'wrong actual source-fault diagnosis: '+project['project']+' '+cell['host']+' '+row['fault']+' '+str(row['category'])+' != '+str(row['expected_category']))
            ordinary_total+=len(cell['ordinary']);calibration_total+=len(cell['calibration'])
    require((ordinary_total,calibration_total)==(4800,186),'global denominator differs')
    return dict(projects=10,native_cells=20,ordinary_executions=ordinary_total,calibration_executions=calibration_total)


def main():
    candidate=load(DOC/'migration-candidate-freeze.json');model=build_model();positive=validate(model,candidate)
    root=RAW/'final-matrix-audit';root.mkdir(exist_ok=False)
    immutable_json(root/'actual-model.json',model)
    controls=[]
    changes=[('missing-run',lambda m:m['projects'][0].update(run='')),
        ('wrong-binary',lambda m:m['projects'][0]['cells'][0].update(runner_sha256='0'*64)),
        ('duplicated-project',lambda m:m['projects'].__setitem__(1,copy.deepcopy(m['projects'][0]))),
        ('mismatched-contract',lambda m:m['projects'][0]['cells'][0]['ordinary'][0].update(contract_actual_sha256='0'*64)),
        ('absent-fault-restoration',lambda m:m['projects'][0]['cells'][0]['faults'][0].update(restored_exact=False)),
        ('cross-execution-state',lambda m:next(s['state'] for p in m['projects'] for c in p['cells'] for r in c['ordinary'] for s in r['steps'] if s['state']).update(invocation_id='0'*32)),
        ('partial-host-series',lambda m:m['projects'][0]['cells'][0]['ordinary'].pop()),
        ('missing-first-failure',lambda m:m['first_failures'].pop('fff')),
        ('unsafe-native-cleanup',lambda m:m['projects'][0]['cells'][0]['cleanup'].update(owned_relative_path='../outside')),
        ('unconfirmed-process-cleanup',lambda m:m['projects'][0]['cells'][0]['ordinary'][0].update(confirmed_exited=False)),
        ('missing-native-host',lambda m:m['projects'][0]['cells'].pop())]
    for name,change in changes:
        bad=copy.deepcopy(model);change(bad)
        try:validate(bad,candidate)
        except RuntimeError as error:controls.append(dict(control=name,refused=True,reason=str(error)))
        else:raise RuntimeError('global auditor accepted deliberately invalid evidence: '+name)
    require(validate(model,candidate)==positive,'actual global model changed during controls')
    receipt=dict(**positive,controls=controls,actual_model_sha256=sha256(root/'actual-model.json'),
        candidate_freeze_sha256=sha256(DOC/'migration-candidate-freeze.json'),
        scope='Actual retained complete ten-project final report bytes, captured launch plans, native source-fault/restoration reports and cleanup rechecked from self-contained verified packet archives. Eleven independent synthetic semantic corruptions of that complete actual model refused; actual model restored unchanged. Individual cell audits bind full source/runtime/fixture identities. Original failures remain separate. Old-project final rechecks and final packaging/documentation gates remain separate; no overall admission from this audit.',
        overall_final_admissions=0,paid_launch_admissions=0)
    immutable_json(root/'verified.json',receipt);immutable_json(DOC/'final-matrix-audit.json',receipt)
    print('Actual ten-project global matrix and eleven negative controls verified; overall gates remain separate.')


if __name__=='__main__':main()
