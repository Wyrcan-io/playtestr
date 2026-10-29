"""Require exact separate approval for executable wheel scripts and startup hooks."""
import hashlib


def reviewed_hooks(archive,wheel_sha256,approval):
    names=archive.namelist()
    if len(names)!=len(set(names)):raise ValueError('duplicate wheel member')
    scripts={n:hashlib.sha256(archive.read(n)).hexdigest() for n in names if '.data/scripts/' in n}
    startup={n:hashlib.sha256(archive.read(n)).hexdigest() for n in names if n.endswith('.pth')}
    if scripts or startup:
        if (approval.get('wheel_sha256')!=wheel_sha256 or approval.get('scripts',{})!=scripts or
            approval.get('startup_hooks',{})!=startup):
            raise ValueError('wheel startup/script hook requires exact separate source review')
    return scripts,startup
