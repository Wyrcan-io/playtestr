"""Record reviewed original lf source and its bounded local file workflow."""
import hashlib
import tarfile

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    target=RAW/'active/old-lf';source=target/'src'
    acquisition=load(target/'acquisition.json');expected={}
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if not member.isfile():continue
            with archive.extractfile(member) as stream:
                expected['/'.join(member.name.split('/')[1:])]=hashlib.file_digest(stream,'sha256').hexdigest()
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected:
        raise RuntimeError('original regular source differs from pinned archive')
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass/lf'
    for current,previous in [('LICENSE','UPSTREAM-LICENSE.txt'),('go.mod','target-go.mod.txt'),('go.sum','target-go.sum.txt')]:
        if sha256(source/current)!=sha256(old/previous):raise RuntimeError('original license/dependencies changed')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/lf';docs.mkdir(exist_ok=True)
    immutable_json(docs/'source-review.json',dict(repository='gokcehan/lf',pin=acquisition['pin'],
        archive_sha256=acquisition['archive_sha256'],reviewed_inputs=expected,license='MIT',
        reviewed_code=['main.go','copy.go','nav.go','eval.go','os_windows.go','os.go'],
        scope='Original twelve synthetic local file workflows only; -single disables the shared server. No external editor, opener, custom shell command or user files.',
        build_backend='Direct native pure-Go build with pinned owned Go1.27.0; no Makefile, install or generation hooks. go.mod/sum retained exactly from original qualification.',
        build_flags=['-p','2','-mod=readonly','-trimpath','-buildvcs=false'],
        embedded_inputs=['doc.txt','etc/ruler.default'],active_stop_mib=1536,
        corruption='Original copy.go unselected charlie.txt corruption; preserve selected preview and terminal success, then require public same-execution file rejection and exact rebuilt restoration.',
        limitation='Source catalog establishes identity, not a complete security audit. No target execution credit.'))
    print('Reviewed original lf source, MIT license, exact module locks and direct build/local-only scope.')


if __name__=='__main__':main()
