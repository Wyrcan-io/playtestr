"""A real before/after startup regression; restore candidate bytes even on error."""
import hashlib
import json
import os
from adversarial_process import ROOT,DOC,run

def main():
    if os.name!='nt':
        raise RuntimeError('This startup boundary is Windows-specific')
    path=ROOT/'internal/runner/process_windows.go'
    original=path.read_bytes()
    value=original.decode('utf-8').replace('\r\n','\n')
    guard='\tcmd.SysProcAttr.CreationFlags |= windows.CREATE_SUSPENDED\n'
    activation='func activateProcess(cmd *exec.Cmd) error {\n'
    if value.count(guard)!=1 or value.count(activation)!=1:
        raise RuntimeError('Startup repair anchors must be unique')
    before=value.replace(guard,'\t// Reduced original behavior: execute before attachment.\n').replace(
        activation,activation+'\treturn nil // Original launch had no activation barrier.\n')
    command=['go','test','./internal/runner','-run',
        '^TestAdversarialWindowsImmediateDescendantsCannotEscapeStartup$','-count=1','-v']
    try:
        path.write_text(before,encoding='utf-8',newline='\n')
        red=run(command,'core','detached-startup-before',expected=1,timeout=60)
        if red['output'].count('survived cleanup reported confirmed=true')!=2 or 'fallback cleanup unconfirmed' in red['output']:
            raise RuntimeError('Before control did not isolate two false-cleanup descendants with verified fallback')
    finally:
        path.write_bytes(original)
    if path.read_bytes()!=original:
        raise RuntimeError('Startup repair source restoration failed')
    green=run(command[:-2]+['-count=10','-v'],'core','detached-startup-after',timeout=90)
    # Keep standalone text after raw artifact expiry.
    destination=DOC/'core'
    for name,result in [('startup-before',red),('startup-after',green)]:
        (destination/(name+'.txt')).write_text(result['output'],encoding='utf-8')
    (destination/'startup-repair.json').write_text(json.dumps(dict(
        repair='Create suspended, attach Job Object, resume initial thread',
        candidate_sha256=hashlib.sha256(original).hexdigest(),
        before_sha256=hashlib.sha256(before.encode()).hexdigest(),
        before_id=red['id'],after_id=green['id'],fresh_after_repetitions=10,
        layer='Real ConPTY, delayed Start return, target immediately spawns two detached worker generations; independent process handles verify exit',
        before_scope='Remove only suspended creation and activation barrier; retain same test and all cleanup logic',
        fallback='Exact observed process handles terminated and waited independently in both controls'),indent=2)+'\n',encoding='utf-8')
    print('Detached startup: before false cleanup rejected, after ten passes, source restored')

if __name__=='__main__': main()
