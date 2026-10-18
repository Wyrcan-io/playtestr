"""Build a pinned local development runner without replacing historical bytes."""
import asyncio
import os
import subprocess

from adversarial_process import execute
from readiness_acquire_plop import extract_source
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256

SOURCE='3d50d81aae8f1d24f7a718e6e05b39069697b1a6'


async def main():
    destination=RAW/'development-candidates'/SOURCE
    destination.mkdir(parents=True,exist_ok=False)
    archive=destination/'source.tar.gz'
    with archive.open('xb') as output:
        subprocess.run(['git','archive','--format=tar.gz','--prefix=source/',SOURCE,'go.mod','go.sum','cmd','internal'],cwd=ROOT,stdout=output,check=True,timeout=20)
    if archive.stat().st_size>16*1024**2:raise RuntimeError('candidate source archive bound')
    count,total=extract_source(archive.read_bytes(),destination/'src',expanded_limit=64*1024**2,entry_limit=10000,member_limit=8*1024**2)
    sources={p.relative_to(destination/'src').as_posix():sha256(p) for p in (destination/'src').rglob('*') if p.is_file()}
    environment=dict(os.environ,GOTOOLCHAIN='local',GOCACHE=str(RAW/'go-cache'),GOPATH=str(RAW/'gopath'),GOMODCACHE=str(RAW/'gopath/pkg/mod'),
        TEMP=str(RAW/'tmp'),TMP=str(RAW/'tmp'),GOTMPDIR=str(RAW/'tmp'))
    compiler=RAW/'toolchain/go/bin'/('go.exe' if os.name=='nt' else 'go')
    binary=destination/('playtestr.exe' if os.name=='nt' else 'playtestr')
    build=await execute([compiler,'build','-trimpath','-buildvcs=false','-ldflags','-X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version=source-'+SOURCE,'-o',binary,'./cmd/playtestr'],
        'core','exact-pinned-local-development-candidate',cwd=destination/'src',env=environment,timeout=180,campaign=Campaign())
    version=await execute([binary,'--version'],'core','exact-pinned-local-candidate-version',env=environment,timeout=15,campaign=Campaign())
    if version['output'].strip()!='playtestr source-'+SOURCE:raise RuntimeError('candidate version mismatch')
    if sources!={p.relative_to(destination/'src').as_posix():sha256(p) for p in (destination/'src').rglob('*') if p.is_file()}:raise RuntimeError('candidate source changed during build')
    immutable_json(destination/'candidate.json',dict(source_revision=SOURCE,source_archive_sha256=sha256(archive),source_files=sources,source_entries=count,expanded_source_bytes=total,
        compiler_sha256=sha256(compiler),binary=binary.relative_to(ROOT).as_posix(),binary_sha256=sha256(binary),build_attempt=build['id'],version_attempt=version['id'],
        qualification='Development candidate only; historical RAW/bin/dev runner preserved unchanged; no final archive credit.'))
    print('Exact pinned local candidate built at',binary.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
