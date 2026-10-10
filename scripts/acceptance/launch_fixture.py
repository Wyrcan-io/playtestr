#!/usr/bin/env python3
"""Explicit local Git fixture setup, then exec the actual unmodified target.

There is no synthetic screen/output substitute. Public specs opt into this
reviewable setup helper only when a fresh .git cannot be retained as a fixture.
"""
import os
from pathlib import Path
import subprocess
import sys

if sys.argv[1] != '--git' or not Path('seed.txt').is_file() or Path('.git').exists():
    raise SystemExit('Expected fresh synthetic seed.txt fixture without .git')
env=dict(os.environ,GIT_CONFIG_GLOBAL=os.devnull,GIT_CONFIG_SYSTEM=os.devnull,
         GIT_AUTHOR_DATE='2020-01-01T00:00:00+0000',GIT_COMMITTER_DATE='2020-01-01T00:00:00+0000',
         GIT_TERMINAL_PROMPT='0')
for fixture_name in ('seed.txt', 'config.yml', 'launch.py'):
    fixture_path = Path(fixture_name)
    fixture_path.write_bytes(fixture_path.read_bytes().replace(b'\r\n', b'\n'))
    os.chmod(fixture_name, 0o755)
for args in [('init','-q','-b','main'),('config','user.name','Synthetic Author'),
             ('config','user.email','synthetic@example.invalid'),('config','commit.gpgsign','false'),
             ('add','.'),('commit','-qm','Synthetic initial state')]:
    subprocess.run(['git',*args],env=env,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=10)
Path('seed.txt').write_bytes(b'synthetic edited\n')
os.execvpe(sys.argv[2],sys.argv[2:],env)
