"""Challenge complete actual jrnl cell models; no campaign breadth credit."""
import copy
import uuid

from next20_check import RAW
from next20_verify_jrnl import build_model, validate
from readiness_evidence import immutable_json, sha256


def main():
    destination=RAW/'jrnl/audit-controls'/uuid.uuid4().hex
    destination.mkdir(parents=True)
    observations=[]
    for host,generation in [('linux',1),('windows',2)]:
        retained=RAW/'jrnl'/('retained-native-v'+str(generation))
        model,index=build_model(retained,'39797356210',host)
        validate(model)
        positive=destination/(host+'-actual-model.json');immutable_json(positive,model)
        changes=[
            ('missing-case',lambda m:m['ordinary'].pop()),
            ('wrong-phase',lambda m:m['ordinary'][0].update(phase='development')),
            ('duplicate-batch-case',lambda m:m['ordinary'][1].update(case=m['ordinary'][0]['case'])),
            ('duplicate-invocation',lambda m:m['ordinary'][1].update(invocation=m['ordinary'][0]['invocation'],workspace=m['ordinary'][0]['workspace'])),
            ('cross-invocation-state',lambda m:m['ordinary'][0]['steps'][6]['state'].update(invocation_id='another-execution')),
            ('missing-restoration',lambda m:m['faults'][0].update(restored_exact=False)),
            ('earlier-failure-as-saved-corruption',lambda m:m['faults'][2]['outcomes'][1]['steps'][0].update(status='failed')),
            ('false-green-mutation',lambda m:m['faults'][2]['outcomes'][1].update(status='passed')),
            ('missing-first-failure-disposition',lambda m:m.update(first_development_disposition_sha256='0'*64)),
            ('unconfirmed-descendants',lambda m:m['ordinary'][0].update(confirmed_exited=False)),
            ('mixed-archive',lambda m:m['ordinary'][0].update(archive_sha256='0'*64)),
            ('mixed-runner',lambda m:m['ordinary'][0].update(runner_sha256='0'*64)),
        ]
        for name,change in changes:
            altered=copy.deepcopy(model);change(altered)
            path=destination/(host+'-'+name+'.json');immutable_json(path,altered)
            try:validate(altered)
            except ValueError as error:
                observations.append(dict(host=host,control=name,rejected=True,reason=str(error),
                    altered_model_sha256=sha256(path),positive_model_sha256=sha256(positive)))
            else:raise ValueError('Actual complete cell corruption was accepted: '+host+' '+name)
        if validate(model)!=dict(ordinary=240,calibrations=9,cases=20,real_faults=3,native_cells=1):
            raise ValueError('Unchanged actual positive model no longer qualifies')
    immutable_json(destination/'results.json',dict(schema_version=1,controls=observations,
        scope='Twelve semantic cell-model negatives on each complete actual native cell; global campaign twelve-class closure remains separate.',
        application_scenario_credit=0,new_project_credit=0))
    print('Rejected 24 altered complete actual native cell models; unchanged positives still qualify. Global campaign audit remains pending.')


if __name__=='__main__':main()
