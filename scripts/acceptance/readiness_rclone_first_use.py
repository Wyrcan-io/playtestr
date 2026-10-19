"""Record, review and replay a real local Rclone configuration wizard."""
import asyncio
import base64
import json
import os
import uuid

from adversarial_process import execute
from readiness_build_rclone import environment
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


async def main():
    target = RAW / 'active/rclone'
    build = load(target / 'build.json')
    executable = target / build['binary_relative_path']
    if sha256(executable) != build['binary_sha256']:
        raise RuntimeError('Rclone compiled target differs from reviewed build')
    root = RAW / 'rclone/first-use' / uuid.uuid4().hex
    fixture = root / 'fixture'
    fixture.mkdir(parents=True)
    seed = {'rclone.conf': b'', 'sentinel.bin': b'preserve\x00existing\r\n'}
    for name, value in seed.items():
        (fixture / name).write_bytes(value)
    expected = {**seed, 'rclone.conf': b'[demo]\ntype = local\n\n'}
    def line(value):
        return '/text ' + json.dumps(value + '\r')
    controls = ['/expect No remotes found, make a new one?', line('n'), '/expect name>', line('demo'),
                '/expect Storage>', line('local'), '/expect Edit advanced config?', line('n'),
                '/expect Keep this "demo" remote?', line('y'), '/expect Current remotes:',
                '/snapshot saved-config.json', line('q'), '/exit 0', '/file rclone.conf', '/file sentinel.bin',
                '/entries .', '/review', '/replay', '/save']
    if len(controls) != 20:
        raise RuntimeError('first-use control budget changed')
    immutable_json(root / 'intent.json', dict(controls=controls,
        expected_files={n:v.hex() for n,v in expected.items()},
        scope='Local unencrypted storage config; each single submitted line follows an observed prompt.',
        handwritten_spec=False, target_build_sha256=sha256(target / 'build.json')))
    binary, frozen, cell = runner()
    env = environment(target)
    env['PATH'] = str(target / 'bin') + os.pathsep + env.get('PATH', '')
    attempts = []
    async def run(argv, label, input=None):
        result = await execute(argv, 'rclone', 'first-use-' + label, env=env, input=input,
                               timeout=180, campaign=Campaign())
        attempts.append(result['id'])
        return result
    version = await run([binary, '--version'], 'exact-archive-version')
    if version['output'].strip() != 'playtestr ' + frozen['version']:
        raise RuntimeError('wrong frozen runner version')
    spec = root / 'spec.json'
    capture = await run([binary, 'record', '--output', spec.relative_to(ROOT), '--fixture', 'fixture',
        '--temporary-home', '--temporary-temp', '--width', '100', '--height', '28',
        '--timeout-ms', '15000', '--run-timeout-ms', '120000', '--env', 'TERM=xterm-256color',
        '--', 'rclone', '--config', 'rclone.conf', 'config'], 'public-record-review-replay-save',
        '\n'.join(controls) + '\n')
    contract = load(spec)
    actual = {s['state']['path']:base64.b64decode(s['state']['bytes_base64'])
              for s in contract['steps'] if s.get('state', {}).get('kind') == 'file'}
    if actual != expected:
        raise RuntimeError('independent saved config or sentinel bytes differ')
    report = root / 'ordinary-results.json'
    ordinary = await run([binary, 'test', '--report', report.relative_to(ROOT), '--artifacts-dir',
                          (root / 'evidence').relative_to(ROOT), spec.relative_to(ROOT)], 'ordinary-test')
    outcome = load(report)
    result = outcome['results'][0]
    if (outcome['runner_version'] != frozen['version'] or result['status'] != 'passed'
            or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']):
        raise RuntimeError('first-use result/version/cleanup unconfirmed')
    immutable_json(root / 'journey.json', dict(attempts=attempts, capture_attempt=capture['id'],
        ordinary_attempt=ordinary['id'], shell_invocations=len(attempts), recorder_controls=len(controls),
        spec_sha256=sha256(spec), runner_sha256=sha256(binary),
        provisional_archive_sha256=cell['archive_sha256'], target_build_sha256=sha256(target/'build.json'),
        handwritten_playtestr_json=False, human_time='unmeasured',
        confounders=['Prepared synthetic fixture', 'Reviewed source familiarity', 'Warm dependency cache'],
        qualification='First route only; twenty scenarios/faults/native admission/final series remain open.'))
    print('Rclone first useful public route:', len(attempts), 'commands;', len(controls), 'controls.')


if __name__ == '__main__':
    asyncio.run(main())
