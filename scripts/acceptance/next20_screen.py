"""Retain primary pinned upstream metadata; screening never executes targets."""
import asyncio
import base64
import json
import re
import sys

sys.dont_write_bytecode = True
from adversarial_process import execute
from next20_check import NextCampaign, DOC, RAW, ROOT, owned_environment
from readiness_evidence import immutable_json, sha256

# Research lanes only. Neither placement nor available metadata admits a target.
LEADS = [
 ('commitizen/cz-cli','developer','adapter-driven commit message prompt'),
 ('commitizen-tools/commitizen','developer','Python commit/config prompts'),
 ('yeoman/yo','configuration','local generator selection and overwrite prompts'),
 ('cargo-generate/cargo-generate','configuration','local Rust templates with typed prompts'),
 ('pdm-project/pdm','configuration','interactive package initialization'),
 ('pypa/hatch','configuration','project creation and environment selection'),
 ('jrnl-org/jrnl','notes','interactive journal input and exact text storage'),
 ('smallhadroncollider/taskell','tasks','full-screen Markdown kanban editing'),
 ('sioyek/sioyek','documents','reject if graphical PDF reader rather than terminal'),
 ('vigna/ne','editing','C full-screen text editing and saved bytes'),
 ('troglobit/mg','editing','small Emacs-style C editor'),
 ('joe-editor/joe','editing','C editor with prompts and saved files'),
 ('d99kris/note','notes','C++ terminal notes with export feasibility'),
 ('d99kris/nchat','communication','reject live-service credentials if unavoidable'),
 ('mptre/pick','selection','C fuzzy selection with emitted output'),
 ('jhawthorn/fzy','selection','C interactive matching and emitted output'),
 ('peco/peco','selection','Go interactive filtering with emitted output'),
 ('skim-rs/skim','selection','Rust multi-selection with output'),
 ('mooz/percol','selection','Python interactive line selection'),
 ('denisidoro/navi','selection','Rust command selection; forbid unsafe command execution'),
 ('extrawurst/gitui','developer','canonical duplicate of earlier corpus identity'),
 ('sigoden/aichat','developer','reject mandatory AI dependency'),
 ('git-town/git-town','developer','Git configuration and branch prompts in local repositories'),
 ('nexxeln/critic','developer','verify canonical identity and useful interactive route'),
 ('fmoo/python-editor','editing','reject library/framework rather than independent app'),
 ('kyoheiu/felix','files','Rust full-screen file operations'),
 ('sayanarijit/xplr','files','Rust/Lua explorer with owned file operations'),
 ('antonmedv/walk','files','Go explorer; limit repeated file-browser breadth'),
 ('Canop/bacon','monitoring','Rust controlled local build monitor'),
 ('htop-dev/htop','monitoring','C monitoring with bounded synthetic marker and config'),
 ('aristocratos/btop','monitoring','C++ native monitor/config; dynamic values scoped'),
 ('andmarti1424/sc-im','data','C terminal spreadsheet and reviewed text export'),
 ('noperator/sol','tasks','verify task workflow and terminal UI'),
 ('sachaos/todoist','tasks','reject live-service credential dependency'),
 ('mrusme/planor','tasks','Go plain-text task management full-screen UI'),
 ('chriswalz/bit','developer','Git interactive commands with synthetic repositories'),
 ('git-quick-stats/git-quick-stats','developer','Shell interactive local Git reports'),
 ('git-cola/git-cola','developer','reject graphical application'),
 ('ptmcg/wak','data','verify interactive task; reject noninteractive utility'),
 ('saulpw/visidata','data','canonical historical duplicate'),
 ('natecraddock/zf','selection','Zig fuzzy selection; runtime and input/output review'),
 ('ynqa/sig','selection','Go interactive grep with selected output'),
 ('joshmedeski/sesh','workflow','Go terminal session selection; tmux dependency'),
 ('marlam/msmtp','communication','C account/config prompt feasibility; prohibit real mail'),
 ('pvolok/mprocs','workflow','Rust full-screen owned multi-process orchestration'),
 ('koalaman/shellcheck','developer','reject noninteractive analyzer'),
]


async def main():
    campaign = NextCampaign()
    env = owned_environment()
    semaphore = asyncio.Semaphore(2)
    async def api(endpoint, label):
        async with semaphore:
            try:
                result = await execute(['gh','api',endpoint], 'screening', label,
                    cwd=ROOT,env=env,timeout=45,expected=0,campaign=campaign)
            except RuntimeError as error:
                evidence_id = getattr(error,'evidence_id',None)
                if evidence_id is None:
                    raise
                event=json.loads((RAW/'events'/(evidence_id+'-finished.json')).read_text())
                if event['category']!='exit_mismatch':
                    raise
                return None,evidence_id
        return json.loads(result['output']), result['id']
    async def one(repo, category, task):
        key = repo.replace('/','--').lower()
        metadata, meta_id = await api('repos/'+repo, key+'-metadata')
        row = dict(requested_repository=repo,category=category,research_task=task,
                   metadata_attempt=meta_id,acquired=False,admitted=False)
        if metadata is None:
            row['status']='metadata-unavailable'
            return row
        canonical=metadata['full_name']
        row.update(repository=canonical,url=metadata['html_url'],
                   language=metadata['language'],archived=metadata['archived'],
                   fork=metadata['fork'],license=(metadata.get('license') or {}).get('spdx_id'),
                   default_branch=metadata['default_branch'])
        commit,commit_id=await api('repos/'+canonical+'/commits/'+metadata['default_branch'],key+'-pin')
        row['pin_attempt']=commit_id
        if commit is None:
            row['status']='pin-unavailable'
            return row
        row['pin']=commit['sha']
        readme,readme_id=await api('repos/'+canonical+'/readme?ref='+commit['sha'],key+'-readme')
        row['readme_attempt']=readme_id
        if readme is None:
            row['status']='readme-unavailable'
            return row
        content=base64.b64decode(readme['content'],validate=False)
        if len(content)>512*1024:
            raise ValueError('screening readme bound')
        target=RAW/'screening'/key/commit['sha']/'readme.json'
        immutable_json(target,dict(path=readme['path'],source=readme['html_url'],
                                  bytes_base64=base64.b64encode(content).decode()))
        row.update(readme_url=readme['html_url'],readme_local_only=target.relative_to(ROOT).as_posix(),
                   readme_sha256=sha256(target),status='metadata-screened-requires-review')
        text=content.decode('utf-8',errors='replace')
        row['platform_interaction_excerpts']=[line[:500] for line in text.splitlines()
            if re.search(r'Windows|macOS|Linux|[Ii]nteractive|[Ll]icen[cs]e|[Ss]ave|[Ee]xport|[Pp]rompt|[Bb]uild|[Ii]nstall',line)][:45]
        return row
    # Small batches keep output/checkpoints bounded if a provider call fails.
    rows=[]
    for start in range(0,len(LEADS),4):
        for row in await asyncio.gather(*(one(*lead) for lead in LEADS[start:start+4])):
            immutable_json(RAW/'screening/rows'/(row['requested_repository'].replace('/','--').lower()+'.json'),row)
            rows.append(row)
            print(row['requested_repository'],row['status'],row.get('pin','')[:12],flush=True)
    immutable_json(RAW/'screening/registry-v1.json',dict(schema_version=1,rows=rows,
        source='primary GitHub API metadata and pinned upstream README; no target execution',
        client_date='2026-10-22',new_project_admissions=0))
    print('Reviewed metadata rows:',len(rows),'No source acquired or target executed.')


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    asyncio.run(main())
