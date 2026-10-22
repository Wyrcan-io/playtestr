"""Declare provisional metadata allocation and collect pinned build/platform files."""
import asyncio
import base64
import json
import re
import sys

sys.dont_write_bytecode=True
from adversarial_process import execute
from next20_check import NextCampaign, DOC, RAW, ROOT, owned_environment
from readiness_evidence import immutable_json,sha256

# Full-screen and state are feasibility hypotheses until a useful route passes.
# The four late projects receive only license/build/platform metadata inspection.
SELECTED=[
 ('jrnl-org/jrnl','jrnl','windows','notes','Python','interactive text input',False,True),
 ('commitizen-tools/commitizen','commitizen-python','windows','developer','Python','Questionary/prompt-toolkit',False,True),
 ('commitizen/cz-cli','cz-cli','windows','developer','JavaScript','Inquirer adapter prompts',False,True),
 ('yeoman/yo','yo','windows','configuration','JavaScript','Yeoman/Inquirer',False,True),
 ('cargo-generate/cargo-generate','cargo-generate','windows','configuration','Rust','dialoguer',False,True),
 ('pdm-project/pdm','pdm','windows','configuration','Python','Rich/click prompts',False,True),
 ('peco/peco','peco','windows','selection','Go','termbox',False,True),
 ('skim-rs/skim','skim','windows','selection','Rust','skim terminal renderer',False,True),
 ('git-town/git-town','git-town','windows','developer','Go','Bubble Tea',False,True),
 ('pvolok/dekit','dekit','windows','workflow','Rust','ratatui process UI',True,True),
 ('smallhadroncollider/taskell','taskell','macos','tasks','Haskell','Brick/vty',True,True),
 ('troglobit/mg','mg','macos','editing','C','termcap Emacs editor',True,True),
 ('joe-editor/joe','joe','macos','editing','C','custom termcap editor',True,True),
 ('mptre/pick','pick','macos','selection','C','curses',False,True),
 ('jhawthorn/fzy','fzy','macos','selection','C','custom terminal matcher',False,True),
 ('mooz/percol','percol','macos','selection','Python','Python curses',False,True),
 ('vigna/ne','ne','macos','editing','C','custom termcap editor',True,True),
 ('andmarti1424/sc-im','sc-im','macos','data','C','ncurses spreadsheet',True,True),
 ('aristocratos/btop','btop','macos','monitoring','C++','custom ANSI monitor',True,True),
 ('htop-dev/htop','htop','macos','monitoring','C','ncurses monitor',True,True),
]
RESERVES=['pypa/hatch','denisidoro/navi','kyoheiu/felix','sayanarijit/xplr',
          'antonmedv/walk','Canop/bacon','natecraddock/zf','git-quick-stats/git-quick-stats']


async def main():
    campaign=NextCampaign();env=owned_environment();semaphore=asyncio.Semaphore(2)
    registry=json.loads((RAW/'screening/registry-v1.json').read_text())
    byrepo={r.get('repository'):r for r in registry['rows']}
    async def api(endpoint,label):
        async with semaphore:
            try:
                result=await execute(['gh','api',endpoint],'screening',label,cwd=ROOT,
                    env=env,timeout=45,expected=0,campaign=campaign)
            except RuntimeError as error:
                eid=getattr(error,'evidence_id',None)
                if eid is None:raise
                row=json.loads((RAW/'events'/(eid+'-finished.json')).read_text())
                if row['category']!='exit_mismatch':raise
                return None,eid
        return json.loads(result['output']),result['id']
    async def review(repo):
        row=byrepo[repo];pin=row['pin'];key=repo.lower().replace('/','--')
        root=RAW/'screening/reviews'/key/pin
        tree,eid=await api('repos/'+repo+'/git/trees/'+pin+'?recursive=1',key+'-build-platform-tree')
        if tree is None or tree.get('truncated'):raise ValueError('missing/partial primary metadata tree: '+repo)
        immutable_json(root/'tree.json',tree)
        paths=[r['path'] for r in tree['tree'] if r['type']=='blob']
        chosen=[]
        for p in paths:
            if p.lower() in {'license','license.md','license.txt','license-mit','copying','pyproject.toml','package.json','cargo.toml','go.mod','makefile','install.md','readme-mprocs.md'}:
                chosen.append(p)
        workflows=[p for p in paths if p.startswith('.github/workflows/') and p.endswith(('.yml','.yaml'))]
        chosen+=sorted(workflows,key=lambda p:(not any(w in p.lower() for w in ['test','ci','build','windows','macos']),p))[:2]
        files=[]
        for name in chosen[:9]:
            data,attempt=await api('repos/'+repo+'/contents/'+name+'?ref='+pin,key+'-metadata-'+name.replace('/','-'))
            if data is None:continue
            content=base64.b64decode(data['content'])
            if len(content)>256*1024:raise ValueError('pinned review file bound')
            local=root/'files'/(name.replace('/','--')+'.json')
            immutable_json(local,dict(path=name,source=data['html_url'],bytes_base64=base64.b64encode(content).decode()))
            files.append(dict(path=name,url=data['html_url'],receipt=local.relative_to(ROOT).as_posix(),
                              sha256=sha256(local),attempt=attempt))
        result=dict(repository=repo,pin=pin,tree_attempt=eid,tree_sha256=sha256(root/'tree.json'),files=files,
                    approved_for_execution=False,scope='Build/platform/license metadata; no target execution or workflow-test development')
        immutable_json(root/'review-inputs.json',result)
        print('Pinned build/platform review inputs:',repo,len(files),flush=True)
        return result
    reviews=[]
    for start in range(0,28,2):
        repos=[r[0] for r in SELECTED]+RESERVES
        reviews.extend(await asyncio.gather(*(review(repo) for repo in repos[start:start+2])))
    immutable_json(RAW/'screening/selection-inputs-v1.json',dict(schema_version=1,reviews=reviews,
        selected=[dict(repository=r[0],id=r[1],hosts=['linux',r[2]],category=r[3],language_family=r[4],
            terminal_family=r[5],fullscreen_proposed=r[6],stateful_proposed=r[7],late_transfer=i>=16)
            for i,r in enumerate(SELECTED)],reserves=RESERVES,
        status='provisional allocation; manual pinned-source and feasibility review required before target execution'))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');asyncio.run(main())
