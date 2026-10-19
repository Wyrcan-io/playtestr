"""Author declared real Rclone config journeys and independently check saved bytes."""
import argparse
import asyncio
import base64
import json
import os
import platform
import uuid

from adversarial_process import execute
from readiness_build_rclone import environment
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_cases import entry_sets, plan_hash, require, serialise, text
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


def rows(host=None):
    if host is None:require(platform.system() in {'Linux','Windows'},'undeclared Rclone native platform')
    host=host or ('windows' if os.name=='nt' else 'linux')
    require(host in {'linux','windows'},'undeclared Rclone host')
    newline='\r\n' if host=='windows' else '\n'
    def config(sections):
        return ''.join('['+name+']'+newline+''.join(k+' = '+v+newline for k,v in values)+newline
                       for name,values in sections).encode()
    def line(value):return text(value+'\r')
    def contextual(anchor,expected):
        # The console accepts one-line /expect controls. Its public strict JSON
        # editor supports contextual multiline expectations; reconstruct the
        # edited prefix before submitting any further target input.
        return {'anchor':anchor,'contextual_expect':expected}
    def start(existing=False):return ['/expect '+('Current remotes:' if existing else 'No remotes found, make a new one?')]
    def new(name,existing=False,pre=()):
        return start(existing)+[line('n'),'/expect name>',*pre,line(name),'/expect Storage>']
    def local_options(name,answer='y'):
        return (['/expect nounc>',line('')] if host=='windows' else [])+[
            '/expect Edit advanced config?',line('n'),'/expect Keep this "'+name+'" remote?',line(answer)]
    def alias_options(name,path='.',answer='y',previous=None):
        prompt=('/expect remote>' if previous is None else contextual(
            'Enter a value of type string. Press Enter for the default ('+previous+').',
            'Enter a value of type string. Press Enter for the default ('+previous+').\nremote>'))
        advanced=('/expect Edit advanced config?' if previous is None else contextual(
            'remote> '+path,'remote> '+path+'\n\nEdit advanced config?\ny) Yes\nn) No (default)\ny/n>'))
        keep=('/expect Keep this "'+name+'" remote?' if previous is None else contextual(
            '- remote: '+path,'Configuration complete.\nOptions:\n- type: alias\n- remote: '+path+
            '\nKeep this "'+name+'" remote?\ny) Yes this is OK (default)\ne) Edit this remote\nd) Delete this remote\ny/e/d>'))
        return [prompt,line(path),advanced,line('n'),keep,line(answer)]
    def finish(nonempty=True,anchor=None):
        return [anchor or '/expect '+('Current remotes:' if nonempty else 'No remotes found, make a new one?'),
                '/snapshot final.txt',line('q'),'/exit 0']
    local=[('type','local')]
    alias=lambda value:[('type','alias'),('remote',value)]
    seed=config([('seed',local)])
    def row(identity,title,actions,expected,initial=b'',extra=None,initial_config=True,directories=(),initial_absent=()):
        expanded=[];steps=0
        for action in actions:
            if isinstance(action,dict):
                steps+=1
                expanded.extend(['/expect '+action['anchor'],
                    '/replace '+str(steps)+' '+json.dumps({'expect':action['contextual_expect']},ensure_ascii=True),
                    '/rerecord '+str(steps)])
            else:
                expanded.append(action)
                steps+=1
        actions=expanded
        files={**({'rclone.conf':initial} if initial_config else {}),
               'sentinel.bin':b'preserve\x00existing\r\n',**(extra or {})}
        saved={**files}
        if expected is not None:saved['rclone.conf']=expected
        return dict(id=identity,title=title,kind='normal' if identity.startswith('N') else 'edge',
                    user_risk=title,files=files,expected=saved,missing=[],actions=actions,
                    directories=list(directories),initial_absent=list(initial_absent),entry_sets=entry_sets(saved),host=host,
                    checkpoint='Exact saved state after the declared natural exit; initial absence, where declared, is before input.',
                    readiness='Named rendered prompts before submitted lines, then a specific result or exact expected failure.',
                    budgets=dict(step_ms=10000,run_ms=120000,harness_seconds=180),
                    exclusion='No cloud credentials, authentication, remote access, mounting, server operation or encryption.')
    rename=start(True)+[line('r'),'/expect remote>',line('seed'),'/expect name>',line('renamed')]+finish(anchor='/expect '+'renamed'.ljust(20)+' local')
    copy=start(True)+[line('c'),'/expect remote>',line('seed'),'/expect name>',line('backup')]+finish(anchor='/expect '+'backup'.ljust(20)+' local')
    delete=start(True)+[line('d'),'/expect remote>',line('seed')]+finish(False)
    edit_alias=start(True)+[line('e'),'/expect remote>',line('seed')]+alias_options('seed','new',previous='old')+finish()
    main_after_keep='y/e/d> y\n\nCurrent remotes:\n\nName                 Type\n====                 ====\nseed                 local\n\ne) Edit existing remote\nn) New remote\nd) Delete remote\nr) Rename remote\nc) Copy remote\ns) Set configuration password\nq) Quit config\ne/n/d/r/c/s/q>'
    edit_local=start(True)+[line('e'),'/expect remote>',line('seed')]+local_options('seed')+finish(
        anchor=contextual('y/e/d> y',main_after_keep))
    review_alias=new('demo')+[line('alias')]+alias_options('demo','old','e')+alias_options('demo','reviewed',previous='old')+finish()
    missing_config=new('demo')
    missing_config.insert(1,'/missing rclone.conf')
    drive_name='reviewed' if host=='windows' else 'z'
    drive_prefix=[line('z'),'/expect confused with a drive letter.'] if host=='windows' else []
    resize=start()+[line('n'),'/expect name>',text('caf\u00e9 \u96ea'),'/expect caf\u00e9 \u96ea',
        '/resize 70 20',*(['/redraw'] if host=='windows' else []),text('A'),'/expect caf\u00e9 \u96eaA',
        '/resize 100 28',*(['/redraw'] if host=='windows' else []),text('B'),
        '/expect caf\u00e9 \u96eaAB',line(''),'/expect Storage>',line('alias')]+alias_options('caf\u00e9 \u96eaAB')+finish()
    return [
        row('N01','create a local storage configuration',new('demo')+[line('local')]+local_options('demo')+finish(),
            config([('demo',local)])),
        row('N02','create an alias for the synthetic local directory',new('demo')+[line('alias')]+alias_options('demo')+finish(),
            config([('demo',alias('.'))])),
        row('N03','rename an existing local configuration',rename,config([('renamed',local)]),seed),
        row('N04','copy an existing local configuration',copy,config([('seed',local),('backup',local)]),seed),
        row('N05','delete the last configured remote',delete,b'',seed),
        row('N06','change the local path of an existing alias',edit_alias,config([('seed',alias('new'))]),
            config([('seed',alias('old'))]),extra={'old/keep.txt':b'old\n','new/keep.txt':b'new\n'}),
        row('N07','review existing local settings without losing a nondefault option',edit_local,
            config([('seed',local+[('nounc','true')])]),config([('seed',local+[('nounc','true')])])),
        row('N08','correct a new alias during the review loop before accepting',review_alias,config([('demo',alias('reviewed'))])),
        row('E01','create a missing config file after the initial absence checkpoint',
            missing_config+[line('alias')]+alias_options('demo')+finish(),
            config([('demo',alias('.'))]),initial_config=False,initial_absent=['rclone.conf']),
        row('E02','reject forbidden colon syntax in a configuration name',
            new('demo',pre=[line('bad:name'),'/expect config name contains invalid characters'])+[line('alias')]+alias_options('demo')+finish(),
            config([('demo',alias('.'))])),
        row('E03','reject a duplicate name and preserve the existing configuration',
            new('demo',True,pre=[line('seed'),'/expect Remote "seed" already exists.'])+[line('alias')]+alias_options('demo')+finish(),
            config([('seed',local),('demo',alias('.'))]),seed),
        row('E04','respect the native single-letter drive ambiguity policy',
            new(drive_name,pre=drive_prefix)+[line('alias')]+alias_options(drive_name)+finish(),
            config([(drive_name,alias('.'))])),
        row('E05','preserve supported Unicode letters in the configuration name',
            new('caf\u00e9 \u96ea')+[line('alias')]+alias_options('caf\u00e9 \u96ea')+finish(),config([('caf\u00e9 \u96ea',alias('.'))])),
        row('E06','trim outer input whitespace while preserving spaces within the name',
            new('  reviewed local  ')+[line('alias')]+alias_options('reviewed local')+finish(),config([('reviewed local',alias('.'))])),
        row('E07','reject an empty required storage selection',
            new('demo')+[line(''),'/expect This value is required and it has no default.',line('alias')]+alias_options('demo')+finish(),
            config([('demo',alias('.'))])),
        row('E08','reject an out-of-range numeric storage selection',
            new('demo')+[line('99999'),'/expect No choices with this number.',line('alias')]+alias_options('demo')+finish(),
            config([('demo',alias('.'))])),
        row('E09','reject a directory used as config while preserving its contents',
            ['/expect Failed to load config file','/exit 1'],None,initial_config=False,
            extra={'rclone.conf/keep.bin':b'preserve directory child\x00\r\n'},directories=['rclone.conf']),
        row('E10','discard a proposed remote without changing a pre-existing configuration',
            new('demo',True)+[line('alias')]+alias_options('demo',answer='d')+finish(),seed,seed),
        row('E11','preserve a spaced Unicode local alias path and existing binary file',
            new('demo')+[line('alias')]+alias_options('demo','caf\u00e9 \u96ea')+finish(),
            config([('demo',alias('caf\u00e9 \u96ea'))]),extra={'caf\u00e9 \u96ea/keep.bin':b'preserve\x00\r\n'}),
        row('E12','resize active Unicode name entry and require fresh post-resize markers',resize,
            config([('caf\u00e9 \u96eaAB',alias('.'))])),
    ]


