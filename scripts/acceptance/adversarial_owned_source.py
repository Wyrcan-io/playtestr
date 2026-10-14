"""Claim only an explicitly selected, fresh or already identified application root."""
import json
import os
from pathlib import Path
from adversarial_process import ROOT


def claim(root,project,pin,*,other_roots=(),prefix=''):
    if not project or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in project):
        raise RuntimeError('Invalid owned project identity')
    if len(pin)!=40 or any(c not in '0123456789abcdef' for c in pin):
        raise RuntimeError('Invalid immutable application revision')
    root=Path(root)
    if root.is_symlink() or getattr(root,'is_junction',lambda:False)():
        raise RuntimeError('Linked application parent')
    root.mkdir(parents=True,exist_ok=True)
    if prefix not in ('','playtestr-adversarial-'):raise RuntimeError('Invalid owned directory prefix')
    app=root/(prefix+project)
    for parent in [root,*other_roots]:
        for marker in Path(parent).glob('*/task-owned.json'):
            if marker.is_symlink() or marker.stat().st_size>16384:
                raise RuntimeError('Unsafe application ownership marker')
            owner=json.loads(marker.read_text(encoding='utf-8'))
            if owner.get('campaign')=='ten-new-project-adversarial-pass' and owner.get('project')!=project:
                raise RuntimeError('Another owned application is still active')
    if app.is_symlink() or getattr(app,'is_junction',lambda:False)():
        raise RuntimeError('Linked application root')
    app.mkdir(exist_ok=True)
    owner=dict(campaign='ten-new-project-adversarial-pass',workspace=str(ROOT),project=project,source_sha=pin)
    marker=app/'task-owned.json'
    if marker.exists():
        if marker.is_symlink() or marker.stat().st_size>16384 or json.loads(marker.read_text(encoding='utf-8'))!=owner:
            raise RuntimeError('Unknown existing application ownership')
    else:
        if any(app.iterdir()):raise RuntimeError('Refuse adopting nonempty unmarked application')
        with marker.open('xb') as stream:
            stream.write((json.dumps(owner)+'\n').encode('utf-8'))
            stream.flush();os.fsync(stream.fileno())
    return app
