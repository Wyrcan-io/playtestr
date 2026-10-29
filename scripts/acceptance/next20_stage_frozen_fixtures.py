"""Stage exact frozen ordinary fixture blobs without traversing synthetic Git roots."""
import argparse
import hashlib
import json
import re
import subprocess

from next20_check import DOC, ROOT
from readiness_evidence import sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    if not re.fullmatch('[a-z][a-z0-9-]{0,63}',args.project):raise ValueError('unsafe project')
    package=DOC/args.project;freeze=json.loads((package/'development-test-freeze.json').read_text())
    for name,digest in freeze['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('frozen input differs: '+name)
    count=0
    for name,digest in freeze['inputs'].items():
        if not name.startswith(('fixture/','fixtures/')) or '.git' in name.split('/'):continue
        path=(package/name).resolve(strict=True);path.relative_to(package.resolve(strict=True))
        if path.is_symlink():raise ValueError('linked fixture')
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=digest:raise ValueError('fixture changed before staging')
        relative=path.relative_to(ROOT).as_posix()
        blob=subprocess.check_output(['git','hash-object','-w','--stdin'],input=raw,cwd=ROOT).decode().strip()
        subprocess.run(['git','update-index','--add','--cacheinfo','100644',blob,relative],cwd=ROOT,check=True)
        actual=subprocess.check_output(['git','show',':'+relative],cwd=ROOT)
        if actual!=raw:raise ValueError('staged fixture bytes differ')
        count+=1
    print('Staged and read back',count,'exact ordinary fixture blobs; synthetic .git roots untouched.')


if __name__=='__main__':main()
