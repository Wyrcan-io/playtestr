"""Extract the exact retained native archive into this campaign, without rebuilding."""
import hashlib
import argparse
import json
import os
import platform
import tarfile
import zipfile

from next20_check import RAW,ROOT
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume-empty',action='store_true')
    parser.add_argument('--archive');args=parser.parse_args()
    host={'Windows':'windows','Linux':'linux','Darwin':'darwin'}[platform.system()]
    freeze=json.loads((ROOT/'docs/validation/runner-readiness-ten-project-pass/migration-candidate-freeze.json').read_text())
    row=next(r for r in freeze['cells'] if r['host']==host)
    archive=(ROOT/(args.archive or row['archive_local_only'])).resolve(strict=True)
    archive.relative_to(ROOT)
    if sha256(archive)!=row['archive_sha256']:raise ValueError('frozen candidate archive mismatch')
    output=RAW/'candidate'/host
    if output.exists():
        if not args.resume_empty or any(output.iterdir()):raise ValueError('candidate already present; verify and reuse existing bytes')
    else:output.mkdir(parents=True)
    members=[]
    prefix=archive.name.removesuffix('.tar.gz').removesuffix('.zip')
    def basename(value):
        parts=value.split('/')
        if len(parts)!=2 or parts[0]!=prefix or not parts[1] or parts[1] in {'.','..'} or '\\' in value or ':' in value:
            raise ValueError('candidate archive member plan invalid')
        return parts[1]
    if host=='windows':
        with zipfile.ZipFile(archive) as source:
            for info in source.infolist():
                if info.is_dir() or info.file_size>16*1024**2:
                    raise ValueError('candidate archive member plan invalid')
                members.append((basename(info.filename),source.read(info)))
    else:
        with tarfile.open(archive,'r:gz') as source:
            for member in source:
                if not member.isfile() or member.size>16*1024**2:
                    raise ValueError('candidate archive member plan invalid')
                members.append((basename(member.name),source.extractfile(member).read()))
    if len(members)!=4 or len({n for n,_ in members})!=4:raise ValueError('unexpected candidate package coverage')
    binary='playtestr.exe' if host=='windows' else 'playtestr'
    if hashlib.sha256(dict(members)[binary]).hexdigest()!=row['binary_sha256']:raise ValueError('extracted candidate binary mismatch')
    for name,data in members:
        with (output/name).open('xb') as stream:stream.write(data)
    if os.name!='nt':(output/binary).chmod(0o755)
    immutable_json(output/'installed.json',dict(host=host,archive=archive.relative_to(ROOT).as_posix(),
        archive_sha256=row['archive_sha256'],binary_sha256=row['binary_sha256'],
        members={n:hashlib.sha256(data).hexdigest() for n,data in members},source_revision=freeze['source_revision']))
    print('Installed exact retained',host,'rc.5 archive; binary SHA-256',row['binary_sha256'])


if __name__=='__main__':main()
