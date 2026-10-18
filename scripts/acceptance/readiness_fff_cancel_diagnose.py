"""Bounded unchanged E03 reproduction; independent Bash PTY comparison."""
import asyncio
import json
import os
import sys
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_fff_cases import environment
from readiness_fff_input_diagnose import probe


async def main():
    if os.name == 'nt':
        raise RuntimeError('native Unix PTY required')
    root = RAW / 'fff/cancel-diagnostics' / uuid.uuid4().hex
    root.mkdir(parents=True)
    spec = RAW / 'fff/host-contracts/E03.json'
    immutable_json(root / 'intent.json', dict(
        first_failure_run='39146617427', public_repetitions=20,
        public_contract_sha256=sha256(spec), independent_repetitions=12,
        independent_mode='backspace-batched',
        limit='Each public attempt 130 seconds; each independent probe twelve seconds plus bounded shutdown; parent 900 seconds.',
        hypothesis='The empty-rename prompt disappears before Bash accepts the final quit, or pending input is lost across repeated terminal-mode transitions.',
        confounders='Independent raw-PTY probe has one source file, no filtered selection and no Playtestr; it is a comparison, not an identical replay.',
        changes='None to frozen public actions, assertions, target source or product deadlines.',
        qualification_credit=False))
    public = []
    for number in range(20):
        report = root / ('public-' + str(number) + '.json')
        try:
            await execute([RAW / 'bin/playtestr', 'test', '--report', report.relative_to(ROOT),
                           '--artifacts-dir', (root / ('evidence-' + str(number))).relative_to(ROOT),
                           spec.relative_to(ROOT)], 'fff', 'unchanged-current-E03-' + str(number),
                          env=environment(), timeout=130, campaign=Campaign())
        except RuntimeError:
            if not report.is_file():
                raise
        result = json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
        if not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
            raise RuntimeError('public diagnostic cleanup unconfirmed')
        public.append(dict(number=number, status=result['status'], failure=result.get('failure'),
                           report_sha256=sha256(report)))
        print('Current E03', number, result['status'], result.get('failure'), flush=True)
    independent = [probe(root, 'backspace-batched', number) for number in range(12)]
    immutable_json(root / 'summary.json', dict(public=public, independent=independent,
                   qualification_credit=False,
                   claim='All diagnostic attempts retained; successful repeats do not erase the first failed qualification.'))


if __name__ == '__main__':
    asyncio.run(main())
