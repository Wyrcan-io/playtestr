"""Review the original Ranger source-only Unix launch and saved-copy writer."""
import hashlib
import tarfile

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    target=RAW/'active/old-ranger';source=target/'src';acquisition=load(target/'acquisition.json')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/ranger'
    declared=load(docs/'source-acquisition-review.json');expected={}
    if acquisition['pin']!=declared['pin'] or acquisition['archive_sha256']!=declared['archive_sha256']:
        raise RuntimeError('original Ranger source identity differs')
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if member.isfile():
                with archive.extractfile(member) as stream:
                    expected['/'.join(member.name.split('/')[1:])]=hashlib.file_digest(stream,'sha256').hexdigest()
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected:
        raise RuntimeError('original regular Ranger source catalog differs')
    if sha256(source/'LICENSE')!=sha256(ROOT/'docs/validation/ten-new-project-adversarial-pass/ranger/UPSTREAM-LICENSE.txt'):
        raise RuntimeError('original Ranger GPL license differs')
    immutable_json(docs/'source-review.json',dict(schema_version=1,repository='ranger/ranger',pin=acquisition['pin'],
        archive_sha256=acquisition['archive_sha256'],reviewed_inputs=expected,license='GPL-3.0',native_hosts=['linux','macos'],
        omitted_documentation_links=declared['omitted_links'],
        reviewed_code=['ranger.py','setup.py','ranger/__init__.py','ranger/core/main.py',
            'ranger/ext/shutil_generatorized.py','ranger/config/commands.py','ranger/config/rc.conf'],
        setup_policy='Use the documented direct ranger.py entrypoint with ordinary -O and --clean. Owned --without-pip --copies venv; read-only installed native Python/curses prerequisite. Transparent shell exec launcher only, no output processing or manufactured readiness. No setup.py, pip, external preview scripts, optional dependencies or global installation.',
        cache_policy='All homes/cache/temp are owned. --clean disables user/system config and bytecode and creates its temporary cache under owned TMPDIR, removed by upstream atexit. Use --clean for version probes too: ranger.py explicitly overrides sys.dont_write_bytecode based on that flag.',
        version_policy='Source archive has no Git metadata. Set an owned Git ceiling so upstream development-version git describe cannot read enclosing Playtestr history. Source pin/catalog, interpreter and actual version output are independently captured; no reconstructed upstream Git description.',
        scope='Sixteen original synthetic file-navigation/copy/create/rename/delete/preview workflows on native Linux/macOS with TERM=screen-256color. No Windows curses, external editor, image, network or plugin qualification.',
        corruption='Original copy writer replaces Protected with same-length Corrupted in the actual destination file after copystat. Keep terminal-only false green; public same-run file checks must reject; restore exact Python source and unchanged launcher/interpreter.',
        limitation='Scoped trusted source review is not a complete security audit. Local Windows preparation is source-only and earns no target execution credit.'))
    print('Reviewed original Ranger GPL source, direct launcher, clean cache/bytecode policy and actual copy writer.')


if __name__=='__main__':main()
