"""Author portable Poetry profiles before any native target scenario executes."""
import base64
import json
import os
import shutil

from readiness_evidence import RAW, immutable_json, sha256
from readiness_poetry_cases import PACKAGE, rows


def main():
    target=RAW/'poetry/host-contracts'
    target.mkdir(parents=True,exist_ok=False)
    for folder in PACKAGE.iterdir():
        if folder.is_dir():shutil.copytree(folder,target/folder.name)
    contracts=[('N01','normal-init.json'),('N08','normal-build-sdist.json')]+[(r[0],r[1]) for r in rows()]
    records=[]
    for identity,name in contracts:
        source=PACKAGE/name;spec=json.loads(source.read_text())
        differences=[]
        if os.name!='nt':
            spec['env']['GIT_CONFIG_GLOBAL']=os.devnull
            differences.append('native null-device name for isolated synthetic Git configuration')
            # Only newly generated text uses native newline defaults. Existing
            # LF fixtures and their edits preserve the original reviewed bytes.
            if identity in {'N01','N02','E01','E05','E06'}:
                for step in spec['steps']:
                    selected=step.get('state',{})
                    if selected.get('kind')=='file':
                        value=base64.b64decode(selected['bytes_base64'])
                        if b'\r\n' in value:
                            selected['bytes_base64']=base64.b64encode(value.replace(b'\r\n',b'\n')).decode()
                differences.append('reviewed native LF for newly generated TOML; existing LF fixture bytes unchanged')
        (target/name).write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8',newline='\n')
        records.append(dict(id=identity,spec=name,source_sha256=sha256(source),
                            authored_sha256=sha256(target/name),differences=differences))
    immutable_json(target.parent/'host-profile.json',dict(contracts=records,
        source_freeze_sha256=sha256(PACKAGE/'reviewed-contract-freeze.json'),
        windows_resize='E05 red; no Windows cell admission',qualification='authored; execution pending'))
    print('Authored twenty reviewed native Poetry profiles.')


if __name__=='__main__':main()
