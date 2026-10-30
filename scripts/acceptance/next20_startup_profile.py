"""Apply a declared positive-output or exact-first-exit tight startup boundary."""
import copy


def tight_startup(original,case,deadline_ms):
    if type(deadline_ms)!=int or not 1<=deadline_ms<=5000:raise ValueError('undeclared tight startup deadline')
    value=copy.deepcopy(original)
    mode=case.get('startup_evidence','terminal-output')
    if mode=='terminal-output':value['startup_timeout_ms']=deadline_ms
    elif mode=='exact-first-exit':
        steps=value['steps']
        if not steps or set(steps[0])!={'exit'} or type(steps[0]['exit'])!=int or value.get('startup_timeout_ms',0)!=0:
            raise ValueError('exact-first-exit startup requires a declared first exact exit and no output-readiness gate')
        if not 1<=value['timeout_ms']<=deadline_ms or not 1<=value['run_timeout_ms']<=deadline_ms:
            raise ValueError('quiet exact completion must already have the whole-run and step boundary')
        value['startup_timeout_ms']=0
    else:raise ValueError('undeclared positive startup evidence mode')
    return value
