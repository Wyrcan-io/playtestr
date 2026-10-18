"""Public recording with exact frozen archive bytes and a real Enquirer prompt."""
import asyncio
import base64
import json
import os
from pathlib import Path
import platform
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def runner():
    host = {'Linux': 'linux', 'Darwin': 'darwin', 'Windows': 'windows'}[platform.system()]
    arch = {'x86_64': 'amd64', 'amd64': 'amd64', 'aarch64': 'arm64', 'arm64': 'arm64'}[platform.machine().lower()]
    frozen = load(ROOT / 'docs/validation/runner-readiness-ten-project-pass/provisional-candidate-freeze.json')
    cell = next(r for r in frozen['cells'] if r['host'] == host and r['architecture'] == arch)
    installed = load(RAW / 'private-install/provisional-v1' / (host + '-' + arch) / 'installation.json')
    binary = ROOT / installed['binary']
    if installed['archive_sha256'] != cell['archive_sha256'] or sha256(binary) != cell['binary_sha256']:
        raise RuntimeError('first use must execute exact provisional archive bytes')
    return binary, frozen, cell


def environment():
    target = RAW / 'active/hygen'
    env = {k: os.environ[k] for k in ['PATH', 'PATHEXT', 'SYSTEMROOT', 'WINDIR', 'COMSPEC', 'LANG', 'LC_ALL'] if k in os.environ}
    env['PATH'] = str(target / 'bin') + os.pathsep + env.get('PATH', '')
    env.update(TEMP=str(RAW / 'tmp'), TMP=str(RAW / 'tmp'), TMPDIR=str(RAW / 'tmp'))
    return env


def fixture_files():
    return {
        '.hygen.js': b'module.exports = {};\n',
        '_templates/welcome/new/prompt.js': b"module.exports = [{type:'input',name:'message',message:'Message for file?'}];\n",
        '_templates/welcome/new/hello.ejs.t': b'---\nto: generated/hello.txt\n---\nHello, <%= message %>!\n',
        'sentinel.bin': b'preserve\x00existing\r\n',
    }


async def main():
    root = RAW / 'hygen/first-use' / uuid.uuid4().hex
    fixture = root / 'fixture'
    fixture.mkdir(parents=True)
    seed = fixture_files()
    for name, value in seed.items():
        path = fixture / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    expected = {**seed, 'generated/hello.txt': b'Hello, reviewed!\n'}
    controls = ['/expect Message for file?', '/text "reviewed"', '/expect reviewed',
                '/snapshot-rows prompt.rows.json 1 1', '/key Enter',
                '/expect added: generated/hello.txt', '/exit 0',
                *['/file ' + name for name in expected],
                '/entries .', '/entries generated', '/entries _templates', '/entries _templates/welcome',
                '/entries _templates/welcome/new', '/review', '/replay', '/save']
    if len(controls) != 20:
        raise RuntimeError('declared first-use control budget changed')
    immutable_json(root / 'intent.json', dict(controls=controls, expected_files={n: v.hex() for n, v in expected.items()},
                   handwritten_spec=False, scope='Trusted local Enquirer input/EJS file generation; exact preservation and full fixture entry sets.'))
    binary, frozen, cell = runner()
    attempts = []

    async def run(argv, label, input=None):
        result = await execute(argv, 'hygen', 'first-use-' + label, env=environment(), input=input,
                               timeout=180, campaign=Campaign())
        attempts.append(result['id'])
        return result

    version = await run([binary, '--version'], 'exact-archive-version')
    if version['output'].strip() != 'playtestr ' + frozen['version']:
        raise RuntimeError('first-use archive version changed')
    spec = root / 'spec.json'
    capture = await run([binary, 'record', '--output', spec.relative_to(ROOT), '--fixture', 'fixture',
                         '--temporary-home', '--temporary-temp', '--width', '100', '--height', '28',
                         '--timeout-ms', '15000', '--run-timeout-ms', '120000', '--env', 'TERM=xterm-256color',
                         '--', 'hygen', 'welcome', 'new'], 'public-record-review-replay-save', '\n'.join(controls) + '\n')
    contract = load(spec)
    actual = {s['state']['path']: base64.b64decode(s['state']['bytes_base64'])
              for s in contract['steps'] if s.get('state', {}).get('kind') == 'file'}
    if actual != expected:
        raise RuntimeError('independent generated/preserved byte oracle differs')
    report = root / 'ordinary-results.json'
    ordinary = await run([binary, 'test', '--report', report.relative_to(ROOT), '--artifacts-dir',
                          (root / 'evidence').relative_to(ROOT), spec.relative_to(ROOT)], 'ordinary-test')
    outcome = load(report)
    result = outcome['results'][0]
    if (outcome['runner_version'] != frozen['version'] or result['status'] != 'passed'
            or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']):
        raise RuntimeError('first-use result/version/cleanup unconfirmed')
    immutable_json(root / 'journey.json', dict(attempts=attempts, capture_attempt=capture['id'], ordinary_attempt=ordinary['id'],
                   shell_invocations=len(attempts), recorder_controls=len(controls), spec_sha256=sha256(spec),
                   runner_sha256=sha256(binary), provisional_archive_sha256=cell['archive_sha256'],
                   target_build_sha256=sha256(RAW / 'active/hygen/build.json'), handwritten_playtestr_json=False,
                   human_time='unmeasured', confounders=['Prepared trusted synthetic template', 'Reviewed source familiarity', 'Warm dependencies'],
                   qualification='First route only; twenty scenarios/faults/native admission/final archive series remain open.'))
    print('Hygen first useful public route:', len(attempts), 'commands;', len(controls), 'controls; human time unmeasured.')


if __name__ == '__main__':
    asyncio.run(main())
