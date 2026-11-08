"""Fetch and verify the frozen MacPorts LLVM 12 ARM64 package for GHC 9.0.2."""
import argparse
import base64
import hashlib
import json
import os
import posixpath
from pathlib import Path, PurePosixPath
import re
import subprocess
import tarfile
import urllib.request

from next20_check import RAW
from readiness_evidence import immutable_json,sha256


PACKAGE='llvm-12-12.0.1_5.darwin_24.arm64.tbz2'
BASE='https://packages.macports.org/llvm-12/'
LIBFFI_PACKAGE='libffi-3.4.8_0.darwin_24.arm64.tbz2'
LIBFFI_BASE='https://packages.macports.org/libffi/'
LIBFFI_SOURCE_SHA256='bc9842a18898bfacb0ed1252c4febcc7e78fa139fd27fdc7a3e30d9d9356119b'
LIBEDIT_PACKAGE='libedit-20260512-3.1_0.darwin_24.arm64.tbz2'
LIBEDIT_BASE='https://packages.macports.org/libedit/'
LIBEDIT_SOURCE_SHA256='432d5e7ea8b0116dd39f2eca7bc11d0eed77faa6b77ea526ace89907c23ea4a0'
NCURSES_PACKAGE='ncurses-6.6_0.darwin_24.arm64.tbz2'
NCURSES_BASE='https://packages.macports.org/ncurses/'
NCURSES_SOURCE_SHA256='355b4cbbed880b0381a04c46617b7656e362585d52e9cf84a67e2009b749ff11'
# macports/macports-base:keys/base/macports-base-2024.pub
PUBLIC_KEY='RWR+PhirBCclQlM0Khae0up57K9Yy8hRstG1AOyawt/HIIGMckQQWlKn'
# macports/macports-base:keys/archives/macports-archives-2025.pub
PUBLIC_KEY_GIT_BLOB='477a77d4363525ba8afc32331fb389897fba193c'
SIGNATURE_COMMENT='untrusted comment: verify with macports-archives-2025.pub'
MACPORTS_LLVM_BIN_ALIAS=re.compile(r'[A-Za-z0-9_.+-]+-mp-12\Z')
MACPORTS_LIBFFI_DYLIB=re.compile(r'libffi(?:\.\d+)*\.dylib\Z')
MACPORTS_LIBEDIT_DYLIB=re.compile(r'libedit(?:\.\d+)*\.dylib\Z')
MACPORTS_NCURSES_DYLIB=re.compile(r'lib(?:ncurses(?:\+{0,2}w?)?|tinfo|form|menu|panel)(?:\.\d+)*\.dylib\Z')


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
                resolved=PurePosixPath(posixpath.normpath(str(relative.parent/link)))
                if resolved.is_absolute() or '..' in resolved.parts:raise ValueError('Escaping symlink in MacPorts LLVM package')
                pending.append((destination/Path(*relative.parts),member.linkname))
            else:raise ValueError('Unsupported special entry in MacPorts LLVM package')
    for path,target in pending:
        path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(target)
    opt=destination/'bin/opt';llc=destination/'bin/llc'
    if not opt.is_file() or not llc.is_file():raise ValueError('MacPorts LLVM package is missing opt/llc')
    return expanded,opt,llc


