"""Author/review and run declared Plop scenarios through ordinary public tests.

The primary spec is recorder-exported; these are the explicit technical-author
route for the remaining declared workflows. No target output generates or updates
an expectation. First failures and retries retain separate attempt identities.
"""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256

PACKAGE=ROOT/'docs/validation/runner-readiness-ten-project-pass/plop'


def state(path,kind='file',value=b''):
    result={'path':path,'kind':kind}
    if kind=='file':result['bytes_base64']=base64.b64encode(value).decode()
    elif kind=='entries':result['entries']=value
    return {'state':result}


def answer(value):return [{'text':value},{'key':'Enter'}] if value else [{'key':'Enter'}]


def cases():
    existing=b'reviewed existing bytes\n'
    collision=b'reviewed collision bytes\n'
    def flow(prompt,value,complete,exit_code,checks):
        return [{'expect':prompt},*answer(value),{'expect':complete},{'exit':exit_code},*checks]
    rows=[('N01','normal-artifact.json',None,None)]
    rows += [
      ('N02','normal-module.json','module',flow('Module name','atlas','2 files added',0,[
        state('modules/atlas/index.txt',value=b'module=atlas\n'),state('modules/atlas/nested/readme.txt',value=b'nested=atlas\n'),
        state('modules/atlas','entries',['index.txt','nested']),state('modules/atlas/nested','entries',['readme.txt'])])),
      ('N03','normal-route.json','route',flow('Route name','beta','registry.txt',0,[
        state('registry.txt',value=b'prefix=preserve\nROUTES\nroute=beta\nsuffix=preserve\n')])),
      ('N04','normal-version.json','version',flow('Replacement version','2','version.txt',0,[
        state('version.txt',value=b'prefix=preserve\nversion=2\nsuffix=preserve\n')])),
      ('N05','normal-decline-optional.json','optional',[
        {'expect':'Required artifact name'},*answer('alpha'),{'expect':'Include optional file?'},*answer('n'),
        {'expect':'required.txt'},{'exit':0},state('required.txt',value=b'required=alpha\n'),state('optional.txt','absent')]),
      ('N06','normal-preserve-existing.json','preserve',flow('Preserve existing file?','','[SKIPPED]',0,[state('existing.txt',value=existing)])),
      ('N07','normal-overwrite.json','overwrite',flow('Replace generated file?','y','existing.txt',0,[state('existing.txt',value=b'approved replacement\n'),state('collision.txt',value=collision)])),
      ('N08','normal-case-helpers.json','case-helpers',flow('Module identifier','Hello World','hello-world.txt',0,[state('case/hello-world.txt',value=b'class HelloWorld\n')])),
      ('E01','edge-validation-recovery.json','artifact',[
        {'expect':'Artifact name'},{'key':'Enter'},{'expect':'Enter a nonempty artifact name'},*answer('fixed'),
        {'expect':'fixed.txt'},{'exit':0},state('out/fixed.txt',value=b'name=fixed\n'),state('out','entries',['fixed.txt'])]),
      ('E02','edge-collision.json','collision',flow('Collision attempt name','alpha','File already exists',1,[state('existing.txt',value=existing),state('out','absent'),
        state('.','entries',['blocked','collision.txt','existing.txt','extended.cjs','plopfile.cjs','registry.txt','templates','unique-registry.txt','version.txt'])])),
      ('E03','edge-blocked-parent.json','blocked-parent',flow('Blocked output name','alpha','EEXIST',1,[state('blocked',value=b'reviewed regular ancestor\n')])),
      ('E04','edge-cancel-confirmation.json','optional',[
        {'expect':'Required artifact name'},*answer('cancelled'),{'expect':'Include optional file?'},{'key':'CtrlC'},
        {'exit':1 if os.name=='nt' else 130},state('required.txt','absent'),state('optional.txt','absent'),state('existing.txt',value=existing)]),
      ('E05','edge-resize-menu.json','',[
        {'expect':'Please choose a generator.'},{'resize':{'width':100,'height':16}},{'wait_for_redraw':True},
        {'resize':{'width':80,'height':12}},{'wait_for_redraw':True},{'key':'ArrowDown'},{'key':'Enter'},
        {'expect':'Route name'},*answer('resized'),{'expect':'registry.txt'},{'exit':0},
        state('registry.txt',value=b'prefix=preserve\nROUTES\nroute=resized\nsuffix=preserve\n'),state('modules','absent')]),
      ('E06','edge-long-choice.json','late-choice',[
        {'expect':'Choose a reviewed destination'},*[{'key':'ArrowDown'} for _ in range(17)],{'key':'Enter'},
        {'expect':'selection.txt'},{'exit':0},state('selection.txt',value=b'selected=item-18\n')]),
      ('E07','edge-unicode-spaced-path.json','artifact',flow('Artifact name','nested/caf\u00e9 notes','notes.txt',0,[
        state('out/nested/caf\u00e9 notes.txt',value='name=nested/caf\u00e9 notes\n'.encode()),state('existing.txt',value=existing)])),
      ('E08','edge-binary-crlf.json','raw-files',flow('Copy raw reviewed fixtures?','','2 files added',0,[
        state('raw-output/line-endings.txt',value=b'first\r\nsecond\r\n'),state('raw-output/binary.bin',value=b'\x00\x01\x02\xff\x00reviewed\n'),
        state('raw-output','entries',['line-endings.txt','binary.bin'])])),
      ('E09','edge-unique-dirty-append.json','route-unique',flow('Register the existing route once?','','unique-registry.txt',0,[
        state('unique-registry.txt',value=b'prefix=preserve\nROUTES\nroute=alpha\nsuffix=preserve\n')])),
      ('E10','edge-missing-template.json','missing-template',flow('Missing template artifact','alpha','ENOENT',1,[state('missing-output.txt','absent')])),
      ('E11','edge-partial-abort.json','partial-abort',flow('Partial generation name','delta','Aborted due to previous action failure',1,[
        state('partial.txt',value=b'first=delta\n'),state('collision.txt',value=collision),state('never-created.txt','absent')])),
      ('E12','edge-continue-after-error.json','continue-after-error',flow('Continue generation name','delta','continued.txt',1,[
        state('continued.txt',value=b'continued=delta\n'),state('collision.txt',value=collision)])),
    ]
    return rows


