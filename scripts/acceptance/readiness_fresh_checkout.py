"""Verify an actual fresh Windows checkout without ignored campaign history."""
import asyncio
import argparse
import json
import os
from pathlib import Path
import re
import uuid

from adversarial_process import execute
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    if os.name!='nt':raise RuntimeError('this local checkout verification is declared Windows only')
    parser=argparse.ArgumentParser();parser.add_argument('--resume');parser.add_argument('--public-only',action='store_true');args=parser.parse_args()
    if args.resume and not re.fullmatch('[0-9a-f]{32}',args.resume):raise RuntimeError('invalid fresh checkout owner')
    identity=args.resume or uuid.uuid4().hex;parent=RAW/'fresh-checkout'/identity
    if not args.resume:parent.mkdir(parents=True)
    for path in [RAW,RAW/'fresh-checkout',parent]:
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise RuntimeError('linked fresh checkout ancestor')
    checkout=parent/'payload/checkout';checkout.parent.mkdir(exist_ok=bool(args.resume))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',GIT_CONFIG_NOSYSTEM='1',GOTOOLCHAIN='local',GIT_TERMINAL_PROMPT='0')
    # The existing checkout belongs to the sandbox account while an approved
    # native check runs as the desktop account. Trust this exact known source
    # only in these child commands; never change user/system Git configuration.
    env.update(GIT_CONFIG_COUNT='3',GIT_CONFIG_KEY_0='safe.directory',GIT_CONFIG_VALUE_0=ROOT.as_posix(),
        GIT_CONFIG_KEY_1='safe.directory',GIT_CONFIG_VALUE_1=(ROOT/'.git').as_posix(),
        GIT_CONFIG_KEY_2='core.longpaths',GIT_CONFIG_VALUE_2='true')
    for key,name in [('HOME','home'),('USERPROFILE','home'),('APPDATA','home/appdata'),('LOCALAPPDATA','home/localappdata'),
        ('XDG_CACHE_HOME','home/cache'),('TEMP','tmp'),('TMP','tmp'),('TMPDIR','tmp'),('GOTMPDIR','tmp'),
        ('GOCACHE','go-cache'),('GOPATH','gopath'),('GOMODCACHE','gopath/pkg/mod'),('GIT_TEMPLATE_DIR','templates')]:
        path=parent/'payload'/name;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
    config=parent/'payload/gitconfig';config.write_bytes(b'');env['GIT_CONFIG_GLOBAL']=str(config)
    shell_cache=parent/'shell-cache';shell_cache.mkdir(exist_ok=True)
    env['PSModuleAnalysisCachePath']=str(shell_cache/'ModuleAnalysisCache')
    calls=[]
    async def run(label,argv,cwd=ROOT,timeout=120):
        operation=asyncio.create_task(execute(argv,'core','fresh-checkout-'+label,cwd=cwd,env=env,timeout=timeout,campaign=Campaign()))
        observed=[]
        try:
            while not operation.done():
                size=await asyncio.to_thread(usage,parent/'payload');observed.append(size)
                if size>1024**3:raise RuntimeError('fresh checkout stopped at one-GiB owned storage bound')
                await asyncio.wait({operation},timeout=2)
            result=await operation
        finally:
            if not operation.done():
                operation.cancel()
                try:await operation
                except asyncio.CancelledError:pass
            immutable_json(parent/('storage-'+label+'-'+uuid.uuid4().hex+'.json'),dict(observed_bytes=observed,
                scope='Periodic owned logical bytes, not exact peak or OS quota.'))
        calls.append(dict(label=label,attempt=result['id']));return result
    current=await run('revision',['git','rev-parse','HEAD']);revision=current['output'].strip()
    if args.resume:
        intent=json.loads((parent/'intent.json').read_text(encoding='utf-8-sig'))
        if intent['id']!=identity or intent['revision']!=revision or intent['source']!=str(ROOT) or intent.get('public_only',False)!=args.public_only:raise RuntimeError('resumed checkout ownership/source differs')
        remote=await run('resumed-remote',['git','-C',checkout,'remote','get-url','origin'])
        if remote['output'].strip()!='https://github.com/Wyrcan-io/playtestr.git':raise RuntimeError('resumed clone source differs')
    else:
        immutable_json(parent/'intent.json',dict(id=identity,revision=revision,source=str(ROOT),
            public_only=args.public_only,
            scope='Actual shallow approved GitHub branch clone and checkout; exact tracked campaign bytes/modes and empty ignored history. Default also runs uncached Go tests/vet/examples; explicit public-only supplement does not claim those checks. No global installs or modifications.'))
        await run('clone',['git','clone','--depth','1','--single-branch','--branch','work/p0-p2-implementation',
            '--no-checkout','https://github.com/Wyrcan-io/playtestr.git',checkout],timeout=180)
    for path in [checkout,checkout/'.git']:
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise RuntimeError('linked fresh clone')
        path.resolve(strict=True).relative_to((parent/'payload').resolve(strict=True))
    # Finish this owned clone's interrupted first checkout. Its partial files
    # were created by the recorded failed checkout; never target the source.
    await run('checkout',['git','-C',checkout,'checkout','--force','--detach',revision])
    tracked=await run('tracked-public',['git','-c','core.quotePath=false','ls-files','--','docs/validation/runner-readiness-ten-project-pass'])
    public=tracked['output'].splitlines()
    if not public or len(public)>10000:raise RuntimeError('fresh public file inventory bound')
    total=0
    for name in public:
        original=ROOT/name;fresh=checkout/name
        total+=original.stat().st_size
        if total>25*1024**2 or sha256(original)!=sha256(fresh):raise RuntimeError('public fixture/snapshot/contract bytes changed in fresh checkout: '+name)
    before=await run('source-index',['git','ls-files','--stage'])
    after=await run('fresh-index',['git','ls-files','--stage'],cwd=checkout)
    if before['output']!=after['output']:raise RuntimeError('fresh Git tracked blob/mode inventory differs')
    if (checkout/'artifacts/runner-readiness-ten-project-pass').exists():raise RuntimeError('fresh checkout unexpectedly includes ignored campaign evidence')
    sdk=RAW/'toolchain/go/bin/go.exe'
    if not sdk.is_file():raise RuntimeError('existing owned Go prerequisite missing')
    if args.public_only:
        await run('unchanged-production',['git','diff','--exit-code','129b7a45c0006be550f798ce52c2fbbfd327e515','--','*.go','go.mod','go.sum'])
    else:
        await run('go-test',[sdk,'test','-count=1','./...'],cwd=checkout,timeout=1200)
        await run('go-vet',[sdk,'vet','./...'],cwd=checkout,timeout=300)
        (checkout/'bin').mkdir(exist_ok=True)
        await run('demo-build',[sdk,'build','-o','bin/demo.exe','./cmd/demo'],cwd=checkout,timeout=120)
        await run('public-examples',[sdk,'run','./cmd/playtestr','test','examples/menu.json','examples/menu-exit.json'],cwd=checkout,timeout=180)
    files={};size=0
    for path in (parent/'payload').rglob('*'):
        if path.is_symlink() or getattr(path,'is_junction',lambda:False)():raise RuntimeError('linked fresh checkout removal member')
        if path.is_file():
            size+=path.stat().st_size
            if len(files)>=50000 or size>1024**3:raise RuntimeError('fresh checkout removal inventory bound')
            files[path.relative_to(parent/'payload').as_posix()]=sha256(path)
    immutable_json(parent/'payload-index.json',dict(files=files,bytes=size))
    await run('checked-removal',['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        ROOT/'scripts/acceptance/readiness_remove_fresh_checkout.ps1','-CheckoutId',identity],timeout=300)
    if (parent/'payload').exists():raise RuntimeError('fresh checkout remains after native removal')
    receipt=dict(id=identity,revision=revision,resumed_setup=bool(args.resume),public_files=len(public),public_bytes=total,go_sha256=sha256(sdk),
        calls=calls,payload_index_sha256=sha256(parent/'payload-index.json'),removed=True,public_only=args.public_only,
        scope=('Actual Windows fresh Git checkout; all tracked Git blob/mode entries and campaign public bytes exact, no ignored history. '
            +('Explicit public-only supplement: production Go/module bytes unchanged; tests/vet/examples are qualified by the earlier full fresh-checkout receipt and were not repeated here. ' if args.public_only else 'Uncached ordinary tests/vet and manual examples pass. ')
            +'Windows executable-bit semantics are not Unix filesystem execution evidence. Owned checkout/cache removed through native PowerShell after complete hash verification.'))
    immutable_json(parent/'verified.json',receipt)
    immutable_json(ROOT/('docs/validation/runner-readiness-ten-project-pass/'+('fresh-public-closing.json' if args.public_only else 'fresh-checkout-verification.json')),receipt)
    print('Fresh actual checkout, uncached tests, public bytes/modes and checked removal verified.')


if __name__=='__main__':asyncio.run(main())
