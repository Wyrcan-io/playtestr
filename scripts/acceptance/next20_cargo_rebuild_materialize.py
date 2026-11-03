"""Restore exact retained Cargo Windows inputs for the declared rebuild correction."""
import asyncio
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tarfile

from adversarial_process import execute
from next20_check import DOC, RAW, ROOT, NextCampaign, owned_environment
from next20_cargo_source_corpus import Decoder
from next20_local_records import read_packet
from readiness_evidence import immutable_json, sha256


def require(value, message):
    if not value:
        raise ValueError(message)


async def main():
    require(os.name == 'nt', 'retained Windows materialization only')
    target = RAW / 'active/cargo-generate'
    package = DOC / 'cargo-generate'
    require(not any((RAW / 'active').iterdir()), 'single active target required')
    require((package / 'rebuild-recovery-declaration-v1.json').is_file(), 'declare rebuild correction first')
    _, records = read_packet('cargo-generate')

    def old(name):
        path = RAW / 'cargo-generate/retained-source' / name
        return path.read_bytes() if path.is_file() else records['cargo-generate/retained-source/' + name]

    require(json.loads(old('removed.json'))['removed'], 'original cleanup proof missing')
    build = json.loads(old('build.json'))
    for field in ['compiler', 'cargo']:
        require(sha256(Path(build[field + '_path'])) == build[field + '_sha256'], 'original read-only compiler prerequisite changed')
    declaration = dict(schema_version=1, project='cargo-generate', method='retained-primary-and-baseline-with-fresh-checksum-verified-locked-dependencies',
                       gate_sha256=sha256(package / 'restoration-rebuild-gate.json'), original_build_sha256=hashlib.sha256(old('build.json')).hexdigest(),
                       original_removal_sha256=hashlib.sha256(old('removed.json')).hexdigest(), ordinary_credit=0, project_admissions=0,
                       scope='Explicit new lifecycle. No original attempts or failure frames reconstructed. Preserve the fresh fetch receipt before reinstating exact original build input metadata.')
    immutable_json(RAW / 'cargo-generate/rebuild-materialization-v1.json', declaration)
    target.mkdir()

    def put(name, body):
        require(name and all(p not in {'', '.', '..'} and ':' not in p and '\\' not in p for p in name.split('/')), 'unsafe materialization path')
        path = target / name
        path.resolve().relative_to(target.resolve())
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(body)
        require(path.read_bytes() == body, 'materialized bytes changed')

    for name in ['task-owned.json', 'acquisition.json', 'source.tar.gz']:
        put(name, old(name))
    put('recovery-materialization.json', (RAW / 'cargo-generate/rebuild-materialization-v1.json').read_bytes())
    primary = json.loads((package / 'source-provenance.json').read_text())['files']
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(old('source.tar.gz')), mode='r:gz') as stream:
        for member in stream:
            if member.isdir():
                continue
            name = member.name.split('/', 1)[1]
            require(member.isfile() and name in primary and name not in seen and member.size <= 8 * 1024**2, 'unsafe original primary member')
            body = stream.extractfile(member).read(member.size + 1)
            require(hashlib.sha256(body).hexdigest() == primary[name], 'primary source changed')
            put('src/' + name, body)
            seen.add(name)
    require(seen == set(primary), 'primary source incomplete')
    await execute([sys.executable, '-B', ROOT / 'scripts/acceptance/next20_rust_fetch.py', 'cargo-generate', '--native-host'],
                  'cargo-generate', 'normal-rebuild-fresh-locked-dependency-fetch', cwd=ROOT, env=owned_environment(), timeout=900, campaign=NextCampaign())
    fresh = json.loads((target / 'dependency-fetch-review.json').read_text())
    original = json.loads(old('dependency-fetch-review.json'))
    for field in ['lock_sha256', 'files', 'build_hooks', 'rustc_path', 'rustc_sha256', 'cargo_path', 'cargo_sha256']:
        require(fresh[field] == original[field], 'fresh locked input/prerequisite differs: ' + field)
    destination = RAW / 'cargo-generate/rebuild-fresh-dependency-fetch-v1.json'
    shutil.copyfile(target / 'dependency-fetch-review.json', destination)
    require(destination.read_bytes() == (target / 'dependency-fetch-review.json').read_bytes(), 'fresh receipt retention differs')
    (target / 'dependency-fetch-review.json').write_bytes(old('dependency-fetch-review.json'))
    await execute([sys.executable, '-B', ROOT / 'scripts/acceptance/next20_cargo_hook_review.py', '--native-readback'],
                  'cargo-generate', 'normal-rebuild-locked-source-hook-readback', cwd=ROOT, env=owned_environment(), timeout=240, campaign=NextCampaign())
    require(sha256(target / 'dependency-source-catalog.json') == build['dependency_source_catalog_sha256'], 'actual source catalog differs from original build')
    for name in ['build.json', 'runtime.json', 'installed-inventory.json']:
        put(name, old(name))
    solid = RAW / 'cargo-generate/native-solid-variants/windows'
    index = json.loads((solid / 'index.json').read_text())
    require(sha256(solid / 'executables.tar.xz') == index['archive_sha256'], 'original executable corpus changed')
    decoder = Decoder(solid / 'executables.tar.xz')
    found = False
    try:
        with tarfile.open(fileobj=decoder, mode='r|') as stream:
            for member in stream:
                if member.name != 'original':
                    continue
                require(member.isfile() and member.size == index['files']['original']['bytes'] and member.size <= 64 * 1024**2, 'original executable member differs')
                body = stream.extractfile(member).read(member.size + 1)
                require(hashlib.sha256(body).hexdigest() == build['binary_sha256'], 'actual original executable changed')
                put(build['binary_relative_path'], body)
                found = True
        while decoder.read(65536):
            pass
    finally:
        decoder.close()
    require(found, 'original executable missing')
    contracts = RAW / 'cargo-generate/host-contracts-rebuild-v1'
    require(not contracts.exists(), 'preserve original materialization attempt')
    for name, body in records.items():
        prefix = 'cargo-generate/host-contracts/'
        if name.startswith(prefix):
            relative = name.removeprefix(prefix)
            path = contracts / relative
            path.resolve().relative_to(contracts.resolve())
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open('xb') as stream:
                stream.write(body)
    profile = json.loads((contracts / 'scenarios.json').read_text())
    require(profile['native_binary_sha256'] == build['binary_sha256'] and len(profile['cases']) == 20, 'original host contracts incomplete')
    for case in profile['cases']:
        require(sha256(contracts / case['spec']) == case['spec_sha256'], 'original contract changed')
    immutable_json(RAW / 'cargo-generate/rebuild-materialization-complete-v1.json', dict(schema_version=1,
        declaration_sha256=sha256(RAW / 'cargo-generate/rebuild-materialization-v1.json'), actual_original_binary_sha256=build['binary_sha256'],
        fresh_dependency_fetch_sha256=sha256(destination), source_catalog_sha256=sha256(target / 'dependency-source-catalog.json'),
        host_profile_sha256=sha256(contracts / 'scenarios.json'), target_executions=0, ordinary_credit=0, project_admissions=0))
    print('Original Windows primary/compiler/source catalog/baseline/contracts restored; fresh locked fetch retained. No target execution.')


if __name__ == '__main__':
    asyncio.run(main())
