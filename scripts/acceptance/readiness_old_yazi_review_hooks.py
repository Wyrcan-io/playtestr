"""Bind Yazi's scoped pre-build hook review to locked registry and Git bytes."""
from pathlib import Path

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def verify(target, receipt, review=None):
    if sha256(target/'src/Cargo.lock') != receipt['lock_sha256']:
        raise RuntimeError('original Yazi dependency lock changed')
    for name, digest in receipt['build_hooks'].items():
        matches=([target/name[4:]] if name.startswith('git:') else
                 list((target/'cargo-home/registry/src').glob('*/'+name)))
        if len(matches)!=1 or sha256(matches[0])!=digest:
            raise RuntimeError('Yazi dependency hook changed')
        if review is not None and review['reviewed_hook_sha256'].get(name)!=digest:
            raise RuntimeError('Yazi dependency hook lacks pre-build review')
    for name, row in receipt['files'].items():
        if sha256(target/name)!=row['sha256']:
            raise RuntimeError('Yazi registry archive changed')
        if review is not None and review['registry_archives_sha256'].get(Path(name).name)!=row['sha256']:
            raise RuntimeError('unreviewed Yazi registry archive')
    git=receipt['git_dependency']
    if len(git['checkouts'])!=1 or git['checkouts'][0]['commit']!='dde5e05eccfe5b7cb7712b4bdf76edd0c2cd1f25':
        raise RuntimeError('different original Yazi Git dependency')
    for name,row in git['files'].items():
        if sha256(target/name)!=row['sha256']:
            raise RuntimeError('Yazi locked Git dependency bytes changed')
    if review is not None:
        expected=review['git_dependency_files']
        # Checkout directory abbreviations are Cargo implementation details;
        # compare the independently reviewed source-relative byte catalog.
        prefix=git['checkouts'][0]['root']+'/'
        actual={name.removeprefix(prefix):row for name,row in git['files'].items()}
        if actual!=expected:raise RuntimeError('unreviewed Git dependency source catalog')


def main():
    target=RAW/'active/old-yazi';receipt=load(target/'dependency-fetch-review.json')
    if receipt['build_hooks_executed'] or (target/'build.json').exists():
        raise RuntimeError('pre-build review requires unbuilt dependencies')
    verify(target,receipt)
    git=receipt['git_dependency'];prefix=git['checkouts'][0]['root']+'/'
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/yazi'
    immutable_json(docs/'dependency-hook-review.json',dict(schema_version=1,project='yazi',
        source_lock_sha256=receipt['lock_sha256'],reviewed_hook_sha256=receipt['build_hooks'],
        registry_archives_sha256={Path(n).name:r['sha256'] for n,r in receipt['files'].items()},
        git_dependency_commit=git['checkouts'][0]['commit'],
        git_dependency_files={n.removeprefix(prefix):r for n,r in git['files'].items()},
        fetch_receipt_sha256=sha256(target/'dependency-fetch-review.json'),native_targets=receipt['targets'],
        build_hooks_executed=False,
        review='Reviewed hook command/write sites and included Lua/native build code. Rust compiler/version/feature probes and generated Rust data use Cargo OUT_DIR. Default vendored-lua enables packaged Lua 5.5 C compilation through lua-src/cc, not LuaJIT or a system Lua installer. Oniguruma compiles packaged C and generates config in OUT_DIR; ring uses packaged pregenerated assembly and native compiler, not its maintainer regeneration path. Linux-only jemalloc copies packaged source into OUT_DIR and configures/builds/installs static headers/library under that same OUT_DIR; no global install. Its tests and allocator overrides remain unset. Native C toolchains are read-only prerequisites. Vergen build-date uses SOURCE_DATE_EPOCH; YAZI_NO_GITCL disables enclosing-checkout revision discovery. Git-patched ratatui source catalog and actual HEAD match the original lock; no Git dependency build hook found.',
        policy='Locked offline Cargo builds, exact Rust 1.99.0 native targets, two jobs, owned homes/caches/output/temp; no ambient wrappers, completion generator, release bootstrap or yazi-build installer. Scoped review is not a complete dependency security audit.'))
    print('Bound',len(receipt['build_hooks']),'reviewed hooks and exact locked Git source before target compilation.')


if __name__=='__main__':main()
