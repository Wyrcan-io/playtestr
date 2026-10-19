"""Read only selected primary-source option registration from the retained pin."""
import hashlib
import tarfile
from pathlib import PurePosixPath

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    review=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone/source-review.json')
    archive=RAW/'rclone/retained-source/source.tar.gz'
    if sha256(archive)!=review['archive_sha256']:raise RuntimeError('original source archive differs')
    requested={'fs/registry.go','fs/config.go','fs/backend_config.go','fs/log.go'}
    destination=RAW/'rclone/option-source-review'
    destination.mkdir(exist_ok=False)
    found={}
    with tarfile.open(archive,'r:gz') as bundle:
        for member in bundle:
            name='/'.join(PurePosixPath(member.name).parts[1:])
            if name not in requested:continue
            if not member.isfile() or member.size>256*1024:raise RuntimeError('source inspection member bound')
            data=bundle.extractfile(member).read(member.size+1)
            digest=hashlib.sha256(data).hexdigest()
            if digest!=review['reviewed_inputs'][name]:raise RuntimeError('source inspection bytes differ')
            path=destination/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
            found[name]=digest
    if set(found)!=requested:raise RuntimeError('missing source inspection inputs')
    immutable_json(destination/'index.json',dict(pin=review['pin'],files=found,target_executed=False))
    print('Selected original registration/config/log source verified; no repository reacquired or target executed.')


if __name__=='__main__':main()
