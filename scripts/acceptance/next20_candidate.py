"""Explicit candidate selection; historical rc.5 remains the default."""
import json
import platform

from next20_check import RAW,ROOT,DOC
from readiness_evidence import sha256

SERIES=('rc5','native-exit-v1')


def contract(series,host=None):
    if series not in SERIES:raise ValueError('undeclared candidate series')
    host=host or {'Windows':'windows','Linux':'linux','Darwin':'darwin'}[platform.system()]
    freeze_path=(ROOT/'docs/validation/runner-readiness-ten-project-pass/migration-candidate-freeze.json'
        if series=='rc5' else DOC/'replacement-candidate-freeze-native-exit-v1.json')
    freeze=json.loads(freeze_path.read_text())
    rows=[r for r in freeze['cells'] if r['host']==host]
    if len(rows)!=1:raise ValueError('missing/duplicate exact native candidate cell')
    row=rows[0]
    if host not in {'windows','linux','darwin'}:raise ValueError('undeclared native host')
    output=RAW/('candidate' if series=='rc5' else 'candidate-native-exit-v1')/host
    return freeze,row,output


def executable(series,host=None):
    freeze,row,output=contract(series,host)
    binary=output/('playtestr.exe' if row['host']=='windows' else 'playtestr')
    binary.resolve(strict=True).relative_to(RAW.resolve(strict=True))
    for path in [output,output.parent,binary]:
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('linked candidate executable/root')
    installed=json.loads((output/'installed.json').read_text())
    if sha256(binary)!=row['binary_sha256'] or installed['binary_sha256']!=row['binary_sha256'] or installed['archive_sha256']!=row['archive_sha256']:
        raise ValueError('selected candidate differs from exact frozen archive')
    return binary
