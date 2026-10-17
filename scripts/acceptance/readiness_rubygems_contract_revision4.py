"""Review a real paged diff and the exact upstream missing-spec diagnostic."""
import json
from readiness_evidence import immutable_json, sha256
from readiness_rubygems_cases import PACKAGE


def main():
    receipt=PACKAGE/'contract-revision-4.json'
    if receipt.exists():raise RuntimeError('preserve revision')
    changes=[]
    for name in ['edge-build-missing.json','edge-resize-collision.json']:
        path=PACKAGE/name;before=sha256(path);spec=json.loads(path.read_text())
        if name=='edge-build-missing.json':spec['steps'][0]['expect']="Couldn't find a gemspec file matching 'missing.gemspec'"
        else:
            spec['env'].update(THOR_DIFF='git --paginate -c core.pager=less diff --no-index --',LESSHISTFILE='-',LESSSECURE='1')
            spec['steps'][6:6]=[{'text':'q'},{'expect':'Retrying...'}]
        path.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8',newline='\n')
        changes.append(dict(spec=name,before=before,after=sha256(path)))
    immutable_json(receipt,dict(changes=changes,qualification='reviewed authored correction; execution pending',
        rationale='retain missing-spec diagnostic and use actual interactive pager instead of an already-finished unpaged diff'))


if __name__=='__main__':main()
