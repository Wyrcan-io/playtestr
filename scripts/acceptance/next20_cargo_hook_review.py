"""Bind the scoped hook review to independently reconstructed registry payloads."""
import hashlib
import argparse
import json
from pathlib import PurePosixPath
import tarfile
import tomllib

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native-readback',action='store_true');args=parser.parse_args()
    target=RAW/'active/cargo-generate';receipt=json.loads((target/'dependency-fetch-review.json').read_text())
    if receipt['build_hooks_executed'] or (target/'build.json').exists():raise ValueError('pre-build review only')
    if sha256(target/'src/Cargo.lock')!=receipt['lock_sha256']:raise ValueError('lock changed')
    catalog={};count=0;total=0;licenses={}
    for name,row in receipt['files'].items():
        archive=target/name
        if sha256(archive)!=row['sha256']:raise ValueError('changed archive')
        package=archive.name.removesuffix('.crate')
        matches=list((target/'cargo-home/registry/src').glob('*/'+package))
        if len(matches)!=1:raise ValueError('ambiguous unpacked crate')
        folder=matches[0];expected=set()
        with tarfile.open(archive,'r:gz') as stream:
            for member in stream:
                path=PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts or path.parts[0]!=package:
                    raise ValueError('unsafe registry member')
                if member.isdir():continue
                if not member.isfile() or member.size>32*1024**2:raise ValueError('unreviewed registry member kind/size')
                relative=PurePosixPath(*path.parts[1:]).as_posix()
                if relative in expected:raise ValueError('duplicate registry member')
                expected.add(relative);data=stream.extractfile(member).read(member.size+1)
                actual=folder/relative
                if actual.is_symlink() or getattr(actual,'is_junction',lambda:False)():raise ValueError('linked registry source')
                digest=hashlib.sha256(data).hexdigest()
                if len(data)!=member.size or sha256(actual)!=digest:raise ValueError('unpacked registry content differs: '+member.name)
                catalog[actual.relative_to(target).as_posix()]=digest
                count+=1;total+=len(data)
                if count>60000 or total>1024**3:raise ValueError('registry source review bound')
        actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
        if actual-expected-{'.cargo-ok','.cargo-checksum.json'}:raise ValueError('unexpected unpacked registry files')
        manifest=tomllib.loads((folder/'Cargo.toml').read_text(encoding='utf-8'))['package']
        licenses[package]=manifest.get('license',manifest.get('license-file','not declared'))
    for name,digest in receipt['build_hooks'].items():
        if catalog.get(name)!=digest:raise ValueError('hook not bound to reconstructed archive')
    immutable_json(target/'dependency-source-catalog.json',dict(schema_version=1,files=catalog,
        archives_sha256={n:r['sha256'] for n,r in receipt['files'].items()},
        ignored_generated_metadata=['.cargo-ok','.cargo-checksum.json']))
    if args.native_readback:
        canonical=DOC/'cargo-generate/dependency-hook-review.json';approved=json.loads(canonical.read_text())
        def hook_keys(rows):return {'/'.join(PurePosixPath(n).parts[4:]):h for n,h in rows.items()}
        if not approved['approved'] or approved['lock_sha256']!=receipt['lock_sha256'] or approved['registry_licenses']!=licenses or hook_keys(approved['reviewed_hooks'])!=hook_keys(receipt['build_hooks']):
            raise ValueError('native dependency set/hook bytes differ from the scoped canonical review')
        immutable_json(target/'native-hook-review.json',dict(schema_version=1,approved=True,
            canonical_review_sha256=sha256(canonical),lock_sha256=receipt['lock_sha256'],
            source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),fetch_receipt_sha256=sha256(target/'dependency-fetch-review.json'),
            reviewed_hooks=receipt['build_hooks'],registry_licenses=licenses,source_files=count,source_bytes=total,
            build_policy='Same exact locked package payloads and reviewed hook bytes, including normal native builder branches. Read-only installed native stable Rust is identified by actual version/hash; locked offline default-feature CLI only, two jobs, owned homes/cache/temp/output. No global tool installation.',
            build_hooks_executed=False,target_executed=False))
        print('Native locked archives and all unpacked files match the canonical hook/license review; build not executed.');return
    immutable_json(DOC/'cargo-generate/dependency-hook-review.json',dict(schema_version=1,
        lock_sha256=receipt['lock_sha256'],fetch_receipt_sha256=sha256(target/'dependency-fetch-review.json'),
        source_catalog_sha256=sha256(target/'dependency-source-catalog.json'),
        reviewed_hooks=receipt['build_hooks'],registry_licenses=licenses,source_files=count,source_bytes=total,
        review='Reviewed hook command and write sites, included probe code, and native builder branches. Most hooks emit target/compiler cfgs, invoke the exact RUSTC for version/probe metadata, or generate Rust data below OUT_DIR. names reads packaged adjective/noun lists into OUT_DIR. psm compiles packaged platform assembly; stacker compiles packaged Windows C using cc. ring uses packaged pregenerated inputs on registry builds; its maintainer .git regeneration route is absent. aws-lc-sys builds packaged C/assembly with cc/CMake or copies packaged NASM objects and pregenerated bindings into OUT_DIR. System/FIPS/bindgen/regeneration overrides remain unset. No global installation or dependency acquisition is approved from a build hook. Registry sources independently match every archive member and the Cargo.lock checksum. This scoped hook review is not a full dependency security audit.',
        build_policy='Locked offline ordinary default-feature release CLI; two jobs; no LTO/debug/incremental output. Installed Rust 1.97.1 and native MSVC tools are read-only prerequisites. All homes, compiler/cache/temp/output paths are campaign-owned. No ambient RUSTC_WRAPPER, RUSTFLAGS, AWS_LC overrides, nightly/data regeneration flags, or credentials are inherited.',
        approved=True,build_hooks_executed=False,target_executed=False))
    print('Verified',count,'unpacked files from',len(receipt['files']),'locked archives; bound',len(receipt['build_hooks']),'reviewed hooks before compilation.')


if __name__=='__main__':main()
