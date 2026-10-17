"""Native owned editor setup, frozen portable profile and runtime identities."""
import asyncio
import json
import os
from pathlib import Path
import shutil
import sys

from adversarial_process import execute
from readiness_cleanup_plop import runtime_inventory
from readiness_edit_environment import build_environment
from readiness_edit_profiles import native_profile
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256


def runtime_receipt():
    active,cargo,triple,env=build_environment()
    prerequisites={}
    if os.name=='nt':
        for name in ['icu.dll','icuin.dll','icuuc.dll']:
            path=Path(os.environ['SystemRoot'])/'System32'/name
            if path.is_file():prerequisites[str(path)]=sha256(path)
    immutable_json(active/'runtime.json',dict(native_triple=triple,rustc_path=env['RUSTC'],
        rustc_sha256=sha256(Path(env['RUSTC'])),cargo_path=str(cargo),cargo_sha256=sha256(cargo),
        read_only_installed_prerequisites=prerequisites,installed_globally=False,
        policy='Read/execute existing native stable Rust, linker/SDK and ICU; all new caches/build/temp/home under active/edit.'))


async def main():
    candidate=ROOT/'.playtestr-bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    binary=RAW/'bin'/candidate.name;binary.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(candidate,binary)
    if os.name!='nt':binary.chmod(0o755)
    immutable_json(RAW/'edit-native-runner.json',dict(source_revision='e7b5f29e575e44babe7fdaa2e83e55b62d318305',
        candidate_sha256=sha256(candidate),copied_sha256=sha256(binary)))
    if os.name!='nt':
        immutable_json(RAW/'edit-runtime-baseline.json',await runtime_inventory('edit','runtime-baseline-before-acquisition'))
    for script,label,timeout in [('readiness_acquire_edit.py','native-pinned-editor-acquisition',180),
        ('readiness_fetch_edit.py','native-editor-owned-locked-fetch',300)]:
        await execute([sys.executable,'scripts/acceptance/'+script],'edit',label,timeout=timeout,campaign=Campaign())
    active=RAW/'active/edit'
    reviewed=json.loads((ROOT/'docs/validation/runner-readiness-ten-project-pass/edit/source-review.json').read_text())
    if sha256(active/'source.tar.gz')!=reviewed['archive_sha256']:
        raise RuntimeError('native editor archive differs from reviewed pinned source')
    runtime_receipt()
    await execute([sys.executable,'scripts/acceptance/readiness_build_edit.py'],'edit','native-reviewed-editor-build',
        timeout=940,campaign=Campaign())
    source=ROOT/'docs/validation/runner-readiness-ten-project-pass/edit/contracts'
    package=RAW/'edit/host-contracts';shutil.copytree(source,package)
    freeze=json.loads((source.parent/'reviewed-contract-freeze.json').read_text())
    for name,digest in freeze['all_package_inputs'].items():
        if sha256(package/name)!=digest:raise RuntimeError('native checked-out frozen input differs: '+name)
    profile=[]
    if os.name!='nt':
        documents=active/'src/crates/edit/src/bin/edit/documents.rs'
        if sha256(documents)!='1fc0794cc58b1d1dc11c81721d2494b96ad218dafa8448e17a4517e567835830':
            raise RuntimeError('Unix new-document source policy differs from reviewed pin')
        for path in sorted(package.glob('*.json')):
            value=native_profile(json.loads(path.read_text()),path.name,False);original=sha256(path)
            path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8',newline='\n')
            profile.append(dict(contract=path.name,before_sha256=original,after_sha256=sha256(path),
                change='Remove Windows-only SystemDrive inheritance.'+(' N02 new-document output explicitly ends in LF under pinned Unix policy; other assertions unchanged.' if path.name=='N02.json' else ' All actions, expected bytes and snapshots unchanged.')))
    immutable_json(RAW/'edit/native-profile.json',dict(changes=profile,host=os.name,
        canonical_freeze_sha256=sha256(source.parent/'reviewed-contract-freeze.json')))
    built=json.loads((active/'build.json').read_text());target=active/built['binary_relative_path']
    for key in ['GITHUB_PATH','GITHUB_ENV']:
        if not os.environ.get(key):raise RuntimeError('native prepare requires workflow environment files')
    with Path(os.environ['GITHUB_PATH']).open('a',encoding='utf-8') as output:output.write(str(target.parent)+'\n')
    print('Pinned native Edit and twenty unchanged-action public contracts prepared.')


if __name__=='__main__':asyncio.run(main())
