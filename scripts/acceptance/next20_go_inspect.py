"""Inspect actual native Go package inputs offline before compiling a target."""
import argparse
import asyncio
import json
from pathlib import Path
import shutil

from adversarial_process import execute
from next20_check import DOC,RAW,ROOT,NextCampaign
from readiness_build_rclone import environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--resume-inspection-after');parser.add_argument('--native-module-lock',action='store_true');args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project:raise ValueError('unsafe Go inspection project')
    package=DOC/project;target=RAW/'active'/project;source=target/'src'
    provenance=json.loads((package/'source-provenance.json').read_text());declaration=json.loads((package/'dependency-inspection-declaration.json').read_text());fetch=json.loads((target/'module-fetch.json').read_text())
    if args.native_module_lock:
        native=json.loads((package/'native-module-lock.json').read_text())
        if native['pin']!=provenance['pin']:raise ValueError('native module lock pin differs')
        declaration=dict(declaration,checksum_input=native['checksum_input'],checksum_sha256=native['checksum_sha256'])
    if declaration['pin']!=provenance['pin'] or sha256(fetch['compiler'])!=fetch['compiler_sha256']:raise ValueError('Go inspection source/compiler differs')
    for name,digest in provenance['files'].items():
        if sha256(source/name)!=digest:raise ValueError('pinned source changed before package inspection')
    root=target/'build-inputs';mod=root/'pinned.mod';sums=root/'pinned.sum'
    checksum=ROOT/declaration['checksum_input'];checksum.resolve(strict=True).relative_to((package if args.native_module_lock else RAW).resolve(strict=True))
    if sha256(checksum)!=declaration['checksum_sha256']:raise ValueError('declared review checksum bytes differ')
    if args.resume_inspection_after:
        eid=args.resume_inspection_after
        if len(eid)!=32 or any(c not in '0123456789abcdef' for c in eid):raise ValueError('invalid prior inspection attempt')
        failed=json.loads((RAW/'events'/(eid+'-finished.json')).read_text())
        if failed['project']!=project or failed['label']!='offline-native-package-source-inspection' or failed['category']!='exit_mismatch' or failed['exit_code']!=1:raise ValueError('explicit failed inspection required')
        planned=json.loads((root/'planned.json').read_text())
        if sha256(mod)!=planned['go_mod_sha256'] or sha256(mod)!=sha256(source/'go.mod') or sha256(sums)!=planned['go_sum_sha256'] or sha256(sums)!=declaration['checksum_sha256']:raise ValueError('existing inspection inputs changed')
        immutable_json(root/'resume-planned.json',dict(schema_version=1,failed_inspection=eid,original_plan_sha256=sha256(root/'planned.json'),change='Disable unrelated parent Git VCS stamping with declared -buildvcs=false; no target or module input change.'))
    else:
        root.mkdir(exist_ok=False);shutil.copyfile(source/'go.mod',mod);shutil.copyfile(checksum,sums)
    env=environment(target);env.update(GOENV='off',GOPROXY='off',GOSUMDB='off',GONOPROXY='none',GONOSUMDB='none')
    if not args.resume_inspection_after:immutable_json(root/'planned.json',dict(schema_version=1,declaration_sha256=sha256(package/'dependency-inspection-declaration.json'),go_mod_sha256=sha256(mod),go_sum_sha256=sha256(sums),target_code_built=False,target_code_executed=False,
        **(dict(native_module_lock_sha256=sha256(package/'native-module-lock.json')) if args.native_module_lock else {})))
    campaign=NextCampaign()
    verified=await execute([fetch['compiler'],'mod','verify','-modfile='+str(mod)],project,'offline-downloaded-module-integrity-check',cwd=source,env=env,timeout=60,campaign=campaign)
    if verified['output'].strip()!='all modules verified':raise ValueError('actual downloaded module integrity not verified')
    listed=await execute([fetch['compiler'],'list','-buildvcs=false','-mod=readonly','-modfile='+str(mod),'-deps','-json',declaration['main_package']],project,'offline-native-package-source-inspection',cwd=source,env=env,timeout=120,campaign=campaign)
    decoder=json.JSONDecoder();text=listed['output'];rows=[]
    while text.strip():
        row,end=decoder.raw_decode(text.lstrip());text=text.lstrip()[end:]
        if row.get('Error') or row.get('DepsErrors') or len(rows)>=1000:raise ValueError('incomplete Go package inspection')
        rows.append(row)
    inputs={};modules=set()
    for row in rows:
        if row.get('Standard'):continue
        directory=Path(row['Dir']);directory.resolve(strict=True).relative_to(target.resolve(strict=True))
        if row.get('CgoFiles'):raise ValueError('unreviewed cgo package')
        if row.get('Module'):modules.add((row['Module']['Path'],row['Module'].get('Version','primary-source')))
        for field in ['GoFiles','SFiles','SysoFiles','HFiles','EmbedFiles']:
            for name in row.get(field,[]):
                path=directory/name;path.resolve(strict=True).relative_to(target.resolve(strict=True));inputs[path.relative_to(target).as_posix()]=sha256(path)
    for name,digest in provenance['files'].items():
        if sha256(source/name)!=digest:raise ValueError('package inspection changed primary source')
    immutable_json(target/'native-package-inputs.json',dict(schema_version=1,packages=rows,actual_module_versions=[dict(path=n,version=v) for n,v in sorted(modules)],
        files=inputs,go_mod_sha256=sha256(mod),go_sum_sha256=sha256(sums),verify_attempt=verified['id'],list_attempt=listed['id'],target_built=False,target_executed=False,
        scope='Native package metadata and exact Go/assembly/embed inputs only,using declared external copy of original go.mod plus preserved checksum supplement. Offline,no build,go generate,dependency init or target execution. Standard library/SDK remains explicit compiler prerequisite.'))
    print('Inspected',len(rows),'native packages and',len(inputs),'owned source/embed/assembly inputs; no target build/execution.')


if __name__=='__main__':asyncio.run(main())
