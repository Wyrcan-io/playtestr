"""Create a new explicitly XZ-encoded native generation; preserve gzip defaults."""
import argparse
import tarfile

from next20_check import RAW,ROOT
from next20_packet_archive import verify
from readiness_compact_native import inventory,physical_members
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',choices=['yo'],required=True)
    parser.add_argument('--run',required=True);parser.add_argument('--generation',type=int,required=True);args=parser.parse_args()
    if not 1<=args.generation<=1000:raise ValueError('Native XZ generation bound')
    RAW.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
    for ancestor in [RAW,RAW/args.project]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('Linked native XZ output ancestor')
    (RAW/args.project).resolve(strict=True).relative_to(RAW.resolve(strict=True))
    files,total=inventory(RAW,[args.run],16*1024**2);canonical={}
    for name,row in sorted(files.items()):
        member=canonical.setdefault((row['bytes'],row['sha256']),name)
        if member!=name:row['member']=member
    members=physical_members(files);output=RAW/args.project/('retained-native-v'+str(args.generation));output.mkdir()
    archive=output/'packets.tar.xz'
    with tarfile.open(archive,'w:xz',format=tarfile.PAX_FORMAT,preset=6) as bundle:
        for name,row in sorted(members.items()):
            path=RAW/name
            if sha256(path)!=row['sha256']:raise ValueError('Native evidence changed during XZ retention')
            member=tarfile.TarInfo(name);member.size=row['bytes'];member.mode=0o644
            with path.open('rb') as stream:bundle.addfile(member,stream)
    verify(archive,files)
    selected=next(n for n in files if n.endswith('/final-series/0/N01.report.json'))
    with tarfile.open(archive,'r:xz') as bundle:
        data=bundle.extractfile(files[selected].get('member',selected)).read(16*1024**2+1)
    restore=output/'selected-restore.bin';restore.write_bytes(data)
    if sha256(restore)!=files[selected]['sha256']:raise ValueError('Native XZ selected actual report restore differs')
    immutable_json(output/'index.json',dict(schema_version=2,project=args.project,generation=args.generation,
        runs=[args.run],compression='tar.xz',files=files,expanded_bytes=total,unique_payloads=len(members),
        archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,max_file_bytes=16*1024**2,
        max_archive_bytes=24*1024**2,selected_restore=[selected],selected_restore_path='selected-restore.bin',
        scope='New self-contained native XZ encoding, all original logical payloads byte exact with checked one-level aliases. No retired or rewritten gzip indices/archives. Canonical source dependency remains explicit.'))
    immutable_json(output/'verified.json',dict(index_sha256=sha256(output/'index.json'),archive_sha256=sha256(archive),
        members_verified=len(files),physical_members_verified=len(members),selected_restore_verified=1,expanded_removal_performed=False))
    print('Verified native XZ compaction:',len(files),'logical files;',len(members),'physical;',total,'expanded ->',archive.stat().st_size,'XZ bytes.')


if __name__=='__main__':main()
