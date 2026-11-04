"""Build Skim's reviewed CLI from pinned source and locked cache, offline."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from next20_check import RAW, ROOT, NextCampaign
from next20_rust_fetch import environment, short_owned_path
from readiness_build_plop import usage
from readiness_evidence import immutable_json, sha256


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--native-host', action='store_true')
    parser.add_argument('--source-review', default='docs/validation/runner-readiness-next-twenty-project-pass/skim/source-review-v1.json')
    parser.add_argument('--hook-review', default='docs/validation/runner-readiness-next-twenty-project-pass/skim/dependency-hook-review-v1.json')
    args = parser.parse_args()
    project = 'skim'
    target = RAW / 'active' / project
    source = target / 'src'
    docs = Path('docs/validation/runner-readiness-next-twenty-project-pass/skim')
    if (target / 'build.json').exists():
        raise ValueError('refuse replacing an existing Skim build receipt')
    review_path = (ROOT / args.source_review).resolve(strict=True)
    hooks_path = (ROOT / args.hook_review).resolve(strict=True)
    review_path.relative_to(ROOT)
    hooks_path.relative_to(ROOT)
    review = json.loads(review_path.read_text(encoding='utf-8'))
    hooks = json.loads(hooks_path.read_text())
    fetched = json.loads((target / 'dependency-fetch-review.json').read_text())
    if not hooks['build_authorization']['approved'] or hooks['dependency_fetch_review_sha256'] != sha256(target / 'dependency-fetch-review.json'):
        raise ValueError('build inputs are not approved and hash-bound')
    lock_hash = sha256(source / 'Cargo.lock')
    if lock_hash != fetched['lock_sha256']:
        raise ValueError('Cargo.lock differs from exact source-fetch input')
    for name, row in fetched['files'].items():
        if sha256(target / name) != row['sha256']:
            raise ValueError('locked registry archive changed: ' + name)
    if sha256(docs / 'source-provenance.json') != review['source_provenance_sha256']:
        raise ValueError('source provenance changed after review')
    compiler = Path(fetched['rustc_path'])
    cargo = Path(fetched['cargo_path'])
    if sha256(compiler) != fetched['rustc_sha256'] or sha256(cargo) != fetched['cargo_sha256']:
        raise ValueError('installed Rust toolchain changed after fetch')
    suffix = '.exe' if os.name == 'nt' else ''
    env = environment(target)
    env.update(RUSTC=str(compiler), RUSTDOC=str(compiler.with_name('rustdoc' + suffix)),
               CARGO_NET_OFFLINE='true', SOURCE_DATE_EPOCH='1793030400')
    env['CARGO_HOME'] = str(target / 'cargo-home')
    env['PATH'] = str(compiler.parent) + os.pathsep + env['PATH']
    if os.name == 'nt':
        for key in ['CARGO_HOME', 'CARGO_TARGET_DIR', 'TEMP', 'TMP', 'TMPDIR']:
            env[key] = short_owned_path(env[key])
    triple = 'x86_64-pc-windows-msvc' if os.name == 'nt' else 'x86_64-unknown-linux-gnu'
    if args.native_host and os.name != 'nt':
        raise ValueError('this native package preparation is currently declared for Windows only')
    command = [cargo, 'build', '--release', '--locked', '--offline', '--target', triple,
               '--no-default-features', '--features', 'cli,frizbee', '--bin', 'sk']
    samples = []
    task = asyncio.create_task(execute(command, project, 'reviewed-cli-features-offline-native-build',
        cwd=Path(short_owned_path(source)), env=env, timeout=1800, campaign=NextCampaign(), output_cap=2*1024*1024))
    try:
        while not task.done():
            size = await asyncio.to_thread(usage, RAW)
            samples.append(size)
            if size > 3*1024**3:
                raise ValueError('Skim build raw-storage stop')
            await asyncio.sleep(2)
        result = await task
    finally:
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        immutable_json(target / ('build-storage-' + uuid.uuid4().hex + '.json'),
            dict(observed_raw_bytes=samples, stop_bytes=3*1024**3,
                 scope='Periodic logical samples; not an exact peak or filesystem quota.'))
    built = target / 'cargo-target' / triple / 'release' / ('sk' + suffix)
    if not built.is_file():
        raise ValueError('Cargo succeeded without the expected target executable')
    binary = target / 'bin' / ('sk' + suffix)
    binary.parent.mkdir(exist_ok=True)
    shutil.copyfile(built, binary)
    if os.name != 'nt':
        binary.chmod(0o755)
    digest = sha256(binary)
    contract_alias = None
    if os.name != 'nt':
        # Frozen cross-platform specs use the Windows .exe spelling; ELF does
        # not require a suffix, so retain a byte-identical executable alias.
        alias = binary.with_name('sk.exe')
        if alias.exists():
            raise ValueError('refuse replacing the Skim cross-platform contract alias')
        shutil.copyfile(binary, alias)
        alias.chmod(0o755)
        if sha256(alias) != digest:
            raise ValueError('cross-platform contract alias differs from the built ELF')
        contract_alias = dict(binary_relative_path=alias.relative_to(target).as_posix(),
                              binary_sha256=digest, byte_identical=True, installed_globally=False)
    if sha256(source / 'Cargo.lock') != lock_hash:
        raise ValueError('Cargo changed the reviewed lockfile')
    immutable_json(target / 'build.json', dict(
        schema_version=1, project=project, pin=review['pin'], runtime_kind='native',
        binary_relative_path=binary.relative_to(target).as_posix(), binary_sha256=digest,
        build_attempt=result['id'], compiler_path=str(compiler), compiler_sha256=sha256(compiler),
        cargo_path=str(cargo), cargo_sha256=sha256(cargo), native_triple=triple,
        contract_alias=contract_alias,
        features=['cli', 'frizbee'], source_review_sha256=sha256(review_path),
        dependency_hook_review_sha256=sha256(hooks_path),
        dependency_fetch_review_sha256=sha256(target / 'dependency-fetch-review.json'),
        cargo_lock_sha256=lock_hash, command=list(map(str, command)), installed_globally=False,
        build_hooks_executed=True, build_hooks_reviewed=hooks['hook_count'],
        target_application_executed=False))
    immutable_json(target / 'runtime.json', dict(schema_version=1, kind='native', native=str(binary),
        native_sha256=digest, native_triple=triple, source=review['pin'], source_pin=review['pin'],
        source_path=str(source), source_revision=review['pin'], binary=str(binary),
        build_sha256=sha256(target / 'build.json')))
    version = await execute([binary, '--version'], project, 'actual-built-native-version',
        cwd=source, env=env, timeout=30, campaign=NextCampaign())
    if version['output'].strip() not in {'sk 5.8.0', '5.8.0'}:
        raise ValueError('unexpected Skim --version output: ' + version['output'][:300])
    immutable_json(target / 'version-check.json', dict(attempt=version['id'], binary_sha256=digest,
        output=version['output'], build_sha256=sha256(target / 'build.json')))
    print('Built and version-checked pinned Skim CLI:', digest)


if __name__ == '__main__':
    asyncio.run(main())
