"""Real tracked JavaScript source faults against unchanged reviewed contracts."""
import argparse
import asyncio
import difflib
import hashlib
import os
from pathlib import Path
import platform
import uuid

from adversarial_process import execute
from readiness_build_hygen import environment as validation_environment
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import environment, runner
from readiness_new_control_matrix import read_json as load


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original-heldout', action='store_true')
    parser.add_argument('--series', choices=['provisional-v1','migration-v2'], default='provisional-v1')
    parser.add_argument('--local-exploratory', action='store_true')
    parser.add_argument('--fault', action='append', choices=['F01', 'F02', 'F03'])
    args = parser.parse_args()
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass/hygen'
    selection = load(docs / 'fault-selection.json')
    review = {r['id']: r for r in load(docs / 'source-fault-review.json')['faults']}
    require(selection['frozen_contract_sha256'] == sha256(docs / 'reviewed-contract-freeze.json'),
            'faults belong to another canonical freeze')
    faults = [r for r in selection['faults'] if not args.fault or r['id'] in args.fault]
    if args.original_heldout:
        require(platform.system() == 'Linux' and os.environ.get('GITHUB_ACTIONS') == 'true'
                and not args.local_exploratory and {r['id'] for r in faults} == {'F01', 'F02', 'F03'}
                and not (docs / 'original-source-faults').exists(), 'F03 original is initial hosted Linux only')
    if args.local_exploratory:
        require(platform.system() == 'Windows' and all(r['id'] != 'F03' for r in faults),
                'local exploration must not consume reserved F03')
        profile = RAW / 'hygen'
        package = profile / 'contracts'
    else:
        require(platform.system() in {'Linux', 'Darwin'}, 'undeclared native fault host')
        profile = docs / 'native-profiles/macos' if platform.system() == 'Darwin' else docs
        package = RAW / 'hygen/host-contracts'
    frozen = load(profile / 'reviewed-contract-freeze.json')
    for name, digest in frozen['all_package_inputs'].items():
        require(sha256(package / name) == digest, 'fault altered frozen contract/fixture')
    root = RAW / 'hygen/faults' / uuid.uuid4().hex
    root.mkdir(parents=True)
    faults = [{**f, 'held_out': bool(args.original_heldout and f['id'] == 'F03')} for f in faults]
    immutable_json(root / 'selected-faults.json', dict(faults=faults,
                   frozen_contract_sha256=selection['frozen_contract_sha256'], native_freeze_sha256=sha256(profile / 'reviewed-contract-freeze.json'),
                   original_heldout=args.original_heldout, local_exploratory=args.local_exploratory,
                   execution='Actual pinned tracked interpreted dist code. No target wrapper fault or expectation edits.'))
    active = RAW / 'active/hygen'
    runtime = load(active / 'runtime.json')
    node = Path(runtime['node'])
    require(sha256(node) == runtime['node_sha256'], 'actual Node executable changed')
    binary, candidate, cell = runner(args.series)

    async def validate(label, source):
        env = validation_environment(active)
        syntax = await execute([node, '--check', source], 'hygen', label + '-syntax', env=env,
                               timeout=30, campaign=Campaign())
        help_result = await execute([node, active / 'src/dist/bin.js', '--help'], 'hygen', label + '-help',
                                    cwd=active / 'validation', env=env, timeout=30, campaign=Campaign())
        require('hygen [option] GENERATOR ACTION' in help_result['output'], 'actual help route changed')
        return dict(syntax_attempt=syntax['id'], help_attempt=help_result['id'], source_sha256=sha256(source),
                    interpreter_sha256=sha256(node))

    async def run(fault, phase, expected):
        report = root / (fault['id'] + '-' + phase + '.json')
        attempt = await execute([binary, 'test', '--report', report.relative_to(ROOT), '--artifacts-dir',
            report.with_suffix('').relative_to(ROOT), (package / fault['spec']).relative_to(ROOT)],
            'hygen', fault['id'] + '-' + phase, env=environment(), expected=expected, timeout=150, campaign=Campaign())
        value = load(report)
        outcome = value['results'][0]
        require(value['runner_version'] == candidate['version'] and outcome['cleanup']['confirmed_exited']
                and outcome['workspace']['cleaned'], 'fault runner or cleanup differs')
        return attempt, outcome

    receipts = []
    for fault in faults:
        source = active / 'src' / fault['path']
        original = source.read_bytes()
        require(sha256(source) == review[fault['id']]['original_source_sha256'], 'upstream source changed before mutation')
        before, after = fault['before'].encode(), fault['after'].encode()
        require(original.count(before) == 1, 'ambiguous actual source mutation')
        mutated = original.replace(before, after)
        require(hashlib.sha256(mutated).hexdigest() == review[fault['id']]['mutated_source_sha256'], 'mutation differs from review')
        patch = ''.join(difflib.unified_diff(original.decode().splitlines(True), mutated.decode().splitlines(True),
                                            fromfile='a/' + fault['path'], tofile='b/' + fault['path']))
        (root / (fault['id'] + '.patch')).write_text(patch, encoding='utf-8', newline='\n')
        baseline, _ = await run(fault, 'baseline', 0)
        try:
            source.write_bytes(mutated)
            mutation_validation = await validate(fault['id'] + '-mutated', source)
            mutation, outcome = await run(fault, 'mutated', 1)
            require(outcome['status'] == 'failed' and outcome['failure']['category'] == fault['category'],
                    'wrong actual source-fault diagnosis')
            if fault['id'] == 'F02':
                require(outcome['target']['exited'] and outcome['target']['exit_code'] == 7, 'fault did not produce actual OS exit7')
            if fault['id'] in {'F01', 'F03'}:
                failed = next(i for i, step in enumerate(outcome['steps']) if step['status'] == 'failed')
                prior = outcome['steps'][:failed]
                require(all(s['status'] == 'passed' for s in prior)
                        and {'snapshot', 'exit'} <= {s['action'] for s in prior}
                        and outcome['target']['exited'] and outcome['target']['exit_code'] == 0,
                        'file fault lacks earlier passing screen and exact exit0')
                state = outcome['steps'][failed]['state']
                require((state['kind'], state['path']) == (('file', 'generated/result.txt') if fault['id'] == 'F01' else ('entries', 'generated'))
                        and state['invocation_id'] == outcome['invocation_id']
                        and state['workspace_id'] == outcome['workspace']['id'], 'wrong or cross-execution saved-state rejection')
                if fault['id'] == 'F03':
                    require(sum(s.get('state', {}).get('kind') == 'file' for s in prior) == 5,
                            'extra-file fault lacks passing exact generated/preserved files')
        finally:
            source.write_bytes(original)
            restored_validation = await validate(fault['id'] + '-restored', source)
        require(source.read_bytes() == original, 'source restoration changed bytes')
        restored, _ = await run(fault, 'restored', 0)
        receipt = dict(**fault, baseline_attempt=baseline['id'], mutation_attempt=mutation['id'], restored_attempt=restored['id'],
                       original_source_sha256=sha256(source), mutated_source_sha256=hashlib.sha256(mutated).hexdigest(),
                       restored_exact=True, mutation_validation=mutation_validation, restored_validation=restored_validation,
                       same_execution_state_rejection=fault['id'] in {'F01', 'F03'})
        immutable_json(root / (fault['id'] + '-receipt.json'), receipt)
        receipts.append(receipt)
        print(fault['id'], 'actual interpreted source fault detected and exactly restored', flush=True)
    immutable_json(root / 'summary.json', dict(faults=receipts, runner_sha256=cell['binary_sha256'],
                   provisional_archive_sha256=cell['archive_sha256'], interpreter_sha256=runtime['node_sha256'],
                   source_execution='Real pinned tracked JavaScript dist code per new process'))


if __name__ == '__main__':
    asyncio.run(main())