def safe_extract_dylib_family(package,destination,pattern,required,label,cap=16*1024**2):
    """Select a named dylib family from one bounded, signed MacPorts package."""
    roots={'opt/local/bin','opt/local/include','opt/local/lib','opt/local/lib/pkgconfig',
           'opt/local/share','opt/local/share/man','opt/local/share/man/man3'}
    scaffolds={'opt','opt/local',*roots}
    seen=set();pending=[];expanded=0;archive_expanded=0;selected=set()
    with tarfile.open(package,'r:bz2') as archive:
        members=archive.getmembers()
        if len(members)>20000:raise ValueError(f'MacPorts {label} package has too many archive entries')
        for member in members:
            if member.isfile():
                archive_expanded+=member.size
                if archive_expanded>64*1024**2:raise ValueError(f'MacPorts {label} archive expansion exceeded 64 MiB')
            name=member.name.removeprefix('./');normalized=name.rstrip('/')
            if name in {'','.','./'} and member.isdir():continue
            if normalized.startswith('+'):
                if member.size>2*1024*1024:raise ValueError('MacPorts package metadata exceeds bound')
                continue
            if normalized in scaffolds:
                if not member.isdir():raise ValueError(f'Unexpected non-directory {label} package scaffold: '+name)
                continue
            parts=PurePosixPath(name)
            if parts.is_absolute() or any(part in {'','.', '..'} for part in parts.parts):
                raise ValueError(f'Unsafe MacPorts {label} archive member path')
            if name in seen:raise ValueError(f'Duplicate MacPorts {label} archive member')
            seen.add(name)
            if not any(name.startswith(root+'/') for root in roots):
                raise ValueError(f'Unexpected path in MacPorts {label} archive: '+name)
            if member.isdir():continue
            if name.startswith('opt/local/lib/') and pattern.fullmatch(parts.name):
                relative=Path(*parts.parts[3:]);output=destination/'lib'/relative
                selected.add(parts.name)
                if member.isfile():
                    expanded+=member.size
                    if expanded>cap:raise ValueError(f'MacPorts {label} dylib expansion exceeded {cap} bytes')
                    output.parent.mkdir(parents=True,exist_ok=True);stream=archive.extractfile(member)
                    if stream is None:raise ValueError(f'Unable to read {label} archive member')
                    with output.open('xb') as target:
                        while True:
                            block=stream.read(1024*1024)
                            if not block:break
                            target.write(block)
                    output.chmod(member.mode&0o755)
                elif member.issym():
                    link=PurePosixPath(member.linkname)
                    if link.is_absolute():raise ValueError(f'Absolute symlink in MacPorts {label} package')
                    resolved=PurePosixPath(posixpath.normpath(str(PurePosixPath('lib')/link)))
                    if resolved.is_absolute() or '..' in resolved.parts:raise ValueError(f'Escaping symlink in MacPorts {label} package')
                    pending.append((output,member.linkname))
                else:raise ValueError(f'Unsupported special entry in MacPorts {label} package')
            elif member.isfile() and member.size<=4*1024**2:
                # Headers, pkg-config metadata and man pages are signed package
                # contents, but LLVM needs only the exact dylib family.
                continue
            else:raise ValueError(f'Unexpected or oversized MacPorts {label} package member: '+name)
    for path,target in pending:
        path.parent.mkdir(parents=True,exist_ok=True);path.symlink_to(target)
    missing=[name for name in required if not (destination/'lib'/name).is_file()]
    if missing or not selected:raise ValueError(f'MacPorts {label} package missing required dylibs: {missing}')
    return expanded,sorted(selected)


def safe_extract_libffi(package,destination):
    """Select only the signed package's bounded libffi dylib family."""
    return safe_extract_dylib_family(package,destination,MACPORTS_LIBFFI_DYLIB,
                                     ['libffi.8.dylib'],'libffi')


