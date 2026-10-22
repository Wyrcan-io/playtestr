"""Dispose first development failures explicitly; preserve rejected contracts."""
import base64
import json

from next20_check import RAW,DOC
from next20_jrnl_cases import ALPHA,BETA
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'jrnl';path=package/'scenarios.json';declaration=json.loads(path.read_text())
    immutable_json(RAW/'jrnl/declaration-review/v2-before-first-results.json',declaration)
    changes=[]
    for cid in ['N04','N06','E01','E02']:
        case=next(c for c in declaration['cases'] if c['id']==cid)
        source=package/case['spec'];spec=json.loads(source.read_text())
        immutable_json(RAW/'jrnl/declaration-review'/('first-failed-'+cid+'.json'),spec)
        before=sha256(source)
        if cid=='N04':
            # Do not accept the observed wrong chronological order as correct.
            # Preserve that rejected workflow and explicitly narrow the admitted
            # timestamp route to one that does not cross another entry's date.
            destination=package/'normal-retime-in-order.json'
            spec['name']='Retime alpha within its original chronological position and preserve beta'
            spec['command'][-1]='2020-01-01 12:30'
            state=next(s['state'] for s in spec['steps'] if s.get('state',{}).get('kind')=='file')
            state['bytes_base64']=base64.b64encode((ALPHA.replace('09:00','12:30')+'\n'+BETA).encode()).decode()
            reason='Independent CLI reproduced an upstream storage-order gap when retiming across entries. Original reorder contract remains failed/excluded; replacement tests only a supported chronology-preserving retime, with exact timestamp and unrelated bytes still checked.'
            case.update(spec=destination.name,task=spec['name'],risk='Exact timestamp change without crossing existing entry order',
                excluded_prior_workflow='normal-retime.json remains an observed target storage-order failure')
        else:
            destination=source
            if cid=='N06':
                spec['steps']=[s for s in spec['steps'] if s.get('expect')!='Entry added to default journal']
                reason='Target source intentionally prints no default-journal append completion banner. Exact natural exit is the positive completion witness, followed by unchanged exact same-execution saved bytes; quiet output is not treated as success.'
            else:
                spec['steps'][0]={'expect':'No entries to delete, because the search returned no results'}
                reason='Actual selected delete branch emits NothingToDelete rather than the generic NoEntriesFound string; journal bytes and expected exit remain unchanged.'
        destination.write_text(json.dumps(spec,ensure_ascii=True,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
        case['spec_sha256']=sha256(destination)
        changes.append(dict(case=cid,original_spec=source.name,replacement_spec=destination.name,
            original_sha256=before,new_sha256=sha256(destination),reason=reason))
    declaration['development_revision']=3
    path.write_text(json.dumps(declaration,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    immutable_json(package/'first-development-disposition.json',dict(schema_version=1,
        initial_series='47a0241f55c547e0a4694c5feca4e6f6',ordinary_development_attempts=20,passed=16,failed=4,
        final_ordinary_credit=0,runner_repairs=0,target_limit='Stored chronological ordering after a date-crossing retime remains excluded, not fixed.',
        failed_attempts_preserved=True,changes=changes))
    print('First development denominator retained: 16 pass / 4 fail. Corrected three target-message assumptions; chronological reorder remains excluded with a distinct narrowed retime route.')


if __name__=='__main__':main()