def author():
    declared=[]
    for identity,filename,generator,steps in cases():
        path=PACKAGE/filename
        if identity=='N01':
            if not path.is_file():raise RuntimeError('primary recorder export is missing')
        else:
            simple=generator=='artifact'
            args=['--no-progress']+([] if simple else ['--plopfile','extended.cjs'])+([generator] if generator else [])
            command=['cmd.exe','/d','/s','/c','plop '+' '.join(args)] if os.name=='nt' else ['plop',*args]
            spec=dict(version=3,name='Plop '+identity,command=command,
                      workspace=dict(fixture='fixture',home='temporary',temp='temporary'),
                      width=80,height=12 if identity=='E05' else 24,timeout_ms=10000,
                      run_timeout_ms=120000,max_output_bytes=2_000_000,steps=steps)
            data=(json.dumps(spec,indent=2,ensure_ascii=True)+'\n').encode()
            if path.exists():
                if path.read_bytes()!=data:raise RuntimeError('preserve/review existing contract before replacing '+filename)
            else:path.write_bytes(data)
        declared.append(dict(id=identity,spec=filename,class_='normal' if identity.startswith('N') else 'edge',spec_sha256=sha256(path),status='authored-not-qualified'))
    immutable_json(PACKAGE/'scenario-contracts-initial.json',dict(schema_version=1,contracts=declared,
        expected_bytes_source='reviewed synthetic templates/configuration, independently derived before execution',
        holdout_fault_selected=False))
    print('Authored technical-route contracts; primary remains recorder-exported. No execution credit.')


async def run(selected):
    suffix='.exe' if os.name=='nt' else ''
    runner=RAW/'bin'/('playtestr'+suffix)
    env=dict(os.environ);env['PATH']=str(RAW/'active/plop/bin')+os.pathsep+env['PATH']
    campaign=Campaign()
    for identity,filename,_,_ in cases():
        if selected and identity not in selected:continue
        path=PACKAGE/filename
        report_root=RAW/'plop'/'development-results';report_root.mkdir(parents=True,exist_ok=True)
        # Each run gets its own report path; reruns never overwrite first evidence.
        import uuid
        report=report_root/(identity+'-'+uuid.uuid4().hex+'.json')
        argv=[runner,'test','--artifacts-dir',str(report.with_suffix('').relative_to(ROOT)),
              '--report',str(report.relative_to(ROOT)),str(path.relative_to(ROOT))]
        result=await execute(argv,'plop','scenario-'+identity,cwd=ROOT,env=env,timeout=120,campaign=campaign)
        data=json.loads(report.read_text(encoding='utf-8'))['results'][0]
        if data['status']!='passed' or not data['cleanup']['confirmed_exited'] or not data['workspace']['cleaned']:
            raise RuntimeError('scenario cleanup/result did not qualify: '+identity)
        print(identity,'passed',result['id'],flush=True)


def main():
    global PACKAGE
    parser=argparse.ArgumentParser()
    parser.add_argument('--author',action='store_true')
    parser.add_argument('--case',action='append',default=[])
    parser.add_argument('--package',type=Path)
    args=parser.parse_args()
    if args.package:
        PACKAGE=args.package.resolve();PACKAGE.relative_to(ROOT)
    if args.author:author()
    else:asyncio.run(run(set(args.case)))


if __name__=='__main__':main()
