"""Run one bounded engineering check with prelaunch immutable evidence."""
import argparse
import asyncio
import os
import sys
sys.dont_write_bytecode = True

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT


def main():
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser()
    parser.add_argument('--label', required=True)
    parser.add_argument('--timeout', type=int, default=300)
    parser.add_argument('--expected', type=int, default=0)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    argv = args.command
    if argv and argv[0] == '--': argv = argv[1:]
    if not argv or not 1 <= args.timeout <= 1200: parser.error('command and bounded timeout required')
    env = dict(os.environ)
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    for name, folder in [('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('GOTMPDIR','tmp'),
                         ('GOCACHE','go-cache'),('GOPATH','gopath'),('GOMODCACHE','gopath/pkg/mod')]:
        path = RAW/folder
        path.mkdir(parents=True, exist_ok=True)
        env[name] = str(path)
    result = asyncio.run(execute(argv, 'core', args.label, cwd=ROOT, env=env,
                                timeout=args.timeout, expected=args.expected, campaign=Campaign()))
    print(result['output'][-12000:])
    print('Evidence:', result['directory'].relative_to(ROOT))


if __name__ == '__main__': main()
