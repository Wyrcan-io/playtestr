"""Record the eighth old-project migration after both actual native cell audits."""
import hashlib
import json
import re
import tarfile

from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


def main():
    campaign=ROOT/'docs/validation/runner-readiness-ten-project-pass';docs=campaign/'old-migration/yazi'
    cells=[load(docs/('verified-'+host+'.json')) for host in ['windows','linux','macos']]
    require({c['host'] for c in cells}=={'windows','linux','macos'} and all(c['scenarios']==14 for c in cells),'three complete original native cells required')
    require(not (RAW/'active/old-yazi').exists(),'local original target remains active')
    retained=RAW/'old-yazi/retained-source';review=load(docs/'source-review.json')
    require(load(retained/'removed.json')['removed'] and sha256(retained/'source.tar.gz')==review['source_archive_sha256'],
            'local original source retention/removal incomplete')
    require(all(c['canonical_source_sha256']==sha256(retained/'source.tar.gz') for c in cells),'native canonical source reference differs')
    inventory=[];observed=0;archives=[]
    for generation in [1,2,3,4,5,6]:
        root=RAW/'old-yazi'/('retained-native-v'+str(generation))
        index=load(root/'index.json',maximum=4*1024**2);checked=load(root/'verified.json');removed=load(root/'expanded-removed.json')
        require(sha256(root/'index.json')==checked['index_sha256'] and sha256(root/'packets.tar.gz')==index['archive_sha256']
                and removed['all_expanded_removed'] and all(not (RAW/'native'/run).exists() for run in index['runs']),
                'native evidence retention or expanded removal incomplete')
        verify(root/'packets.tar.gz',index['files']);inventory.append(index)
        archives.append(dict(generation=generation,index_sha256=sha256(root/'index.json'),archive_sha256=index['archive_sha256']))
        with tarfile.open(root/'packets.tar.gz','r:gz') as bundle:
            for name,row in index['files'].items():
                if not re.fullmatch(r'native/[0-9]+/old-yazi-(?:Linux|macOS)/old-migration/yazi/(?:linux|macos)/(runs/[0-9a-f]{32}/results|corruption/[0-9a-f]{32}/(?:legacy-terminal-false-green|public-state-corruption-rejected|public-state-corruption-restored))\.json',name):continue
                payload=bundle.extractfile(row.get('member',name)).read(4*1024**2+1)
                require(hashlib.sha256(payload).hexdigest()==row['sha256'],'retained actual report changed')
                observed+=json.loads(payload)['summary']['total']
    for cell in cells:
        if cell['host'] in {'linux','macos'}:
            prefix='native/'+cell['run']+'/old-yazi-'+('Linux' if cell['host']=='linux' else 'macOS')+'/'
            for key in ['full_suite_sha256','corruption_sha256','cleanup_sha256']:
                require(any(n.startswith(prefix) and r['sha256']==cell[key] for i in inventory for n,r in i['files'].items()),
                        'audited native migration payload not retained')
    local=RAW/'old-migration/yazi/windows'
    for path in [*local.glob('runs/*/results.json'),*local.glob('corruption/*/legacy-terminal-false-green.json'),
                 *local.glob('corruption/*/public-state-corruption-rejected.json'),*local.glob('corruption/*/public-state-corruption-restored.json')]:
        observed+=load(path)['summary']['total']
    require(observed==51,'actual original/failed-cleanup/repaired attempt accounting differs')
    status_path=campaign/'old-migration-status.json'
    status=load(status_path) if status_path.exists() else dict(schema_version=1,migrated_projects=0,canonical_scenarios=0,
        native_cells=0,qualified_primary_executions=0,qualified_calibration_executions=0,observed_ordinary_executions=0,projects=[])
    require(not any(p['project']=='yazi' for p in status['projects']),'original project already credited')
    receipt=dict(project='yazi',pin=review['pin'],cells=cells,canonical_scenarios=14,qualified_primary_executions=42,
        qualified_calibration_executions=9,observed_ordinary_executions=observed,
        retained_archives=archives,
        scope='Fourteen original workflows on local Windows and hosted Linux/macOS, unchanged native terminal prefixes and snapshots with public same-execution saved outcomes. Actual compiled copy corruption, terminal-only false green, public rejection and exact source/binary restoration on all three hosts. Every qualifying cell independently audited with checked cleanup; first prerequisite/version-check failures and the local cold-build timeout remain separate failed attempts.',
        new_project_credit=0,final_runner_credit=0,final_archive_credit=0)
    immutable_json(docs/'migration-admission.json',receipt)
    status['migrated_projects']+=1;status['canonical_scenarios']+=14;status['native_cells']+=3
    status['qualified_primary_executions']+=42;status['qualified_calibration_executions']+=9;status['observed_ordinary_executions']+=observed
    status['projects'].append(dict(project='yazi',receipt_sha256=sha256(docs/'migration-admission.json')))
    if status_path.exists():status_path.write_text(json.dumps(status,indent=2)+'\n',encoding='utf-8',newline='\n')
    else:immutable_json(status_path,status)
    print('Original yazi migration complete: one old project, fourteen canonical cases, three native cells; new/final credit remains zero.')


if __name__=='__main__':main()
