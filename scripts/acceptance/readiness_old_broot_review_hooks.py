"""Record the reviewed, checksum-bound original Unix Broot build hook set."""
from pathlib import Path

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    target=RAW/'active/old-broot';receipt=load(target/'dependency-fetch-review.json')
    if sha256(target/'src/Cargo.lock')!=receipt['lock_sha256'] or receipt['build_hooks_executed']:
        raise RuntimeError('unbuilt original locked dependency set required')
    for name,digest in receipt['build_hooks'].items():
        paths=list((target/'cargo-home/registry/src').glob('*/'+name))
        if len(paths)!=1 or sha256(paths[0])!=digest:raise RuntimeError('hook changed during review')
    archives={}
    for name,row in receipt['files'].items():
        if sha256(target/name)!=row['sha256']:raise RuntimeError('crate changed during review')
        archives[Path(name).name]=row['sha256']
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/broot'
    immutable_json(docs/'dependency-hook-review.json',dict(schema_version=1,project='broot',
        source_lock_sha256=receipt['lock_sha256'],reviewed_hook_sha256=receipt['build_hooks'],
        registry_archives_sha256=archives,fetch_receipt_sha256=sha256(target/'dependency-fetch-review.json'),
        native_targets=receipt['targets'],build_hooks_executed=False,
        review='Reviewed first-party completion generation, crate hook command/write sites and included configuration modules. Compiler/version/feature probes invoke the selected Rust compiler and write only Cargo OUT_DIR; serde/ref-cast/rustversion/pulp generate bounded build files there. Objective-C conditional compilation uses the native compiler and packaged exception source. libc/inotify alternate-system probes are conditional. wasm-bindgen shared reads packaged schema files and optional Git revision, with the owned Git ceiling. Image disables default/AVIF encoder features, so fetched rav1e/av-scenechange NASM branches are not enabled by this Broot profile. No dependency installation or application execution during review.',
        policy='Locked offline Cargo builds, explicit native target, two jobs, owned homes/caches/output/temp, no ambient Rust wrappers or installer hooks. This scoped hook review and exact checksums are not a complete dependency security audit.'))
    print('Recorded',len(receipt['build_hooks']),'checksum-bound hooks before native compilation.')


if __name__=='__main__':main()
