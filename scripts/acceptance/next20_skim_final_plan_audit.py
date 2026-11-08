"""Independently reconstruct every frozen Skim final-series contract before launch."""
import argparse
import copy
import json
from pathlib import Path
import platform
import shutil

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


PIN = '1ab47f6ba7f1bfc355273bbdd98d4b2056ef95a3'
CASES = [f'N{i:02d}' for i in range(1, 9)] + [f'E{i:02d}' for i in range(1, 13)]
BATCHES = [
    ('ordinary-cold-1', 'First logical use of fresh SHA-256-verified owned target copy A.'),
    ('ordinary-warm-1', 'Reuse exact target copy A from batch 0; no OS cache eviction claim.'),
    ('ordinary-cold-2', 'First logical use of independent fresh SHA-256-verified owned target copy B.'),
    ('ordinary-warm-2', 'Reuse exact target copy B from batch 2; no OS cache eviction claim.'),
    ('viewport', 'Increase width by 10 and height by 2 on N01-N07, E01-E02, E07-E12; preserve N08 exact wrapping snapshot and explicit parser, small-screen, and resize boundaries.'),
    ('spaced-unicode-path', 'Run exact target copy B from an owned path containing spaces and café 雪; no contract assertions retuned.'),
    ('ordinary-input-readiness', 'Frozen supported input and positive checkpoints unchanged.'),
    ('segmented-printable-input', 'Split printable text writes longer than three Unicode code points into bounded ordered chunks.'),
    ('bounded-contention-1', 'One owned 2-second 8-MiB SHA-256 worker per invocation.'),
    ('bounded-contention-2', 'A second independent bounded 2-second 8-MiB SHA-256 worker window.'),
    ('highest-risk-small-completion', 'N01 height reduced to 12; other frozen risk boundaries remain unchanged.'),
    ('highest-risk-startup-boundary', 'Set positive-output startup deadline to 2000 ms; exact-first-exit parser cases retain startup gate 0.'),
]


def actual_host():
    return {'Windows':'windows','Linux':'linux'}.get(platform.system())


def split_text(steps):
    result = []
    for step in steps:
        if (set(step) == {'text'} and len(step['text']) > 1 and
                all(ord(ch) >= 32 and ord(ch) != 127 for ch in step['text'])):
            result.extend({'text':step['text'][i:i+3]} for i in range(0, len(step['text']), 3))
        else:
            result.append(copy.deepcopy(step))
    return result


def reconstruct(batch, case, canonical, target_path):
    value = copy.deepcopy(canonical)
    value['workspace']['fixture'] = f'fixtures/{case}'
    if Path(value['command'][0]).name.lower() in {'sk', 'sk.exe'}:
        value['command'][0] = str(target_path)
    if batch == 4 and case not in {'N08','E03','E04','E05','E06'}:
        value['width'] += 10
        value['height'] += 2
    if batch == 7:
        value['steps'] = split_text(value['steps'])
    if batch == 10 and case == 'N01':
        value['height'] = 12
    if batch == 11 and case not in {'E03','E04'}:
        value['startup_timeout_ms'] = 2000
    return value


def inventory(directory):
    output = {}
    for path in sorted(directory.rglob('*')):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('linked fixture/snapshot is refused')
        if path.is_file():
            output[path.relative_to(directory).as_posix()] = sha256(path)
    return output


