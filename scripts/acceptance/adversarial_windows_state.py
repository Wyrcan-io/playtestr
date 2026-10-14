"""Own and reset actual target state on disposable hosted Windows profiles.

This campaign helper is not a sandbox or a public workspace capability.
"""
from contextlib import contextmanager
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import uuid
from adversarial_process import ROOT, RAW

MARKER='.playtestr-adversarial-owner.json'


def hosted_only():
    if os.name!='nt' or os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_ENVIRONMENT')!='github-hosted':
        raise RuntimeError('Actual Windows state leases require a disposable GitHub-hosted runner')


def known_folder(guid):
    class GUID(ctypes.Structure):
        _fields_=[('Data1',wintypes.DWORD),('Data2',wintypes.WORD),('Data3',wintypes.WORD),('Data4',ctypes.c_ubyte*8)]
    value=GUID.from_buffer_copy(uuid.UUID(guid).bytes_le)
    pointer=ctypes.c_void_p()
    shell=ctypes.windll.shell32
    shell.SHGetKnownFolderPath.argtypes=[ctypes.POINTER(GUID),wintypes.DWORD,wintypes.HANDLE,ctypes.POINTER(ctypes.c_void_p)]
    shell.SHGetKnownFolderPath.restype=ctypes.c_long
    if shell.SHGetKnownFolderPath(ctypes.byref(value),0,None,ctypes.byref(pointer))!=0:
        raise RuntimeError('Cannot resolve hosted Windows known folder')
    try:return Path(ctypes.wstring_at(pointer)).resolve(strict=True)
    finally:
        ctypes.windll.ole32.CoTaskMemFree.argtypes=[ctypes.c_void_p]
        ctypes.windll.ole32.CoTaskMemFree(pointer)


def lease_path(project):
    return ROOT/'.cache/ten-new-project-apps'/project/'external-windows-state.json'


