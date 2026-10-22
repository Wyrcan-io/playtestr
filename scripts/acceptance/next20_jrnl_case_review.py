"""Preserve and correct two unexecuted development declarations from source review."""
import json

from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'jrnl';declaration=package/'scenarios.json'
    original=json.loads(declaration.read_text())
    immutable_json(RAW/'jrnl/declaration-review/v1.json',original)
    changes=[]
    for name in ['edge-interrupted-multi.json','edge-wrong-type.json']:
        path=package/name;spec=json.loads(path.read_text())
        immutable_json(RAW/'jrnl/declaration-review'/('v1-'+name),spec)
        old=sha256(path)
        if name=='edge-interrupted-multi.json':
            spec['steps'][5]={'expect':'Aborted by user'}
            why='Pinned MsgText.KeyboardInterruptMsg renders Aborted by user, not the internal enum name.'
        else:
            folder=package/'fixtures/e11-config-dir';folder.mkdir()
            (folder/'config.yaml').mkdir()
            (folder/'config.yaml/owned-marker.txt').write_bytes(b'synthetic directory at config path\n')
            (folder/'journal.txt').write_bytes((package/'fixture/journal.txt').read_bytes())
            spec['workspace']['fixture']='fixtures/e11-config-dir'
            spec['name']='Refuse a directory supplied as the configuration file and preserve journal'
            payload=__import__('base64').b64encode((folder/'journal.txt').read_bytes()).decode()
            spec['steps']=[{'expect':'Error'},{'exit':1},
                {'state':{'path':'journal.txt','kind':'file','bytes_base64':payload}},
                {'state':{'path':'config.yaml','kind':'directory'}},
                {'state':{'path':'.','kind':'entries','entries':['config.yaml','journal.txt']}}]
            why='Source explicitly supports directory journals. The actual wrong-type refusal belongs to the configuration file, whose reader requires a regular file.'
        path.write_text(json.dumps(spec,ensure_ascii=True,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        row=next(c for c in original['cases'] if c['spec']==name)
        row['spec_sha256']=sha256(path)
        if name=='edge-wrong-type.json':
            row.update(task=spec['name'],risk='Directory where configuration file is required',initial_fixture='fixtures/e11-config-dir')
        changes.append(dict(spec=name,before_sha256=old,after_sha256=sha256(path),reason=why,previously_executed=False))
    original['development_revision']=2
    declaration.write_text(json.dumps(original,ensure_ascii=True,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'declaration-review.json',dict(schema_version=1,changes=changes,
        source='Pinned target source inspection before first twenty-case execution; no observed failures or project credit.',
        preserved_original_local_only='artifacts/runner-readiness-next-twenty-project-pass/jrnl/declaration-review/'))
    print('Corrected two unexecuted case declarations from actual source; original declarations retained.')


if __name__=='__main__':main()
