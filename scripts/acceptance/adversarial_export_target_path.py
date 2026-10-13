"""Export the reviewed owned target directory for a subsequent Actions step."""
import argparse
import json
import os
from pathlib import Path
from adversarial_process import ROOT


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',required=True)
    args=parser.parse_args()
    if not args.project or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.project):
        raise RuntimeError('Invalid project identity')
    app=ROOT/'.cache/ten-new-project-apps'/args.project
    if app.is_symlink() or getattr(app,'is_junction',lambda:False)():
        raise RuntimeError('Linked target ownership root')
    owner=json.loads((app/'task-owned.json').read_text(encoding='utf-8'))
    if owner.get('workspace')!=str(ROOT) or owner.get('project')!=args.project:
        raise RuntimeError('Unknown target ownership')
    identity=json.loads((app/'runtime.json').read_text(encoding='utf-8'))
    entries=identity['path'].split(os.pathsep)
    for value in entries:
        path=Path(value)
        if not value or any(c in value for c in '\r\n\0') or not path.is_absolute() or not path.is_dir():
            raise RuntimeError('Invalid target PATH directory')
        if not path.resolve(strict=True).is_relative_to(app.resolve(strict=True)):
            raise RuntimeError('Target PATH directory escapes owned root')
    control=os.environ.get('GITHUB_PATH')
    if not control:
        raise RuntimeError('GITHUB_PATH missing; no persistent Actions PATH export occurred')
    with open(control,'a',encoding='utf-8',newline='\n') as stream:
        stream.write('\n'.join(entries)+'\n')
    print('Exported owned target PATH for subsequent Actions steps')


if __name__=='__main__':main()
