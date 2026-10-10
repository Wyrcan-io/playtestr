#!/usr/bin/env python3
"""Explicit expectation changes: reviewed mismatch, selected update, ordinary run."""
import argparse, json, hashlib
from pathlib import Path
import user_journeys as j

p = argparse.ArgumentParser()
p.add_argument('slug')
a = p.parse_args()
base = j.DOC / a.slug
config = json.loads((base / 'scenarios.json').read_text())
if config.get('runtime_path'):
    import os
    runtime = (j.ROOT / config['runtime_path']).resolve()
    runtime.relative_to((j.ROOT / '.cache/ten-project-apps').resolve())
    os.environ['PATH'] = str(runtime) + os.pathsep + os.environ['PATH']
verified = []
for control in config['maintenance_controls']:
    spec = base / control['spec']
    baseline = base / 'snapshots' / control['baseline']
    # Repeat the explicit old expectation without touching the original contract.
    baseline.write_bytes((base / 'snapshots' / control['old_baseline']).read_bytes())
    before = hashlib.sha256(baseline.read_bytes()).hexdigest()
    label = a.slug + '/intentional-expected-change'
    report = j.RAW / a.slug / 'intentional-expected-change.json'
    j.run([j.BIN, 'test', '--artifacts-dir', j.RAW / a.slug / 'intentional-expected-change-evidence', '--report', report, spec], label, expected=1)
    result = json.loads(report.read_text())['results'][0]
    if result.get('failure', {}).get('category') != 'snapshot_mismatch':
        raise RuntimeError('Intentional change failed outside its reviewed snapshot')
    actual = Path(result['evidence']['screen_path']).read_text()
    if control['changed_text'] not in actual:
        raise RuntimeError('Missing positive evidence for the deliberately changed state')
    j.run([j.BIN, 'test', '--update', '--snapshot', control['baseline'], '--report', j.RAW / a.slug / 'intentional-update.json', spec], a.slug + '/intentional-update')
    text = baseline.read_text()
    if control['changed_text'] not in text:
        raise RuntimeError('Updated baseline does not capture the declared change')
    print('Explicit reviewed baseline:', text, flush=True)
    j.run([j.BIN, 'test', '--report', j.RAW / a.slug / 'intentional-ordinary.json', spec], a.slug + '/intentional-ordinary')
    verified.append(dict(spec=control['spec'], baseline=control['baseline'], before_sha256=before,
                         after_sha256=hashlib.sha256(baseline.read_bytes()).hexdigest(), passed=True))
(j.RAW / a.slug / 'maintenance-summary.json').write_text(json.dumps(verified, indent=2) + '\n')
manual = sorted(base.glob('manual-*.json'))
for spec in manual:
    j.run([j.BIN, 'test', '--report', j.RAW / a.slug / (spec.stem + '-final.json'), spec], a.slug + '/' + spec.stem)
