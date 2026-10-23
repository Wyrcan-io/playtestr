"""Bounded, reconstructible challenges to complete actual native cell models."""
import argparse
import copy
import hashlib
import json
import uuid

from next20_check import RAW
from next20_verify_jrnl import build_model, validate
from readiness_evidence import immutable_json, sha256


def encoded(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=True,separators=(',',':')).encode()


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project',choices=['commitizen-python','cz-cli'])
    parser.add_argument('--run',required=True)
    args=parser.parse_args()
    destination=RAW/args.project/'audit-controls'/uuid.uuid4().hex
    destination.mkdir(parents=True)
    observations=[]
    for host,generation in [('linux',1),('windows',2)]:
        model,index=build_model(RAW/args.project/('retained-native-v'+str(generation)),args.run,host,args.project)
        counts=validate(model)
        positive=destination/(host+'-actual-model.json');immutable_json(positive,model)
        state=next(i for i,s in enumerate(model['ordinary'][0]['steps']) if s['state'])
        patches=[
            ('missing-case',['ordinary'],model['ordinary'][:-1]),
            ('wrong-phase',['ordinary',0,'phase'],'development'),
            ('duplicate-batch-case',['ordinary',1,'case'],model['ordinary'][0]['case']),
            ('duplicate-invocation',['ordinary',1,'invocation'],model['ordinary'][0]['invocation']),
            ('cross-invocation-state',['ordinary',0,'steps',state,'state','invocation_id'],'another-execution'),
            ('missing-restoration',['faults',0,'restored_exact'],False),
            ('earlier-failure-as-saved-corruption',['faults',2,'outcomes',1,'steps',0,'status'],'failed'),
            ('false-green-mutation',['faults',2,'outcomes',1,'status'],'passed'),
            ('missing-first-failure-disposition',['first_development_disposition_sha256'],'0'*64),
            ('unconfirmed-descendants',['ordinary',0,'confirmed_exited'],False),
            ('mixed-archive',['ordinary',0,'archive_sha256'],'0'*64),
            ('mixed-runner',['ordinary',0,'runner_sha256'],'0'*64),
        ]
        for name,path,value in patches:
            altered=copy.deepcopy(model);parent=altered
            for key in path[:-1]:parent=parent[key]
            parent[path[-1]]=value
            # The sole large replacement is represented as a deterministic
            # truncate operation, so repeated full model payloads stay bounded.
            patch=dict(operation='truncate',path=path,length=len(value)) if name=='missing-case' else dict(operation='replace',path=path,value=value)
            try:validate(altered)
            except ValueError as error:
                observations.append(dict(host=host,control=name,rejected=True,reason=str(error),
                    positive_model=positive.name,positive_model_sha256=sha256(positive),
                    mutation=patch,altered_canonical_json_sha256=hashlib.sha256(encoded(altered)).hexdigest()))
            else:raise ValueError('Altered complete actual cell was accepted: '+host+' '+name)
        if validate(model)!=counts:raise ValueError('Unchanged actual positive lost qualification')
    immutable_json(destination/'results.json',dict(schema_version=1,controls=observations,
        model_serialization='UTF-8 JSON sort_keys=True ensure_ascii=True separators comma/colon',
        scope='Twelve semantic cell-model corruptions per complete actual cell. Global campaign twelve-class closure remains separate.',
        application_scenario_credit=0,new_project_credit=0))
    print('Rejected24 reconstructible actual cell-model corruptions; unchanged positives qualify.')


if __name__=='__main__':main()
