"""Materialize an explicit native profile from cargo-generate's frozen contracts."""
import copy
import json
import os
from pathlib import Path
import platform

from next20_check import RAW,ROOT,DOC
from readiness_evidence import immutable_json,sha256


def main():
    host={'Windows':'windows','Linux':'linux'}[platform.system()]
    project='cargo-generate';package=DOC/project;target=RAW/'active'/project
    freeze_path=package/'development-test-freeze.json';freeze=json.loads(freeze_path.read_text())
    declaration_path=package/'scenarios.json';declaration=json.loads(declaration_path.read_text())
    if sha256(declaration_path)!=freeze['scenarios_sha256']:raise ValueError('canonical scenario declaration changed')
    runtime=json.loads((target/'runtime.json').read_text());build=json.loads((target/'build.json').read_text())
    binary=Path(runtime['native']);binary.resolve(strict=True).relative_to(target.resolve(strict=True))
    if runtime['kind']!='native' or sha256(binary)!=runtime['native_sha256'] or build['binary_sha256']!=runtime['native_sha256']:
        raise ValueError('host profile requires exact actual compiled native target')
    output=RAW/project/'host-contracts'
    if output.exists():raise ValueError('preserve completed native contract profile')
    # Verify the complete canonical contract before publishing the native copy.
    for name,digest in freeze['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('frozen canonical input changed')
    output.mkdir(parents=True)
    for directory in freeze['directories']:(output/directory).mkdir(parents=True,exist_ok=True)
    spec_names={c['spec'] for c in declaration['cases']}
    for name,digest in freeze['inputs'].items():
        if name in spec_names:continue
        destination=output/name;destination.parent.mkdir(parents=True,exist_ok=True)
        with destination.open('xb') as stream:stream.write((package/name).read_bytes())
        if sha256(destination)!=digest:raise ValueError('native fixture/snapshot copy differs')
    cases=[];changes=[]
    if host=='linux':
        profile_path=package/'native-linux-profile-review-v2.json';profile=json.loads(profile_path.read_text())
        native_snapshot=package/profile['native_snapshot'];copied_snapshot=output/'snapshots/normal-project.rows.json'
        if sha256(native_snapshot)!=profile['native_snapshot_sha256'] or sha256(copied_snapshot)!=profile['canonical_snapshot_sha256']:
            raise ValueError('reviewed native snapshot profile or original canonical snapshot differs')
        copied_snapshot.write_bytes(native_snapshot.read_bytes())
        changes.append(dict(path='snapshots/normal-project.rows.json',canonical_sha256=profile['canonical_snapshot_sha256'],
            native_sha256=sha256(copied_snapshot),review_sha256=sha256(profile_path),reason='Exact normal native emoji rendering; identical selected rows and semantic text. No normalization or assertions removed.'))
    for case in declaration['cases']:
        spec=package/case['spec'];value=json.loads(spec.read_text());native=copy.deepcopy(case)
        original_command=value['command'][0];value['command'][0]=os.path.relpath(binary,output).replace('\\','/')
        delta=dict(case=case['id'],command_executable_before=original_command,command_executable_after=value['command'][0])
        if host=='linux':
            if value.get('env',{}).get('GIT_CONFIG_GLOBAL')!='nul':raise ValueError('canonical Git null-device profile changed')
            value['env']['GIT_CONFIG_GLOBAL']='/dev/null'
            delta['git_config_global']=dict(before='nul',after='/dev/null',reason='native null-device spelling; no user Git config inheritance')
            value['env'].update(profile['native_environment'])
            delta['native_environment']=profile['native_environment']
        if 'native_exit_profile' in case:
            status=case['native_exit_profile'][host];exits=[s for s in value['steps'] if 'exit' in s]
            if len(exits)!=1:raise ValueError('ambiguous native cancellation expectation')
            delta.update(expected_exit_before=exits[0]['exit'],expected_exit_after=status)
            exits[0]['exit']=status;native['expected_exit']=status
        destination=output/case['spec'];immutable_json(destination,value)
        native.update(canonical_sha256=sha256(spec),spec_sha256=sha256(destination));cases.append(native);changes.append(delta)
    immutable_json(output/'scenarios.json',dict(declaration,cases=cases,host=host,
        canonical_declaration_sha256=sha256(declaration_path),development_freeze_sha256=sha256(freeze_path),
        native_binary_sha256=sha256(binary),changes=changes,
        profile_scope='Explicit executable, Git null-device, UTF-8 locale, native cancellation and reviewed exact Linux emoji snapshot profile. Original canonical inputs, fixtures, saved-state assertions, selected row range and interactions unchanged. Actual execution still required.'))
    print('Prepared20 frozen native contracts:',host,'no execution or admission credit')


if __name__=='__main__':main()
