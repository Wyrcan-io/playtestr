"""Review the original ordinary nnn Makefile build before native execution."""
import hashlib
import tarfile

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    target=RAW/'active/old-nnn';source=target/'src';acquisition=load(target/'acquisition.json');expected={}
    if acquisition['pin']!='c3e00d99cc83c71a9a0d285669775ae3c82db38e' or acquisition['omitted_links']:
        raise RuntimeError('original nnn source acquisition differs')
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if member.isfile():
                with archive.extractfile(member) as stream:
                    expected['/'.join(member.name.split('/')[1:])]=hashlib.file_digest(stream,'sha256').hexdigest()
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected:
        raise RuntimeError('original nnn source catalog differs')
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass/nnn'
    for name,previous in [('LICENSE','UPSTREAM-LICENSE.txt'),('Makefile','target-Makefile.txt')]:
        if sha256(source/name)!=sha256(old/previous):raise RuntimeError('original nnn license/build recipe differs')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/nnn';docs.mkdir(parents=True,exist_ok=True)
    immutable_json(docs/'source-acquisition-review.json',acquisition)
    immutable_json(docs/'source-review.json',dict(schema_version=1,repository='jarun/nnn',pin=acquisition['pin'],
        archive_sha256=acquisition['archive_sha256'],reviewed_inputs=expected,license='BSD-2-Clause',native_hosts=['linux','macos'],
        reviewed_code=['Makefile','src/nnn.c','src/nnn.h'],
        build_policy='Original make -B all with existing read-only native cc/make/pkg-config and curses. Keep default O_NORL=1, locale enabled, -O3, default patch flags zero; filtered owned environment prevents ambient make/compiler flag injection. No global install, package acquisition, static/musl/icon generator, signing or upload target.',
        hook_policy='Default prepatch/postpatch targets contain no commands with all four upstream patch flags zero. Normal build writes only src/nnn within the owned source root, then copies to owned bin/nnn. Verify every original source byte before/after compilation; force -B for mutation and exact restoration.',
        locale_policy='Require actual existing native locale charmap UTF-8; preserve normal locale inheritance, never substitute a Linux locale name on macOS.',
        corruption='Original actual copy operation succeeds, then one compiled source patch changes the first byte of the copied second line while preserving first-line screen content. Terminal-only false green, public same-run rejection, exact source AND compiled binary restoration required.',
        scope='Seventeen original synthetic file operations on native Linux/macOS with TERM=screen-256color and original -A -C arguments. No Windows curses, plugins, clipboard, external editor or network qualification.',
        limitation='Scoped trusted source/build review is not a complete security audit. Local Windows source-only review earns no build/runtime credit.'))
    print('Reviewed original nnn BSD license, full source, default Makefile/no-op hooks and actual compiled copy fault.')


if __name__=='__main__':main()
