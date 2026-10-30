"""Compile a reviewed Go target and the bounded stdout-capture fixture offline."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import time

from adversarial_process import execute
from next20_check import DOC,RAW,ROOT,NextCampaign
from readiness_build_plop import usage
from readiness_build_rclone import environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project:raise ValueError('unsafe Go build project')
    package=DOC/project;target=RAW/'active'/project;source=target/'src'
    review=json.loads((package/'dependency-source-review-declaration.json').read_text());approved=json.loads((target/'dependency-fetch-review.json').read_text())
    catalog=json.loads((target/'dependency-source-catalog.json').read_text());fetch=json.loads((target/'module-fetch.json').read_text());inputs=json.loads((target/'native-package-inputs.json').read_text())
    if not review['approved_for_native_build'] or not approved['approved'] or approved['source_catalog_sha256']!=sha256(target/'dependency-source-catalog.json') or approved['source_review_declaration_sha256']!=sha256(package/'dependency-source-review-declaration.json'):raise ValueError('unreviewed native build source')
    if (target/'build.json').exists():raise ValueError('preserve completed native build')
    def verify():
        for name,digest in catalog['files'].items():
            if sha256(target/name)!=digest:raise ValueError('reviewed target/module code changed')
        if sha256(fetch['compiler'])!=fetch['compiler_sha256']:raise ValueError('compiler prerequisite changed')
        for name,expected in [('pinned.mod',inputs['go_mod_sha256']),('pinned.sum',inputs['go_sum_sha256'])]:
            if sha256(target/'build-inputs'/name)!=expected:raise ValueError('reviewed effective module input changed')
        if sha256(ROOT/review['capture_helper'])!=review['capture_helper_sha256']:raise ValueError('reviewed capture fixture changed')
        metadata=target/'module-metadata-readback.json'
        if metadata.is_file():
            for name,digest in json.loads(metadata.read_text())['files'].items():
                if sha256(target/name)!=digest:raise ValueError('reviewed module graph metadata changed')
    verify();binary_root=target/'bin';binary_root.mkdir(exist_ok=False);suffix='.exe' if os.name=='nt' else '';app=binary_root/(project+suffix);capture=binary_root/('nativecapture'+suffix)
    env=environment(target);env.update(GOENV='off',GOPROXY='off',GOSUMDB='off',GONOPROXY='none',GONOSUMDB='none')
    flags=review['build_flags'];modflag='-modfile='+str(target/'build-inputs/pinned.mod');campaign=NextCampaign();observations=[]
    compiler=Path(fetch['compiler']);sdk=Path(fetch['settings']['GOROOT']);tool_directory=sdk/'pkg/tool'/(fetch['settings']['GOOS']+'_'+fetch['settings']['GOARCH'])
    tools={}
    for name in ['compile','asm','link']:
        path=tool_directory/(name+suffix);tools[str(path)]=sha256(path)
    immutable_json(target/'build-planned.json',dict(schema_version=1,pin=review['pin'],review_sha256=sha256(package/'dependency-source-review-declaration.json'),
        source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),compiler_sha256=sha256(compiler),compiler_tools=tools,
        effective_go_mod_sha256=inputs['go_mod_sha256'],effective_go_sum_sha256=inputs['go_sum_sha256'],
        commands=[[str(compiler),'build',*flags,modflag,'-o',str(app),review['main_package']],[str(compiler),'build',*flags,modflag,'-o',str(capture),str(ROOT/review['capture_helper'])]],target_executed=False))
    async def build(label,destination,entry):
        operation=asyncio.create_task(execute([compiler,'build',*flags,modflag,'-o',destination,entry],project,label,cwd=source,env=env,timeout=480,campaign=campaign))
        started=time.monotonic();notice=-30
        try:
            while not operation.done():
                size=await asyncio.to_thread(usage,target);observations.append(size)
                if size>review['active_stop_mib']*1024**2:raise ValueError('Go target build active storage stop')
                if time.monotonic()-started-notice>=30:
                    print(label,round(time.monotonic()-started),'seconds;',size,'owned bytes',flush=True);notice=time.monotonic()-started
                await asyncio.sleep(2)
            return await operation
        finally:
            if not operation.done():
                operation.cancel()
                try:await operation
                except asyncio.CancelledError:pass
    application=await build('reviewed-offline-native-go-target-build',app,review['main_package'])
    helper=await build('reviewed-offline-bounded-capture-fixture-build',capture,str(ROOT/review['capture_helper']))
    buildinfo=await execute([compiler,'version','-m',app],project,'actual-native-go-binary-buildinfo-readback',cwd=source,env=env,timeout=30,campaign=campaign)
    if review['compiler_version'] not in buildinfo['output']:raise ValueError('actual linked Go version differs')
    linked={line.strip().split()[1]:line.strip().split()[2] for line in buildinfo['output'].splitlines() if line.strip().startswith('dep\t')}
    expected={r['path']:r['version'] for r in inputs['actual_module_versions'] if r['version']!='primary-source'}
    if linked!=expected:raise ValueError('actual linked module versions differ from reviewed package inputs')
    immutable_json(target/'binary-buildinfo.json',dict(schema_version=1,attempt=buildinfo['id'],console_sha256=hashlib.sha256(buildinfo['output'].encode()).hexdigest(),linked_modules=linked,compiler_version=review['compiler_version'],actual_target_sha256=sha256(app)))
    verify();compiled={p.name:sha256(p) for p in binary_root.iterdir() if p.is_file()}
    immutable_json(target/'installed-inventory.json',dict(schema_version=1,runtime_root=binary_root.relative_to(ROOT).as_posix(),files={},scope='Pure Go native executables are separately bound by compiled_files. No interpreter runtime or dynamically installed dependency code.'))
    immutable_json(target/'build.json',dict(schema_version=1,runtime_kind='native',pin=review['pin'],binary_relative_path=capture.relative_to(target).as_posix(),binary_sha256=sha256(capture),
        actual_target_relative_path=app.relative_to(target).as_posix(),actual_target_sha256=sha256(app),compiled_files=compiled,compiler_sha256=sha256(compiler),compiler_tools=tools,
        actual_native_settings=fetch['settings'],build_attempt=application['id'],capture_build_attempt=helper['id'],build_plan_sha256=sha256(target/'build-planned.json'),
        source_review_sha256=sha256(package/'dependency-source-review-declaration.json'),source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),
        actual_package_inputs_sha256=sha256(target/'native-package-inputs.json'),target_executed=False))
    immutable_json(target/'runtime.json',dict(kind='native',native=str(capture),native_sha256=sha256(capture),target=str(app),target_sha256=sha256(app),source_pin=review['pin'],
        installed_inventory_sha256=sha256(target/'installed-inventory.json'),scope='Reviewed sibling stdout-capture fixture launches the actual unchanged source-built CLI,with real PTY input/UI and bounded redirected selected output. Both executable hashes are mandatory runtime inputs. No target execution yet.'))
    immutable_json(target/'build-storage-observations.json',dict(schema_version=1,observed_bytes=observations,scope='Periodic logical storage observations,not exact peak/allocation/quota.'))
    print('Built actual source-pinned native target and reviewed capture fixture offline; all source/module inputs unchanged. Target not executed.')


if __name__=='__main__':asyncio.run(main())
