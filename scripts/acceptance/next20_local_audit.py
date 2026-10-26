"""Shared independent checks for preserved public local journey evidence."""
import json

from next20_check import RAW, ROOT, DOC, NAME
from next20_verify_jrnl import require
from readiness_evidence import sha256


class LocalAudit:
    def __init__(self,project):
        self.project=project;self.raw=RAW/project;self.subjects={};self.seen=set()
        freeze=self.load(ROOT/'docs/validation/runner-readiness-ten-project-pass/migration-candidate-freeze.json')
        self.runner=next(c['binary_sha256'] for c in freeze['cells'] if c['host']=='windows')

    def subject(self,path):
        path.resolve(strict=True).relative_to(ROOT)
        self.subjects[path.relative_to(ROOT).as_posix()]=sha256(path)

    def load(self,path):
        self.subject(path)
        return json.loads(path.read_text(encoding='utf-8-sig'))

    def reference(self,row):
        path=RAW/row['manifest'];path.resolve(strict=True).relative_to(RAW)
        require(sha256(path)==row['sha256'],'changed local launch identity')
        return self.load(path)

    def command(self,eid,*,original_failure=False,mismatch=None,runner=True,source=None):
        events={k:self.load(RAW/'events'/(eid+'-'+k+'.json')) for k in ['started','identified','launched','finished']}
        require(all(e['campaign']==NAME and e['project']==self.project and e['phase']=='development' and e['id']==eid for e in events.values()),'wrong local command phase/project')
        started=events['started'];finish=events['finished']
        require(finish['harness_cleanup']=='harness_process_reaped' and not finish['cleanup_errors'],'unconfirmed local harness cleanup')
        if original_failure:mismatch=(0,1)
        require(finish['category']==('exit_mismatch' if mismatch else 'passed'),'unaccounted local command outcome')
        require(finish['exit_code']==(mismatch[1] if mismatch else started['expected_exit']),'local exit code differs from declared observation')
        if mismatch:require(started['expected_exit']==mismatch[0],'original failure relabeled expected')
        console=self.raw/eid/'console.log';require(sha256(console)==finish['console_sha256'],'changed local command console');self.subject(console)
        identity=self.reference(events['identified']['identity'])
        target=self.reference(identity['target_catalog']) if 'target_catalog' in identity else None
        base=self.reference(identity['base']) if 'base' in identity else identity
        if runner:require(base['files'].get('artifacts/'+NAME+'/candidate/windows/playtestr.exe')==self.runner,'public command used another runner')
        if source is not None:
            require(target is not None,'missing local actual target source identity')
            actual={n.split('/src/',1)[1]:v for n,v in target['files'].items() if '/active/'+self.project+'/src/' in n}
            require(actual==source,'local actual target source differs')
        return dict(label=started['label'],base=base,target=target,events=events)

    def report(self,path,status='passed',category=None,contract=None):
        data=self.load(path)
        require(data['report_version']==3 and data['runner_version']=='v0.4.0-rc.5' and data['os']=='windows' and data['arch']=='amd64','wrong local report identity')
        require(len(data['results'])==1,'not individual local report')
        row=data['results'][0]
        require(row['status']==status and row['workspace']['cleaned'] and row['cleanup']['confirmed_exited'],'wrong or unclean local report')
        require(row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in self.seen,'duplicate/cross-invocation local report')
        self.seen.add(row['invocation_id'])
        if status=='passed':require(all(s['status']=='passed' for s in row['steps']),'missing positive local evidence')
        else:require(row['failure']['category']==category,'wrong local rejection category')
        for step in row['steps']:
            state=step.get('state')
            if state:require(state['invocation_id']==row['invocation_id'] and state['workspace_id']==row['workspace']['id'],'cross-invocation local state evidence')
        if contract is not None:
            require([s['action'] for s in row['steps']]==[next(iter(s)) for s in contract['steps']],'local action sequence differs')
            for observed,expected in zip(row['steps'],contract['steps']):
                if 'state' not in expected or observed['status']=='not_run':continue
                state=observed.get('state');require(state is not None,'missing actual local state predicate evidence')
                require((state['path'],state['kind'])==(expected['state']['path'],expected['state']['kind']),'local state predicate path/kind differs')
        for name in row.get('evidence',{}).values():
            if isinstance(name,str):
                evidence=ROOT/name;resolved=evidence.resolve(strict=True)
                require(resolved.is_relative_to(self.raw) or resolved.parent==DOC/self.project and resolved.name.endswith('.actual.txt'),'local screen evidence outside declared project roots')
                self.subject(evidence)
        return row