def assert_no_target():
    # Inventory only; never kill or alter an unrelated process.
    if os.name!='nt':raise RuntimeError('Native Windows process inventory required')
    class PROCESSENTRY32W(ctypes.Structure):
        _fields_=[('dwSize',wintypes.DWORD),('cntUsage',wintypes.DWORD),
            ('th32ProcessID',wintypes.DWORD),('th32DefaultHeapID',ctypes.c_size_t),
            ('th32ModuleID',wintypes.DWORD),('cntThreads',wintypes.DWORD),
            ('th32ParentProcessID',wintypes.DWORD),('pcPriClassBase',wintypes.LONG),
            ('dwFlags',wintypes.DWORD),('szExeFile',wintypes.WCHAR*260)]
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes=[wintypes.DWORD,wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype=wintypes.HANDLE
    kernel.Process32FirstW.argtypes=[wintypes.HANDLE,ctypes.POINTER(PROCESSENTRY32W)]
    kernel.Process32NextW.argtypes=kernel.Process32FirstW.argtypes
    kernel.CloseHandle.argtypes=[wintypes.HANDLE]
    snapshot=kernel.CreateToolhelp32Snapshot(2,0)
    if snapshot==ctypes.c_void_p(-1).value:raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry=PROCESSENTRY32W();entry.dwSize=ctypes.sizeof(entry)
        current=kernel.Process32FirstW(snapshot,ctypes.byref(entry))
        count=0;started=time.monotonic()
        while current:
            count+=1
            if count>65536 or time.monotonic()-started>3:
                raise RuntimeError('Native Windows process inventory bound')
            if entry.szExeFile.casefold()=='yazi.exe':
                raise RuntimeError('Cannot reset state while Yazi may be running')
            current=kernel.Process32NextW(snapshot,ctypes.byref(entry))
        if ctypes.get_last_error()!=18:raise ctypes.WinError(ctypes.get_last_error())
    finally:kernel.CloseHandle(snapshot)


def claim(project):
    hosted_only()
    if project!='yazi':raise RuntimeError('No reviewed known-folder recipe for this target')
    path=lease_path(project)
    if path.exists():raise RuntimeError('Refuse replacing an existing Windows state lease')
    assert_no_target()
    owner=dict(campaign='ten-new-project-adversarial-pass',project=project,workspace=str(ROOT),
               run_id=os.environ['GITHUB_RUN_ID'])
    roots=[known_folder('3EB685DB-65F9-4CF6-A03A-E3EF65729F3D')/'yazi',
           known_folder('F1B32785-6FBA-4FCF-9D55-7B8E7F157091')/'yazi']
    for root in roots:
        if root.exists() or root.is_symlink() or getattr(root,'is_junction',lambda:False)():
            raise RuntimeError('Refuse adopting existing target state: '+str(root))
    for root in roots:
        root.mkdir()
        (root/MARKER).write_text(json.dumps(owner,sort_keys=True)+'\n',encoding='utf-8')
    path.write_text(json.dumps(dict(owner=owner,roots=[str(r) for r in roots]),indent=2)+'\n',encoding='utf-8')


def reset(project):
    hosted_only();assert_no_target()
    lease=json.loads(lease_path(project).read_text(encoding='utf-8'))
    owner=lease['owner']
    if owner!=dict(campaign='ten-new-project-adversarial-pass',project=project,workspace=str(ROOT),run_id=os.environ['GITHUB_RUN_ID']):
        raise RuntimeError('Windows state lease ownership differs')
    allowed={known_folder('3EB685DB-65F9-4CF6-A03A-E3EF65729F3D')/'yazi',
             known_folder('F1B32785-6FBA-4FCF-9D55-7B8E7F157091')/'yazi'}
    roots=[Path(p) for p in lease['roots']]
    if set(roots)!=allowed:raise RuntimeError('Unknown Windows state roots')
    files={};entries=0;size=0;started=time.monotonic()
    for root in roots:
        if root.is_symlink() or getattr(root,'is_junction',lambda:False)() or root.resolve(strict=True)!=root:
            raise RuntimeError('Linked Windows state root')
        if json.loads((root/MARKER).read_text(encoding='utf-8'))!=owner:
            raise RuntimeError('Windows state marker differs')
        for folder,dirs,names in os.walk(root,followlinks=False):
            for name in [*dirs,*names]:
                p=Path(folder)/name;entries+=1
                if entries>4096 or time.monotonic()-started>10:raise RuntimeError('Windows state inventory bound')
                if p.is_symlink() or getattr(p,'is_junction',lambda:False)():raise RuntimeError('Linked target state')
                p.resolve(strict=True).relative_to(root)
                if p.is_file() and p.name!=MARKER:
                    length=p.stat().st_size;size+=length
                    if size>4*1024*1024:raise RuntimeError('Windows state byte bound')
                    files[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
    # Validate both complete trees before any recursive removal.
    for root in roots:
        for child in root.iterdir():
            if child.name==MARKER:continue
            if child.is_dir():shutil.rmtree(child)
            else:child.unlink()
    return dict(owner=owner,roots=lease['roots'],files_sha256=files,bytes=size,reset=True)


@contextmanager
def target_state(project,argv):
    enabled=os.name=='nt' and project=='yazi' and Path(str(argv[0])).name.lower() in {'playtestr.exe','playtestr-frozen.exe'}
    if not enabled:
        yield
        return
    hosted_only()
    if not lease_path(project).is_file():
        raise RuntimeError('Windows target execution requires an owned actual-state lease')
    before=reset(project)
    error=None
    try:yield
    except BaseException as caught:
        error=caught
        raise
    finally:
        try:
            after=reset(project)
            folder=RAW/project;folder.mkdir(parents=True,exist_ok=True)
            (folder/('external-state-'+uuid.uuid4().hex+'.json')).write_text(
                json.dumps(dict(before=before,after=after,scope='Separate hosted target known-folder state; not managed by Playtestr'),indent=2)+'\n',encoding='utf-8')
        except Exception as cleanup:
            if error is None:raise
            error.add_note('External target state cleanup failed: '+str(cleanup))


def release(project):
    state=reset(project)
    for name in state['roots']:
        root=Path(name);(root/MARKER).unlink();root.rmdir()
        if root.exists():raise RuntimeError('External Windows target state remains')
    return dict(roots=state['roots'],removed=True,scope='Owned disposable hosted Windows known-folder paths')
