"""Prepare the restored Cargo build cache separately from calibration deadlines."""
import asyncio
import json
import os
from pathlib import Path
import shutil

from adversarial_process import execute
from next20_check import DOC, RAW, ROOT, NextCampaign
from next20_rust_fetch import environment, materialize_short_cache, short_owned_path
from readiness_evidence import immutable_json, sha256


async def main():
    if os.name != 'nt':
        raise ValueError('explicit Windows cold-build preparation only')
    package = DOC / 'cargo-generate'
    target = RAW / 'active/cargo-generate'
    disposition = package / 'windows-normal-rebuild-first-window-timeout-v1.json'
    failure = json.loads(disposition.read_text())
    if failure['qualified_calibrations'] != 0 or not failure['all_primary_source_restored_exact']:
        raise ValueError('original partial-window disposition required')
    build = json.loads((target / 'build.json').read_text())
    primary = json.loads((package / 'source-provenance.json').read_text())['files']
    dependencies = json.loads((target / 'dependency-fetch-review.json').read_text())
    catalog = json.loads((target / 'dependency-source-catalog.json').read_text())
    root = RAW / 'cargo-generate/rebuild-preparation-v1'
    root.mkdir(exist_ok=False)

    def verify():
        if any(sha256(target / 'src' / n) != h for n, h in primary.items()):
            raise ValueError('restored primary source differs')
        if sha256(Path(build['compiler_path'])) != build['compiler_sha256'] or sha256(Path(build['cargo_path'])) != build['cargo_sha256']:
            raise ValueError('original read-only compiler changed')
        if sha256(target / build['binary_relative_path']) != build['binary_sha256']:
            raise ValueError('original ordinary baseline changed')

    verify()
    env = environment(target)
    compiler = Path(build['compiler_path'])
    env.update(RUSTC=str(compiler), RUSTDOC=str(compiler.with_name('rustdoc.exe')),
               CARGO_NET_OFFLINE='true', SOURCE_DATE_EPOCH='1793030400')
    env['PATH'] = str(compiler.parent) + os.pathsep + env['PATH']
    env['CARGO_HOME'] = str(materialize_short_cache(target, dependencies, catalog))
    for key in ['CARGO_HOME', 'CARGO_TARGET_DIR', 'TEMP', 'TMP', 'TMPDIR']:
        env[key] = short_owned_path(env[key])
    command = [build['cargo_path'], 'rustc', '--locked', '--offline', '--release', '--target', build['native_triple'],
               '--bin', 'cargo-generate', '--', '-C', 'link-arg=/Brepro']
    immutable_json(root / 'planned.json', dict(schema_version=1, original_timeout_disposition_sha256=sha256(disposition),
        build_sha256=sha256(target / 'build.json'), command=command, target_executions=0, calibration_credit=0,
        scope='Separate bounded preparation of exact restored-source ordinary build cache. No target launch or accepted repetition. Preserve original partial calibration unchanged.'))
    result = await execute(command, 'cargo-generate', 'normal-restored-source-cold-build-preparation',
        cwd=Path(short_owned_path(target / 'src')), env=env, timeout=900, campaign=NextCampaign(phase='development'))
    verify()
    output = target / 'cargo-target' / build['native_triple'] / 'release/cargo-generate.exe'
    retained = target / 'fault-builds/preparation-v1/cargo-generate.exe'
    retained.parent.mkdir(exist_ok=False)
    shutil.copyfile(output, retained)
    if sha256(output) != sha256(retained):
        raise ValueError('actual prepared image copy differs')
    immutable_json(root / 'compiled.json', dict(schema_version=1, compile_attempt=result['id'], command=command,
        compiler_sha256=build['compiler_sha256'], cargo_sha256=build['cargo_sha256'],
        binary=retained.relative_to(ROOT).as_posix(), binary_sha256=sha256(retained), binary_bytes=retained.stat().st_size,
        source_inputs={(target / 'src' / n).relative_to(ROOT).as_posix(): h for n, h in primary.items()},
        pristine_build_sha256=sha256(target / 'build.json'), matches_original=sha256(retained) == build['binary_sha256'],
        original_image_dictionary='cargo-generate/native-solid-variants/windows', target_executions=0, calibration_credit=0))
    if sha256(retained) != build['binary_sha256']:
        raise ValueError('prepared source image differs from old baseline; preserve it for explicit retention before proceeding')
    print('Separate normal-source preparation compiled successfully; actual image equals mandatory retained original. No target execution/calibration credit.')


if __name__ == '__main__':
    asyncio.run(main())
