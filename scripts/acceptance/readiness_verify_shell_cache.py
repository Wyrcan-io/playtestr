"""Prove explicit child PowerShell cache ownership with a bounded native control."""
import asyncio
import argparse
import json
import os
import re
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    if os.name!='nt':raise RuntimeError('native Windows cache control only')
    parser=argparse.ArgumentParser();parser.add_argument('--resume');args=parser.parse_args()
    if args.resume and not re.fullmatch('[0-9a-f]{32}',args.resume):raise RuntimeError('invalid cache control owner')
    identity=args.resume or uuid.uuid4().hex;root=RAW/'shell-cache-control'/identity
    if not args.resume:root.mkdir(parents=True)
    source=ROOT/'Microsoft/Windows/PowerShell/ModuleAnalysisCache'
    copy=root/'original-ModuleAnalysisCache.bin'
    if args.resume:
        observed=json.loads((root/'original.json').read_text(encoding='utf-8-sig'))
        removal=json.loads((root/'original-removed.json').read_text(encoding='utf-8-sig'))
        if source.exists() or sha256(copy)!=observed['sha256'] or not removal['removed']:raise RuntimeError('resumed original cache proof differs')
    else:
        if not source.is_file() or source.stat().st_size>1024**2:raise RuntimeError('unexpected root cache observation')
        shutil.copyfile(source,copy)
        if sha256(copy)!=sha256(source):raise RuntimeError('root module cache copy differs')
        immutable_json(root/'original.json',dict(path=source.relative_to(ROOT).as_posix(),bytes=source.stat().st_size,sha256=sha256(source),
            scope='New untracked file absent before fresh-checkout run; native root cache ownership gap. Original causal branch not proven.'))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
    for name in ['TEMP','TMP','TMPDIR','APPDATA','LOCALAPPDATA','HOME','USERPROFILE']:
        path=root/'home'/name.lower();path.mkdir(parents=True,exist_ok=True);env[name]=str(path)
    cache=root/'cache';cache.mkdir(exist_ok=True);env['PSModuleAnalysisCachePath']=str(cache/'parent-ModuleAnalysisCache')
    removed=None
    if not args.resume:
        removed=await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
            ROOT/'scripts/acceptance/readiness_remove_root_shell_cache.ps1','-EvidenceId',identity],
            'core','root-shell-cache-retained-native-removal',env=env,timeout=60,campaign=Campaign())
    script=root/'control-v2.ps1'
    script.write_text("""param([string]$Payload,[string]$Cache)
$ErrorActionPreference='Stop'
if((Resolve-Path -LiteralPath $Payload).ProviderPath -ne $Payload -or (Get-Item -LiteralPath $Payload).Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Redirected synthetic payload'}
if(@(Get-ChildItem -LiteralPath $Payload -Recurse -Force -File).Count -ne 1 -or (Get-Content -LiteralPath (Join-Path $Payload 'marker.txt') -Raw) -ne 'owned marker'){throw 'Unexpected synthetic payload'}
foreach($entry in Get-ChildItem -LiteralPath $Payload -Recurse -Force){if($entry.Attributes -band [IO.FileAttributes]::ReparsePoint){throw 'Linked synthetic payload'}}
Remove-Item -LiteralPath $Payload -Recurse -Force
Get-Command Get-FileHash | Out-Null
$deadline=[DateTime]::UtcNow.AddSeconds(15)
while(-not (Test-Path -LiteralPath $Cache)){
    if([DateTime]::UtcNow -ge $deadline){throw 'No positive module cache publication'}
    Start-Sleep -Milliseconds 100
}
if((Get-Item -LiteralPath $Cache).Length -eq 0){throw 'Empty module cache publication'}
Write-Output 'Observed actual background module-cache publication after synthetic payload removal.'
""",encoding='utf-8',newline='\n')
    controls=[]
    for fixed in [False,True]:
        label='explicit-owned-cache-v2' if fixed else 'removed-owned-appdata-default-v2'
        case=root/label;case.mkdir();payload=case/'payload';payload.mkdir();(payload/'marker.txt').write_text('owned marker',encoding='ascii')
        child=dict(env);child.pop('PSModuleAnalysisCachePath',None)
        for key,name in [('HOME','home'),('USERPROFILE','home'),('LOCALAPPDATA','home/localappdata'),('APPDATA','home/appdata')]:
            path=payload/name;path.mkdir(parents=True,exist_ok=True);child[key]=str(path)
        expected=case/'Microsoft/Windows/PowerShell/ModuleAnalysisCache'
        if fixed:
            expected=cache/'explicit-ModuleAnalysisCache';child['PSModuleAnalysisCachePath']=str(expected)
        result=await execute(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',script,'-Payload',payload,'-Cache',expected],
            'core','shell-cache-'+label,cwd=case,env=child,timeout=30,campaign=Campaign())
        if payload.exists() or not expected.is_file():raise RuntimeError('missing actual cache/removal proof')
        if fixed and (case/'Microsoft').exists():raise RuntimeError('explicit cache still escaped to cwd')
        controls.append(dict(profile=label,attempt=result['id'],cache_sha256=sha256(expected),cache_bytes=expected.stat().st_size))
    if (ROOT/'Microsoft').exists():raise RuntimeError('root cache unexpectedly recreated')
    receipt=dict(id=identity,original_sha256=sha256(copy),original_removal_attempt=removed['id'] if removed else None,
        original_removal_receipt_sha256=sha256(root/'original-removed.json'),controls=controls,
        scope='Original task-created root cache retained and native removed. Controlled removal of owned home/appdata reproduces relative cwd cache publication; explicit pre-start PSModuleAnalysisCachePath positively publishes only to owned absolute cache after payload removal. This demonstrates the fallback and prevention, not retrospective proof of the original background write ordering. Initial broad module-enumeration control timed out and remains separately retained. No Go/archive changes or product-control credit.',
        primary_documentation='https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_windows_powershell_5.1?view=powershell-5.1')
    immutable_json(root/'verified.json',receipt)
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/shell-cache-ownership-verification.json',receipt)
    print('Native shell cache fallback and explicit owned-path publication verified; original root cache removed.')


if __name__=='__main__':asyncio.run(main())