async def author(row):
    binary,frozen,cell=runner()
    target=RAW/'active/rclone'
    env=environment(target)
    env['PATH']=str(target/'bin')+os.pathsep+env.get('PATH','')
    root=RAW/'rclone/authoring'/row['id']/uuid.uuid4().hex
    fixture=root/'fixture'
    fixture.mkdir(parents=True)
    for name,value in row['files'].items():
        path=fixture/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(value)
    immutable_json(root/'declared-plan.json',serialise(row))
    actions=[]
    for action in row['actions']:
        actions.append(action)
        if action.startswith('/expect ') and row['id']!='E09':actions.append('/screen')
    controls=[*actions,*['/file '+name for name in sorted(row['expected'])],
              *['/directory '+name for name in row['directories']],
              *['/entries '+name for name in sorted(row['entry_sets'])],'/review','/replay','/save']
    spec=root/'spec.json'
    immutable_json(root/'requested-controls.json',dict(controls=controls,
        policy='Inspect the actual rendered screen immediately after each named prompt/result before further input; wrong-type startup uses its stable error/exit instead. No retry or oracle supplied.'))
    captured=await execute([binary,'record','--output',spec.relative_to(ROOT),'--fixture','fixture',
        '--temporary-home','--temporary-temp','--width','100','--height','28','--timeout-ms','10000',
        '--run-timeout-ms','120000','--env','TERM=xterm-256color','--','rclone','--config','rclone.conf','config'],
        'rclone',row['id']+'-public-author-review-replay',input='\n'.join(controls)+'\n',
        env=env,timeout=180,campaign=Campaign())
    contract=load(spec)
    states=[s['state'] for s in contract['steps'] if 'state' in s]
    actual={s['path']:base64.b64decode(s['bytes_base64']) for s in states if s['kind']=='file'}
    require(actual==row['expected'],row['id']+' independent saved-file oracle rejects export')
    require({s['path'] for s in states if s['kind']=='directory'}==set(row['directories']),
            'expected directory type oracle differs')
    absences=[(i,s['state']['path']) for i,s in enumerate(contract['steps']) if s.get('state',{}).get('kind')=='absent']
    require([name for _,name in absences]==row['initial_absent'],'initial absence oracle differs')
    if absences:
        first_input=next(i for i,s in enumerate(contract['steps']) if any(k in s for k in ['text','key','resize']))
        require(all(i<first_input for i,_ in absences),'absence proof occurs after mutation input')
    entries={s['path']:s['entries'] for s in states if s['kind']=='entries'}
    require({n:sorted(v) for n,v in entries.items()}==row['entry_sets']
            and all(len(v)==len(set(v)) for v in entries.values()),'complete directory entry oracle differs')
    report=root/'ordinary-result.json'
    ordinary=await execute([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
        (root/'evidence').relative_to(ROOT),spec.relative_to(ROOT)],'rclone',row['id']+'-ordinary-authored-contract',
        env=env,timeout=130,campaign=Campaign())
    outcome=load(report)
    result=outcome['results'][0]
    require(outcome['runner_version']==frozen['version'] and result['status']=='passed'
            and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'],'ordinary outcome/cleanup differs')
    for step in result['steps']:
        require(step['status']=='passed','ordinary step incomplete')
        if 'state' in step:
            require(step['state']['invocation_id']==result['invocation_id']
                    and step['state']['workspace_id']==result['workspace']['id'],'cross-execution state proof')
    immutable_json(RAW/'rclone/approved'/(row['id']+'.json'),dict(case=row['id'],plan_sha256=plan_hash(row),
        spec=spec.relative_to(ROOT).as_posix(),spec_sha256=sha256(spec),capture_attempt=captured['id'],ordinary_attempt=ordinary['id'],
        report_sha256=sha256(report),runner_sha256=cell['binary_sha256'],provisional_archive_sha256=cell['archive_sha256'],
        independently_checked=True))
    print(row['id'],'publicly authored, independently checked and ordinary replay passed',flush=True)


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--case',action='append')
    parser.add_argument('--declare-only',action='store_true')
    parser.add_argument('--declaration-version',type=int,default=1)
    args=parser.parse_args()
    if args.declare_only:
        require(1<=args.declaration_version<=100,'invalid declaration revision')
        filename='scenario-declaration'+('' if args.declaration_version==1 else '-v'+str(args.declaration_version))+'.json'
        immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'/filename,
            dict(executed=False,native_profiles={h:[serialise(r) for r in rows(h)] for h in ['linux','windows']},
                 normal_cases=8,edge_cases=12,source_faults_selected=False,
                 combined_risks={'E03':['duplicate name','pre-existing config preservation'],
                    'E09':['wrong resource type','expected nonzero exit','preserved nested binary entries'],
                    'E10':['cancel after proposed changes','pre-existing configuration preservation'],
                    'E11':['Unicode local path value','binary preservation','complete directory entries'],
                    'E12':['active Unicode input','two resizes','fresh readiness markers','exact saved name']},
                 revision=args.declaration_version,
                 scope='Synthetic local and alias config wizard; no cloud, credentials, mounts or server.',
                 native_variants='Windows basic nounc prompt, native CRLF writer and drive-letter rejection; Linux LF and single-letter acceptance. Declared before authoring.'))
        print('Declared twenty meaningful workflows with explicit native variants; no execution credit.')
        return
    declared=rows()
    require(len(declared)==20 and sum(r['kind']=='normal' for r in declared)==8,'wrong meaningful scenario boundary')
    selected=[r for r in declared if not args.case or r['id'] in args.case]
    require(not args.case or {r['id'] for r in selected}==set(args.case),'unknown case')
    batch=RAW/'rclone/authoring-batches'/uuid.uuid4().hex
    immutable_json(batch/'declared.json',dict(rows=[serialise(r) for r in selected],executed=False))
    failures=[];completed=[]
    for row in selected:
        approved=RAW/'rclone/approved'/(row['id']+'.json')
        if approved.exists():
            require(load(approved)['plan_sha256']==plan_hash(row),'approved plan changed; explicit revision required')
            completed.append(row['id'])
            continue
        try:
            await author(row)
            completed.append(row['id'])
        except Exception as error:
            failures.append(dict(case=row['id'],type=type(error).__name__,message=str(error)))
            print(row['id'],'failed; original evidence retained:',error,flush=True)
            if len(failures)>=3:break
    immutable_json(batch/'outcomes.json',dict(selected=len(selected),completed=completed,failures=failures,
        not_run=[r['id'] for r in selected if r['id'] not in completed and r['id'] not in {f['case'] for f in failures}]))
    require(not failures,'Some public authoring failed; inspect original evidence before revision')


if __name__=='__main__':asyncio.run(main())
