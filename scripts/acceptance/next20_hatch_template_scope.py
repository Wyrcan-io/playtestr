"""Approve a reviewed immutable data cache for built-in Hatch generation cases."""
import hashlib
import json
import zipfile

from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


def main():
    target=RAW/'active/hatch';package=DOC/'hatch'
    provider=RAW/'hatch/template-cache-inputs/Apache-2.0.provider.txt';body=provider.read_bytes()
    wheel=next((target/'wheels').glob('packaging-*.whl'))
    with zipfile.ZipFile(wheel) as archive:spdx=archive.read('packaging/licenses/_spdx.py')
    if b"VERSION = '3.27.0'" not in spdx or not body.startswith(b'Apache License\nVersion 2.0, January 2004\n'):raise ValueError('reviewed SPDX cache subject differs')
    canonical=body.decode('utf-8').rstrip()+'\n'
    destination=package/'template-license-Apache-2.0.txt'
    with destination.open('xb') as stream:stream.write(canonical.encode('utf-8'))
    paths=['src/hatch/cli/new/__init__.py','src/hatch/cli/config/__init__.py','src/hatch/config/model.py','src/hatch/config/utils.py',
        'src/hatch/template/default.py','src/hatch/template/__init__.py','src/hatch/template/files_default.py',
        'src/hatch/template/files_feature_cli.py','src/hatch/template/files_feature_tests.py','src/hatch/template/files_feature_ci.py',
        'src/hatch/cli/version/__init__.py']
    original=json.loads((package/'source-provenance.json').read_text())['files']
    reviewed={name:sha256(target/'src'/name) for name in paths}
    if any(original.get(n)!=d for n,d in reviewed.items()):raise ValueError('primary reviewed source changed')
    immutable_json(package/'template-scope-extension.json',dict(schema_version=1,
        pin='ad6d66e7c5dba7deea7601e50072676defae8b3e',source_review_sha256=sha256(package/'source-review.json'),
        reviewed_source=reviewed,packaging_wheel_sha256=sha256(wheel),spdx_module_sha256=hashlib.sha256(spdx).hexdigest(),
        provider='https://api.github.com/repos/spdx/license-list-data/contents/text/Apache-2.0.txt?ref=v3.27.0',
        provider_text_sha256=sha256(provider),owned_cache_file=destination.name,owned_cache_sha256=sha256(destination),
        normalization='UTF-8 provider text with trailing whitespace removed and exactly one LF. Generated license uses the same upstream rstrip plus LF operation; native text writer may use CRLF.',
        trusted_data_not_executable=True,
        approved_scope=[
            'Copy the exact reviewed Apache-2.0 text to each owned fixture cache/licenses/Apache-2.0.txt. Explicit --cache-dir cache and existing cache hit; no runtime network acquisition.',
            'Template license headers false and sole Apache-2.0 ID: get_license_text has no date substitution for this license. Never execute generated package/CI files.',
            'Built-in src/flat library, CLI, tests and CI file generation with explicit owned author/config values. Review independent complete metadata and all relevant file trees before final qualification.',
            'Static project.version update path only: directly updates TOML via reviewed StandardScheme. Dynamic version/build-environment creation remains excluded.',
            'Owned interactive config set for nonsensitive author fields with explicitly seeded directories; no publish values, projects outside fixture or file-manager launch.'
        ],excluded=['uv execution','environment creation','Python acquisition','publishing','external plugins/templates','setuptools migration','generated workflow dispatch'],
        project_admissions=0,scenario_credit=0,source_fault_credit=0))
    print('Approved exact owned Apache data cache and built-in generation/static-version/config scope; no target launched.')


if __name__=='__main__':main()
