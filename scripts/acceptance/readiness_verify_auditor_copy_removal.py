"""Restore the actual final packet and verify native Windows copy removal."""
import asyncio
import os
from pathlib import PurePosixPath
import sys
import tarfile
import uuid

from adversarial_process import execute
from readiness_compact_native import verify
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load


async def main():
    require(os.name=='nt','this cleanup control declares native Windows PowerShell')
    retained=RAW/'plop/retained-native-v4';index=load(retained/'index.json',maximum=4*1024**2)
    verify(retained/'packets.tar.gz',index['files'])
    require(index['runs']==['39672351954'],'different exact final packet')
    root=RAW/'final-auditor-controls'/uuid.uuid4().hex;payload=root/'payload'
    root.mkdir(parents=True);payload.mkdir()
    immutable_json(root/'intent.json',dict(project='plop',host='linux',run='39672351954',controls=0,
        index_sha256=sha256(retained/'index.json'),archive_sha256=sha256(retained/'packets.tar.gz'),
        scope='Restore the already independently verified actual final Linux packet in a new owned copy, then require native Windows PowerShell inventory/removal. No new application or negative-control execution credit.'))
    files={};total=0
    with tarfile.open(retained/'packets.tar.gz','r:gz') as archive:
        for name,record in index['files'].items():
            prefix='native/39672351954/';require(name.startswith(prefix),'packet contains another run')
            relative=name.removeprefix(prefix);path=PurePosixPath(relative)
            require(not path.is_absolute() and all(p not in {'','.','..'} and ':' not in p and '\\' not in p for p in path.parts),
                'unsafe retained evidence path')
            total+=record['bytes'];require(record['bytes']<=4*1024**2 and total<=32*1024**2 and len(files)<10000,'copy restoration bound')
            destination=payload.joinpath(*path.parts);destination.resolve().relative_to(payload.resolve())
            destination.parent.mkdir(parents=True,exist_ok=True)
            with archive.extractfile(record.get('member',name)) as source,destination.open('xb') as output:
                remaining=record['bytes']
                while remaining:
                    data=source.read(min(65536,remaining));require(bool(data),'truncated retained packet')
                    output.write(data);remaining-=len(data)
                require(not source.read(1),'retained member exceeds declared size')
            require(sha256(destination)==record['sha256'],'restored final packet differs');files[relative]=record['sha256']
    immutable_json(root/'payload-index.json',dict(files=files))
    checked=await execute([sys.executable,ROOT/'scripts/acceptance/readiness_final_plop_verify.py','--run','39672351954',
        '--host','linux','--packet-root',payload,'--check-only'],'core','restored-final-packet-before-native-removal',timeout=90,campaign=Campaign())
    removed=await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        ROOT/'scripts/acceptance/readiness_remove_auditor_copy.ps1','-ControlId',root.name],
        'core','restored-final-packet-native-powershell-removal',timeout=120,campaign=Campaign())
    require(not payload.exists() and load(root/'powershell-removed.json')['removed'],'native auditor payload remains')
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/final-auditor-cleanup-verification.json',dict(
        original_controls_sha256=sha256(ROOT/'docs/validation/runner-readiness-ten-project-pass/final-cell-auditor-negative-controls.json'),
        restored_packet_audit=checked['id'],native_removal_attempt=removed['id'],removal_sha256=sha256(root/'powershell-removed.json'),
        restored_files=len(files),restored_bytes=total,owned_copy_removed=True,
        prior_method='The first control copy used hash-checked, owned-path Python removal. Windows copies now use native PowerShell per execution prompt section18; this exact restored packet passed audit and native removal.',
        scope='Cleanup procedure verification using self-contained retained evidence; twelve original specific negative controls remain unchanged.'))
    print('Verified restored actual final packet and native PowerShell owned-copy removal.')


if __name__=='__main__':asyncio.run(main())
