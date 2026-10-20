"""Record reviewed original superfile source and its bounded local file workflow."""
import hashlib
import tarfile

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    target=RAW/'active/old-superfile';source=target/'src'
    acquisition=load(target/'acquisition.json');expected={}
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if not member.isfile():continue
            with archive.extractfile(member) as stream:
                expected['/'.join(member.name.split('/')[1:])]=hashlib.file_digest(stream,'sha256').hexdigest()
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected:
        raise RuntimeError('original regular source differs from pinned archive')
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass/superfile'
    for current,previous in [('LICENSE','UPSTREAM-LICENSE.txt'),('go.mod','target-go.mod.txt'),('go.sum','target-go.sum.txt')]:
        if sha256(source/current)!=sha256(old/previous):raise RuntimeError('original license/dependencies changed')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/superfile';docs.mkdir(exist_ok=True)
    immutable_json(docs/'source-review.json',dict(repository='yorukot/superfile',pin=acquisition['pin'],
        archive_sha256=acquisition['archive_sha256'],reviewed_inputs=expected,license='MIT',
        reviewed_code=['main.go','src/cmd/main.go','src/config/fixed_variable.go','src/internal/handle_modal.go','src/internal/handle_file_operations.go'],
        scope='Original twelve synthetic local file workflows on Linux/macOS. Original configuration disables update checks and image previews. No external editor/opener, clipboard, trash, shell integration or user files.',
        build_backend='Direct native pure-Go build with pinned owned Go1.27.0; no Makefile, install or generation hooks. go.mod/sum retained exactly from original qualification.',
        build_flags=['-p','2','-mod=readonly','-trimpath','-buildvcs=false'],
        embedded_inputs=['src/superfile_config/*'],active_stop_mib=1536,version_arguments=['--version'],
        corruption='Original src/internal/handle_file_operations.go unselected charlie.txt copy corruption; preserve selected preview and terminal success, then require public same-execution file rejection and exact rebuilt restoration.',
        limitation='Source catalog establishes identity, not a complete security audit. No target execution credit.'))
    print('Reviewed original superfile source, MIT license, exact module locks and direct build/local-only scope.')


if __name__=='__main__':main()
