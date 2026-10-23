"""Reconstruct only declared synthetic empty Git fixture bytes and directories."""
import argparse
import base64
import json

from next20_check import DOC


def reconstruct(package):
    package.resolve(strict=True).relative_to(DOC.resolve())
    declaration=json.loads((package/'fixture-git.json').read_text())
    fixture=package/'fixture';fixture.mkdir(exist_ok=True)
    root=fixture/'.git';root.mkdir(exist_ok=True)
    for ancestor in [package,fixture,root]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('linked synthetic Git ancestor')
    for name,data in declaration['files'].items():
        if name not in {'HEAD','config'}:raise ValueError('unexpected synthetic Git file')
        path=root/name;content=base64.b64decode(data,validate=True)
        if path.exists():
            if path.is_symlink() or path.read_bytes()!=content:raise ValueError('existing Git fixture differs from approved bytes')
        else:
            with path.open('xb') as stream:stream.write(content)
    for name in declaration['directories']:
        if name not in {'objects','refs','refs/heads','refs/tags'}:raise ValueError('unexpected synthetic Git directory')
        path=root/name
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('linked synthetic Git directory')
        path.mkdir(parents=True,exist_ok=True)
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if actual!=set(declaration['files']):raise ValueError('extra/missing synthetic Git fixture file')
    print('Reconstructed/verified declared empty synthetic Git boundary without executing Git.')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args()
    reconstruct(DOC/args.project)


if __name__=='__main__':main()
