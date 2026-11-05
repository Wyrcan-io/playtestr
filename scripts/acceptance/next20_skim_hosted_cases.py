"""Execute the frozen Skim matrix while preserving every case outcome."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


CASES = [f'N{i:02d}' for i in range(1, 9)] + [f'E{i:02d}' for i in range(1, 13)]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', choices=['linux', 'windows'], required=True)
    parser.add_argument('--rounds', type=int, default=1)
    args = parser.parse_args()
    if not 1 <= args.rounds <= 12:
        raise ValueError('rounds must be between 1 and 12')
    package = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass/skim'
    declaration = json.loads((package / 'scenario-declaration-v5.json').read_text(encoding='utf-8'))
    rows = {row['id']: row for row in declaration['scenarios']}
    if set(rows) != set(CASES):
        raise ValueError('frozen Skim scenario declaration must contain exactly twenty cases')
    evidence = RAW / 'active/skim/case-evidence'
    evidence.mkdir(parents=True, exist_ok=True)
    outcomes = []
    for round_number in range(1, args.rounds + 1):
        for case in CASES:
            row = rows[case]
            spec = package / row['contract']
            if sha256(spec) != row['contract_sha256']:
                raise ValueError('frozen case contract changed: ' + case)
            label = f'{case}-hosted-{args.host}-r{round_number:02d}'
            command = [sys.executable, '-B', 'scripts/acceptance/next20_playtestr_case.py',
                       '--project', 'skim', '--label', label, '--',
                       str(spec.relative_to(ROOT))]
            try:
                result = subprocess.run(command, cwd=ROOT, check=False, timeout=300,
                                        capture_output=True, text=True,
                                        encoding='utf-8', errors='replace',
                                        env=os.environ.copy())
                console = (result.stdout + result.stderr)[-16_384:]
                finished = sorted(evidence.glob('*/finished.json'),
                                  key=lambda p: p.stat().st_mtime, reverse=True)
                match = None
                for path in finished:
                    record = json.loads(path.read_text(encoding='utf-8'))
                    if record.get('label') == label:
                        match = (path, record)
                        break
                if match is None:
                    outcomes.append(dict(case=case, round=round_number, label=label,
                                         process_exit=result.returncode, status='missing-finished-event',
                                         console=console))
                    continue
                path, record = match
                report = record.get('report') or {}
                result_record = (report.get('results') or [{}])[0]
                failure = result_record.get('failure') or {}
                outcomes.append(dict(case=case, round=round_number, label=label,
                                     process_exit=result.returncode, status=record.get('status'),
                                     finished_path=path.relative_to(ROOT).as_posix(),
                                     finished_sha256=sha256(path), report_sha256=record.get('report_sha256'),
                                     target_sha256=record.get('executable_sha256'),
                                     failure_category=failure.get('category'),
                                     failure_message=failure.get('message'),
                                     step_statuses=[step.get('status') for step in result_record.get('steps', [])],
                                     target_exit=(result_record.get('target') or {}).get('exit_code'),
                                     workspace_cleanup=(result_record.get('workspace') or {}).get('cleaned'),
                                     case_error=record.get('error'),
                                     case_console=record.get('console'),
                                     console=console))
            except subprocess.TimeoutExpired as error:
                outcomes.append(dict(case=case, round=round_number, label=label,
                                     status='wrapper-timeout', timeout_seconds=300,
                                     stdout=str(error.stdout or '')[-8192:],
                                     stderr=str(error.stderr or '')[-8192:]))
    passed = sum(item.get('status') == 'completed' and item.get('process_exit') == 0
                 for item in outcomes)
    receipt = dict(schema_version=1, project='skim', host=args.host,
                   source_pin='1ab47f6ba7f1bfc355273bbdd98d4b2056ef95a3',
                   scenario_declaration_sha256=sha256(package / 'scenario-declaration-v5.json'),
                   rounds=args.rounds, expected_cases=20 * args.rounds,
                   completed=len(outcomes), passing=passed, failed=len(outcomes) - passed,
                   outcomes=outcomes)
    out = RAW / 'active/skim' / f'hosted-{args.host}-rounds-{args.rounds:02d}-{uuid.uuid4().hex}.json'
    immutable_json(out, receipt)
    for item in outcomes:
        print(json.dumps({key: item.get(key) for key in (
            'case', 'round', 'status', 'process_exit', 'failure_category',
            'failure_message', 'step_statuses', 'target_exit', 'workspace_cleanup',
            'case_error', 'case_console')},
            ensure_ascii=True))
    print(json.dumps(dict(receipt=str(out.relative_to(ROOT)), completed=len(outcomes),
                          passed=passed, failed=len(outcomes) - passed)))
    if len(outcomes) != 20 * args.rounds or passed != len(outcomes):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
