#!/usr/bin/env python3
"""Real-process failure controls for independent campaign state probes."""
import json, sys, tempfile, time
from pathlib import Path
import user_journeys as j

results = []
with tempfile.TemporaryDirectory(prefix='playtestr-probe-control-') as directory:
    assert j.probe_bytes([sys.executable, '-c', "print('caf\\u00e9')"], directory) == b'caf\xc3\xa9\n'
    results.append('exact Unicode success')
    for name, code, expected in [
        ('nonzero', 'raise SystemExit(7)', 'nonzero'),
        ('output flood', "import sys; sys.stdout.buffer.write(b'x'*(5*1024*1024))", 'output limit'),
        ('timeout', 'import time; time.sleep(30)', 'deadline'),
    ]:
        started = time.monotonic()
        try:
            j.probe_bytes([sys.executable, '-c', code], directory)
        except RuntimeError as error:
            assert expected in str(error), str(error)
            assert time.monotonic() - started < 13
            results.append(name + ': bounded error and reaped owned process')
        else:
            raise AssertionError(name + ' failed to reject')
(j.RAW / 'state-probe-controls.json').write_text(json.dumps(dict(passed=True, checks=results), indent=2) + '\n')
print(results)
