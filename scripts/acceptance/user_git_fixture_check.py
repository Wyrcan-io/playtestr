#!/usr/bin/env python3
"""Prove fixture commit independence from checkout executable permissions."""
import json, os, shutil, subprocess, tempfile
from pathlib import Path
import user_journeys as j

fixtures=j.DOC/'lazygit/fixtures'
original=(fixtures/'launch.py').read_text()
block="for fixture_name in ('seed.txt', 'config.yml', 'launch.py'):\n    fixture_path = Path(fixture_name)\n    fixture_path.write_bytes(fixture_path.read_bytes().replace(b'\\r\\n', b'\\n'))\n    os.chmod(fixture_name, 0o755)\n"
assert block in original
hashes={}
for variant in ('before','after'):
    hashes[variant]=[]
    # Equal launcher bytes across the two initial-mode cases; before/after are
    # separate helper implementations and not expected to share a commit hash.
    body=original.replace(block,'') if variant=='before' else original
    for initial_mode, initial_newline in ((0o644,'LF'),(0o755,'CRLF')):
        with tempfile.TemporaryDirectory(prefix='playtestr-git-fixture-') as tmp:
            cwd=Path(tmp)/'fixture';shutil.copytree(fixtures,cwd)
            (cwd/'launch.py').write_text(body)
            for file in cwd.iterdir():
                content=file.read_bytes().replace(b'\r\n',b'\n')
                file.write_bytes(content.replace(b'\n',b'\r\n') if initial_newline=='CRLF' else content)
                os.chmod(file,initial_mode)
            subprocess.run(['python3','launch.py','--git','/usr/bin/true'],cwd=cwd,check=True,timeout=20)
            hashes[variant].append(subprocess.check_output(['git','rev-parse','HEAD'],cwd=cwd,text=True,timeout=10).strip())
assert hashes['before'][0]!=hashes['before'][1]
assert hashes['after'][0]==hashes['after'][1]
output=dict(passed=True,initial_modes=['0644/LF','0755/CRLF'],commit_hashes=hashes,
            behavior='Actual synthetic Git commit differed before normalization and is identical after; native temporary filesystems, no target application substitute.')
(j.RAW/'lazygit/fixture-mode-regression.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps(output))
