"""Qualify fixed production source and package a distinct unpublished native archive."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tarfile
import zipfile

from adversarial_process import execute
from next20_check import RAW,ROOT,NextCampaign,owned_environment
from readiness_evidence import immutable_json,sha256

VERSION='v0.4.0-rc.6'
SERIES='native-exit-v1'
FOCUSED='^(TestExitStatusBoundsBySpecVersion|TestNativeWindowsWideExitStatusAndSameRunState|TestHTMLPreservesNativeWindowsExitStatus|TestRecorderExportsAndReplaysNativeWindowsExit|TestNativeExitSchemaRangesPreserveOlderSpecBounds|TestNativeSignalExitStatusAndSameRunState)$'


class SourceCampaign(NextCampaign):
    def __init__(self,inputs,raw=RAW):
        super().__init__(raw,phase='development');self.inputs=inputs

    def identity(self,project,argv):
        # Go's -run operand is a regexp, never a file input. The shared legacy
        # collector probes argv as paths; a valid long regexp can exceed the
        # filesystem's component limit. Keep the actual command unchanged and
        # bind the regexp through this exact helper source instead.
        file_argv=[value for i,value in enumerate(argv) if not i or str(argv[i-1])!='-run']
        return super().identity(project,[*file_argv,*self.inputs])


def source_inputs(source,revision):
    def git(*args):
        return subprocess.check_output(['git','-C',str(source),*args],timeout=15)
    if git('rev-parse','HEAD').decode().strip()!=revision:raise ValueError('wrong fixed production checkout')
    if git('status','--porcelain','--untracked-files=all').strip():raise ValueError('production checkout is not clean')
    names=git('ls-files','-z').decode().split('\0')
    selected=sorted(n for n in names if n.endswith('.go') or n.startswith('schema/') and n.endswith('.json') or
        n in {'go.mod','go.sum','README.md','LICENSE','THIRD_PARTY_NOTICES.md'})
    files={};total=0
    for name in selected:
        path=source/name;path.resolve(strict=True).relative_to(source.resolve(strict=True))
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise ValueError('linked production input')
        total+=path.stat().st_size
        if len(files)>=10000 or total>64*1024**2:raise ValueError('production input bound')
        files[name]=sha256(path)
    return files


def environment():
    env=owned_environment()
    for key,folder in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),
        ('LOCALAPPDATA','home/localappdata'),('XDG_CACHE_HOME','home/cache'),('XDG_CONFIG_HOME','home/config')]:
        path=RAW/'replacement-build'/folder;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
    env.update(GOTOOLCHAIN='local',GOROOT=str(RAW/'toolchain/go'),GOENV='off',GOWORK='off',
        GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    for key in ['GOOS','GOARCH','GOFLAGS','RUSTC_WRAPPER']:
        env.pop(key,None)
    return env


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True)
    parser.add_argument('--stage',choices=['sdk','core','package'],required=True);args=parser.parse_args()
    if not re.fullmatch('[0-9a-f]{40}',args.source):raise ValueError('fixed full source revision required')
    source=ROOT/'.candidate-source';source.resolve(strict=True).relative_to(ROOT.resolve(strict=True))
    if source.is_symlink() or getattr(source,'is_junction',lambda:False)():raise ValueError('linked production checkout')
    inputs=source_inputs(source,args.source)
    if args.stage=='sdk':
        from readiness_bootstrap_go import main as bootstrap
        bootstrap(owned=RAW/'toolchain');return
    host={'Linux':'linux','Darwin':'darwin','Windows':'windows'}[platform.system()]
    arch={'x86_64':'amd64','amd64':'amd64','aarch64':'arm64','arm64':'arm64'}[platform.machine().lower()]
    suffix='.exe' if os.name=='nt' else '';tool=RAW/'toolchain/go/bin'/('go'+suffix)
    sdk=json.loads((RAW/'toolchain/sdk.json').read_text())
    if sdk['version']!='go1.25.0' or sdk['host']!=host or sdk['architecture']!=arch:raise ValueError('native SDK differs')
    root=RAW/'replacement-candidate'/SERIES/(host+'-'+arch);root.mkdir(parents=True,exist_ok=True)
    env=environment();env['PATH']=str(tool.parent)+os.pathsep+env.get('PATH','')
    campaign=SourceCampaign([source/name for name in inputs]);attempts=[]
    async def run(argv,label,timeout=180,selected_env=None):
        result=await execute(argv,'core','replacement-'+label,cwd=source,env=selected_env or env,
            timeout=timeout,campaign=campaign);attempts.append(dict(label=label,id=result['id']))
        return result
    if args.stage=='core':
        if (root/'native-core.json').exists():raise ValueError('preserve completed native core qualification')
        actual=await run([tool,'env','-json','GOOS','GOARCH','GOVERSION','GOROOT','GOTOOLCHAIN'],'native-sdk-settings')
        settings=json.loads(actual['output'])
        if (settings.get('GOOS')!=host or settings.get('GOARCH')!=arch or settings.get('GOVERSION')!='go1.25.0'
            or settings.get('GOTOOLCHAIN')!='local' or Path(settings['GOROOT']).resolve()!=tool.parent.parent.resolve()):
            raise ValueError('cross/incorrect SDK execution or ambient standard library')
        await run([tool,'test','./...','-timeout','5m'],'all-go-tests',600)
        await run([tool,'test','-v','./internal/runner','./internal/report','./cmd/playtestr','./schema',
            '-run',FOCUSED,'-count=1','-timeout','3m'],'focused-native-status-controls',240)
        await run([tool,'vet','./...'],'go-vet',240)
        race=dict(env,CGO_ENABLED='1')
        if os.name=='nt':
            options=[Path('C:/mingw64/bin/gcc.exe'),Path('C:/msys64/mingw64/bin/gcc.exe'),Path('C:/msys64/ucrt64/bin/gcc.exe')]
            compiler=next((p for p in options if p.is_file()),None)
            if compiler is None:raise ValueError('required read-only native race GCC prerequisite missing')
            race['CC']=str(compiler);race['PATH']=str(compiler.parent)+os.pathsep+race['PATH']
        await run([tool,'test','-race','-count=1','./...','-timeout','8m'],'native-race-tests',900,race)
        if source_inputs(source,args.source)!=inputs:raise ValueError('source changed during native core checks')
        immutable_json(root/'native-core.json',dict(schema_version=1,version=VERSION,source_revision=args.source,
            qualification_revision=os.environ.get('GITHUB_SHA'),host=host,architecture=arch,
            source_inputs=inputs,sdk_sha256=sha256(RAW/'toolchain/sdk.json'),compiler_sha256=sha256(tool),
            attempts=attempts,ordinary_project_credit=0,
            applicability='Windows-wide-exit and Windows recorder families execute only on Windows; Unix signal family executes only on Unix. All common bounds/HTML/schema checks and full native Go/vet/race run on each host. This is not the external-project or whole-acceptance campaign.'))
        print('Actual native source core completed:',host,arch,args.source);return
    core=root/'native-core.json';qualified=json.loads(core.read_text())
    if qualified['source_revision']!=args.source or qualified['source_inputs']!=inputs:
        raise ValueError('private package requires exact same-host successful native source checks')
    if (root/'candidate.json').exists():raise ValueError('never rebuild/relabel completed candidate')
    binary=root/('playtestr'+suffix)
    build=await run([tool,'build','-trimpath','-buildvcs=false','-ldflags',
        '-s -w -X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version='+VERSION,
        '-o',binary,'./cmd/playtestr'],'native-build-once',240)
    await run([tool,'run','./cmd/package-release','-binary',binary,'-version',VERSION,
        '-os',host,'-arch',arch,'-out',root/'dist'],'native-package',240)
    base='playtestr_'+VERSION.removeprefix('v')+'_'+host+'_'+arch
    archive=root/'dist'/(base+('.zip' if os.name=='nt' else '.tar.gz'))
    if archive.stat().st_size>16*1024**2:raise ValueError('private archive size bound')
    if archive.with_name(archive.name+'.sha256').read_text().strip()!=sha256(archive)+'  '+archive.name:
        raise ValueError('archive checksum sidecar differs')
    expected={base+'/'+n for n in [binary.name,'README.md','LICENSE','THIRD_PARTY_NOTICES.md']};members={}
    extracted=root/'extracted';extracted.mkdir()
    def save(name,data):
        if name not in expected or name in members or len(data)>16*1024**2:raise ValueError('archive member rejected')
        path=extracted/name;path.parent.mkdir(exist_ok=True);path.write_bytes(data)
        members[name]=dict(bytes=len(data),sha256=sha256(path))
    if os.name=='nt':
        with zipfile.ZipFile(archive) as stream:
            if len(stream.infolist())!=4:raise ValueError('archive layout differs')
            for member in stream.infolist():
                if member.is_dir() or member.file_size>16*1024**2:raise ValueError('unsafe archive member')
                save(member.filename,stream.read(member))
    else:
        with tarfile.open(archive,'r:gz') as stream:
            for member in stream:
                if not member.isfile() or member.size>16*1024**2:raise ValueError('unsafe archive member')
                save(member.name,stream.extractfile(member).read(member.size+1))
    if set(members)!=expected:raise ValueError('private archive coverage differs')
    released=extracted/base/binary.name
    if os.name!='nt':released.chmod(0o755)
    if sha256(released)!=sha256(binary):raise ValueError('extracted executable differs')
    for name in ['README.md','LICENSE','THIRD_PARTY_NOTICES.md']:
        if sha256(extracted/base/name)!=inputs[name]:raise ValueError('packaged documentation differs')
    version=await run([released,'--version'],'extracted-version')
    if version['output'].strip()!='playtestr '+VERSION:raise ValueError('actual archive version differs')
    await run([released,'--help'],'extracted-help')
    if source_inputs(source,args.source)!=inputs:raise ValueError('source changed during packaging')
    immutable_json(root/'candidate.json',dict(schema_version=1,series=SERIES,version=VERSION,
        source_revision=args.source,qualification_revision=os.environ.get('GITHUB_SHA'),host=host,architecture=arch,
        source_inputs=inputs,compiler_sha256=sha256(tool),native_core_sha256=sha256(core),
        archive=archive.relative_to(ROOT).as_posix(),archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,
        binary_sha256=sha256(binary),archive_members=members,build_attempt=build['id'],attempts=attempts,
        project_qualification=False,publication=False,
        scope='Distinct unpublished native-status repair archive. Freeze only after all three native packets are independently audited; no rc.5 execution transfer and no final-campaign qualification claim.'))
    print('Built/inspected one distinct private native archive:',archive.name,sha256(archive))


if __name__=='__main__':asyncio.run(main())
