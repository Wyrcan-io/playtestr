"""Build and inspect a private native archive; project qualification is separate."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import platform
import subprocess
import tarfile
import zipfile

from adversarial_process import execute
from readiness_evidence import Campaign,RAW,ROOT,immutable_json,sha256

SOURCE='3d50d81aae8f1d24f7a718e6e05b39069697b1a6'
VERSION='v0.4.0-rc.4'


class SourceCampaign(Campaign):
    def __init__(self,inputs):
        super().__init__();self.inputs=inputs

    def identity(self,project,argv):
        # Bind checkout inputs without changing the actual executed command.
        return super().identity(project,[*argv,*self.inputs])


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--series',choices=['provisional-v1'],required=True);args=parser.parse_args()
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    ledger=json.loads((docs/'candidates.json').read_text(encoding='utf-8-sig'))
    if ledger['development_admissions']!=8:raise RuntimeError('provisional freeze requires eight completed development admissions')
    for repo,status in [('jondot/hygen','provisional-holdout-9'),('rclone/rclone','provisional-holdout-10')]:
        if next(r for r in ledger['rows'] if r['repository']==repo)['status']!=status:raise RuntimeError('reserved transfer target was already consumed')
    qualification=docs/'earlier-project-requalification-retention-3d50d81.json'
    current=json.loads(qualification.read_text(encoding='utf-8-sig'))
    if current['runner_source']!=SOURCE or len(current['projects'])!=7 or {r['project'] for r in current['projects']}!={'plop','poetry','rubygems','edit','vis','fff','papis'}:raise RuntimeError('seven earlier projects lack current-source requalification')
    for row in current['projects']:
        receipt=docs/row['project']/'requalification-3d50d81.json'
        value=json.loads(receipt.read_text(encoding='utf-8-sig'))
        if sha256(receipt)!=row['requalification_sha256'] or value['runner_source']!=SOURCE or value['cells']!=row['cells']:raise RuntimeError('current-source project verification changed')
    admission=docs/'frogmouth/development-admission.json'
    if json.loads(admission.read_text(encoding='utf-8-sig'))['runner_source']!=SOURCE:raise RuntimeError('eighth admission uses stale source')
    checkout=ROOT/'.playtestr-tooling'
    if subprocess.check_output(['git','-C',str(checkout),'rev-parse','HEAD'],text=True,timeout=15).strip()!=SOURCE:raise RuntimeError('candidate source checkout differs')
    host={'Linux':'linux','Darwin':'darwin','Windows':'windows'}[platform.system()]
    arch={'x86_64':'amd64','amd64':'amd64','arm64':'arm64','aarch64':'arm64'}[platform.machine().lower()]
    root=RAW/'candidate-packages'/args.series/(host+'-'+arch);root.mkdir(parents=True,exist_ok=False)
    tool=RAW/'toolchain/go/bin'/('go.exe' if os.name=='nt' else 'go')
    env=dict(os.environ,GOTOOLCHAIN='local',GOCACHE=str(RAW/'go-cache'),GOPATH=str(RAW/'gopath'),GOMODCACHE=str(RAW/'gopath/pkg/mod'),TEMP=str(RAW/'tmp'),TMP=str(RAW/'tmp'),TMPDIR=str(RAW/'tmp'),GOTMPDIR=str(RAW/'tmp'))
    binary=root/('playtestr.exe' if os.name=='nt' else 'playtestr')
    tracked=subprocess.check_output(['git','-C',str(checkout),'ls-files','-z'],timeout=15).decode().split('\0')
    names=sorted(n for n in tracked if n.endswith('.go') or n in {'go.mod','go.sum','README.md','LICENSE','THIRD_PARTY_NOTICES.md'})
    inputs={n:sha256(checkout/n) for n in names}
    async def run(argv,label):return await execute(argv,'core','candidate-'+label,cwd=checkout,env=env,timeout=180,campaign=SourceCampaign([checkout/n for n in names]))
    sdk=await run([tool,'version'],'sdk-version')
    settings=await run([tool,'env','-json','GOOS','GOARCH','GOVERSION'],'native-sdk-settings')
    native=json.loads(settings['output'])
    if native['GOOS']!=host or native['GOARCH']!=arch:raise RuntimeError('candidate build would not be native to this host architecture')
    build=await run([tool,'build','-trimpath','-buildvcs=false','-ldflags','-s -w -X github.com/Wyrcan-io/playtestr/internal/buildinfo.Version='+VERSION,'-o',binary,'./cmd/playtestr'],'native-build')
    await run([tool,'run','./cmd/package-release','-binary',binary,'-version',VERSION,'-os',host,'-arch',arch,'-out',root/'dist'],'native-package')
    base='playtestr_'+VERSION.removeprefix('v')+'_'+host+'_'+arch
    archive=root/'dist'/(base+('.zip' if os.name=='nt' else '.tar.gz'))
    if archive.stat().st_size>32*1024**2:raise RuntimeError('private archive bound')
    checksum=archive.with_name(archive.name+'.sha256').read_text().strip()
    if checksum!=sha256(archive)+'  '+archive.name:raise RuntimeError('private archive checksum differs')
    expected={base+'/'+name for name in [binary.name,'LICENSE','README.md','THIRD_PARTY_NOTICES.md']}
    extracted=root/'extracted';extracted.mkdir();members={}
    def save(name,data):
        if name not in expected or len(data)>32*1024**2 or name in members:raise RuntimeError('unreviewed archive payload')
        path=extracted/name;path.parent.mkdir(exist_ok=True);path.write_bytes(data);members[name]=dict(bytes=len(data),sha256=sha256(path))
    if os.name=='nt':
        with zipfile.ZipFile(archive) as stream:
            if set(stream.namelist())!=expected or len(stream.infolist())!=4:raise RuntimeError('private archive layout differs')
            for member in stream.infolist():
                if member.file_size>32*1024**2:raise RuntimeError('private member bound')
                save(member.filename,stream.read(member))
    else:
        with tarfile.open(archive,'r:gz') as stream:
            entries=stream.getmembers()
            if {m.name for m in entries}!=expected or len(entries)!=4:raise RuntimeError('private archive layout differs')
            for member in entries:
                if not member.isfile() or member.size>32*1024**2:raise RuntimeError('private member bound/type')
                save(member.name,stream.extractfile(member).read(member.size+1))
        (extracted/base/binary.name).chmod(0o755)
    released=extracted/base/binary.name
    if sha256(released)!=sha256(binary):raise RuntimeError('extracted runner bytes differ')
    for name in ['LICENSE','README.md','THIRD_PARTY_NOTICES.md']:
        if sha256(extracted/base/name)!=inputs[name]:raise RuntimeError('packaged documentation differs')
    version=await run([released,'--version'],'extracted-version')
    if version['output'].strip()!='playtestr '+VERSION:raise RuntimeError('private archive version differs')
    await run([released,'--help'],'extracted-help')
    if inputs!={n:sha256(checkout/n) for n in names}:raise RuntimeError('candidate source inputs changed during build')
    immutable_json(root/'candidate.json',dict(schema_version=1,series=args.series,version=VERSION,source_revision=SOURCE,host=host,architecture=arch,
        source_qualification_index_sha256=sha256(qualification),eighth_admission_sha256=sha256(admission),source_inputs=inputs,compiler_sha256=sha256(tool),sdk=sdk['output'].strip(),sdk_settings=native,sdk_attempt=sdk['id'],settings_attempt=settings['id'],binary_sha256=sha256(binary),extracted_binary_sha256=sha256(released),
        archive=archive.relative_to(ROOT).as_posix(),archive_sha256=sha256(archive),archive_bytes=archive.stat().st_size,archive_members=members,
        build_attempt=build['id'],version_attempt=version['id'],ledger_sha256=sha256(docs/'candidates.json'),project_qualification=False,
        freeze='Private provisional archive before reserved projects nine/ten. No release/tag/publication authorized; final qualification remains separate.'))
    print('Private native provisional archive inspected:',archive.relative_to(ROOT),sha256(archive))


if __name__=='__main__':asyncio.run(main())
