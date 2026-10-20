"""Calibrate legacy false green against public same-run corruption rejection."""
import ast
import difflib
import hashlib
import platform
import shutil
import uuid
import asyncio

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load
from readiness_old_yazi_environment import environment


def require(value,message):
    if not value:raise RuntimeError(message)


async def main():
    host={'Windows':'windows','Darwin':'macos','Linux':'linux'}.get(platform.system());require(host,'undeclared native yazi host')
    parent=RAW/'old-migration/yazi'/host
    runs=[p for p in (parent/'runs').glob('*/verified.json') if load(p)['cases']==14]
    require(len(runs)==1,'exactly one complete original native migration suite required')
    verified=load(runs[0]);package=runs[0].parent/'contracts'
    spec=package/'normal-copy.json';approved={p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}
    root=parent/'corruption'/uuid.uuid4().hex;root.mkdir(parents=True)
    legacy_package=root/'legacy-package';shutil.copytree(package,legacy_package)
    contract=load(spec);legacy=dict(contract,version=2,steps=[s for s in contract['steps'] if 'state' not in s])
    legacy_spec=legacy_package/'terminal-only-v2.json';immutable_json(legacy_spec,legacy)
    target=RAW/'active/old-yazi';source=target/'src/yazi-fs/src/engine/local/copier.rs'
    review=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/yazi/source-review.json')
    original=source.read_bytes();require(sha256(source)==review['reviewed_inputs']['yazi-fs/src/engine/local/copier.rs'],'original writer changed')
    definition=load(ROOT/'docs/validation/ten-new-project-adversarial-pass/yazi/faults/definitions.json')[2]
    require(definition['name']=='silent-copy-corrupts-unasserted-second-line' and definition['file']=='yazi-fs/src/engine/local/copier.rs'
            and definition['case']=='normal-copy','original corruption definition changed')
    before=definition['old'].encode();after=definition['new'].encode()
    require(original.count(before)==1,'actual original corruption site is not unique')
    mutated=original.replace(before,after)
    patch=''.join(difflib.unified_diff(original.decode().splitlines(True),mutated.decode().splitlines(True),
        fromfile='a/yazi-fs/src/engine/local/copier.rs',tofile='b/yazi-fs/src/engine/local/copier.rs'))
    (root/'silent-saved-corruption.patch').write_text(patch,encoding='utf-8',newline='\n')
    immutable_json(root/'declared.json',dict(source_path='yazi-fs/src/engine/local/copier.rs',original_source_sha256=sha256(source),
        mutated_source_sha256=hashlib.sha256(mutated).hexdigest(),original_native_suite_sha256=sha256(runs[0]),
        approved_package_inputs=approved,legacy_scope='Original terminal/exit prefix only; no public saved-state assertions.',
        expected_migrated_category='state_assertion_failure',new_project_fault_credit=0))
    binary,candidate,cell=runner('migration-v2');calls={};builds={}
    build=load(target/'build.json');runtime=load(target/'runtime.json')
    target_binary=target/build['binary_relative_path'];original_binary=sha256(target_binary)
    require(original_binary==build['binary_sha256'],'original binary changed before corruption')
    async def rebuild(label):
        from readiness_old_helix_build import compile_target
        outcome,built=await compile_target('migration-'+label,clean=True,project='yazi')
        require(built==target_binary,'rebuild changed target executable path')
        builds[label]=dict(attempt=outcome['id'],binary_sha256=sha256(target_binary),source_sha256=sha256(source))

    async def test(label,path,expected):
        report=root/(label+'.json')
        result=await execute([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(label+'-evidence')).relative_to(ROOT),path.relative_to(ROOT)],'old-yazi','migration-'+label,
            env=environment(),expected=expected,timeout=140,campaign=Campaign())
        outcome=load(report);row=outcome['results'][0]
        require(outcome['runner_version']==candidate['version'] and row['cleanup']['confirmed_exited']
                and row['workspace']['cleaned'],'calibration runner or cleanup differs')
        calls[label]=dict(attempt=result['id'],report_sha256=sha256(report))
        return row
    try:
        source.write_bytes(mutated)
        await rebuild('actual-corrupted-writer-build')
        require(sha256(target_binary)!=original_binary,'source mutation did not change compiled target')
        old=await test('legacy-terminal-false-green',legacy_spec,0)
        require(old['status']=='passed' and old['target']['exited'] and old['target']['exit_code']==0,'corruption did not preserve original terminal/exit success')
        bad=await test('public-state-corruption-rejected',spec,1)
        require(bad['failure']['category']=='state_assertion_failure' and bad['target']['exited'] and bad['target']['exit_code']==0,
                'wrong same-run corruption diagnosis')
        failed=next(i for i,s in enumerate(bad['steps']) if s['status']=='failed');prior=bad['steps'][:failed]
        state=bad['steps'][failed]['state']
        require(all(s['status']=='passed' for s in prior) and {'snapshot','exit'}<={s['action'] for s in prior}
                and state['kind']=='file' and state['invocation_id']==bad['invocation_id']
                and state['workspace_id']==bad['workspace']['id'],'public state rejection lacks same-run passing screen and exit proof')
    finally:
        source.write_bytes(original)
        await rebuild('exact-original-writer-rebuild')
        require(sha256(target_binary)==original_binary,'original compiled target not restored exactly')
    require(source.read_bytes()==original,'original source not restored exactly')
    restored=await test('public-state-corruption-restored',spec,0);require(restored['status']=='passed','restored original failed')
    require({p.relative_to(package).as_posix():sha256(p) for p in package.rglob('*') if p.is_file()}==approved,
            'corruption weakened approved contracts, fixtures or snapshots')
    immutable_json(root/'verified.json',dict(project='yazi',host=host,calls=calls,builds=builds,original_binary_sha256=original_binary,
        original_source_sha256=hashlib.sha256(original).hexdigest(),mutated_source_sha256=hashlib.sha256(mutated).hexdigest(),
        restored_exact=True,approved_inputs_unchanged=True,runner_sha256=cell['binary_sha256'],
        provisional_archive_sha256=cell['archive_sha256'],first_failed_state=dict(kind=state['kind'],path=state['path']),
        original_native_suite_sha256=sha256(runs[0]),scope='Actual original source writer fault. Legacy screen/exit success remains a calibrated false green; public v3 rejects wrong bytes in its own execution and passes after exact source restoration.',
        migrated_project_credit=0,new_project_fault_credit=0,final_archive_credit=0))
    print('Actual original yazi saved corruption: legacy terminal false green, public state rejection, exact recovery:',host)


if __name__=='__main__':asyncio.run(main())
