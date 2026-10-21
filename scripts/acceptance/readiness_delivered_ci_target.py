"""Explicit reviewed real-target build/cleanup for the delivered CI journey."""
import argparse
import asyncio
import difflib
import os
from pathlib import Path
import platform
import shutil
import sys

from adversarial_process import execute
from readiness_build_rclone import environment
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--phase',choices=['prepare','finalize'],required=True)
    parser.add_argument('--mode',choices=['success','corruption','recovery'],required=True)
    args=parser.parse_args()
    require(platform.system()=='Linux' and platform.machine()=='x86_64','delivered CI journey declares Linux amd64 only')
    state=RAW/'delivered-ci-target';target=RAW/'active/rclone'
    artifact=ROOT/'artifacts/playtestr'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'
    selection=load(docs/'fault-selection.json');fault=next(f for f in selection['faults'] if f['id']=='F03')
    source=target/'src'/fault['path']
    async def run(label,argv,timeout=120,*,env=None,cwd=ROOT):
        return await execute(argv,'rclone','delivered-ci-'+label,timeout=timeout,env=env,cwd=cwd,campaign=Campaign())
    async def rebuild(label):
        build=load(target/'build.json');runtime=load(target/'runtime.json')
        binary=target/build['binary_relative_path']
        result=await run(label,[Path(runtime['go']),'build','-p','2','-mod=readonly','-trimpath',
            '-buildvcs=false','-ldflags','-s -w','-o',binary,'.'],300,env=environment(target),cwd=target/'src')
        return result,binary
    if args.phase=='prepare':
        state.mkdir(parents=True)
        immutable_json(state/'intent.json',dict(mode=args.mode,target_pin=load(docs/'source-review.json')['pin'],
            reviewed_fault='F03' if args.mode=='corruption' else None,
            scope='Real source-built Rclone and public exported N02 contract under the delivered workflow. Source-built runner129b7a4, not exact-archive matrix credit.'))
        operation=asyncio.create_task(run('reviewed-target-prepare',
            [sys.executable,ROOT/'scripts/acceptance/readiness_rclone_native_prepare.py'],1200))
        sizes=[]
        try:
            while not operation.done():
                size=await asyncio.to_thread(usage,RAW);sizes.append(size)
                require(size<=4*1024**3,'combined owned target/CI prerequisite storage stop')
                await asyncio.sleep(2)
            await operation
        finally:
            if not operation.done():
                operation.cancel()
                try:await operation
                except asyncio.CancelledError:pass
            immutable_json(state/'storage-observations.json',dict(observed_owned_raw_bytes=sizes,
                scope='Periodic logical bytes of target plus owned CI SDK/cache roots; not exact peak or an OS quota. Four-GiB stop retained.'))
        frozen=load(docs/'reviewed-contract-freeze.json')
        package=RAW/'rclone/host-contracts';shutil.copytree(docs/'contracts',package)
        require({p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}==frozen['all_package_inputs'],
                'delivered CI contract/fixture/snapshot differs')
        before=source.read_bytes()
        require(sha256(source)==fault['original_source_sha256'],'reviewed real writer changed')
        (state/'original-writer.go').write_bytes(before)
        build=load(target/'build.json');binary=target/build['binary_relative_path']
        require(sha256(binary)==build['binary_sha256'],'original compiled target differs')
        rebuilt=None
        if args.mode=='corruption':
            needle=fault['before'].encode();replacement=fault['after'].encode()
            require(before.count(needle)==1,'reviewed actual writer mutation not unique')
            source.write_bytes(before.replace(needle,replacement))
            require(sha256(source)==fault['mutated_source_sha256'],'actual writer mutation differs')
            (state/'actual-writer.patch').write_text(''.join(difflib.unified_diff(before.decode().splitlines(True),
                source.read_text(encoding='utf-8').splitlines(True),fromfile='a/'+fault['path'],tofile='b/'+fault['path'])),encoding='utf-8',newline='\n')
            rebuilt,binary=await rebuild('actual-corrupted-writer-build')
            require(sha256(binary)!=build['binary_sha256'],'actual writer mutation did not change executable')
        artifact.mkdir(parents=True,exist_ok=True)
        immutable_json(artifact/'target-build.json',dict(mode=args.mode,target_pin=build['pin'],
            pristine_binary_sha256=build['binary_sha256'],executed_binary_sha256=sha256(binary),
            source_path=fault['path'],pristine_source_sha256=fault['original_source_sha256'],
            executed_source_sha256=sha256(source),actual_mutation_build=rebuilt['id'] if rebuilt else None,
            suite='artifacts/runner-readiness-ten-project-pass/rclone/host-contracts/N02.json',
            suite_sha256=sha256(package/'N02.json'),freeze_sha256=sha256(docs/'reviewed-contract-freeze.json'),
            target_build_sha256=sha256(target/'build.json'),target_runtime_sha256=sha256(target/'runtime.json'),
            scope='Explicit build prerequisites for a generated CI integration control; zero final-archive ordinary/project credit.'))
        with Path(os.environ['GITHUB_PATH']).open('a',encoding='utf-8') as output:output.write(str(binary.parent)+'\n')
        print('Prepared actual pinned Rclone for delivered public workflow:',args.mode)
        return
    require(load(state/'intent.json')['mode']==args.mode,'cleanup mode differs from prepared target')
    before=load(artifact/'target-build.json');build=load(target/'build.json')
    report=artifact/'results.json'
    require(report.is_file(),'delivered workflow produced no public report; no success can be inferred')
    collected=RAW/'rclone/generated-ci';collected.mkdir()
    shutil.copyfile(report,collected/'results.json')
    require(sha256(report)==sha256(collected/'results.json'),'actual generated report copy differs')
    if args.mode=='corruption':
        require(sha256(source)==fault['mutated_source_sha256'],'actual failed writer changed before restoration')
        original=state/'original-writer.go'
        require(sha256(original)==fault['original_source_sha256'],'preserved original writer changed')
        source.write_bytes(original.read_bytes())
        _,binary=await rebuild('exact-original-writer-restore')
    else:binary=target/build['binary_relative_path']
    require(sha256(binary)==before['pristine_binary_sha256'] and sha256(source)==fault['original_source_sha256'],
            'real writer source or executable did not restore exactly')
    restored=sha256(binary)
    await run('owned-target-cleanup',[sys.executable,ROOT/'scripts/acceptance/readiness_cleanup_plop.py','--project','rclone'],240)
    require(not target.exists(),'owned Rclone source/runtime remains')
    destination=artifact/'build-evidence';destination.mkdir()
    selected=[]
    for folder in [RAW/'events',RAW/'identities',RAW/'core',RAW/'rclone',state]:
        selected.extend(p for p in folder.rglob('*') if p.is_file() and p.name!='source.tar.gz')
    total=0;files={}
    for path in selected:
        require(not path.is_symlink() and path.stat().st_size<=4*1024**2,'unsafe CI build evidence')
        total+=path.stat().st_size
        require(total<=32*1024**2 and len(files)<10000,'CI build evidence bound')
        name=path.relative_to(RAW).as_posix();copy=destination/name;copy.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(path,copy);require(sha256(path)==sha256(copy),'CI evidence copy differs');files[name]=sha256(copy)
    value=load(report);row=value['results'][0];red=args.mode=='corruption'
    expected=dict(total=1,passed=int(not red),failed=int(red),cancelled=0,not_run=0)
    valid=(value['summary']==expected and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned']
           and (not red or row['failure']['category']=='state_assertion_failure'))
    immutable_json(artifact/'target-finalized.json',dict(mode=args.mode,report_sha256=sha256(report),
        context_sha256=sha256(artifact/'context.json'),target_build_sha256=sha256(artifact/'target-build.json'),
        actual_expected_public_outcome=valid,restored_binary_sha256=restored,source_and_runtime_removed=True,
        evidence_files=files,evidence_bytes=total,final_archive_credit=0))
    require(valid,'delivered public outcome differs from declared success/fault/recovery control')
    print('Restored actual writer, verified public outcome and retained checked cleanup evidence:',args.mode)


if __name__=='__main__':asyncio.run(main())
