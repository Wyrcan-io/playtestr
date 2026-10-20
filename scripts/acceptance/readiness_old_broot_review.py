"""Bind the original Broot source and review its native build boundary."""
import hashlib
import tarfile
import tomllib

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    target=RAW/'active/old-broot';source=target/'src'
    acquisition=load(target/'acquisition.json')
    if acquisition['pin']!='41cb4c78d9d7736dfe83c65f8a393fc962e50662' or acquisition['omitted_links']:
        raise RuntimeError('original Broot acquisition differs')
    expected={}
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if member.isfile():
                with archive.extractfile(member) as stream:
                    expected['/'.join(member.name.split('/')[1:])]=hashlib.file_digest(stream,'sha256').hexdigest()
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected:
        raise RuntimeError('original regular source catalog differs')
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass/broot'
    for current,previous in [('LICENSE','UPSTREAM-LICENSE.txt'),('Cargo.toml','target-Cargo.toml.txt'),('Cargo.lock','target-Cargo.lock.txt')]:
        if sha256(source/current)!=sha256(old/previous):raise RuntimeError('original license/Cargo inputs changed')
    packages=tomllib.loads((source/'Cargo.lock').read_text())['package']
    if any(p.get('source') not in {None,'registry+https://github.com/rust-lang/crates.io-index'} for p in packages):
        raise RuntimeError('unreviewed dependency transport')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/broot'
    docs.mkdir(parents=True,exist_ok=True)
    immutable_json(docs/'source-acquisition-review.json',acquisition)
    immutable_json(target/'source-review.json',dict(schema_version=1,project='broot',pin=acquisition['pin'],
        source_archive_sha256=acquisition['archive_sha256'],reviewed_inputs=expected,license='MIT',
        omitted_convenience_links={},native_hosts=['linux','macos'],
        reviewed_code=['build.rs','src/cli/args.rs','src/verb/verb_store.rs','src/preview/preview_state.rs'],
        hook_policy='First-party build.rs generates shell completions only inside Cargo OUT_DIR. BUILD_MAN_PAGE is false; its optional writer is also OUT_DIR. No shell installation. Dependency checksums/hooks require separate review before compilation.',
        toolchain='1.97.1',package='broot',binary='broot',profile='release',
        build_policy='Locked offline native release build, two jobs, no LTO/debug/incremental output. All new homes, caches, toolchains and build output inside owned target root.',
        scope='Original thirteen Linux/macOS synthetic file-tree workflows; TERM=screen-256color and BR_INSTALL=no. Reviewed built-in copy/move/mkdir commands use ordinary native tools. No Windows target runtime credit, external editor, clipboard, image, network or user-file coverage.',
        limitation='Source identity and explicit hook review do not constitute a complete security audit.'))
    print('Original Broot regular source, license, Cargo lock and native build boundary verified.')


if __name__=='__main__':main()
