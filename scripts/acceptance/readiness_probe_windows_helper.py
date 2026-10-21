"""Bounded own-PID probe of Bash-resolved Python command-line ownership."""
import argparse
import asyncio
import base64
import json
import os
from pathlib import Path
import subprocess

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--child',action='store_true');args=parser.parse_args()
    if os.name!='nt':raise RuntimeError('native Windows helper ownership probe only')
    if args.child:
        import sys
        prefix=str(Path(sys.executable).parent).replace("'","''")
        script=("$ErrorActionPreference='Stop'; $p=Get-CimInstance Win32_Process -Filter 'ProcessId = "+str(os.getpid())+"'; "
            "if($null -eq $p){throw 'Own process observation missing'}; "
            "[bool]($p.CommandLine.IndexOf('"+prefix+"',[StringComparison]::OrdinalIgnoreCase) -ge 0)")
        encoded=base64.b64encode(script.encode('utf-16-le')).decode()
        result=subprocess.run(['powershell.exe','-NoProfile','-EncodedCommand',encoded],capture_output=True,timeout=15,check=True)
        value=result.stdout.decode('utf-8-sig').strip()
        if value not in {'True','False'}:raise RuntimeError('unexpected own-PID result')
        print(json.dumps(dict(own_python_command_line_contains_resolved_executable_directory=value=='True',
            command_values_persisted=False,scope='Own PID only; no process killed or other command line retained.')))
        return
    bash=Path(r'C:\Program Files\Git\bin\bash.exe')
    if not bash.is_file():raise RuntimeError('installed Git Bash missing; no installation attempted')
    root=RAW/'windows-helper-ownership';root.mkdir()
    home=root/'home';home.mkdir()
    env=dict(os.environ,HOME=str(home),USERPROFILE=str(home),TMP=str(RAW/'tmp'),TEMP=str(RAW/'tmp'),
        PYTHONDONTWRITEBYTECODE='1')
    result=await execute([bash,'--noprofile','--norc','-c','python -B scripts/acceptance/readiness_probe_windows_helper.py --child'],
        'core','native-git-bash-python-own-commandline',cwd=ROOT,env=env,timeout=30,campaign=Campaign())
    value=json.loads(result['output'])
    immutable_json(root/'verified.json',dict(attempt=result['id'],**value))
    print('Bash Python command line includes interpreter directory:',value['own_python_command_line_contains_resolved_executable_directory'])


if __name__=='__main__':asyncio.run(main())
