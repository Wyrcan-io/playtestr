"""Publish zero-credit screening decisions and deduplicated provisional allocation."""
import collections
import json
import sys

sys.dont_write_bytecode=True
from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json,sha256


def canonical(value):
    value=value.removeprefix('https://github.com/').removesuffix('/').removesuffix('.git').lower()
    return {'extrawurst/gitui':'gitui-org/gitui','zyedidia/micro':'micro-editor/micro',
            'pvolok/mprocs':'pvolok/dekit'}.get(value,value)


def main():
    historical={}
    inputs=['corpus/manifest.json','docs/validation/ten-project-user-pass/candidates.json',
        'docs/validation/ten-new-project-adversarial-pass/candidates.json',
        'docs/validation/runner-readiness-ten-project-pass/candidates.json']
    for name in inputs:
        data=json.loads((ROOT/name).read_text(encoding='utf-8'))
        rows=data if isinstance(data,list) else data.get('projects',data.get('rows',[]))
        for row in rows:
            repo=row.get('repository',row.get('repo'))
            if not repo:continue
            completed=(name=='corpus/manifest.json' or name.endswith('ten-project-user-pass/candidates.json')
                or row.get('disposition')=='selected' or row.get('status')=='development-admitted')
            if completed:historical.setdefault(canonical(repo),[]).append(name)
    registry=json.loads((RAW/'screening/registry-v1.json').read_text())
    allocation=json.loads((RAW/'screening/selection-inputs-v1.json').read_text())
    selected={canonical(p['repository']):p for p in allocation['selected']}
    reserves={canonical(p) for p in allocation['reserves']}
    if set(selected)&set(historical):raise ValueError('selected historical duplicate')
    if len(selected)!=20 or len(reserves)!=8 or set(selected)&reserves:raise ValueError('allocation duplication')
    decisions=[]
    reject_reasons={
        'sigoden/aichat':'AI/network dependency conflicts with this deterministic offline scope',
        'd99kris/nchat':'Live messaging accounts/credentials; no reviewed offline twenty-scenario route',
        'mrusme/planor':'Cloud-service API/credentials required; README is not a local task manager',
        'noperator/sol':'Shell one-liner expansion; no sufficiently broad independently useful interactive journey established',
        'sachaos/todoist':'Live Todoist account/API credential dependency',
        'fmoo/python-editor':'Library providing external-editor integration, not independent interactive application',
        'git-cola/git-cola':'Qt graphical UI outside terminal contract',
        'marlam/msmtp':'Mail transport; no safe meaningful interactive terminal journey established',
        'koalaman/shellcheck':'Static noninteractive analyzer; interactive shell use is not a terminal UI',
        'ynqa/sig':'Additional screened reserve lead; initial reserve quota already allocated',
        'joshmedeski/sesh':'Requires owned tmux service/session lifecycle; defer beyond initial bounded allocation',
        'chriswalz/bit':'Additional screened reserve lead; initial reserve quota already allocated',
    }
    for row in registry['rows']:
        repo=canonical(row.get('repository',row['requested_repository']))
        decision=dict(row)
        if row['status']!='metadata-screened-requires-review':
            decision.update(disposition='metadata-unavailable-not-screened',reason='Primary lookup failed; no feasibility or screened credit')
        elif repo in historical:
            decision.update(disposition='excluded-completed-canonical-identity',reason='Earlier completed corpus/journey; zero new breadth')
        elif repo in selected:
            decision.update(disposition='selected-for-bounded-attempt',reason='Provisional native/state/UI allocation; execution approval remains per target',**selected[repo])
        elif repo in reserves:
            decision.update(disposition='metadata-reserve',reason='Pinned metadata/build/native sources retained; detailed workflow feasibility remains to prove')
        else:
            decision.update(disposition='screened-not-selected',reason=reject_reasons.get(repo,'No reviewed feasible terminal workflow within initial allocation'))
        decisions.append(decision)
    counts=collections.Counter(d['disposition'] for d in decisions)
    languages=collections.Counter(p['language_family'] for p in selected.values())
    categories=collections.Counter(p['category'] for p in selected.values())
    full=sum(p['fullscreen_proposed'] for p in selected.values())
    prompt=sum(p['id'] in {'jrnl','commitizen-python','cz-cli','yo','cargo-generate','pdm'} for p in selected.values())
    if len(languages)<5 or max(languages.values())>10 or len(categories)<6 or max(categories.values())>6 or full<8 or prompt<6:
        raise ValueError('provisional diversity allocation inadequate')
    manifest=dict(schema_version=1,source_inputs={n:sha256(ROOT/n) for n in inputs},
        completed_canonical_identities=historical,aliases={'extrawurst/gitui':'gitui-org/gitui','pvolok/mprocs':'pvolok/dekit'},
        scope='Completed corpora/journeys excluded; metadata-only earlier reserves remain eligible with disclosed exposure')
    immutable_json(DOC/'historical-identity-inventory.json',manifest)
    immutable_json(DOC/'screening-decisions.json',dict(schema_version=1,client_date='2026-10-22',
        screened=sum(d['status']=='metadata-screened-requires-review' for d in decisions),lookup_attempts=len(decisions),
        counts=dict(counts),rows=decisions,new_admissions=0))
    immutable_json(DOC/'selection-declaration.json',dict(schema_version=1,status='provisional-before-target-acquisition',
        selected=list(selected.values()),reserves=allocation['reserves'],languages=dict(languages),
        categories=dict(categories),fullscreen_proposed=full,prompt_proposed=prompt,stateful_proposed=20,
        planned_cells=dict(linux=20,windows=10,macos=10),new_risks=[
            'interactive Git message adapters and repository-local configuration',
            'nested owned process orchestration with stop/restart and saved child outcomes',
            'spreadsheet formula editing and independently reviewed export bytes'],
        late_transfer=[p['id'] for p in selected.values() if p['late_transfer']],
        metadata_inputs_sha256=sha256(RAW/'screening/selection-inputs-v1.json'),
        all_target_execution_approvals=False,new_project_admissions=0))
    print(json.dumps(dict(historical_canonical_identities=len(historical),screening=counts,
        language_families=languages,categories=categories,fullscreen=full,prompt=prompt,
        proposed_native_cells=40,admissions=0),indent=2))


if __name__=='__main__':main()
