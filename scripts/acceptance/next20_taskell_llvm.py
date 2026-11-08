"""Fetch and verify the frozen MacPorts LLVM 12 ARM64 package for GHC 9.0.2."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import urllib.request

from next20_check import RAW
from readiness_evidence import immutable_json,sha256


PACKAGE='llvm-12-12.0.1_5.darwin_24.arm64.tbz2'
BASE='https://packages.macports.org/llvm-12/'
# macports/macports-base:keys/base/macports-base-2024.pub
PUBLIC_KEY='RWR+PhirBCclQlM0Khae0up57K9Yy8hRstG1AOyawt/HIIGMckQQWlKn'
# macports/macports-base:keys/archives/macports-archives-2025.pub
PUBLIC_KEY_GIT_BLOB='477a77d4363525ba8afc32331fb389897fba193c'
SIGNATURE_COMMENT='untrusted comment: verify with macports-archives-2025.pub'
MACPORTS_LLVM_BIN_ALIAS=re.compile(r'[A-Za-z0-9_.+-]+-mp-12\Z')


def download(url,path,limit):
    request=urllib.request.Request(url,headers={'User-Agent':'playtestr-runner-readiness/1'})
    total=0
    with urllib.request.urlopen(request,timeout=90) as response,path.open('xb') as output:
        while True:
            block=response.read(1024*1024)
            if not block:break
            total+=len(block)
            if total>limit:raise ValueError('LLVM package download exceeded its byte cap')
            output.write(block)
    return total


def decode_signify_signature(signature,public_key=PUBLIC_KEY):
    rows=signature.read_text(encoding='ascii').splitlines()
    if len(rows)!=2 or rows[0]!=SIGNATURE_COMMENT:
        raise ValueError('MacPorts package signature has an unexpected signify envelope')
    public=base64.b64decode(public_key,validate=True)
    signed=base64.b64decode(rows[1],validate=True)
    if len(public)!=42 or public[:2]!=b'Ed' or len(signed)!=74 or signed[:2]!=b'Ed':
        raise ValueError('MacPorts package signature/key encoding is invalid')
    if public[2:10]!=signed[2:10]:raise ValueError('MacPorts package signature key ID mismatch')
    return public,signed


def verify_signify(package,signature,tool_root):
    public,signed=decode_signify_signature(signature)
    key_path=tool_root/'macports-archives-2025-ed25519.pem'
    der=bytes.fromhex('302a300506032b6570032100')+public[10:]
    key_path.write_text('-----BEGIN PUBLIC KEY-----\n'+base64.b64encode(der).decode('ascii')+'\n-----END PUBLIC KEY-----\n',encoding='ascii')
    cache=tool_root/'go-cache';modcache=tool_root/'go-mod-cache'
    cache.mkdir(parents=True,exist_ok=True);modcache.mkdir(parents=True,exist_ok=True)
    env=dict(os.environ,GOENV='off',GOTOOLCHAIN='local',GOWORK='off',
        GOCACHE=str(cache),GOMODCACHE=str(modcache))
    verifier=Path(__file__).with_name('next20_taskell_signify_verify.go')
    result=subprocess.run(['go','run',verifier,base64.b64encode(public[10:]).decode('ascii'),
        base64.b64encode(signed[10:]).decode('ascii'),package],capture_output=True,text=True,
        timeout=120,env=env)
    if result.returncode:raise ValueError('MacPorts package Ed25519 signature failed: '+result.stderr[-1000:])
    return signed[2:10].hex(),sha256(key_path)


def safe_extract(package,destination):
    prefix='opt/local/libexec/llvm-12/'
    prefix_root=prefix.rstrip('/')
    seen=set();aliases=set();pending=[];expanded=0
    with tarfile.open(package,'r:bz2') as archive:
        members=archive.getmembers()
        if len(members)>20000:raise ValueError('MacPorts LLVM package has too many archive entries')
        for member in members:
            name=member.name.removeprefix('./')
            if name in {'','.','./'} and member.isdir():continue
            normalized=name.rstrip('/')
            if normalized.startswith('+'):
                if member.size>2*1024*1024:raise ValueError('MacPorts package metadata exceeds bound')
                continue
            if normalized in {'opt','opt/local','opt/local/bin','opt/local/libexec'}:
                if not member.isdir():raise ValueError('Unexpected non-directory MacPorts package scaffold: '+name)
                continue
            if normalized==prefix_root:
                if not member.isdir():raise ValueError('LLVM package prefix is not a directory')
                destination.mkdir(parents=True,exist_ok=True)
                continue
            if normalized.startswith('opt/local/bin/'):
                alias=normalized.removeprefix('opt/local/bin/')
                if (not member.isfile() or not MACPORTS_LLVM_BIN_ALIAS.fullmatch(alias) or
                        member.size<=0 or member.size>4096 or alias in aliases):
                    raise ValueError('Unexpected MacPorts LLVM command alias: '+name)
                aliases.add(alias)
                continue
            if not name.startswith(prefix):raise ValueError('Unexpected path in MacPorts LLVM archive: '+name)
            relative=PurePosixPath(name[len(prefix):])
            if not relative.parts or any(p in {'','.', '..'} for p in relative.parts):
                raise ValueError('Unsafe MacPorts LLVM archive member path')
            if relative.as_posix() in seen:raise ValueError('Duplicate MacPorts LLVM archive member')
            seen.add(relative.as_posix())
            if not relative.parts or relative.as_posix()=='.':
                if member.isdir():destination.mkdir(parents=True,exist_ok=True);continue
                raise ValueError('LLVM package prefix entry is not a directory')
            if member.isdir():
                (destination/Path(*relative.parts)).mkdir(parents=True,exist_ok=True)
            elif member.isfile():
                expanded+=member.size
                if expanded>512*1024**2:raise ValueError('MacPorts LLVM expansion exceeded 512 MiB')
                output=destination/Path(*relative.parts);output.parent.mkdir(parents=True,exist_ok=True)
                stream=archive.extractfile(member)
                if stream is None:raise ValueError('Unable to read regular LLVM archive member')
                with output.open('xb') as target:
                    while True:
                        block=stream.read(1024*1024)
                        if not block:break
                        target.write(block)
                output.chmod(member.mode&0o755)
            elif member.issym():
                link=PurePosixPath(member.linkname)
                if link.is_absolute():raise ValueError('Absolute symlink in MacPorts LLVM package')
                resolved=PurePosixPath(os.path.normpath(str(relative.parent/link)))
                if resolved.is_absolute() or '..' in resolved.parts:raise ValueError('Escaping symlink in MacPorts LLVM package')
                pending.append((destination/Path(*relative.parts),member.linkname))
            else:raise ValueError('Unsupported special entry in MacPorts LLVM package')
    for path,target in pending:
        path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(target)
    opt=destination/'bin/opt';llc=destination/'bin/llc'
    if not opt.is_file() or not llc.is_file():raise ValueError('MacPorts LLVM package is missing opt/llc')
    return expanded,opt,llc


def tool_inventory(prefix):
    """Bind regular tool files and literal symlink targets under the owned root."""
    prefix=Path(prefix).resolve(strict=True)
    rows={}
    for path in sorted(prefix.rglob('*')):
        if path.is_symlink():
            path.resolve(strict=True).relative_to(prefix)
            rows[path.relative_to(prefix).as_posix()]='symlink:'+os.readlink(path)
        elif path.is_file():
            rows[path.relative_to(prefix).as_posix()]=sha256(path)
    return rows


def verify_tool_inventory(prefix,files):
    """Reject changed files, changed links, and any tool resolving outside root."""
    prefix=Path(prefix).resolve(strict=True)
    for name,expected in files.items():
        path=prefix/name
        resolved=path.resolve(strict=True)
        resolved.relative_to(prefix)
        if expected.startswith('symlink:'):
            if not path.is_symlink() or os.readlink(path)!=expected.removeprefix('symlink:'):
                raise ValueError('Frozen LLVM toolchain link changed: '+name)
        elif path.is_symlink() or not path.is_file() or sha256(path)!=expected:
            raise ValueError('Frozen LLVM toolchain file changed: '+name)


def checked_version(executable,env):
    """Run one bounded tool probe and retain actionable native diagnostics."""
    result=subprocess.run([executable,'--version'],env=env,capture_output=True,
                          text=True,timeout=30,check=False)
    if result.returncode:
        stdout=(result.stdout or '')[-4096:]
        stderr=(result.stderr or '')[-4096:]
        raise RuntimeError(f'{executable} --version exited {result.returncode}; '
                           f'stdout={stdout!r}; stderr={stderr!r}')
    return (result.stdout or '')+(result.stderr or '')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--github-env',required=True)
    args=parser.parse_args()
    tool_root=RAW/'toolchain/llvm/macports-12.0.1_5';tool_root.mkdir(parents=True,exist_ok=True)
    package=tool_root/PACKAGE;signature=tool_root/(PACKAGE+'.sig')
    if package.exists() or signature.exists():raise ValueError('LLVM acquisition destination already exists')
    size=download(BASE+PACKAGE,package,100*1024**2)
    if not 60*1024**2<=size<=100*1024**2:raise ValueError('Unexpected MacPorts LLVM package size')
    download(BASE+PACKAGE+'.sig',signature,4096)
    key_id,key_sha256=verify_signify(package,signature,tool_root)
    prefix=tool_root/'prefix/libexec/llvm-12'
    prefix.parent.mkdir(parents=True,exist_ok=True)
    expanded,opt,llc=safe_extract(package,prefix)
    env=dict(os.environ);env['PATH']=str(prefix/'bin')+os.pathsep+env.get('PATH','')
    env['DYLD_LIBRARY_PATH']=str(prefix/'lib')+os.pathsep+env.get('DYLD_LIBRARY_PATH','')
    opt_text=checked_version(opt,env)
    llc_text=checked_version(llc,env)
    if '12.0.1' not in opt_text or '12.0.1' not in llc_text or 'AArch64' not in llc_text:
        raise ValueError('Verified LLVM package did not report LLVM 12.0.1 with the AArch64 backend')
    files=tool_inventory(prefix)
    manifest=tool_root/'manifest.json'
    immutable_json(manifest,dict(schema_version=1,project='taskell',provider='MacPorts signed binary archive',
        package=PACKAGE,package_url=BASE+PACKAGE,package_bytes=size,package_sha256=sha256(package),
        signify_key='macports-archives-2025',signify_key_repository='macports/macports-base',
        signify_key_path='keys/archives/macports-archives-2025.pub',signify_key_git_blob=PUBLIC_KEY_GIT_BLOB,
        signify_key_id=key_id,signify_public_key_sha256=key_sha256,
        signature_sha256=sha256(signature),signature_verified=True,package_version='llvm-12 12.0.1_5',
        package_expanded_bytes=expanded,tool_prefix=str(prefix),opt_sha256=sha256(opt),llc_sha256=sha256(llc),
        files=files,opt_version=opt_text.strip(),llc_version=llc_text.strip(),
        scope='Signature-verified exact MacPorts LLVM 12.0.1 ARM64 tools and owned libraries for Taskell GHC 9.0.2; archive and extracted files stay in the campaign toolchain root.'))
    with Path(args.github_env).open('a',encoding='utf-8',newline='\n') as stream:
        stream.write('PATH='+env['PATH']+'\n')
        stream.write('DYLD_LIBRARY_PATH='+env['DYLD_LIBRARY_PATH']+'\n')
        stream.write('TASKELL_LLVM_MANIFEST='+str(manifest)+'\n')
    print(json.dumps(dict(manifest=str(manifest),package_sha256=sha256(package),expanded_bytes=expanded,
        opt_sha256=sha256(opt),llc_sha256=sha256(llc)),sort_keys=True))


if __name__=='__main__':main()
