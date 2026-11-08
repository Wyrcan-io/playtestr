"""Bind Skim's v14 plan, executable target copies, viewport-bound snapshot, and bounded cache cleanup."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from next20_skim_final_series import BATCHES
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v14 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'skim'
    prior_path = package / 'final-series-declaration-native-exit-v8.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    declaration = dict(prior)
    declaration['replacement_plan_namespace'] = 'final-series-plan-native-exit-v14'
    declaration['batches'] = BATCHES
    declaration['supersedes'] = dict(
        path=prior_path.name,
        sha256=sha256(prior_path),
        reason=(
            'V13 independently audited both plans and attempted candidate execution. Linux '
            'lost executable mode on byte-identical copies made with copyfile and failed all '
            '20 starts. Windows passed 99 cases and N08 failed its exact wrapping snapshot '
            'after viewport expansion. Cache inventories were bounded, but deletion stopped '
            'on read-only Go module/conpty entries; uploaded artifacts also omitted case '
            'evidence. V14 preserves executable metadata, keeps N08 at its reviewed viewport, '
            'retries deletion only within the inventoried allowlisted cache roots, and uploads '
            'case-level evidence.'
        ),
    )
    harness = dict(prior['harness_files'])
    harness['scripts/acceptance/next20_skim_final_declare_v9.py'] = 'staged-self-hash'
    for name in tuple(harness):
        if name == 'scripts/acceptance/next20_skim_final_declare_v9.py':
            continue
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    harness['scripts/acceptance/next20_skim_final_declare_v9.py'] = hashlib.sha256(
        staged_bytes('scripts/acceptance/next20_skim_final_declare_v9.py')).hexdigest()
    declaration['harness_files'] = dict(sorted(harness.items()))
    immutable_json(package / 'final-series-declaration-native-exit-v9.json', declaration)
    print('Declared Skim v14 against staged harness; plan only, zero candidate launches or credit.')


if __name__ == '__main__':
    main()
