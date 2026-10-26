"""Challenge independent yo package reconstruction against actual local bytes."""
import copy
import json
import os
import uuid

from next20_check import RAW, DOC
from next20_verify_yo import dependencies
from readiness_evidence import immutable_json, sha256


def main():
    target=RAW/'active/yo';provenance=json.loads((DOC/'yo/source-provenance.json').read_text())
    def local(name):return target/name.removeprefix('yo/retained-source/')
    def get(name):return json.loads(local(name).read_text())
    cache={'yo/retained-source/'+p.relative_to(target).as_posix():p.read_bytes()
           for p in (target/'npm-cache/_cacache/content-v2').rglob('*') if p.is_file()}
    def raw(name):return cache if name is None else local(name).read_bytes()
    def hash_of(name):return sha256(local(name))
    host='windows' if os.name=='nt' else 'linux'
    result=dependencies(get,raw,hash_of,host,provenance)
    for scope,files in result.items():
        for name,digest in files.items():
            if sha256(target/'runtime'/scope/name)!=digest:raise ValueError('Actual reviewed runtime changed')
    controls=[]
    for control in ['changed-source-lock','changed-installed-module','missing-registry-payloads']:
        def altered_get(name):
            value=get(name)
            if name.endswith('/dependency-fetch.json'):
                value=copy.deepcopy(value)
                if control=='changed-source-lock':value['source_lock_sha256']='0'*64
                if control=='changed-installed-module':value['installed_files']['app']['lib/cli.js']='0'*64
            return value
        def altered_raw(name):return {} if name is None and control=='missing-registry-payloads' else raw(name)
        try:dependencies(altered_get,altered_raw,hash_of,host,provenance)
        except ValueError as error:controls.append(dict(control=control,rejected=True,reason=str(error)))
        else:raise ValueError('Independent yo dependency auditor accepted corruption: '+control)
    root=RAW/'yo/dependency-audits'/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'verified.json',dict(schema_version=1,host=host,source_pin=provenance['pin'],
        reconstructed_files=sum(len(files) for files in result.values()),controls=controls,
        actual_installed_files_match=True,final_ordinary_credit=0,new_project_admissions=0))
    print('Independently reconstructed actual yo runtime and rejected three corrupted package-evidence controls.')


if __name__=='__main__':main()
