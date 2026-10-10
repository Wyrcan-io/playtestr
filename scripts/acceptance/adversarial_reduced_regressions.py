"""Retain failing-before/passing-after evidence for the short-input repair."""
import hashlib
import json
from adversarial_process import ROOT,DOC,run

def main():
    path=ROOT/'internal/runner/session.go'
    original=path.read_bytes()
    value=original.decode('utf-8').replace('\r\n','\n')
    guard='\t\tif n != len(value) && err == nil {\n\t\t\terr = io.ErrShortWrite\n\t\t}\n'
    if value.count(guard)!=1:
        raise RuntimeError('Reduced repair anchor missing or ambiguous')
    # Before behavior ignored the returned count. Preserve compilability while
    # removing only the new incomplete-write rejection.
    before=value.replace(guard,'\t\t_ = n // original behavior ignored partial input\n')
    command=['go','test','./internal/runner','-run','^TestPartialBackendInputCannotPass$','-count=1','-v']
    try:
        path.write_text(before,encoding='utf-8',newline='\n')
        red=run(command,'core','short-input-before',expected=1,timeout=60)
        if 'incomplete real input reported <nil>' not in red['output'] or 'partial-input target cleanup:' in red['output']:
            raise RuntimeError('Before evidence did not isolate the false passing input action')
    finally:
        path.write_bytes(original)
    if path.read_bytes()!=original:
        raise RuntimeError('Reduced source restoration failed')
    green=run(command,'core','short-input-after',timeout=60)
    destination=DOC/'core'
    destination.mkdir(exist_ok=True)
    (destination/'short-input-repair.json').write_text(json.dumps(dict(
        repair='Reject a backend incomplete write instead of silently passing the action',
        source='internal/runner/session.go',candidate_sha256=hashlib.sha256(original).hexdigest(),
        before_sha256=hashlib.sha256(before.encode()).hexdigest(),before_id=red['id'],after_id=green['id'],
        layer='Fault-injected writer forwards a real byte into a real PTY; actual target and cleanup run in both controls',
        limits='Demonstrates a faulty backend return, not an observed OS short-write or explanation of the wizard timeout'),indent=2)+'\n',encoding='utf-8')
    print('Incomplete-input rejection: before red, after green, source restored')

if __name__=='__main__': main()
