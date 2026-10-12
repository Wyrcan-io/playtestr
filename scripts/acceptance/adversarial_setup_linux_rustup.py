"""Digest-pinned, task-owned Rustup bootstrap for local WSL exploration."""
import hashlib
import json
import os
from pathlib import Path
import platform
import urllib.request
from adversarial_process import ROOT,DOC,run


def main():
    if platform.system()!='Linux' or 'microsoft' not in platform.release().lower():
        raise RuntimeError('This bootstrap is explicitly scoped to Linux/WSL exploration')
    version='1.29.0'
    digest='4acc9acc76d5079515b46346a485974457b5a79893cfb01112423c89aeb5aa10'
    url='https://static.rust-lang.org/rustup/archive/'+version+'/x86_64-unknown-linux-gnu/rustup-init'
    root=Path('/var/tmp/playtestr-adversarial-rust-bootstrap')
    if root.is_symlink():raise RuntimeError('Linked bootstrap root')
    root.mkdir(exist_ok=True)
    owner=dict(campaign='ten-new-project-adversarial-pass',workspace=str(ROOT),
        runtime='rustup-'+version,archive_sha256=digest)
    marker=root/'task-runtime-owned.json'
    if marker.exists():
        if json.loads(marker.read_text(encoding='utf-8'))!=owner:raise RuntimeError('Unknown bootstrap ownership')
    elif any(root.iterdir()):raise RuntimeError('Unmarked nonempty bootstrap directory')
    marker.write_text(json.dumps(owner)+'\n',encoding='utf-8')
    installer=root/'rustup-init'
    if not installer.exists():
        with urllib.request.urlopen(url,timeout=30) as response,installer.open('xb') as output:
            total=0
            while chunk:=response.read(1024*1024):
                total+=len(chunk)
                if total>50*1024*1024:raise RuntimeError('Bootstrap exceeds independent size bound')
                output.write(chunk)
    if hashlib.sha256(installer.read_bytes()).hexdigest()!=digest:raise RuntimeError('Bootstrap differs from reviewed exact official digest')
    installer.chmod(0o700)
    env=dict(os.environ,CARGO_HOME=str(root/'cargo-home'),RUSTUP_HOME=str(root/'rustup-home'))
    executable=root/'cargo-home/bin/rustup'
    if not executable.exists():
        run([installer,'-y','--no-modify-path','--default-toolchain','none','--profile','minimal'],
            'core','owned-wsl-rustup-bootstrap',env=env,timeout=120)
    actual=run([executable,'--version'],'core','actual-owned-rustup-version',env=env)['output']
    if not actual.startswith('rustup '+version+' '):raise RuntimeError('Unexpected bootstrap version')
    record=dict(owner,url=url,digest_source=url+'.sha256',executable=str(executable),
        actual_version=actual.strip(),scope='WSL exploratory prerequisite only; no application or native Linux qualification')
    (DOC/'core/linux-exploratory-rustup.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(record,indent=2))


if __name__=='__main__':main()
