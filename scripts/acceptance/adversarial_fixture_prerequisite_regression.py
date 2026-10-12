"""Real public-CLI reproduction of an empty-directory-free Git fixture checkout."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
from adversarial_process import ROOT,DOC,RAW,run
from adversarial_fixture_directories import prepare

project='lf'
app=ROOT/'.cache/ten-new-project-apps'/project
owner=json.loads((app/'task-owned.json').read_text(encoding='utf-8'))
if owner['project']!=project or owner['workspace']!=str(ROOT):
    raise RuntimeError('Unknown exploratory prerequisite ownership')
package=DOC/project
copy=app/('prerequisite-regression-'+str(time.time_ns()))
copy.mkdir()
for name in ['fixtures','fixtures-empty','snapshots']:
    shutil.copytree(package/name,copy/name)
for name in ['scenarios.json','fixture-directories.json','normal-project.json']:
    shutil.copyfile(package/name,copy/name)
declared=json.loads((copy/'fixture-directories.json').read_text())
for name in declared:
    path=copy/name
    path.resolve(strict=True).relative_to(copy.resolve())
    if path.is_symlink() or getattr(path,'is_junction',lambda:False)():
        raise RuntimeError('Refuse linked owned synthetic directory')
    path.rmdir() # Only the exact newly copied empty directory, nonrecursive.
identity=json.loads((app/'runtime.json').read_text(encoding='utf-8'))
env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'])
binary=ROOT/'bin/playtestr.exe'
spec=copy/'normal-project.json'
baseline=copy/'snapshots/normal-project.rows.json'
hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [spec,baseline]}
report=RAW/project/('missing-empty-directories-'+str(time.time_ns())+'.json')
before=run([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',report.with_suffix('').relative_to(ROOT),spec],
    project,'empty-directory-prerequisite-before',env=env,expected=1)
value=json.loads(report.read_text(encoding='utf-8'))['results'][0]
if value['failure']['category']!='assertion_timeout' or not value['cleanup']['confirmed_exited']:
    raise RuntimeError('Missing-directory reproduction is not the original bounded failure')
screen=ROOT/value['evidence']['screen_path']
screen.resolve().relative_to(RAW.resolve())
if not screen.read_text(encoding='utf-8').startswith('LF 02-nested\n'):
    raise RuntimeError('Missing-directory reproduction did not reach the actual native wrong initial state')
prepare(copy)
after=run([binary,'test',spec],project,'empty-directory-prerequisite-after',env=env)
if {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in [spec,baseline]}!=hashes:
    raise RuntimeError('Prerequisite repair changed approved spec or baseline')
output=package/'fixture-prerequisite-repair.json'
output.write_text(json.dumps(dict(before=before['id'],after=after['id'],contracts=hashes,
    unchanged=True,actual_before_screen_sha256=hashlib.sha256(screen.read_bytes()).hexdigest(),
    actual_before_screen_path=str(screen.relative_to(ROOT)),
    owned_regression_copy=str(copy.relative_to(ROOT)),
    scope='Actual trusted lf binary through ordinary public CLI; empty synthetic directories only restored'),indent=2)+'\n')
print('Actual missing-directory red and unchanged-contract recovery verified')
