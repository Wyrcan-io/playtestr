"""Bind Cargo's one reviewed Git patch to its actual checkout and source bytes."""
import os
import hashlib
from pathlib import Path
import shutil
import tomllib

from adversarial_process import execute
from readiness_evidence import Campaign, sha256


def license_link(path,checkout):
    allowed={name+'/LICENSE' for name in ['ratatui','ratatui-core','ratatui-crossterm',
        'ratatui-termion','ratatui-termwiz','ratatui-widgets']}
    if (not path.is_symlink() or path.relative_to(checkout).as_posix() not in allowed
            or os.readlink(path)!='../LICENSE'):
        raise RuntimeError('unreviewed Git dependency link')
    destination=checkout/'LICENSE'
    if destination.is_symlink() or not destination.is_file() or path.resolve(strict=True)!=destination.resolve(strict=True):
        raise RuntimeError('Git dependency license link redirects')
    return b'../LICENSE'


async def inspect(target,sources,env):
    git=shutil.which('git',path=env['PATH'])
    if git is None:raise RuntimeError('read-only Git prerequisite missing')
    wanted={source.rsplit('#',1)[1] for source in sources}
    manifests=list((target/'cargo-home/git/checkouts').glob('*/*/Cargo.toml'))
    checkouts=[];files={};hooks={};links={};total=0
    for manifest in manifests:
        checkout=manifest.parent
        head=await execute([git,'-C',checkout,'rev-parse','HEAD'],'old-yazi','migration-locked-git-dependency-head',
            cwd=target/'src',env=env,timeout=30,campaign=Campaign())
        commit=head['output'].strip()
        if commit not in wanted:raise RuntimeError('Git checkout differs from original lock')
        checkouts.append(dict(root=checkout.relative_to(target).as_posix(),commit=commit,head_attempt=head['id']))
        for directory,folders,names in os.walk(checkout,followlinks=False):
            folders[:]=[name for name in folders if name!='.git']
            for name in [*folders,*names]:
                if name=='.git':continue
                path=Path(directory)/name
                if path.is_symlink():
                    payload=license_link(path,checkout);name=path.relative_to(target).as_posix()
                    files[name]=dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest())
                    links[name]='../LICENSE'
                    continue
                if getattr(path,'is_junction',lambda:False)():raise RuntimeError('unreviewed Git dependency junction')
                if not path.is_file():continue
                size=path.stat().st_size;total+=size
                if len(files)>=25000 or size>16*1024**2 or total>128*1024**2:raise RuntimeError('Git dependency source bound')
                files[path.relative_to(target).as_posix()]=dict(bytes=size,sha256=sha256(path))
        for path in checkout.rglob('Cargo.toml'):
            package=tomllib.loads(path.read_text(encoding='utf-8')).get('package',{})
            declared=package.get('build');hook=path.parent/(declared if isinstance(declared,str) else 'build.rs')
            if declared is False or not hook.is_file():continue
            hook.resolve(strict=True).relative_to(checkout.resolve())
            if hook.stat().st_size>128*1024:raise RuntimeError('Git dependency hook bound')
            hooks['git:'+hook.relative_to(target).as_posix()]=sha256(hook)
    if {row['commit'] for row in checkouts}!=wanted or len(checkouts)!=len(wanted):
        raise RuntimeError('missing or ambiguous exact Git dependency checkout')
    return dict(checkouts=checkouts,files=files,build_hooks=hooks,links=links,
        metadata_excluded='.git administrative files are not compiler source inputs; actual HEAD is positively observed against the original lock.',
        link_policy='Six exact package LICENSE links to ../LICENSE are cataloged as literal Git link text without following them; root LICENSE bytes are separately bound. Windows Git regular link-text stubs retain the same catalog bytes.')
