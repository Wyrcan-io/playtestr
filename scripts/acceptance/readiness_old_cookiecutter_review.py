"""Record exact original Cookiecutter build inputs before editable installation."""
import ast
import hashlib
import tarfile
import tomllib

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/cookiecutter'
    target=RAW/'active/old-cookiecutter';source=target/'src'
    prior=load(docs/'source-acquisition-review.json');acquisition=load(target/'acquisition.json')
    if acquisition['archive_sha256']!=prior['archive_sha256'] or acquisition['omitted_links']!=prior['omitted_links']:
        raise RuntimeError('source acquisition differs from exact reviewed archive')
    expected={}
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        for member in archive:
            if not member.isfile():continue
            name='/'.join(member.name.split('/')[1:]);digest=hashlib.sha256()
            with archive.extractfile(member) as stream:
                while block:=stream.read(65536):digest.update(block)
            expected[name]=digest.hexdigest()
    actual={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}
    if actual!=expected:raise RuntimeError('extracted regular source files differ from original archive')
    for path in (source/'cookiecutter').glob('*.py'):ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    metadata=tomllib.loads((source/'pyproject.toml').read_text(encoding='utf-8'))
    if (metadata['project']['name']!='cookiecutter' or metadata['project']['version']!='2.7.1'
            or metadata['project']['scripts']!={'cookiecutter':'cookiecutter.__main__:main'}
            or metadata['tool']['setuptools']['packages']!=['cookiecutter'] or 'build-system' in metadata
            or (source/'setup.py').exists() or (source/'setup.cfg').exists()):
        raise RuntimeError('unreviewed source build or entrypoint')
    old=ROOT/'docs/validation/ten-new-project-adversarial-pass/cookiecutter'
    if sha256(source/'LICENSE')!=sha256(old/'UPSTREAM-LICENSE.txt'):raise RuntimeError('original license changed')
    hook=old/'fixtures/hooked/hooks/post_gen_project.py'
    if hook.read_text(encoding='utf-8').splitlines()!=[
        'from pathlib import Path',"Path('hook-result.txt').write_text('hook executed\\n',encoding='utf-8',newline='\\n')",
        "print('Reviewed local generation hook completed')"]:raise RuntimeError('reviewed synthetic generation hook changed')
    immutable_json(docs/'source-review.json',dict(repository=prior['repository'],pin=prior['pin'],
        archive_sha256=prior['archive_sha256'],reviewed_inputs=expected,omitted_documentation_links=prior['omitted_links'],
        license_sha256=sha256(source/'LICENSE'),pyproject_sha256=sha256(source/'pyproject.toml'),
        dependency_constraints_sha256=sha256(old/'dependency-constraints.txt'),synthetic_hook_sha256=sha256(hook),
        build_backend='Default setuptools PEP 660; static pyproject project metadata, no root setup.py/setup.cfg; only cookiecutter packaged.',
        packaging_prerequisites=['setuptools==80.9.0','wheel==0.45.1'],
        reviewed_code=['cookiecutter/__main__.py','cookiecutter/cli.py','cookiecutter/hooks.py','cookiecutter/generate.py','cookiecutter/prompt.py'],
        scope='Original local synthetic generation scenarios only. Reviewed Python hook writes one owned file and prints a fixed message. Other hooks, remote templates and user configurations are excluded.',
        limitation='Source catalog is identity coverage, not a complete security audit. No build or target execution credit.'))
    print('Reviewed exact original source catalog, static packaging, original license, constraints and one synthetic local hook.')


if __name__=='__main__':main()
