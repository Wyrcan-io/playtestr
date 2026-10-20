"""Review the original Yazi source, exact Git patch and native build boundary."""
from datetime import datetime
import hashlib
import tarfile
import tomllib

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    target=RAW/'active/old-yazi';source=target/'src';acquisition=load(target/'acquisition.json')
    if acquisition['pin']!='f220cb6fb1018c7c656077e30b1aefbac136f719' or acquisition['omitted_links']:
        raise RuntimeError('original Yazi acquisition differs')
    expected={}
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if member.isfile():
                with archive.extractfile(member) as stream:
                    expected['/'.join(member.name.split('/')[1:])]=hashlib.file_digest(stream,'sha256').hexdigest()
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected:
        raise RuntimeError('original regular source catalog differs')
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass/yazi'
    for current,previous in [('LICENSE','UPSTREAM-LICENSE.txt'),('Cargo.toml','target-Cargo.toml.txt'),('Cargo.lock','target-Cargo.lock.txt')]:
        if sha256(source/current)!=sha256(old/previous):raise RuntimeError('original license/Cargo input changed')
    packages=tomllib.loads((source/'Cargo.lock').read_text())['package']
    git_source='git+https://github.com/yazi-rs/ratatui.git?branch=fix_buffer_diff_wide_cells#dde5e05eccfe5b7cb7712b4bdf76edd0c2cd1f25'
    if [(p['name'],p['source']) for p in packages if p.get('source','').startswith('git+')]!=[('ratatui-core',git_source)]:
        raise RuntimeError('original locked Git dependency differs')
    if any(p.get('source') not in {None,'registry+https://github.com/rust-lang/crates.io-index',git_source} for p in packages):
        raise RuntimeError('unreviewed dependency transport')
    value=dict(schema_version=1,project='yazi',pin=acquisition['pin'],source_archive_sha256=acquisition['archive_sha256'],
        reviewed_inputs=expected,license='MIT',native_hosts=['linux','macos','windows'],toolchain='1.99.0',
        package='yazi-fm',binary='yazi',profiles=dict(unix='release',windows='release-windows'),
        locked_git_sources=[git_source],git_dependency_commit='dde5e05eccfe5b7cb7712b4bdf76edd0c2cd1f25',
        upstream_commit_date='2026-10-10T05:08:43Z',
        source_date_epoch=int(datetime.fromisoformat('2026-10-10T05:08:43+00:00').timestamp()),
        commit_date_source='https://api.github.com/repos/sxyazi/yazi/git/commits/f220cb6fb1018c7c656077e30b1aefbac136f719',
        reviewed_code=['yazi-version/build.rs','yazi-fm/build.rs','yazi-fs/build.rs','yazi-boot/build.rs','yazi-cli/build.rs',
            'yazi-build/build.rs','yazi-build/src/build.rs','.cargo/config.toml','yazi-fs/src/engine/local/copier.rs'],
        hook_policy='Build only yazi-fm/yazi, not the separate yazi-build installer. Leave YAZI_GEN_COMPLETIONS unset; boot/CLI completion generation otherwise writes into source. Version hook uses supported YAZI_NO_GITCL to avoid enclosing Playtestr Git metadata and SOURCE_DATE_EPOCH for reproducible date metadata. FS hook emits cfg aliases; FM hook requires the original Windows unwind profile. Dependency hooks and locked Git source require review before compilation.',
        build_policy='Original stable Rust release profiles, two jobs, no LTO/debug/incremental artifacts. Windows release-windows and final /Brepro; invalidate yazi-fs and yazi-fm for the actual copy fault/recovery. Respect the pinned .cargo platform configuration; do not invoke the installer/release bootstrap or use nightly.',
        scope='Fourteen original synthetic file operations on native Linux/macOS/Windows with TERM=screen-256color. No network filesystem, package/plugin installer, image, clipboard or external editor qualification.',
        limitation='Source catalog and explicit hook review establish scoped trusted inputs, not a complete dependency security audit. No target build or runtime credit yet.')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/yazi';docs.mkdir(parents=True,exist_ok=True)
    immutable_json(docs/'source-acquisition-review.json',acquisition)
    immutable_json(docs/'source-review.json',value);immutable_json(target/'source-review.json',value)
    print('Reviewed original Yazi license, all regular source bytes, first-party hooks and exact locked Git patch.')


if __name__=='__main__':main()