def verify_macos_link_closure(prefix,binaries):
    """Require each absolute MacPorts dylib reference in the owned prefix."""
    prefix=Path(prefix).resolve(strict=True);dependencies=[];missing=set();pending=list(binaries);visited=set()
    while pending:
        path=pending.pop().resolve(strict=True)
        try:path.relative_to(prefix)
        except ValueError as error:raise ValueError('LLVM executable or dylib resolves outside owned prefix') from error
        key=path.as_posix()
        if key in visited:continue
        visited.add(key)
        if len(visited)>512:raise ValueError('LLVM dependency inspection exceeded its file bound')
        result=subprocess.run(['otool','-L',path],capture_output=True,text=True,timeout=30,check=False)
        if result.returncode:raise RuntimeError(f'otool -L failed for {path}: {(result.stderr or "")[-2000:]}')
        for line in result.stdout.splitlines()[1:]:
            dependency=line.strip().split(' (compatibility version',1)[0]
            if not dependency:continue
            dependencies.append(dict(source=path.relative_to(prefix).as_posix(),library=dependency))
            if dependency.startswith('/opt/local/lib/'):
                target=prefix/'lib'/Path(dependency).name
                try:resolved=target.resolve(strict=True);resolved.relative_to(prefix)
                except (OSError,ValueError):missing.add(Path(dependency).name)
                else:pending.append(resolved)
            elif dependency.startswith('@rpath/'):
                target=prefix/'lib'/Path(dependency).name
                if target.exists():pending.append(target)
            elif dependency.startswith('@loader_path/'):
                target=path.parent/dependency.removeprefix('@loader_path/')
                if target.exists():pending.append(target)
    if missing:raise RuntimeError('Unbundled MacPorts dylib dependencies: '+', '.join(sorted(missing)))
    return dependencies


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
    ffi_package=tool_root/LIBFFI_PACKAGE;ffi_signature=tool_root/(LIBFFI_PACKAGE+'.sig')
    if ffi_package.exists() or ffi_signature.exists():raise ValueError('libffi acquisition destination already exists')
    ffi_size=download(LIBFFI_BASE+LIBFFI_PACKAGE,ffi_package,2*1024**2)
    if not 16*1024<=ffi_size<=2*1024**2:raise ValueError('Unexpected signed MacPorts libffi archive size')
    download(LIBFFI_BASE+LIBFFI_PACKAGE+'.sig',ffi_signature,4096)
    ffi_key_id,ffi_key_sha256=verify_signify(ffi_package,ffi_signature,tool_root)
    edit_package=tool_root/LIBEDIT_PACKAGE;edit_signature=tool_root/(LIBEDIT_PACKAGE+'.sig')
    if edit_package.exists() or edit_signature.exists():raise ValueError('libedit acquisition destination already exists')
    edit_size=download(LIBEDIT_BASE+LIBEDIT_PACKAGE,edit_package,2*1024**2)
    if not 64*1024<=edit_size<=2*1024**2:raise ValueError('Unexpected signed MacPorts libedit archive size')
    download(LIBEDIT_BASE+LIBEDIT_PACKAGE+'.sig',edit_signature,4096)
    edit_key_id,edit_key_sha256=verify_signify(edit_package,edit_signature,tool_root)
    ncurses_package=tool_root/NCURSES_PACKAGE;ncurses_signature=tool_root/(NCURSES_PACKAGE+'.sig')
    if ncurses_package.exists() or ncurses_signature.exists():raise ValueError('ncurses acquisition destination already exists')
    ncurses_size=download(NCURSES_BASE+NCURSES_PACKAGE,ncurses_package,4*1024**2)
    if not 512*1024<=ncurses_size<=4*1024**2:raise ValueError('Unexpected signed MacPorts ncurses archive size')
    download(NCURSES_BASE+NCURSES_PACKAGE+'.sig',ncurses_signature,4096)
    ncurses_key_id,ncurses_key_sha256=verify_signify(ncurses_package,ncurses_signature,tool_root)
    prefix=tool_root/'prefix/libexec/llvm-12'
    prefix.parent.mkdir(parents=True,exist_ok=True)
    expanded,opt,llc=safe_extract(package,prefix)
    ffi_expanded,ffi_files=safe_extract_libffi(ffi_package,prefix)
    edit_expanded,edit_files=safe_extract_dylib_family(edit_package,prefix,MACPORTS_LIBEDIT_DYLIB,
        ['libedit.0.dylib'],'libedit')
    ncurses_expanded,ncurses_files=safe_extract_dylib_family(ncurses_package,prefix,MACPORTS_NCURSES_DYLIB,
        ['libncurses.6.dylib'],'ncurses',cap=32*1024**2)
    dependency_inventory=verify_macos_link_closure(prefix,[opt,llc])
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
        package_expanded_bytes=expanded,libffi=dict(package=LIBFFI_PACKAGE,package_url=LIBFFI_BASE+LIBFFI_PACKAGE,
            package_bytes=ffi_size,package_sha256=sha256(ffi_package),signature_sha256=sha256(ffi_signature),
            signature_verified=True,signify_key_id=ffi_key_id,signify_public_key_sha256=ffi_key_sha256,
            upstream_repository='https://github.com/libffi/libffi',upstream_tag='v3.4.8',
            upstream_source_sha256=LIBFFI_SOURCE_SHA256,license='MIT',
            portfile='https://github.com/macports/macports-ports/blob/master/devel/libffi/Portfile',
            extraction_scope='selected signed libffi dylib family only; no package scripts or install hooks are run',
            package_expanded_bytes=ffi_expanded,selected_dylibs={name:sha256(prefix/'lib'/name) for name in ffi_files if (prefix/'lib'/name).is_file()}),
        libedit=dict(package=LIBEDIT_PACKAGE,package_url=LIBEDIT_BASE+LIBEDIT_PACKAGE,package_bytes=edit_size,
            package_sha256=sha256(edit_package),signature_sha256=sha256(edit_signature),signature_verified=True,
            signify_key_id=edit_key_id,signify_public_key_sha256=edit_key_sha256,version='20260512-3.1_0',
            upstream_source_sha256=LIBEDIT_SOURCE_SHA256,license='BSD',
            portfile='https://github.com/macports/macports-ports/blob/master/devel/libedit/Portfile',
            extraction_scope='selected signed libedit dylib family only; no package scripts or install hooks are run',
            package_expanded_bytes=edit_expanded,selected_dylibs={name:sha256(prefix/'lib'/name) for name in edit_files if (prefix/'lib'/name).is_file()}),
        ncurses=dict(package=NCURSES_PACKAGE,package_url=NCURSES_BASE+NCURSES_PACKAGE,package_bytes=ncurses_size,
            package_sha256=sha256(ncurses_package),signature_sha256=sha256(ncurses_signature),signature_verified=True,
            signify_key_id=ncurses_key_id,signify_public_key_sha256=ncurses_key_sha256,version='6.6_0',
            upstream_source_sha256=NCURSES_SOURCE_SHA256,license='MIT',
            portfile='https://github.com/macports/macports-ports/blob/master/devel/ncurses/Portfile',
            extraction_scope='selected signed ncurses dylib family only; no package scripts or install hooks are run',
            package_expanded_bytes=ncurses_expanded,selected_dylibs={name:sha256(prefix/'lib'/name) for name in ncurses_files if (prefix/'lib'/name).is_file()}),
        macports_link_dependencies=dependency_inventory,
        tool_prefix=str(prefix),opt_sha256=sha256(opt),llc_sha256=sha256(llc),
        files=files,opt_version=opt_text.strip(),llc_version=llc_text.strip(),
        scope='Signature-verified exact MacPorts LLVM 12.0.1 ARM64 tools and owned libraries for Taskell GHC 9.0.2; archive and extracted files stay in the campaign toolchain root.'))
    with Path(args.github_env).open('a',encoding='utf-8',newline='\n') as stream:
        stream.write('PATH='+env['PATH']+'\n')
        stream.write('DYLD_LIBRARY_PATH='+env['DYLD_LIBRARY_PATH']+'\n')
        stream.write('TASKELL_LLVM_MANIFEST='+str(manifest)+'\n')
    print(json.dumps(dict(manifest=str(manifest),package_sha256=sha256(package),expanded_bytes=expanded,
        opt_sha256=sha256(opt),llc_sha256=sha256(llc),libffi_package_sha256=sha256(ffi_package),
        libedit_package_sha256=sha256(edit_package),ncurses_package_sha256=sha256(ncurses_package)),sort_keys=True))


if __name__=='__main__':main()
