#!/usr/bin/env python3
"""Read-only validation of the retained corpus, helpers and workflow recipes."""
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path
import yaml  # Validation-only prerequisite; not a Playtestr dependency.

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/validation/ten-project-user-pass'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
ledger=read(DOC/'ledger.json')
assert ledger['status']=='completed_early_p5_reliability'
assert ledger['totals']['final_passed']==330 and ledger['complete_product_campaign_credit']==0
cleanup=read(DOC/'cleanup.json')
assert cleanup['prerequisite_runtime_removed'] and cleanup['clean_source_worktree_removed']
assert not list((ROOT/'.cache/ten-project-apps').iterdir())
assert not (ROOT/'.tools/ten-project-runtime').exists()
assert not (ROOT/'.cache/playtestr-final-source').exists()
for script in (ROOT/'scripts/acceptance').glob('user_*.py'):
    ast.parse(script.read_text(encoding='utf-8'),filename=str(script))
specs=[];workflow_blocks=0
for project in ledger['projects']:
    directory=DOC/project['project']
    config=read(directory/'scenarios.json')
    specs.extend(str(directory/(case['name']+'.json')) for case in config['cases'])
    workflow=yaml.load((directory/'workflow.yml').read_text(encoding='utf-8'),Loader=yaml.BaseLoader)
    assert workflow['jobs']['terminal']['strategy']['matrix']['os']==['ubuntu-24.04']
    assert workflow['permissions']=={'contents':'read'}
    for step in workflow['jobs']['terminal']['steps']:
        if 'run' not in step: continue
        # Expressions are valid template placeholders; static parsing substitutes
        # a neutral token only for bash syntax checking, never executes commands.
        script=re.sub(r'\$\{\{.*?\}\}','template_value',step['run'])
        subprocess.run(['wsl','-d','Ubuntu','--','bash','-n'],input=script.encode(),check=True,timeout=30)
        workflow_blocks+=1
    for name,expected in project['fixture_hashes'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected
        indexed=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
        assert hashlib.sha256(indexed).hexdigest()==expected,('index fixture',name)
    for case in project['final_qualification']['scenarios']:
        for name,expected in case['contract_hashes'].items():
            indexed=subprocess.check_output(['git','show',':'+name],cwd=ROOT)
            assert hashlib.sha256(indexed).hexdigest()==expected,('index contract',name)
    assert (directory/'UPSTREAM-LICENSE.txt').is_file()
assert len(specs)==33
selected=subprocess.run([str(ROOT/'bin/playtestr.exe'),'test','--list',*specs],capture_output=True,text=True,encoding='utf-8',check=True,timeout=30)
# Check local Markdown targets; do not request external URLs or execute links.
markdown=list(DOC.rglob('*.md'))+[ROOT/'roadmap.md',ROOT/'docs/plans/README.md',ROOT/'docs/plans/09-delivery-milestones.md']
for document in markdown:
    for target in re.findall(r'\]\(([^)]+)\)',document.read_text(encoding='utf-8')):
        if target.startswith(('http:','https:','#','app:')):continue
        target=target.split('#',1)[0].split(' "',1)[0]
        if target: assert (document.parent/target).exists(),(document,target)
output=dict(passed=True,source=ledger['final_runner']['source'],primary_specs_listed=33,
            helpers='Python AST syntax passed; campaign execution and real-process controls provide behavioral evidence',
            workflows=10,bash_blocks_syntax_checked=workflow_blocks,local_markdown_targets='passed',
            fixture_hashes='working tree and Git index verified',contract_hashes='Git index matches final executed specs/baselines',cleanup='verified',scope='Read-only package checks; no hosted workflow execution claimed')
(DOC/'package-checks.json').write_text(json.dumps(output,indent=2)+'\n',encoding='utf-8')
print(json.dumps(output))
