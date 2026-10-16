"""Prepare explicitly reviewed native launch/screen profiles, before target runs."""
import json
import os
import shutil

from readiness_evidence import RAW, immutable_json, sha256
from readiness_plop_cases import PACKAGE, cases


def main():
    target=RAW/'plop/host-contracts'
    if target.exists():raise RuntimeError('refuse to replace an authored host profile')
    target.mkdir(parents=True)
    shutil.copytree(PACKAGE/'fixture',target/'fixture')
    shutil.copytree(PACKAGE/'snapshots',target/'snapshots')
    records=[]
    for identity,filename,generator,_ in cases():
        original=PACKAGE/filename
        spec=json.loads(original.read_text(encoding='utf-8'))
        differences=[]
        if os.name!='nt':
            args=['--no-progress']+([] if generator in {None,'artifact'} else ['--plopfile','extended.cjs'])+([generator] if generator else [])
            spec['command']=['plop',*args];differences.append('native POSIX launcher argv')
            if identity=='E04':
                next(s for s in spec['steps'] if 'exit' in s)['exit']=130
                differences.append('POSIX SIGINT exit 130, Windows shell exit 1')
            if identity=='E05':
                spec['steps']=[s for s in spec['steps'] if not s.get('wait_for_redraw')]
                differences.append('Inquirer list has no resize listener; require semantic selected-generator prompt after navigation, not unsolicited application redraw')
        data=(json.dumps(spec,indent=2,ensure_ascii=True)+'\n').encode()
        (target/filename).write_bytes(data)
        records.append(dict(id=identity,spec=filename,source_sha256=sha256(original),
                            authored_sha256=sha256(target/filename),differences=differences))
    if os.name!='nt':
        # Explicit platform baseline, derived from the reviewed prompt/result
        # format and POSIX path separator, never from captured target output.
        (target/'snapshots/normal-artifact.txt').write_bytes('? Artifact name alpha\n\u2714  ++ /out/alpha.txt\n'.encode())
    immutable_json(target.parent/'host-profile.json',dict(schema_version=1,contracts=records,
        snapshot_sha256=sha256(target/'snapshots/normal-artifact.txt'),
        windows_resize='E05 remains an open bounded transport-fence failure; no Windows project qualification',
        qualification='authored only; actual ordinary tests must pass'))
    print('Prepared reviewed native profile:',target)


if __name__=='__main__':main()
