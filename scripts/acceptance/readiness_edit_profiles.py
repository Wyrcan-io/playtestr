"""Explicit source-reviewed editor host differences; no byte normalization."""
import base64
import copy


def native_profile(original,name,windows):
    value=copy.deepcopy(original)
    if windows:return value
    value.pop('inherit_env',None)
    if name=='N02.json':
        states=[s['state'] for s in value['steps'] if s.get('state',{}).get('path')=='new-note.txt']
        if len(states)!=1 or states[0]!={'path':'new-note.txt','kind':'file',
            'bytes_base64':base64.b64encode(b'fresh document').decode()}:
            raise RuntimeError('unexpected frozen new-document contract')
        # Pinned documents.rs sets insert_final_newline(!cfg!(windows)) for new files.
        # Existing-file reads infer their own final-newline policy; E07 remains exact.
        states[0]['bytes_base64']=base64.b64encode(b'fresh document\n').decode()
    return value
