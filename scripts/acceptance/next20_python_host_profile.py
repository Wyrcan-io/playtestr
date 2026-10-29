"""Apply only declared native fields in reviewed Python wizard contracts."""
import base64
import copy


def wizard_profile(original, case, python, host):
    if host not in {'linux','windows'}:raise ValueError('undeclared wizard host')
    value=copy.deepcopy(original);argv=value['command']
    if argv.count('--python')!=1:raise ValueError('one explicit target interpreter required')
    argv[argv.index('--python')+1]=str(python)
    if host=='linux':
        value['env']['GIT_CONFIG_GLOBAL']='/dev/null'
        generated=set(case['native_generated_text_paths'])
        preserved=set(case.get('preserve_generated_newlines',[]))
        if not preserved<=generated:raise ValueError('newline preservation must name declared generated paths')
        generated-=preserved
        steps=[]
        for step in value['steps']:
            if step.get('exit')==3221225786:step['exit']=130
            state=step.get('state',{})
            if state.get('path') in generated and 'bytes_base64' in state:
                raw=base64.b64decode(state['bytes_base64'],validate=True)
                state['bytes_base64']=base64.b64encode(raw.replace(b'\r\n',b'\n')).decode()
            steps.append(step)
        eof=[i for i,s in enumerate(steps) if s.get('key')=='CtrlZ']
        if eof:
            if len(eof)!=1 or steps[eof[0]+1]!={'key':'Enter'}:raise ValueError('undeclared EOF group')
            i=eof[0];steps[i:i+2]=[{'key':'CtrlD'}]
        value['steps']=steps
    steps=value['steps'];readiness=case.get('readiness_before_step',{})
    if any(not str(k).isdigit() or not 1<=int(k)<=len(steps) or not isinstance(v,str) or not v for k,v in readiness.items()):
        raise ValueError('invalid declared readiness checkpoint')
    value['steps']=[item for number,step in enumerate(steps,1)
        for item in ([{'expect':readiness[str(number)]},step] if str(number) in readiness else [step])]
    return value
