"""Fetch locked Go module sources for review without building or running a target."""
import argparse
import asyncio
import json
import platform
import shutil

from adversarial_process import execute
from next20_check import DOC,RAW,ROOT,NextCampaign
from readiness_build_rclone import environment
from readiness_evidence import immutable_json,sha256


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project or not (DOC/project/'source-provenance.json').is_file():raise ValueError('undeclared reviewed Go source')
    target=RAW/'active'/project;source=target/'src';provenance=json.loads((DOC/project/'source-provenance.json').read_text())
    review=json.loads((DOC/project/'module-fetch-declaration.json').read_text())
    owner=json.loads((target/'task-owned.json').read_text())
    if owner['workspace']!=str(ROOT) or owner['pin']!=provenance['pin'] or review['pin']!=owner['pin']:raise ValueError('Go fetch source ownership differs')
    for name,digest in provenance['files'].items():
        if sha256(source/name)!=digest:raise ValueError('primary source changed before dependency review')
    if review['go_mod_sha256']!=sha256(source/'go.mod') or review['go_sum_sha256']!=sha256(source/'go.sum'):raise ValueError('unreviewed module lock')
    go=shutil.which('go')
    if not go:raise ValueError('installed Go prerequisite missing')
    env=environment(target);env.update(GOENV='off',GOPROXY='https://proxy.golang.org',GONOPROXY='none',GONOSUMDB='none',GOSUMDB='sum.golang.org')
    modroot=target/'module-review';modroot.mkdir(exist_ok=False)
    alternate=modroot/'pinned.mod';shutil.copyfile(source/'go.mod',alternate);shutil.copyfile(source/'go.sum',modroot/'pinned.sum')
    immutable_json(target/'go-fetch-plan.json',dict(schema_version=1,compiler=go,compiler_sha256=sha256(go),source_provenance_sha256=sha256(DOC/project/'source-provenance.json'),
        module_fetch_declaration_sha256=sha256(DOC/project/'module-fetch-declaration.json'),alternate_go_mod_sha256=sha256(alternate),target_code_built=False,target_code_executed=False))
    campaign=NextCampaign()
    settings=await execute([go,'env','-json','GOOS','GOARCH','GOVERSION','CGO_ENABLED','GOROOT'],project,'review-only-native-go-settings',cwd=source,env=env,timeout=30,campaign=campaign)
    actual=json.loads(settings['output']);host={'Windows':'windows','Linux':'linux','Darwin':'darwin'}[platform.system()]
    architecture={'amd64':'amd64','x86_64':'amd64','arm64':'arm64','aarch64':'arm64'}.get(platform.machine().lower())
    if actual['GOOS']!=host or actual['GOARCH']!=architecture or actual['GOVERSION']!=review['compiler_version'] or actual['CGO_ENABLED']!='0':raise ValueError('unexpected native Go prerequisite')
    fetched=await execute([go,'mod','download','-modfile='+str(alternate),'-json','all'],project,'review-only-locked-module-download',cwd=source,env=env,timeout=180,campaign=campaign)
    text=fetched['output'];decoder=json.JSONDecoder();rows=[]
    while text.strip():
        row,end=decoder.raw_decode(text.lstrip());text=text.lstrip()[end:]
        if row.get('Error') or not {'Path','Version','Sum','GoModSum','Dir','Zip','GoMod'}<=set(row):raise ValueError('incomplete actual downloaded module')
        for field in ['Dir','Zip','GoMod']:
            from pathlib import Path
            Path(row[field]).resolve(strict=True).relative_to(target.resolve(strict=True))
        rows.append(row)
        if len(rows)>100:raise ValueError('Go module review count bound')
    if not rows:raise ValueError('no actual reviewed module sources')
    for name,digest in provenance['files'].items():
        if sha256(source/name)!=digest:raise ValueError('dependency download changed pinned source/locks')
    immutable_json(target/'module-fetch.json',dict(schema_version=1,modules=rows,settings=actual,settings_attempt=settings['id'],download_attempt=fetched['id'],
        alternate_go_mod_sha256=sha256(alternate),alternate_go_sum_sha256=sha256(modroot/'pinned.sum'),
        compiler=go,compiler_sha256=sha256(go),target_built=False,target_executed=False,scope='Only official compiler settings and locked module-source download. No target build,go generate,make,tests or dependency init executed; full code/license review required before build.'))
    print('Fetched',len(rows),'locked module sources for review; target not built or executed.')


if __name__=='__main__':asyncio.run(main())
