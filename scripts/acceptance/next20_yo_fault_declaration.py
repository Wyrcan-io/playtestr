"""Select three actual yo source faults only after the positive contract freeze."""
import json

from next20_check import DOC, RAW
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'yo';freeze=package/'development-test-freeze.json'
    if json.loads(freeze.read_text())['status']!='frozen-before-fault-selection':
        raise ValueError('Positive frozen tests required before source fault selection')
    source=RAW/'active/yo/src/lib/cli.js'
    before='await env.run(generator.args, generator.opts);'
    if source.read_text(encoding='utf-8').count(before)!=1:raise ValueError('Exact unique actual source anchor required')
    faults=[]
    for fid,category,after,meaning in [
        ('F01','assertion_timeout','await new Promise(() => { setInterval(() => {}, 1000); });',
         'Actual command dispatch never starts the generator; the first positive prompt assertion times out and cleanup must terminate the live target.'),
        ('F02','unexpected_exit',before+'\n      process.exit(7);',
         'Actual completed generator flow incorrectly exits7 instead of0.'),
        ('F03','state_assertion_failure',before+"\n      const saved = path.resolve('output/project.json');\n      fs.writeFileSync(saved, fs.readFileSync(saved, 'utf8').replace('Synthetic notes', 'Synthetic notex'));",
         'Actual CLI corrupts one saved label byte after unchanged visible completion, preserving output length; a terminal-only contract should miss it.')]:
        faults.append(dict(id=fid,path='lib/cli.js',before=before,after=after,category=category,meaning=meaning,
                           **({'terminal_only_probe':True} if fid=='F03' else {})))
    immutable_json(package/'fault-declaration.json',dict(schema_version=1,project='yo',primary_spec='normal-project.json',
        selected_after_freeze_sha256=sha256(freeze),faults=faults,required_calibrations_per_host=9,
        additional_terminal_only_calibrations_per_host=1,
        assembly='Each actual declared source variant is copied byte exactly into the owned runtime app; all dependency and Node bytes remain verified. Retain exact source payloads and launch catalogs. No compiler execution.',
        exposure='Prepared operator reviewed normal workflows and retained first18/2 development predictions. Three concrete mutations selected only after positive20-case/87-input freeze; no blind or independent-human claim.'))
    print('Declared three actual yo source mutations after positive freeze; no mutation executed yet.')


if __name__=='__main__':main()
