"""Bind Skim's v11 zero-launch plan to the complete bounded host workflow."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v11 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v5.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v11'
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V10 independently reconstructed 240 exact Windows contracts with zero target '
            'launches. Final harness review found the source-fault calibration wrapper still '
            'requested 7200 seconds above the same 2400-second command cap that blocked V9. '
            'V11 applies the supported 2400-second cap to both ordinary and fault-series '
            'commands and binds the complete cache cleanup, prepared-inventory removal, '
            'socket-path, and hosted workflow fixes. V10 plan and V9 failures remain preserved '
            'and uncredited.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v6.py'] = 'staged-self-hash'
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v6.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v6.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v6.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v6.json', declaration)
    print('Declared Skim v11 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