def audit(plan_path):
    plan_path = plan_path.resolve(strict=True)
    plan_path.relative_to(RAW.resolve(strict=True))
    plan = json.loads(plan_path.read_text(encoding='utf-8'))
    host = actual_host()
    package = ROOT/'docs/validation/runner-readiness-next-twenty-project-pass/skim'
    declaration_path = package/'final-series-declaration-native-exit-v31.json'
    declaration = json.loads(declaration_path.read_text(encoding='utf-8'))
    base_path = package/'scenario-declaration-v5.json'
    revision_path = package/'scenario-declaration-v6.json'
    base = json.loads(base_path.read_text(encoding='utf-8'))
    revision = json.loads(revision_path.read_text(encoding='utf-8'))
    cases = {row['id']:row for row in base['scenarios']}
    cases.update({row['id']:row for row in revision['replacements']})
    if (host != plan.get('host') or plan.get('source_pin') != PIN or declaration.get('source_pin') != PIN or
            set(cases) != set(CASES) or len(plan.get('batches', [])) != 12 or
            plan.get('expected_ordinary') != 240 or plan.get('scenario_base_sha256') != sha256(base_path) or
            plan.get('scenario_revision_sha256') != sha256(revision_path) or
            plan.get('declaration_sha256') != sha256(declaration_path)):
        raise ValueError('Skim final plan, declarations, or native host do not agree')
    freeze_path = ROOT/'docs/validation/runner-readiness-next-twenty-project-pass/replacement-candidate-freeze-native-exit-v1.json'
    freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
    freeze_rows = [row for row in freeze['cells'] if row['host'] == host]
    if len(freeze_rows) != 1:
        raise ValueError('candidate freeze is missing/duplicated for host')
    frozen_candidate = freeze_rows[0]
    candidate_dir = RAW/'candidate-native-exit-v1'/host
    candidate_name = 'playtestr.exe' if host == 'windows' else 'playtestr'
    candidate = candidate_dir/candidate_name
    install = json.loads((candidate_dir/'installed.json').read_text(encoding='utf-8'))
    if (sha256(candidate) != frozen_candidate['binary_sha256'] or
            sha256(candidate) != plan.get('candidate_sha256') or
            install.get('archive_sha256') != frozen_candidate['archive_sha256'] or
            plan.get('candidate_archive_sha256') != frozen_candidate['archive_sha256'] or
            sha256(freeze_path) != declaration.get('candidate_freeze_sha256')):
        raise ValueError('installed runner differs from frozen native rc.6 archive')
    target_root = RAW/'active/skim'
    build = json.loads((target_root/'build.json').read_text(encoding='utf-8'))
    target_hash = build.get('binary_sha256')
    if target_hash != plan.get('target_sha256') or build.get('pin') != PIN:
        raise ValueError('pinned target build identity differs from frozen plan')
    for relative in ('bin/sk.exe','final-series-copies-v12/cold-warm-a/sk.exe','final-series-copies-v12/cold-warm-b/sk.exe'):
        binary = target_root/relative
        if sha256(binary) != target_hash:
            raise ValueError('fresh/warm target copy mismatch: '+relative)

    expected_batches = []
    contract_checks = []
    contract_root = RAW/'skim/final-contracts/native-exit-v26'/host
    if len(plan['batches']) != len(BATCHES):
        raise ValueError('wrong final batch denominator')
    for batch_id, ((name, change), actual) in enumerate(zip(BATCHES, plan['batches'])):
        if actual.get('batch') != {'id':batch_id,'name':name,'change':change} or len(actual.get('cases', [])) != 20:
            raise ValueError('batch profile changed or case count is not twenty')
        expected_batch_cases = []
        target_name = {0:'final-series-copies-v12/cold-warm-a/sk.exe',1:'final-series-copies-v12/cold-warm-a/sk.exe',
            2:'final-series-copies-v12/cold-warm-b/sk.exe',3:'final-series-copies-v12/cold-warm-b/sk.exe',
            4:'bin/sk.exe',5:'final-series-copies-v12/relocated café 雪/sk.exe',6:'bin/sk.exe',7:'bin/sk.exe',
            8:'bin/sk.exe',9:'bin/sk.exe',10:'bin/sk.exe',11:'bin/sk.exe'}[batch_id]
        absolute_target = target_root/target_name
        target_value = str(absolute_target.resolve(strict=False))
        for case in CASES:
            actual_case = actual['cases'][CASES.index(case)]
            row = cases[case]
            canonical_path = package/row['contract']
            if sha256(canonical_path) != row['contract_sha256']:
                raise ValueError('canonical case hash differs: '+case)
            expected_contract = reconstruct(batch_id, case,
                json.loads(canonical_path.read_text(encoding='utf-8')), target_value)
            planned_path = (ROOT/actual_case['contract']).resolve(strict=True)
            planned_path.relative_to(contract_root.resolve(strict=True))
            observed_contract = json.loads(planned_path.read_text(encoding='utf-8'))
            if observed_contract != expected_contract or sha256(planned_path) != actual_case['contract_sha256']:
                raise ValueError(f'batch {batch_id} {case}: prepared contract differs from independent reconstruction')
            fixture = planned_path.parent/'fixtures'/case
            original_fixture = canonical_path.parent/json.loads(canonical_path.read_text(encoding='utf-8'))['workspace']['fixture']
            if inventory(fixture) != inventory(original_fixture.resolve(strict=True)):
                raise ValueError(f'batch {batch_id} {case}: fixture bytes differ')
            for step in expected_contract['steps']:
                snapshot = step.get('snapshot')
                if snapshot and sha256(planned_path.parent/'snapshots'/snapshot) != sha256(package/'snapshots'/snapshot):
                    raise ValueError(f'batch {batch_id} {case}: snapshot bytes differ')
            if actual_case.get('case') != case or actual_case.get('target_binary_sha256') != target_hash:
                raise ValueError('case or target identity differs from frozen target')
            expected_batch_cases.append(case)
            contract_checks.append(dict(batch=batch_id,case=case,contract_sha256=sha256(planned_path),fixture_files=len(inventory(fixture))))
        expected_batches.append(dict(id=batch_id,name=name,cases=expected_batch_cases))
    return dict(schema_version=1,project='skim',host=host,plan_sha256=sha256(plan_path),
        declaration_sha256=sha256(declaration_path),candidate_sha256=sha256(candidate),
        candidate_archive_sha256=frozen_candidate['archive_sha256'],target_sha256=target_hash,
        batches=expected_batches,contracts_verified=len(contract_checks),contract_checks=contract_checks,
        scenario_count=20,ordinary_executions_planned=240,calibrations_planned=9,
        executed_cases=0,scope='Independent prelaunch reconstruction; verifies the exact plan and generated fixture/snapshot inputs, but grants no execution or admission credit.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.plan)
    out = args.plan.parent/'plan-audit.json'
    immutable_json(out, result)
    print('Independently reconstructed',result['contracts_verified'],'exact final case contracts; zero target launches.')


if __name__ == '__main__':
    main()
