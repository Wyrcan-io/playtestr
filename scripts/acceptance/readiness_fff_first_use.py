"""Public first useful fff recording with independent empty-file and preservation oracles."""
import asyncio
import base64
import json
import os
from pathlib import Path
import platform
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    root = RAW/'fff/first-use'/uuid.uuid4().hex
    fixture = root/'fixture'
    fixture.mkdir(parents=True)
    expected = {'starter.txt': b'reviewed seed\n', 'sentinel.txt': b'preserve existing work\n', 'new note.txt': b''}
    for name in ['starter.txt', 'sentinel.txt']:
        (fixture/name).write_bytes(expected[name])
    controls = ['/expect starter.txt', '/text "f"', '/expect mkfile:', '/text "new note.txt"', '/key Enter',
                '/absent mkfile:', '/expect new note.txt', '/snapshot-rows created.rows.json 1 24', '/text "q"',
                '/exit 0', '/file new note.txt', '/file starter.txt', '/file sentinel.txt', '/entries .',
                '/review', '/replay', '/save']
    immutable_json(root/'intent.json', dict(controls=controls, planned_shell_invocations=3,
                   expected_files={n:b.hex() for n,b in expected.items()}, hand_written_spec=False,
                   snapshot_scope='Declared rows 1..24 show the file list; bottom cwd/status/prompt rows vary with each managed workspace.'))
    runner = RAW/'bin/playtestr'
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    env['PATH'] = str(RAW/'active/fff/src')+os.pathsep+str(Path('/bin/bash').resolve().parent)+os.pathsep+env['PATH']
    attempts = []

    async def run(argv, label, input=None):
        result = await execute(argv, 'fff', 'first-use-'+label, env=env, input=input, timeout=180, campaign=Campaign())
        attempts.append(result['id'])
        return result

    await run([runner, '--version'], 'version-check')
    spec = root/'spec.json'
    capture = await run([runner, 'record', '--output', spec.relative_to(ROOT), '--fixture', 'fixture',
                         '--temporary-home', '--temporary-temp', '--width', '100', '--height', '28',
                         '--timeout-ms', '10000', '--run-timeout-ms', '120000', '--env', 'TERM=xterm-256color',
                         '--env', 'LC_ALL='+('en_US.UTF-8' if platform.system()=='Darwin' else 'C.UTF-8'),
                         '--env', 'FFF_LS_COLORS=0', '--env', 'FFF_CD_ON_EXIT=1', '--env', 'FFF_TRASH=trash',
                         '--', 'fff'], 'public-record-review-replay-export', '\n'.join(controls)+'\n')
    value = json.loads(spec.read_text(encoding='utf-8-sig'))
    actual = {s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in value['steps']
              if s.get('state', {}).get('kind')=='file'}
    if actual != expected:
        raise RuntimeError('independent first-use saved-byte oracle rejects export')
    names = next(s['state']['entries'] for s in value['steps'] if s.get('state', {}).get('kind')=='entries')
    if set(names) != set(expected)|{'trash'} or len(names) != len(set(names)):
        raise RuntimeError('unreviewed first-use directory side effects')
    report = root/'ordinary-results.json'
    ordinary = await run([runner, 'test', '--report', report.relative_to(ROOT), '--artifacts-dir',
                          (root/'evidence').relative_to(ROOT), spec.relative_to(ROOT)], 'ordinary-public-test')
    result = json.loads(report.read_text(encoding='utf-8-sig'))['results'][0]
    if result['status']!='passed' or not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:
        raise RuntimeError('unconfirmed ordinary first-use result/cleanup')
    immutable_json(root/'journey.json', dict(attempts=attempts, capture_attempt=capture['id'], ordinary_attempt=ordinary['id'],
                   shell_invocations=len(attempts), recorder_controls=len(controls), spec_sha256=sha256(spec),
                   runner_sha256=sha256(runner), target_build_sha256=sha256(RAW/'active/fff/build.json'),
                   handwritten_playtestr_json=False, human_time='unmeasured',
                   confounders=['prepared synthetic fixture', 'agent/source familiarity', 'warm installed Bash and runner'],
                   claim='First useful route only; no twenty-scenario, source-fault or project admission credit.'))
    print('First public fff route passes:', len(attempts), 'commands and', len(controls), 'controls; human time unmeasured.')


if __name__ == '__main__':
    asyncio.run(main())
