"""Fetch explicitly selected missing primary metadata without repeating packets."""
import asyncio
import base64
import json
import sys

sys.dont_write_bytecode=True
from adversarial_process import execute
from next20_check import NextCampaign,RAW,ROOT,owned_environment
from readiness_evidence import immutable_json

REQUESTS=[
 ('jrnl-org/jrnl','jrnl/main.py'),
 ('jrnl-org/jrnl','jrnl/install.py'),
 ('jrnl-org/jrnl','jrnl/Journal.py'),
 ('jrnl-org/jrnl','jrnl/config.py'),
 ('jrnl-org/jrnl','docs/usage.md'),
 ('jrnl-org/jrnl','docs/reference-command-line.md'),
 ('mooz/percol','setup.py'),
 ('troglobit/mg','UNLICENSE'),
 ('smallhadroncollider/taskell','.travis.yml'),
 ('chriswalz/bit','go.mod'),
 ('chriswalz/bit','LICENSE'),
 ('ynqa/sig','Cargo.toml'),
 ('ynqa/sig','LICENSE'),
]


async def main():
    rows=json.loads((RAW/'screening/registry-v1.json').read_text())['rows']
    byrepo={r.get('repository'):r for r in rows}
    campaign=NextCampaign();env=owned_environment()
    for repo,name in REQUESTS:
        row=byrepo[repo];pin=row['pin']
        target=RAW/'screening/supplement'/repo.lower().replace('/','--')/pin/(name.replace('/','--')+'.json')
        if target.exists():raise ValueError('supplement already retained; inspect instead of refetching')
        try:
            result=await execute(['gh','api','repos/'+repo+'/contents/'+name+'?ref='+pin],
                'screening','supplement-'+repo.replace('/','-')+'-'+name.replace('/','-'),
                cwd=ROOT,env=env,timeout=45,campaign=campaign)
        except RuntimeError as error:
            eid=getattr(error,'evidence_id',None)
            if not eid:raise
            event=json.loads((RAW/'events'/(eid+'-finished.json')).read_text())
            if event['category']!='exit_mismatch':raise
            immutable_json(target,dict(repository=repo,pin=pin,path=name,status='unavailable',attempt=eid))
            continue
        data=json.loads(result['output']);content=base64.b64decode(data['content'])
        if len(content)>256*1024:raise ValueError('supplement file bound')
        immutable_json(target,dict(repository=repo,pin=pin,path=name,url=data['html_url'],
            attempt=result['id'],bytes_base64=base64.b64encode(content).decode()))
        print(repo,name,len(content),flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');asyncio.run(main())
