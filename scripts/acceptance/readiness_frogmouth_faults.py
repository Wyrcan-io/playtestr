"""Actual editable Python source faults against already frozen native contracts."""
import argparse
import asyncio
import difflib
import hashlib
import json
import platform
import os
from pathlib import Path
import uuid

from adversarial_process import execute
from readiness_frogmouth_first_use import environment,runner as select_runner
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--original-heldout', action='store_true')
    parser.add_argument('--selection',choices=['original'],default='original')
    args = parser.parse_args()
    if platform.system() not in {'Linux', 'Windows'}:
        raise RuntimeError('undeclared frogmouth native host')
    fresh=False
    if args.original_heldout and (platform.system()!='Linux' or os.environ.get('GITHUB_ACTIONS')!='true'):
        raise RuntimeError('original F03 is designated initial hosted Linux only')
    docs = ROOT/'docs/validation/runner-readiness-ten-project-pass/frogmouth'
    profile = docs/'native-profiles/windows' if platform.system() == 'Windows' else docs
    frozen = load(profile/'reviewed-contract-freeze.json')
    package = RAW/'frogmouth/host-contracts'
    for name, digest in frozen['all_package_inputs'].items():
        if sha256(package/name) != digest:
            raise RuntimeError('fault run changed frozen contract or fixture')
    selection = load(docs/('fault-selection-revision-2.json' if fresh else 'fault-selection.json'))
    source_review={r['id']:r for r in load(docs/('source-fault-review-revision-2.json' if fresh else 'source-fault-review.json'))['faults']}
    if selection['frozen_contract_sha256'] != sha256(docs/'reviewed-contract-freeze.json'):
        raise RuntimeError('source selection belongs to another freeze')
    root = RAW/'frogmouth/faults'/uuid.uuid4().hex
    root.mkdir(parents=True)
    faults = [{**f, 'held_out': bool(args.original_heldout and f['id'] == ('F04' if fresh else 'F03'))}
              for f in selection['faults']]
    immutable_json(root/'selected-faults.json', dict(faults=faults,
        frozen_contract_sha256=selection['frozen_contract_sha256'],
        native_freeze_sha256=sha256(profile/'reviewed-contract-freeze.json'),
        execution='Actual editable Python source; no compiled rebuild or installation per mutation.',
        original_heldout=args.original_heldout,selection_revision=2 if fresh else 1))
    active = RAW/'active/frogmouth'
    runtime = load(active/'runtime.json')
    python = Path(runtime['python'])
    if sha256(python) != runtime['python_sha256']:
        raise RuntimeError('installed interpreter changed')
    runner=select_runner()

    async def validate(label):
        syntax = await execute([python, '-c', "import pathlib,sys; compile(pathlib.Path(sys.argv[1]).read_bytes(),sys.argv[1],'exec')", source], 'frogmouth', label+'-syntax',
            env=environment(), timeout=30, campaign=Campaign())
        version = await execute([python,'-m','frogmouth','--version'], 'frogmouth', label+'-version',
            env=environment(), timeout=30, campaign=Campaign())
        if version['output'].strip()!='frogmouth 0.9.1 (Textual v0.53.1)':
            raise RuntimeError('source fault altered version route')
        return dict(syntax_attempt=syntax['id'], version_attempt=version['id'],
                    source_sha256=sha256(source), interpreter_sha256=runtime['python_sha256'])

    async def run(fault, phase, expected):
        report = root/(fault['id']+'-'+phase+'.json')
        attempt = await execute([runner, 'test', '--report', report.relative_to(ROOT),
            '--artifacts-dir', report.with_suffix('').relative_to(ROOT),
            (package/fault['spec']).relative_to(ROOT)], 'frogmouth', fault['id']+'-'+phase,
            env=environment(), expected=expected, timeout=150, campaign=Campaign())
        evidence=load(report)
        if evidence['runner_version']!='source-'+os.environ.get('SOURCE_REVISION','f46f2409985af077fd29723ab963d24792eabbbe'):
            raise RuntimeError('fault runner is not the exact declared source candidate')
        outcome = evidence['results'][0]
        if not outcome['cleanup']['confirmed_exited'] or not outcome['workspace']['cleaned']:
            raise RuntimeError('fault cleanup unconfirmed')
        return attempt, outcome

    receipts = []
    for fault in faults:
        source=active/'src'/fault['path']
        original = source.read_bytes()
        if sha256(source)!=source_review[fault['id']]['original_source_sha256']:
            raise RuntimeError('actual upstream source differs before mutation')
        before, after = fault['before'].encode(), fault['after'].encode()
        if original.count(before) != 1:
            raise RuntimeError('ambiguous upstream source mutation')
        mutated = original.replace(before, after)
        if hashlib.sha256(mutated).hexdigest()!=source_review[fault['id']]['mutated_source_sha256']:
            raise RuntimeError('actual mutation differs from independent source review')
        patch = ''.join(difflib.unified_diff(original.decode().splitlines(True),
            mutated.decode().splitlines(True), fromfile='a/'+fault['path'], tofile='b/'+fault['path']))
        (root/(fault['id']+'.patch')).write_text(patch, encoding='utf-8', newline='\n')
        baseline, _ = await run(fault, 'baseline', 0)
        try:
            source.write_bytes(mutated)
            mutation_validation = await validate(fault['id']+'-mutated')
            mutation, outcome = await run(fault, 'mutated', 1)
            if outcome['status'] != 'failed' or outcome['failure']['category'] != fault['category']:
                raise RuntimeError('wrong real fault diagnosis: '+json.dumps(outcome.get('failure')))
            if fault['id'] in {'F03','F04'}:
                failed = next(i for i, step in enumerate(outcome['steps']) if step['status'] == 'failed')
                prior = outcome['steps'][:failed]
                if not all(s['status'] == 'passed' for s in prior) or not {'snapshot', 'exit'} <= {s['action'] for s in prior}:
                    raise RuntimeError('F03 lacks prior passing screen and exact exit')
                state = outcome['steps'][failed]['state']
                if fault['id']=='F04' and (state['kind']!='entries' or state['path']!='exported'):
                    raise RuntimeError('fresh unwanted-file fault was not caught by the unchanged exact export entry set')
                if state['invocation_id'] != outcome['invocation_id'] or state['workspace_id'] != outcome['workspace']['id']:
                    raise RuntimeError('F03 cross-execution state')
        finally:
            source.write_bytes(original)
            restored_validation = await validate(fault['id']+'-restored')
        if source.read_bytes() != original:
            raise RuntimeError('source restoration changed bytes')
        restored, _ = await run(fault, 'restored', 0)
        receipt = dict(**fault, baseline_attempt=baseline['id'], mutation_attempt=mutation['id'],
            restored_attempt=restored['id'], original_source_sha256=sha256(source),
            mutated_source_sha256=hashlib.sha256(mutated).hexdigest(), restored_exact=True,
            mutation_validation=mutation_validation, restored_validation=restored_validation,
            same_execution_state_rejection=fault['id'] in {'F03','F04'})
        immutable_json(root/(fault['id']+'-receipt.json'), receipt)
        receipts.append(receipt)
        print(fault['id'], 'actual interpreted source fault detected and restored', flush=True)
    immutable_json(root/'summary.json', dict(faults=receipts, runner_sha256=sha256(runner),
        interpreter_sha256=runtime['python_sha256'], source_execution='Actual pinned upstream editable Python source'))


if __name__ == '__main__':
    asyncio.run(main())
