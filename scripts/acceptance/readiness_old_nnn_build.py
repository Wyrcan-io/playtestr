"""Force the original bounded ordinary C build, including exact restoration."""
import platform
from pathlib import Path
import shutil

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, sha256
from readiness_new_control_matrix import read_json as load
from readiness_old_nnn_environment import environment


async def compile_target(label):
    if platform.system() not in {'Linux','Darwin'}:raise RuntimeError('nnn compilation requires native Unix')
    target=RAW/'active/old-nnn';source=target/'src';runtime=load(target/'runtime.json');env=environment()
    compiler=Path(runtime['compiler_path']);make=Path(runtime['make_path'])
    if sha256(compiler)!=runtime['compiler_sha256'] or sha256(make)!=runtime['make_sha256']:
        raise RuntimeError('actual native C/make prerequisite changed')
    review=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration/nnn/source-review.json')
    current={name:sha256(source/name) for name in review['reviewed_inputs']}
    if any(digest!=review['reviewed_inputs'][name] for name,digest in current.items() if name!='src/nnn.c'):
        raise RuntimeError('unreviewed non-writer source change')
    env['CC']=str(compiler)
    result=await execute([make,'-B','all'],'old-nnn',label,cwd=source,env=env,timeout=180,campaign=Campaign())
    if any(sha256(source/name)!=digest for name,digest in current.items()):raise RuntimeError('Makefile changed selected original/mutated source')
    built=source/'nnn'
    if built.stat().st_size>32*1024**2:raise RuntimeError('actual C output byte bound')
    binary=target/'bin/nnn';binary.parent.mkdir(exist_ok=True);shutil.copyfile(built,binary);binary.chmod(0o755)
    if sha256(built)!=sha256(binary):raise RuntimeError('actual C output copy differs')
    return result,binary
