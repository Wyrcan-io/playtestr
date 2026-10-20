"""Review original plain-text Helix source and its explicit native build hooks."""
import hashlib
import tarfile
import tomllib

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    target=RAW/'active/old-helix';source=target/'src'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/helix'
    prior=load(docs/'source-acquisition-review.json');acquisition=load(target/'acquisition.json')
    if acquisition['archive_sha256']!=prior['archive_sha256'] or acquisition['omitted_links']!=prior['omitted_links']:
        raise RuntimeError('original Helix acquisition differs')
    expected={}
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if not member.isfile():continue
            with archive.extractfile(member) as stream:
                expected['/'.join(member.name.split('/')[1:])]=hashlib.file_digest(stream,'sha256').hexdigest()
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected:
        raise RuntimeError('original regular source catalog differs')
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass/helix'
    for current,previous in [('LICENSE','UPSTREAM-LICENSE.txt'),('Cargo.toml','target-Cargo.toml.txt'),('Cargo.lock','target-Cargo.lock.txt')]:
        if sha256(source/current)!=sha256(old/previous):raise RuntimeError('original license/Cargo inputs changed')
    packages=tomllib.loads((source/'Cargo.lock').read_text())['package']
    if any(p.get('source') not in {None,'registry+https://github.com/rust-lang/crates.io-index'} for p in packages):
        raise RuntimeError('unreviewed dependency source')
    immutable_json(docs/'source-review.json',dict(repository=prior['repository'],pin=prior['pin'],
        archive_sha256=prior['archive_sha256'],reviewed_inputs=expected,license='MPL-2.0',
        omitted_convenience_links=prior['omitted_links'],native_hosts=['linux','windows'],
        reviewed_code=['helix-term/build.rs','helix-loader/build.rs','helix-term/src/application.rs','helix-term/src/commands/typed.rs'],
        hook_policy='Disable the supported automatic grammar acquisition/build hook. Windows resource hook reads SDK registry and invokes installed rc.exe into Cargo OUT_DIR. Loader build hook only reads Git metadata; set a Git ceiling and the supported HELIX_NIX_BUILD_REV fallback to bind the original pin rather than the enclosing Playtestr checkout.',
        toolchain='1.97.1',package='helix-term',binary='hx',profile='release',
        build_policy='Preserve original locked release profile: two jobs, no LTO/debug/incremental artifacts; Windows final link /Brepro. Copy pinned ordinary runtime resources without grammars. No global installation.',
        scope='Original twelve synthetic plain-text editing cases. Configuration disables LSP, formatting, auto-save, clipboard and mouse. No external grammars, user files or external editor integrations.',
        limitation='Source catalog establishes identity, not a complete security audit. Dependency archives/hooks must be checksum-reviewed before compilation.'))
    print('Reviewed original Helix source, MPL license, registry-only locked dependencies and two explicit build hooks.')


if __name__=='__main__':main()
