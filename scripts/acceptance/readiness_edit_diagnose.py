"""Public unsaved field-focus/autocomplete diagnosis, without baseline export."""
import asyncio
import uuid

from adversarial_process import execute
from readiness_edit_cases import environment,expect,key,text
from readiness_evidence import Campaign,RAW,ROOT


async def main():
    root=RAW/'edit/diagnosis'/uuid.uuid4().hex;root.mkdir(parents=True)
    runner=RAW/'runner-revisions/inherited-interrupt/playtestr.exe'
    probes=[('search',b'alpha alpha\n',[expect('alpha alpha'),key('CtrlF'),expect('Find:'),text('alpha'),key('Enter'),
        key('CtrlR'),expect('Replace:'),text('PROBE_ONE'),expect('PROBE_ONE'),'/screen',key('Tab'),text('PROBE_TWO'),expect('PROBE_TWO'),'/screen']),
        ('overwrite',b'reviewed seed\n',[expect('reviewed seed'),key('CtrlN'),expect('Untitled-1'),text('replacement candidate'),
        expect('replacement candidate'),key('CtrlS'),expect('Save As'),key('CtrlA'),text('NAMEPROBE'),expect('NAMEPROBE'),
        '/screen',key('Tab'),key('CtrlA'),text('sentinel.txt'),'/screen',key('Enter'),'/screen',text('n')])]
    for name,content,controls in probes:
        folder=root/name;(folder/'fixture').mkdir(parents=True)
        (folder/'fixture/note.txt').write_bytes(content);(folder/'fixture/sentinel.txt').write_bytes(b'preserve reviewed existing work\n')
        # Close transient widgets, then exit naturally. Any redundant control
        # refusal stays visible; /quit cancels the recorder without exporting.
        controls+=[key('Escape'),'/absent '+('Replace:' if name=='search' else 'Save As'),
            key('CtrlQ'),expect('Unsaved Changes'),text('n'),'/exit 0','/quit']
        result=await execute([runner,'record','--output',(folder/'unexported.json').relative_to(ROOT),'--fixture','fixture',
            '--temporary-home','--temporary-temp','--width','100','--height','28','--timeout-ms','10000','--run-timeout-ms','120000',
            '--inherit-env','SystemDrive','--','edit','note.txt'],'edit','public-unsaved-'+name+'-diagnosis',
            input='\n'.join(controls)+'\n',env=environment(),expected=130,timeout=150,campaign=Campaign())
        print(name,result['id'],flush=True)


if __name__=='__main__':asyncio.run(main())
