"""Restore the original reviewed synthetic Git metadata into a fresh package."""
import hashlib
from pathlib import PurePosixPath
import tarfile

from readiness_evidence import RAW, ROOT, sha256
from readiness_new_control_matrix import read_json as load


def metadata():
    original=ROOT/'docs/validation/ten-new-project-adversarial-pass/copier'
    archive=original/'synthetic-git-metadata.tar.gz'
    if archive.stat().st_size>2*1024**2 or sha256(archive)!=load(original/'synthetic-git-identity.json')['archive_sha256']:
        raise RuntimeError('original synthetic Git archive changed')
    roots={'fixtures/templates/update/.git','fixtures/updated/.git',
        'fixtures-dirty/templates/update/.git','fixtures-dirty/updated/.git'}
    payloads={};total=0
    with tarfile.open(archive,'r:gz') as stream:
        for member in stream:
            path=PurePosixPath(member.name)
            if (not member.isfile() or path.is_absolute() or '..' in path.parts or ':' in member.name
                    or '\\' in member.name or member.name!=path.as_posix()
                    or not any(member.name.startswith(root+'/') for root in roots)
                    or member.name.casefold() in {n.casefold() for n in payloads}
                    or member.size<0 or member.size>1024**2):
                raise RuntimeError('unsafe synthetic Git metadata')
            if '/hooks/' in member.name and not member.name.endswith('.sample'):
                raise RuntimeError('active Git hook in synthetic fixture')
            total+=member.size
            if total>4*1024**2 or len(payloads)>=1000:raise RuntimeError('synthetic Git metadata bound')
            payloads[member.name]=stream.extractfile(member).read(member.size+1)
            if len(payloads[member.name])!=member.size:raise RuntimeError('truncated Git metadata')
    config=('[core]\n\trepositoryformatversion = 0\n\tfilemode = false\n\tbare = false\n'
        '\tlogallrefupdates = true\n\tsymlinks = false\n\tignorecase = true\n\tautocrlf = false\n'
        '[user]\n\tname = Synthetic validation\n\temail = synthetic@example.invalid\n').encode()
    if any(payloads.get(root+'/config')!=config for root in roots):raise RuntimeError('unreviewed synthetic Git config')
    return payloads


def restore(package):
    package.resolve(strict=True).relative_to(RAW.resolve())
    payloads=metadata()
    for name in payloads:
        path=package/name
        if path.exists() or path.is_symlink():raise RuntimeError('refuse existing synthetic Git metadata')
        for parent in path.parents:
            if parent==package:break
            if parent.is_symlink() or getattr(parent,'is_junction',lambda:False)():raise RuntimeError('linked Git destination')
    for name,payload in payloads.items():
        path=package/name;path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(payload)
    return {name:hashlib.sha256(payload).hexdigest() for name,payload in payloads.items()}
