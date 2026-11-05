"""Bind Git Town v18 to the audited startup measurement and retained packet paths."""
import hashlib
import json
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import immutable_json, sha256


def staged_bytes(name):
    result = subprocess.run(['git', 'show', ':' + name], cwd=ROOT,
                            capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError('v18 harness file is not staged: ' + name)
    data = result.stdout
    if name.lower().endswith(('.py', '.ps1', '.yml', '.yaml')):
        data = data.replace(b'\r\n', b'\n')
    return data


def main():
    package = DOC / 'git-town'
    prior_path = package / 'final-series-declaration-native-exit-v17.json'
    prior = json.loads(prior_path.read_text(encoding='utf-8'))
    if prior.get('revision') != 17 or prior.get('candidate_series') != 'native-exit-v1':
        raise ValueError('prior Git Town final declaration is not preserved v17')
    declaration = dict(prior)
    declaration['revision'] = 18
    declaration['startup_timeout_ms_by_host'] = dict(linux=6000, windows=2000)
    batches = [dict(row) for row in prior['batches']]
    batches[11]['change'] = (
        'Linux 6000 ms and Windows 2000 ms first-output startup boundaries; '
        'v17 Linux reached the 5000 ms boundary but timed out before first rendered output; '
        'ordinary step/run budgets unchanged')
    declaration['batches'] = batches
    declaration['supersedes'] = dict(path=prior_path.name, sha256=sha256(prior_path), reason=(
        prior['supersedes']['reason'] +
        ' V17 run 41988031958 fixed the Linux generated contract at the declared 5000 ms, '
        'but its batch-11 N01 startup still timed out at 5040 ms with exit 130; the target '
        'process and workspace were cleaned. All ten preceding Linux N01 reports passed, '
        'each taking about 5050-5067 ms for the first expected output, so v18 raises only '
        'this declared startup edge boundary to 6000 ms. The ordinary 20 s step and 60 s '
        'run limits do not change. Windows passed 240 cases and nine fault phases. The '
        'v17 artifact omitted active case-evidence, fault-build, and mutated-binary records, '
        'so its fault matrix cannot be independently audited; v18 includes those bounded '
        'paths. V17 also let the shared batch helper record its legacy v1 variation/declaration '
        'metadata; v18 passes the selected declaration into that helper and audits the exact '
        'v18 values. Preserve all v17 outcomes without credit or retry credit.'))
    harness = dict(prior['harness_files'])
    for name in [
        'scripts/acceptance/next20_git_town_final_declare_v18.py',
        'scripts/acceptance/next20_git_town_final_series.py',
        'scripts/acceptance/next20_jrnl_final.py',
        'scripts/acceptance/next20_startup_profile.py',
        'scripts/acceptance/test_next20_startup_profile.py',
        'scripts/acceptance/next20_target_cleanup.py',
        'scripts/acceptance/test_next20_target_cleanup.py',
        '.github/workflows/runner-readiness-next20-git-town-final.yml',
    ]:
        harness[name] = hashlib.sha256(staged_bytes(name)).hexdigest()
    declaration['harness_files'] = {
        name: hashlib.sha256(staged_bytes(name)).hexdigest() for name in sorted(harness)
    }
    summary = dict(declaration['revision_summary'])
    summary['preserved_failed_runs'] = list(summary['preserved_failed_runs']) + ['41988031958']
    declaration['revision_summary'] = summary
    immutable_json(package / 'final-series-declaration-native-exit-v18.json', declaration)
    print('Declared a fresh Git Town v18 series with a measured 6000 ms Linux startup edge and retained calibration evidence; zero admission credit.')


if __name__ == '__main__':
    main()
