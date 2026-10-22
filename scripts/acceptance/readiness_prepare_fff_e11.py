"""Declare bounded original-context E11 investigation without target execution."""
from readiness_evidence import ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/fff'
    original=load(docs/'final-series-declaration.json')['batches'][4]
    require=original['input_chunks']==0 and not original['contention'] and original['number']==4
    if not require:raise RuntimeError('original failed E11 context changed')
    frozen=load(docs/'reviewed-contract-freeze.json')
    if sha256(docs/'contracts/E11.json')!=frozen['contracts']['E11.json']:raise RuntimeError('original E11 contract changed')
    declaration=load(docs/'r3-batch-declaration.json')
    declaration.update(incident='Linux E11 resize/create followed by quit timeout in rejected final run39562308064',
        package_directory=original['package_directory'],original_series_declaration_sha256=sha256(docs/'final-series-declaration.json'),
        original_failure_disposition_sha256=sha256(docs/'final-first-series-rejected.json'),
        contract_sha256=sha256(docs/'contracts/E11.json'),
        batches=[dict(number=n,seed=2026102200+n,attempts=50,
            variation='Exact original E11 bytes and original relative package context fff/final-series/4/'+original['package_directory']+'; ordinary execution, no injected load or input/deadline/oracle changes, fresh managed invocation/workspace.') for n in range(1,4)],
        execution_policy='Run only after the six final original-project rechecks, with one native Linux application job. Earlier E03 investigation remains separate; no new project/final-series repetition credit.',
        forecast_minutes=10,native_job_ceiling_minutes=30,
        disposition_policy='Original E11 failure remains retained. Count every planned fresh observation, including failures; continue only with complete public report and positively confirmed cleanup. Zero recurrences permits bounded unreproduced-risk disposition only; no causal repair or zero-flake claim.')
    immutable_json(docs/'r3-e11-batch-declaration.json',declaration)
    workflow=(ROOT/'.github/workflows/runner-readiness-fff-r3.yml').read_text(encoding='utf-8')
    workflow=workflow.replace('Runner readiness bounded fff incident batches','Runner readiness bounded original fff E11 incident')
    workflow=workflow.replace('runner-readiness-fff-r3.yml','runner-readiness-fff-e11-r3.yml')
    workflow=workflow.replace('playtestr-fff-r3-batches','playtestr-fff-e11-r3-batches')
    workflow=workflow.replace('readiness_fff_r3_batches.py','readiness_fff_r3_batches.py --case E11')
    workflow=workflow.replace('name: fff-r3-Linux','name: fff-r3-e11-Linux')
    (ROOT/'.github/workflows/runner-readiness-fff-e11-r3.yml').write_text(workflow,encoding='utf-8',newline='\n')
    print('Declared original E11 exact-context bounded three-by-fifty investigation; no target execution.')


if __name__=='__main__':main()
