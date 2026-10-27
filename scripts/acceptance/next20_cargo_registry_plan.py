"""Plan one exact registry dictionary from actual recorded native compile commands."""
import hashlib
import json
import re
import tarfile

from next20_check import RAW,ROOT,DOC
from readiness_evidence import immutable_json,sha256
from readiness_compact_native import verify


def packages(data,known):
    observed=set()
    for name,version in re.findall(r'^\s*Compiling ([^\s]+) v([^\s]+)',data.decode('utf-8'),re.M):
        if name=='cargo-generate' and version=='0.25.1':continue
        filename=name+'-'+version+'.crate'
        if filename not in known:raise ValueError('actual compiled package absent from the reviewed lock: '+filename)
        observed.add(filename)
    return observed


def main():
    target=RAW/'active/cargo-generate';fetched=json.loads((target/'dependency-fetch-review.json').read_text())
    known={name.split('/')[-1]:dict(row,original_source=name) for name,row in fetched['files'].items()}
    if len(known)!=len(fetched['files']):raise ValueError('ambiguous locked registry archive basenames')
    windows=set();subjects=[]
    for eid,code in [('888f28d071ad4225a1940766d43340a0',101),('82b607164dca4e0795d39314bdf48f5a',101),('26a0ba75c7824b62ab07373c032357f8',0)]:
        finished=json.loads((RAW/'events'/(eid+'-finished.json')).read_text());console=RAW/'cargo-generate'/eid/'console.log'
        if finished['project']!='cargo-generate' or finished['exit_code']!=code or sha256(console)!=finished['console_sha256']:raise ValueError('original Windows compile outcome/log changed')
        selected=packages(console.read_bytes(),known);windows.update(selected)
        subjects.append(dict(host='windows',attempt=eid,exit_code=code,console_sha256=sha256(console),compiled_packages=len(selected)))
    retained=RAW/'cargo-generate/retained-native-v1';index=json.loads((retained/'index.json').read_text());archive=retained/'packets.tar.gz'
    if sha256(archive)!=index['archive_sha256']:raise ValueError('original native Linux packet changed')
    verify(archive,index['files'])
    prefix='native/40462439055/next20-cargo-linux-preflight/'
    with tarfile.open(archive,'r:gz') as stream:
        def payload(name):
            row=index['files'][name];data=stream.extractfile(row.get('member',name)).read(row['bytes']+1)
            if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('original native compile member changed')
            return data
        build=json.loads(payload(prefix+'active/cargo-generate/build.json'));eid=build['build_attempt']
        finished=json.loads(payload(prefix+'events/'+eid+'-finished.json'));console=payload(prefix+'cargo-generate/'+eid+'/console.log')
        if finished['exit_code']!=0 or hashlib.sha256(console).hexdigest()!=finished['console_sha256']:raise ValueError('original Linux compile log/outcome differs')
        linux=packages(console,known);subjects.append(dict(host='linux',run='40462439055',attempt=eid,exit_code=0,
            console_sha256=finished['console_sha256'],compiled_packages=len(linux)))
    if len(windows)<50 or len(linux)<50:raise ValueError('actual compile closure is unexpectedly incomplete; do not prune')
    selected=windows|linux;unused=set(known)-selected
    for name in selected:
        if sha256(target/known[name]['original_source'])!=known[name]['sha256']:raise ValueError('selected locked archive changed')
    immutable_json(DOC/'cargo-generate/compiled-registry-retention-plan.json',dict(schema_version=1,
        lock_sha256=fetched['lock_sha256'],actual_compile_subjects=subjects,
        windows_compiled_packages=sorted(windows),linux_compiled_packages=sorted(linux),
        selected_archives={n:known[n] for n in sorted(selected)},selected_compressed_bytes=sum(known[n]['bytes'] for n in selected),
        unused_fetch_only_archives={n:known[n] for n in sorted(unused)},unused_compressed_bytes=sum(known[n]['bytes'] for n in unused),
        policy='Conservative union of actual recorded native default-feature compilation logs, including preserved failed Windows source attempts. This is compiled-source retention, not runtime branch/feature coverage. Retain selected exact locked archives once across hosts; unused fetched package hashes/licenses/hook/source catalogs remain historical source-only metadata with no execution claim. No deletion performed by this plan.',
        retained_source_dictionary_counted_against_project_and_aggregate_caps=True,project_credit=0))
    print('Actual native compiled-source union:',len(selected),'of',len(known),'archives;',sum(known[n]['bytes'] for n in selected),'bytes; unused fetch-only:',len(unused))


if __name__=='__main__':main()
