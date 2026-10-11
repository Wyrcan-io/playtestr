"""Native short-alias workspace regression, with exact source restoration."""
import hashlib
import json
import os
from adversarial_process import ROOT,DOC,run

def main():
    if os.name!='nt': raise RuntimeError('Windows-only alias regression')
    path=ROOT/'internal/runner/workspace.go'
    original=path.read_bytes()
    value=original.decode('utf-8').replace('\r\n','\n')
    anchor='\tcreatedRoot := root\n\troot, err = canonicalWorkspaceRoot(root)\n'
    if value.count(anchor)!=1: raise RuntimeError('Workspace normalization anchor ambiguous')
    before=value.replace(anchor,'\tcreatedRoot := root\n\troot, err = root, nil // Original native short-alias behavior.\n')
    command=['go','test','./internal/runner','-run','^TestAdversarialWindowsWorkspaceExpandsShortTemporaryPath$','-count=1','-v']
    try:
        path.write_text(before,encoding='utf-8',newline='\n')
        red=run(command,'core','workspace-short-path-before',expected=1,timeout=60)
        if '--- FAIL: TestAdversarialWindowsWorkspaceExpandsShortTemporaryPath' not in red['output'] or 'before assertion matched' not in red['output']:
            raise RuntimeError('Native alias prerequisite did not expose the original real target failure')
    finally:
        path.write_bytes(original)
    if path.read_bytes()!=original: raise RuntimeError('Workspace source restoration failed')
    green=run(command[:-2]+['-count=10','-v'],'core','workspace-short-path-after',timeout=90)
    if '--- SKIP' in green['output']: raise RuntimeError('Skipped aliases cannot qualify')
    destination=DOC/'core'
    for name,result in [('workspace-short-path-before',red),('workspace-short-path-after',green)]:
        (destination/(name+'.txt')).write_text(result['output'],encoding='utf-8')
    (destination/'workspace-short-path-repair.json').write_text(json.dumps(dict(
        candidate_sha256=hashlib.sha256(original).hexdigest(),before_sha256=hashlib.sha256(before.encode()).hexdigest(),
        before_id=red['id'],after_id=green['id'],after_repetitions=10,
        scope='Real Windows short alias, owned temporary workspace, actual ConPTY target verifies long cwd, confirmed process and workspace cleanup'),indent=2)+'\n',encoding='utf-8')

if __name__=='__main__': main()
