"""Build once and verify the exact host runner used by a final batch."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
from adversarial_process import ROOT, run


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_inputs():
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT, timeout=15).decode().split('\0')
    names = sorted(name for name in tracked if name.endswith('.go') or name in {'go.mod', 'go.sum'})
    if not names:
        raise RuntimeError('Frozen runner has no tracked Go inputs')
    # Campaign ledgers are intentionally append-only and can be dirty. Product
    # inputs must exactly match the selected source, including test fixtures.
    dirty = subprocess.check_output(['git', 'diff', 'HEAD', '--', *names], cwd=ROOT, timeout=15)
    if dirty:
        raise RuntimeError('Cannot freeze or reuse modified Go inputs')
    untracked = subprocess.check_output(['git', 'ls-files', '--others', '--exclude-standard', '-z'],
                                       cwd=ROOT, timeout=15).decode().split('\0')
    if any(name.endswith('.go') for name in untracked):
        raise RuntimeError('Cannot freeze with untracked Go source')
    return {name: hashlib.sha256((ROOT/name).read_bytes().replace(b'\r\n', b'\n')).hexdigest()
            for name in names}


def verify(path):
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if manifest.get('version') != 1 or manifest.get('scope') != 'Final frozen runner identity; no project qualification implied':
        raise RuntimeError('Unknown frozen runner manifest')
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=15).strip()
    if source != manifest['source'] or source_inputs() != manifest['source_inputs_normalized_lf_sha256']:
        raise RuntimeError('Frozen runner source changed')
    binary = ROOT/manifest['binary']
    if binary.is_symlink() or getattr(binary, 'is_junction', lambda: False)():
        raise RuntimeError('Frozen runner is linked')
    binary.resolve(strict=True).relative_to((ROOT/'bin').resolve(strict=True))
    if digest(binary) != manifest['binary_sha256']:
        raise RuntimeError('Frozen runner binary changed')
    if platform.system() != manifest['host_system'] or platform.machine() != manifest['host_machine']:
        raise RuntimeError('Frozen runner belongs to a different native host architecture')
    return binary, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        binary, manifest = verify(args.manifest)
        print('Verified frozen runner', manifest['source'], manifest['binary_sha256'], binary)
        return
    if args.manifest.exists():
        raise RuntimeError('Refuse replacing a frozen runner manifest')
    inputs = source_inputs()
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, timeout=15).strip()
    binary = ROOT/'bin'/('playtestr-frozen.exe' if os.name == 'nt' else 'playtestr-frozen')
    if binary.exists():
        raise RuntimeError('Refuse replacing an existing frozen runner binary')
    sdk = run(['go', 'version'], 'core', 'freeze-sdk-version', timeout=15)['output'].strip()
    environment = json.loads(run(['go', 'env', '-json', 'GOVERSION', 'GOOS', 'GOARCH',
                                 'GOTOOLCHAIN', 'CGO_ENABLED', 'GOROOT'], 'core', 'freeze-sdk-settings', timeout=15)['output'])
    compiler_driver=Path(environment['GOROOT'])/'bin'/('go.exe' if os.name=='nt' else 'go')
    compiler_driver=compiler_driver.resolve(strict=True)
    compiler_driver_sha256=digest(compiler_driver)
    modules = run(['go', 'list', '-m', '-json', 'all'], 'core', 'freeze-dependency-identities', timeout=60)['output']
    binary.parent.mkdir(exist_ok=True)
    build = run(['go', 'build', '-trimpath', '-buildvcs=false', '-ldflags',
                 '-X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=source-'+source,
                 '-o', binary, './cmd/playtestr'], 'core', 'freeze-host-runner-build', timeout=180)
    build_info = run(['go', 'version', '-m', binary], 'core', 'freeze-binary-build-info', timeout=15)['output']
    if source_inputs() != inputs:
        raise RuntimeError('Runner inputs changed during freezing')
    manifest = dict(version=1, scope='Final frozen runner identity; no project qualification implied',
                    source=source, binary=binary.relative_to(ROOT).as_posix(), binary_sha256=digest(binary),
                    host_system=platform.system(), host_machine=platform.machine(), actual_host=platform.platform(),
                    sdk=sdk, sdk_environment=environment, modules=modules, binary_build_info=build_info,
                    sdk_compiler_driver=str(compiler_driver), sdk_compiler_driver_sha256=compiler_driver_sha256,
                    source_inputs_normalized_lf_sha256=inputs, build_evidence_id=build['id'],
                    build_vcs_metadata=False, run_id=os.environ.get('GITHUB_RUN_ID'))
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    verify(args.manifest)
    print('Frozen native runner', source, manifest['binary_sha256'])


if __name__ == '__main__':
    main()
