"""Preserve the pre-execution source review for cargo-generate's local workflow."""
import json
import shutil
import tomllib

from next20_check import RAW, DOC
from readiness_evidence import immutable_json, sha256


def main():
    target=RAW/'active/cargo-generate';source=target/'src';package=DOC/'cargo-generate'
    provenance=json.loads((package/'source-provenance.json').read_text())
    files={p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}
    if files!=provenance['files']:raise ValueError('reviewed pinned source changed')
    manifest=tomllib.loads((source/'Cargo.toml').read_text())
    if manifest['package']['name']!='cargo-generate' or manifest['package']['version']!='0.25.1':
        raise ValueError('unexpected upstream package')
    if 'build' in manifest['package'] or (source/'build.rs').exists():raise ValueError('unexpected upstream build hook')
    for name in ['LICENSE-MIT','LICENSE-APACHE','Cargo.toml','Cargo.lock']:
        shutil.copyfile(source/name,package/('upstream-'+name+'.txt'))
    immutable_json(package/'source-review.json',dict(schema_version=1,project='cargo-generate',
        repository=provenance['repository'],pin=provenance['pin'],version='0.25.1',
        license='MIT OR Apache-2.0',source_provenance_sha256=sha256(package/'source-provenance.json'),
        reviewed_inputs=files,source_build_hooks=[],build_scope='Normal locked release CLI with default git feature; no global installation.',
        workflow='Local synthetic template, explicit --vcs none --no-workspace; dialoguer text/select/bool/array prompts, Liquid-generated files and independent exact output checks.',
        reviewed_source_paths=['Cargo.toml','Cargo.lock','src/main.rs','src/lib.rs','src/args.rs',
            'src/interactive.rs','src/fetch.rs','src/copy.rs','src/hooks/system_mod.rs',
            'src/template_variables/project_name_input.rs','src/template_variables/project_dir.rs','src/utils.rs',
            'guide/src/templates/template_defined_placeholders.md','.github/workflows/build.yml'],
        execution_policy='Trusted upstream target runs with user permissions. Fixtures contain no Rhai hooks, command permission or remote template; no --test cargo invocation, external editor, credentials, global Git writes, or outside-workspace destinations. Explicit owned homes/temp/cache precede child launch. Windows and Linux qualification remains pending actual native runs.',
        dependency_policy='Fetch-only Cargo may unpack checksum-locked sources. Review every declared dependency build hook and associated command/code paths before the first compile; offline locked builds thereafter.',
        source_review_complete=True,dependency_hook_review_complete=False,target_executed=False))
    print('Preserved exact pinned source/license/build boundary review; dependency hook approval and target execution remain pending.')


if __name__=='__main__':main()
