"""Public selected updates, suffix reconstruction and exact Unicode relocation."""
import argparse
import asyncio
import base64
import json
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_cases import entry_sets, text
from readiness_hygen_first_use import environment, runner
from readiness_new_control_matrix import read_json as load


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--package', type=Path, default=RAW / 'hygen/contracts')
    args = parser.parse_args()
    source = args.package.resolve(strict=True)
    source.relative_to(RAW.resolve())
    root = RAW / 'hygen' / ('maintenance caf\u00e9 ' + uuid.uuid4().hex[:10])
    root.mkdir(parents=True)
    package = root / 'package'
    shutil.copytree(source, package)
    binary, candidate, cell = runner()
    attempts = []

    async def run(argv, label, expected=0, input=None):
        result = await execute(argv, 'hygen', 'maintenance-' + label, env=environment(), expected=expected,
                               input=input, timeout=180, campaign=Campaign())
        attempts.append(dict(label=label, id=result['id']))
        return result

    async def test(spec, label, expected=0, extra=()):
        report = root / (label + '.json')
        await run([binary, 'test', *extra, '--report', report.relative_to(ROOT), '--artifacts-dir',
                   (root / (label + '-evidence')).relative_to(ROOT), spec.relative_to(ROOT)], label, expected)
        value = load(report)
        result = value['results'][0]
        require(value['runner_version'] == candidate['version'] and result['cleanup']['confirmed_exited']
                and result['workspace']['cleaned'], 'maintenance runner or cleanup differs')
        return report, result

    spec = package / 'N01.json'
    original = load(spec)
    sentinel = package / 'fixtures/N01/sentinel.bin'
    sentinel.write_bytes(b'reviewed sentinel revision two\x00\r\n')
    report, result = await test(spec, 'intended-file-change', 1)
    require(result['failure']['category'] == 'state_assertion_failure', 'wrong selected file diagnosis')
    await run([binary, 'report', '--input', report.relative_to(ROOT), '--evidence-root', root.relative_to(ROOT),
               '--output', (root / 'diagnosis.html').relative_to(ROOT)], 'offline-diagnosis')
    index = next(i for i, step in enumerate(original['steps']) if step.get('state', {}).get('path') == 'sentinel.bin')
    await run([binary, 'record', '--edit', spec.relative_to(ROOT)], 'selected-file-update',
              input=f'/update-state {index+1}\n/review\n/replay\n/save\n')
    changed = load(spec)
    require(base64.b64decode(changed['steps'][index]['state']['bytes_base64']) == sentinel.read_bytes(),
            'selected file update differs')
    comparison = load(spec)
    comparison['steps'][index] = original['steps'][index]
    require(comparison == original, 'selected state update changed unrelated expectations')
    await test(spec, 'selected-file-replay')

    screen_spec = package / 'E01.json'
    screen = load(screen_spec)
    baseline = next(s['snapshot'] for s in screen['steps'] if 'snapshot' in s)
    before = load(package / 'snapshots' / baseline)
    screen['width'] = 28
    # Preserve the complete filename assertion across its explicitly predicted wrap.
    output_step = next(s for s in screen['steps'] if s.get('expect') == 'added: generated/result.txt')
    output_step['expect'] = 'added: generated/resu\nlt.txt'
    screen_spec.write_text(json.dumps(screen, indent=2) + '\n', encoding='utf-8', newline='\n')
    reviewed_spec = screen_spec.read_bytes()
    _, result = await test(screen_spec, 'intended-viewport-change', 1)
    require(result['failure']['category'] == 'snapshot_mismatch', 'wrong deliberate viewport diagnosis')
    await test(screen_spec, 'selected-screen-update', extra=['--update', '--snapshot', baseline])
    require(screen_spec.read_bytes() == reviewed_spec, 'snapshot update changed contract bytes')
    after = load(package / 'snapshots' / baseline)
    require(after['first_row'] == after['last_row'] == 1 and after['text'] != before['text']
            and after['text'].count('Message for file?') == 1
            and before['text'].rstrip('\n').startswith(after['text'].rstrip('\n')),
            'reviewed viewport-only selected row differs')
    immutable_json(root / 'selected-screen-review.json', dict(original=before, updated=after,
                   original_width=100, updated_width=28,
                   wrapped_output_expectation='added: generated/resu\nlt.txt',
                   scope='Explicit live prompt first-row viewport clipping plus the exact wrapped full-filename assertion. Saved-state expectations stay unchanged; actual snapshots retain exact bytes. No product normalization.'))
    await test(screen_spec, 'selected-screen-replay')

    suffix_fixture = package / 'suffix-fixture'
    shutil.copytree(package / 'fixtures/N01', suffix_fixture)
    suffix = package / 'rerecorded-suffix.json'
    controls = ['/expect Message for file?', '/snapshot-rows suffix-prompt.rows.json 1 1',
                text('wrong'), '/expect wrong', '/rerecord 2', text('corrected'), '/expect corrected',
                '/key Enter', '/expect added: generated/result.txt', '/exit 0']
    expected = {p.relative_to(suffix_fixture).as_posix(): p.read_bytes()
                for p in suffix_fixture.rglob('*') if p.is_file()}
    expected['generated/result.txt'] = b'Hello, corrected!\n'
    controls += ['/file ' + name for name in sorted(expected)]
    controls += ['/entries ' + name for name in sorted(entry_sets(expected))]
    controls += ['/review', '/replay', '/save']
    argv = [binary, 'record', '--output', suffix.relative_to(ROOT), '--fixture', 'suffix-fixture',
            '--temporary-home', '--temporary-temp', '--width', '100', '--height', '28',
            '--timeout-ms', '10000', '--run-timeout-ms', '120000', '--env', 'TERM=xterm-256color',
            '--', *original['command']]
    await run(argv, 'fresh-suffix-rerecord', input='\n'.join(controls) + '\n')
    exported = load(suffix)
    saved = {s['state']['path']: base64.b64decode(s['state']['bytes_base64']) for s in exported['steps']
             if s.get('state', {}).get('kind') == 'file'}
    require(saved == expected and all(s.get('text') != 'wrong' and s.get('expect') != 'wrong'
                                     for s in exported['steps'])
            and sum(s.get('text') == 'corrected' for s in exported['steps']) == 1,
            'discarded suffix input or incorrect file bytes survived reconstruction')
    await test(suffix, 'suffix-ordinary-replay')
    relocated = root / 'relocated \u96ea route'
    shutil.copytree(package, relocated)
    for selected in [spec, screen_spec, suffix]:
        require(sha256(relocated / selected.name) == sha256(selected), 'relocation changed public spec bytes')
        await test(relocated / selected.name, 'relocated-' + selected.stem)
    workflow = root / 'generated-workflow.yml'
    await run([binary, 'workflow', '--source-revision', candidate['source_revision'], '--os', 'linux,macos',
               '--suite', 'artifacts/runner-readiness-ten-project-pass/hygen/host-contracts',
               '--build', 'python3 scripts/acceptance/readiness_hygen_native_prepare.py --target-only',
               '--output', workflow.relative_to(ROOT)], 'generate-ordinary-workflow')
    immutable_json(root / 'journey.json', dict(attempts=attempts, selected_file_controls=4,
                   suffix_controls=len(controls), unrelated_steps_preserved=True, selected_screen_spec_bytes_preserved=True,
                   maintained_spec_sha256=sha256(spec), relocated_spec_sha256=sha256(relocated / spec.name),
                   screen_spec_sha256=sha256(screen_spec), generated_workflow_sha256=sha256(workflow),
                   runner_sha256=cell['binary_sha256'], provisional_archive_sha256=cell['archive_sha256'],
                   phase='reserved provisional transfer', human_time='unmeasured', generated_workflow_execution=False))
    print('Hygen selected file/screen updates, suffix reconstruction and Unicode relocation passed; generated CI remains preparation only.')


if __name__ == '__main__':
    asyncio.run(main())
