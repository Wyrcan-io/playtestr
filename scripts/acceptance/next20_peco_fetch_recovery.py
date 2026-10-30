"""Retain the refused checksum supplement, restore primary bytes, reuse actual fetch."""
import hashlib
import json
import tarfile

from next20_check import DOC,RAW,ROOT
from readiness_evidence import immutable_json,sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    target=RAW/'active/peco';package=DOC/'peco';root=RAW/'peco/module-fetch-revision-v2';root.mkdir(parents=True,exist_ok=False)
    primary=json.loads((package/'source-provenance.json').read_text())['files'];source=target/'src'
    changed=[n for n,d in primary.items() if sha256(source/n)!=d];require(changed==['go.sum'],'unexpected primary mutation')
    actual=(source/'go.sum').read_bytes()
    with tarfile.open(target/'source.tar.gz','r:gz') as archive:
        members=[m for m in archive if m.name.endswith('/go.sum') and len(m.name.split('/'))==2]
        require(len(members)==1 and members[0].isfile(),'original pinned checksum member ambiguous');original=archive.extractfile(members[0]).read()
    require(hashlib.sha256(original).hexdigest()==primary['go.sum'] and set(original.splitlines())<=set(actual.splitlines()),'original checksum bytes removed/changed')
    (root/'original.go.sum').write_bytes(original);(root/'download-supplement.go.sum').write_bytes(actual)
    helper=ROOT/'scripts/acceptance/next20_go_fetch.py'
    # Preserve the actual first helper before any later repair; its prelaunch
    # identity is retained with the original failed wrapper.
    helper_body=helper.read_bytes();(root/'original-fetch-helper.py').write_bytes(helper_body)
    events={}
    for label,eid in [('settings','9a44359f1a3e4395a76b22c78a1cad99'),('download','f3c26dce6f37426ba17482087fcef211')]:
        started=json.loads((RAW/'events'/(eid+'-started.json')).read_text());finished=json.loads((RAW/'events'/(eid+'-finished.json')).read_text())
        require(started['project']=='peco' and finished['category']=='passed' and finished['harness_cleanup']=='harness_process_reaped','actual successful fetch/settings missing')
        body=(RAW/'peco'/eid/'console.log').read_bytes();require(hashlib.sha256(body).hexdigest()==finished['console_sha256'],'original fetch console differs')
        events[label]=(eid,body.decode('utf-8-sig'))
    decoder=json.JSONDecoder();text=events['download'][1];rows=[]
    while text.strip():
        row,end=decoder.raw_decode(text.lstrip());text=text.lstrip()[end:];rows.append(row)
        require(len(rows)<=100 and not row.get('Error'),'actual module fetch incomplete/bound')
    declaration=dict(schema_version=1,original_refused_wrapper='a4624027cbd4466c94a90e92c0a5c681',original_download_attempt=events['download'][0],
        original_go_sum_sha256=hashlib.sha256(original).hexdigest(),supplement_go_sum_sha256=hashlib.sha256(actual).hexdigest(),
        added_checksum_lines=[l.decode() for l in actual.splitlines() if l not in original.splitlines()],
        source_action='Restore exact original go.sum after retaining both byte versions. Preserve all module caches and actual successful download event; no refetch.',
        target_built=False,target_executed=False,allow_execution=False,
        scope='The broad all-module graph download added transitive checksums not present in the pinned file. This failed the guard as intended. These are separately reviewed acquisition inputs,not a silent source/lock repair or target qualification.')
    immutable_json(package/'module-fetch-checksum-disposition-v2.json',declaration)
    (source/'go.sum').write_bytes(original)
    for name,digest in primary.items():require(sha256(source/name)==digest,'primary source restoration failed')
    immutable_json(target/'module-fetch.json',dict(schema_version=2,modules=rows,settings=json.loads(events['settings'][1]),settings_attempt=events['settings'][0],download_attempt=events['download'][0],
        compiler=json.loads((target/'go-fetch-plan.json').read_text())['compiler'],compiler_sha256=json.loads((target/'go-fetch-plan.json').read_text())['compiler_sha256'],
        target_built=False,target_executed=False,source_restored_exact=True,checksum_disposition_sha256=sha256(package/'module-fetch-checksum-disposition-v2.json'),
        scope='Original successful module download reused without refetch. Original primary source restored byte-exact; supplement retained separately for full review before build approval.'))
    print('Retained',len(declaration['added_checksum_lines']),'new checksum lines; restored every primary source byte; reused',len(rows),'actual module downloads for review. No build/execution approval.')


if __name__=='__main__':main()
