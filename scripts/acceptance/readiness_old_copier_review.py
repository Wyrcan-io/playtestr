"""Bind reviewed original Copier source and packaging before installation."""
import ast
import hashlib
import tarfile
import tomllib

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/copier'
    target=RAW/'active/old-copier';source=target/'src'
    prior=load(docs/'source-acquisition-review.json');acquisition=load(target/'acquisition.json')
    if acquisition['archive_sha256']!=prior['archive_sha256'] or acquisition['omitted_links']!=prior['omitted_links']:
        raise RuntimeError('source acquisition differs from reviewed archive')
    expected={}
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if not member.isfile():continue
            with archive.extractfile(member) as stream:
                expected['/'.join(member.name.split('/')[1:])]=hashlib.file_digest(stream,'sha256').hexdigest()
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=expected:
        raise RuntimeError('extracted regular source differs from original archive')
    for path in (source/'copier').rglob('*.py'):ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    metadata=tomllib.loads((source/'pyproject.toml').read_text(encoding='utf-8'))
    if (metadata['project']['name']!='copier' or metadata['project']['scripts']!={'copier':'copier.__main__:CopierApp.run'}
            or metadata['build-system']!={'requires':['hatchling','hatch-vcs'],'build-backend':'hatchling.build'}
            or metadata['tool']['hatch']!={'version':{'source':'vcs'}}
            or metadata['tool']['commitizen']['version']!='9.18.2'
            or (source/'hatch_build.py').exists() or (source/'setup.py').exists()):
        raise RuntimeError('unreviewed packaging or entrypoint')
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass/copier'
    if sha256(source/'LICENSE')!=sha256(old/'UPSTREAM-LICENSE.txt'):raise RuntimeError('original license changed')
    hook=old/'fixtures/templates/hooked/hooks/write-marker.py'
    if hook.read_text(encoding='utf-8').splitlines()!=[
        'from pathlib import Path',"Path('task-marker.txt').write_bytes(b'reviewed task executed\\n')"]:
        raise RuntimeError('synthetic task changed')
    immutable_json(docs/'source-review.json',dict(repository=prior['repository'],pin=prior['pin'],
        archive_sha256=prior['archive_sha256'],reviewed_inputs=expected,omitted_documentation_and_test_links=prior['omitted_links'],
        license_sha256=sha256(source/'LICENSE'),pyproject_sha256=sha256(source/'pyproject.toml'),
        dependency_constraints_sha256=sha256(old/'dependency-constraints.txt'),synthetic_hook_sha256=sha256(hook),
        build_backend='Pinned hatchling/hatch-vcs, default editable packaging, no custom build hook. Tar lacks Git metadata; explicit SCM package version 9.18.2 matches pinned pyproject commitizen version and original qualification.',
        packaging_prerequisites=['hatchling==1.27.0','hatch-vcs==0.5.0','setuptools-scm==8.3.1',
            'setuptools==80.9.0','editables==0.5','pluggy==1.5.0','trove-classifiers==2025.5.9.12'],
        reviewed_code=['copier/__main__.py','copier/_cli.py','copier/_main.py','copier/_template.py','copier/_vcs.py'],
        scope='Original local synthetic templates and local Git update/recopy fixtures. One reviewed Python task writes an owned marker. No network templates, arbitrary extensions or user configurations.',
        limitation='Catalog establishes source identity, not a complete security audit. No target execution credit.'))
    print('Reviewed original Copier source, MIT license, packaging prerequisites and synthetic task.')


if __name__=='__main__':main()
