"""Bounded read-only Ruby prerequisite probe; never substitutes for a project test."""
import asyncio
import json
from adversarial_process import execute
from readiness_evidence import Campaign, RAW
from readiness_rubygems_cases import environment


async def main():
    active=RAW/'active/rubygems'
    ruby=active/json.loads((active/'runtime.json').read_text())['ruby_relative_path']
    env=environment()
    for key in ['HOME','USERPROFILE','APPDATA','LOCALAPPDATA','TEMP','TMP']:
        env[key]=str(active/('tmp' if key in ['TEMP','TMP'] else 'home'))
    # Both candidate Windows system-config variables point only to an owned cwd.
    system_drive=next((v for k,v in env.items() if k.upper()=='SYSTEMDRIVE'),None)
    if not system_drive:raise RuntimeError('read-only native SystemDrive prerequisite absent')
    for additions in [{'SystemDrive':system_drive}]:
        clean={key:value for key,value in env.items() if key.upper() in
               {'PATH','PATHEXT','SYSTEMROOT','WINDIR','COMSPEC','HOME','USERPROFILE','APPDATA','LOCALAPPDATA','TEMP','TMP','RUBYLIB'}}
        clean.update(additions)
        result=await execute([ruby,'-retc','-e','p [Etc.sysconfdir, ENV.values_at("PROGRAMDATA", "ALLUSERSPROFILE")]'],
            'rubygems','ruby-system-config-prerequisite',env=clean,cwd=active/'home',timeout=30,campaign=Campaign())
        print(additions,result['output'])
    result=await execute([ruby,'-retc','-e','p Etc.sysconfdir'],
        'rubygems','ruby-ambient-readonly-prerequisite',env=env,cwd=active/'home',timeout=30,campaign=Campaign())
    print('Parent environment with owned user/home/temp:',result['output'])


if __name__=='__main__':asyncio.run(main())
