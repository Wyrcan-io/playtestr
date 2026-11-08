"""Revalidate and challenge the actual read-back Skim native cell models."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import uuid

from readiness_evidence import immutable_json, sha256

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass'
CASES = {f'N{i:02d}' for i in range(1, 9)} | {f'E{i:02d}' for i in range(1, 13)}
HOSTS = {'linux', 'windows'}
FAULT_IDS = {'SKIM-EXIT-EMPTY-01', 'SKIM-MATCH-COUNT-01', 'SKIM-MULTI-COUNT-01'}


def require(value, message):
    if not value:
        raise ValueError(message)


def validate(model, host):
    require(model.get('project') == 'skim' and model.get('host') == host and host in HOSTS,
            'project/native host identity differs')
    require(model.get('candidate_archive_sha256') and len(model['candidate_archive_sha256']) == 64 and
            model.get('candidate_runner_sha256') and len(model['candidate_runner_sha256']) == 64 and
            model.get('target_binary_sha256') and len(model['target_binary_sha256']) == 64,
            'candidate/target identity is malformed')
    require(model.get('normal_scenarios') == 8 and model.get('edge_scenarios') == 12,
            'canonical normal/edge partition differs')
    rows = model.get('ordinary')
    require(isinstance(rows, list) and len(rows) == 240, 'ordinary execution matrix is incomplete')
    invocations = set()
    for batch in range(12):
        current = [row for row in rows if row.get('batch') == batch]
        require(len(current) == 20 and {row.get('case') for row in current} == CASES,
                'batch has missing or duplicate canonical cases')
        for row in current:
            require(row.get('status') == 'passed' and row.get('contract_reconstructed') is True and
                    all(s == 'passed' for s in row.get('step_statuses', [])) and row.get('step_statuses') and
                    row.get('target_cleanup') is True and row.get('workspace_cleanup') is True,
                    'ordinary model contains nonpositive or unverified evidence')
            require(row.get('candidate_archive_sha256') == model['candidate_archive_sha256'] and
                    row.get('candidate_sha256') == model['candidate_runner_sha256'] and
                    row.get('target_sha256') == model['target_binary_sha256'],
                    'ordinary model mixes candidate or target identity')
            invocation = row.get('invocation_id')
            require(invocation and invocation not in invocations and row.get('workspace_id') == invocation,
                    'ordinary model has duplicate or cross-workspace invocation')
            invocations.add(invocation)
            for field in ('contract_sha256', 'report_sha256'):
                require(len(row.get(field, '')) == 64, 'ordinary model hash is malformed: ' + field)
    require(len(invocations) == 240, 'ordinary invocation count differs')

    faults = model.get('faults')
    require(model.get('distinct_faults') == 3 and model.get('fault_phases') == 9 and
            model.get('source_restored') is True and isinstance(faults, list) and len(faults) == 9,
            'source-fault matrix or restoration is incomplete')
    by_fault = {}
    for row in faults:
        require(row.get('invocation_id'), 'fault phase invocation identity is missing')
        require(row['invocation_id'] not in invocations, 'fault phase reuses an ordinary invocation')
        invocations.add(row['invocation_id'])
    for row in faults:
        by_fault.setdefault(row.get('fault_id'), {})[row.get('phase')] = row
    require(set(by_fault) == FAULT_IDS and all(set(phases) == {'baseline', 'corrupted', 'restored'}
                                      for phases in by_fault.values()),
            'declared source fault lacks baseline/corrupted/restored phases')
    for phases in by_fault.values():
        base, corrupted, restored = (phases[name] for name in ('baseline', 'corrupted', 'restored'))
        require(base.get('status') == 'passed' and restored.get('status') == 'passed' and
                corrupted.get('status') == 'failed' and corrupted.get('target_sha256') != model['target_binary_sha256'],
                'source mutation lacks a detected negative between positive controls')
        require(all(row.get('target_cleanup') is True and row.get('workspace_cleanup') is True and
                    row.get('source_restored') is True and row.get('detected') is True and
                    row.get('runner_sha256') == model['candidate_runner_sha256']
                    for row in phases.values()), 'fault cleanup/restoration/candidate binding is incomplete')
    return dict(native_host=host, canonical_scenarios=20, ordinary=240, faults=3,
                calibration_phases=9, positive_matrix=True, source_restoration=True)


def challenge(model, host):
    validate(model, host)
    patches = [
        ('wrong-project', ['project'], 'fork'),
        ('wrong-host', ['host'], 'macos'),
        ('mixed-archive', ['candidate_archive_sha256'], '0' * 64),
        ('mixed-runner', ['candidate_runner_sha256'], '0' * 64),
        ('mixed-target', ['ordinary', 0, 'target_sha256'], '0' * 64),
        ('missing-execution', ['ordinary'], model['ordinary'][:-1]),
        ('duplicate-case', ['ordinary', 1, 'case'], model['ordinary'][0]['case']),
        ('duplicate-invocation', ['ordinary', 1, 'invocation_id'], model['ordinary'][0]['invocation_id']),
        ('false-green', ['ordinary', 0, 'status'], 'failed'),
        ('unconfirmed-process-cleanup', ['ordinary', 0, 'target_cleanup'], False),
        ('missing-restoration-phase', ['faults'], [row for row in model['faults'] if not
                                                  (row['fault_id'] == model['faults'][0]['fault_id'] and row['phase'] == 'restored')]),
        ('false-green-mutation', ['faults', 1, 'status'], 'passed'),
    ]
    observations = []
    for name, path, replacement in patches:
        altered = copy.deepcopy(model)
        parent = altered
        for key in path[:-1]:
            parent = parent[key]
        parent[path[-1]] = replacement
        try:
            validate(altered, host)
        except (ValueError, KeyError, TypeError, IndexError) as error:
            canonical = json.dumps(altered, sort_keys=True, ensure_ascii=True,
                                   separators=(',', ':')).encode('utf-8')
            observations.append(dict(control=name, rejected=True, reason=str(error), path=path,
                                     altered_model_sha256=hashlib.sha256(canonical).hexdigest()))
        else:
            raise ValueError('tampered Skim model was accepted: ' + name)
    validate(model, host)
    return observations


def run(inputs):
    cells = []
    run_ids = set()
    revisions = set()
    freeze_path = DOC/'replacement-candidate-freeze-native-exit-v1.json'
    freeze = json.loads(freeze_path.read_text(encoding='utf-8'))
    for host in ('linux', 'windows'):
        path = inputs[host]
        readback = json.loads(path.read_text(encoding='utf-8'))
        model = readback['actual_model']
        run_ids.add(readback.get('run_id'))
        revisions.add(readback.get('revision'))
        counts = validate(model, host)
        frozen = [row for row in freeze['cells'] if row.get('host') == host]
        require(len(frozen) == 1 and isinstance(readback.get('run_id'), int) and
                len(readback.get('revision', '')) == 40 and
                model['candidate_archive_sha256'] == frozen[0]['archive_sha256'] and
                model['candidate_runner_sha256'] == frozen[0]['binary_sha256'],
                'actual model differs from the exact frozen native candidate')
        controls = challenge(model, host)
        encoded = json.dumps(model, sort_keys=True, ensure_ascii=True,
                             separators=(',', ':')).encode('utf-8')
        require(len(encoded) <= 8 * 1024**2, 'actual reconstructed model exceeds retention bound')
        cells.append(dict(host=host, readback=path.relative_to(DOC).as_posix(),
                          readback_sha256=sha256(path), model=model,
                          model_sha256=hashlib.sha256(encoded).hexdigest(),
                          counts=counts, controls=controls))
    require(len(run_ids) == 1 and len(revisions) == 1, 'native cell models come from different hosted runs/revisions')
    return dict(schema_version=1, project='skim', candidate='v0.4.0-rc.6',
                source_run_id=next(iter(run_ids)), source_revision=next(iter(revisions)),
                cells=cells, semantic_corruptions_rejected=sum(len(cell['controls']) for cell in cells),
                scope='Twelve independent semantic challenges against each actual provider-read-back native cell model. Inputs bind exact reports/contracts/exits/cleanup and reconstructed contracts; no project or campaign admission is inferred.')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--linux', type=Path, default=DOC/'skim/artifact-retrieval-readback-v14-linux.json')
    parser.add_argument('--windows', type=Path, default=DOC/'skim/artifact-retrieval-readback-v14-windows.json')
    parser.add_argument('--output', type=Path, default=DOC/'skim-model-controls-v1.json')
    args = parser.parse_args()
    result = run({'linux': args.linux.resolve(strict=True), 'windows': args.windows.resolve(strict=True)})
    if args.output.exists():
        if json.loads(args.output.read_text(encoding='utf-8')) != result:
            raise ValueError('existing Skim model-control receipt differs; declare a new version')
    else:
        immutable_json(args.output, result)
    print('Skim actual native model controls passed:', result['semantic_corruptions_rejected'],
          'corruptions rejected; both positive models restored.')


if __name__ == '__main__':
    main()
