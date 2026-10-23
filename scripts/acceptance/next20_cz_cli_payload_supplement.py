"""Capture exact already-recorded local compiled bytes; no scenario reruns."""
import asyncio
import hashlib
import json
import shutil

from next20_check import RAW,DOC,ROOT
from next20_cz_cli_rebuild import rebuild
from next20_compiled_payloads import capture
from readiness_evidence import immutable_json,sha256


async def main():
    target=RAW/'active/cz-cli';package=DOC/'cz-cli';source=target/'src'
    provenance=json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))
    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8'));app=target/runtime['app_relative_path']
    build=json.loads((target/'build.json').read_text(encoding='utf-8'))
    original_payloads=capture(app,build['compiled_files'])
    fetched=json.loads((target/'dependency-fetch.json').read_text(encoding='utf-8'))
    locks=target/'npm-installed-locks';locks.mkdir();lock_payloads={}
    for label,folder in [('build-toolchain',target/'build-toolchain'),('app',app)]:
        original=folder/'node_modules/.package-lock.json';expected=fetched['installed_files'][label]['node_modules/.package-lock.json']
        if sha256(original)!=expected:raise ValueError('Recorded installed lock bytes changed')
        copy=locks/(label+'.json');shutil.copyfile(original,copy)
        if sha256(copy)!=expected:raise ValueError('Recorded installed lock payload copy differs')
        lock_payloads[label]=dict(path=copy.relative_to(target).as_posix(),sha256=expected)
    declaration=json.loads((package/'fault-declaration.json').read_text(encoding='utf-8'))
    previous=RAW/'cz-cli/faults/3bdec96f6f2346b494c2a629ca4bfeb5/summary.json'
    observed=json.loads(previous.read_text(encoding='utf-8'));supplements=[]
    for fault in declaration['faults']:
        path=source/fault['path'];original=path.read_bytes()
        mutated=original.replace(fault['before'].encode(),fault['after'].encode())
        if original.count(fault['before'].encode())!=1:raise ValueError('Original calibrated source anchor changed')
        try:
            path.write_bytes(mutated);expected=dict(provenance['files']);expected[fault['path']]=hashlib.sha256(mutated).hexdigest()
            actual=await rebuild(expected,'evidence-only-compiled-byte-supplement-'+fault['id'])
            old=next(f for f in observed['faults'] if f['id']==fault['id'])
            recorded=next(p for p in old['outcomes'] if p['phase']=='mutated')['compiled_build']['compiled_files']
            if actual['compiled_files']!=recorded:raise ValueError('Rebuilt code bytes differ from original actual recorded calibration')
            supplements.append(dict(fault=fault['id'],original_summary_sha256=sha256(previous),rebuilt=actual))
        finally:
            path.write_bytes(original)
            restored=await rebuild(provenance['files'],'evidence-only-original-compiled-restore-'+fault['id'])
            if restored['compiled_files']!=build['compiled_files']:raise ValueError('Original compiled bytes not restored after supplement')
    immutable_json(RAW/'cz-cli/compiled-byte-supplement.json',dict(schema_version=1,original_payloads=original_payloads,
        installed_lock_payloads=lock_payloads,original_build_sha256=sha256(target/'build.json'),supplements=supplements,
        scope='Later payload capture/reconstruction matches the exact SHA256s already recorded in genuine original build/calibrations. No Playtestr test or application scenario rerun, no new ordinary/native/calibration/project credit.',
        source_restored=True,compiled_original_restored=True))
    print('Captured original and three calibrated code variants matching every original recorded compiled hash; restored original. Zero scenario/native credit.')


if __name__=='__main__':asyncio.run(main())
