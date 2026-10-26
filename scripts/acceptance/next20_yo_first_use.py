"""Author a real local-generator yo workflow using the public recorder only."""
import asyncio
import argparse
import base64
import hashlib
import json
import os

from adversarial_process import execute
from next20_check import RAW,ROOT,DOC,NextCampaign
from next20_python_setup import environment
from readiness_evidence import immutable_json,sha256


GENERATOR = '''import {createRequire} from 'node:module';
import {dirname, resolve} from 'node:path';
import {pathToFileURL} from 'node:url';

// Resolve the reviewed official framework beside the actual unmodified yo
// entry. This also follows a cold runtime copy without personal absolute paths.
const requireFramework = createRequire(resolve(dirname(process.argv[1]), '../../generator-toolchain/package.json'));
const {default: Generator} = await import(pathToFileURL(requireFramework.resolve('yeoman-generator')).href);

export default class extends Generator {
  async prompting() {
    this.answers = await this.prompt([
      {type: 'input', name: 'label', message: 'Project label',
       validate: value => value.trim() ? true : 'Project label is required', filter: value => value.trim()},
      {type: 'list', name: 'language', message: 'Project language', choices: ['TypeScript', 'JavaScript'], default: 'TypeScript'},
      {type: 'confirm', name: 'readme', message: 'Include README', default: true}
    ]);
  }
  writing() {
    const value = {label: this.answers.label, language: this.answers.language};
    this.fs.write(this.destinationPath('output/project.json'), JSON.stringify(value, null, 2) + '\\n');
    if (this.answers.readme) {
      this.fs.write(this.destinationPath('output/README.md'), '# ' + value.label + '\\n\\nLanguage: ' + value.language + '\\n');
    }
  }
  end() { this.log('Scaffold complete'); }
}
'''


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--resume-export',action='store_true');args=parser.parse_args()
    project='yo';package=DOC/project;target=RAW/'active'/project;raw=RAW/project;raw.mkdir(exist_ok=True)
    spec=package/'normal-project.json'
    if (package/'first-use.json').exists() or spec.exists()!=args.resume_export:raise ValueError('Preserve existing first authoring outcome; resume only the explicitly existing export')
    approved=json.loads((target/'dependency-review.json').read_text(encoding='utf-8'))
    if not approved['approved'] or not approved['all_installed_payloads_match_canonical_sri']:raise ValueError('Installed target source not reviewed')
    runtime=json.loads((target/'runtime.json').read_text(encoding='utf-8'));node=runtime['node']
    catalog=json.loads((target/'launch-runtime-catalog.json').read_text(encoding='utf-8'))
    for name,digest in catalog['files'].items():
        if sha256(target/runtime['app_relative_path']/name)!=digest:raise ValueError('Reviewed actual runtime file changed: '+name)
    fixture=package/'fixture';generator=fixture/'generator'
    sentinel=b'Unrelated synthetic input must remain unchanged.\n'
    if not args.resume_export:
        generator.mkdir(parents=True)
        immutable_json(generator/'package.json',dict(name='generator-playtestr-demo',version='1.0.0',private=True,type='module',main='index.js',keywords=['yeoman-generator']))
        (generator/'index.js').write_text(GENERATOR,encoding='utf-8',newline='\n')
        (fixture/'sentinel.txt').write_bytes(sentinel)
    elif (generator/'index.js').read_bytes()!=GENERATOR.encode() or (fixture/'sentinel.txt').read_bytes()!=sentinel:
        raise ValueError('Existing original plugin/fixture bytes changed')
    expected_project=(json.dumps(dict(label='Synthetic notes',language='TypeScript'),ensure_ascii=False,indent=2)+'\n').encode()
    expected_readme=b'# Synthetic notes\n\nLanguage: TypeScript\n'
    controls=['/expect Project label','/text "Synthetic notes"','/key Enter',
              '/expect Project language','/key Enter','/expect Include README','/key Enter',
              '/expect Scaffold complete','/exit 0','/file output/project.json','/file output/README.md',
              '/file sentinel.txt','/entries output','/review','/replay','/save']
    launch="const p=require('node:path'),{pathToFileURL}=require('node:url');const e=p.resolve(p.dirname(process.execPath),'../runtime/app/lib/cli.js');process.argv.splice(1,0,e);import(pathToFileURL(e).href);"
    command=[os.path.relpath(node,package).replace('\\','/'),'-e',launch,'--','./generator','--local-only','--skip-install','--skip-cache','--no-color']
    plan=dict(schema_version=1,controls=controls,target_command=command,
        expected_shell_invocations=3,recorder_controls=len(controls),source_review_sha256=sha256(package/'source-review.json'),
        independently_expected={n:dict(bytes_base64=base64.b64encode(data).decode(),sha256=hashlib.sha256(data).hexdigest())
            for n,data in [('output/project.json',expected_project),('output/README.md',expected_readme),('sentinel.txt',sentinel)]},
        plugin_fixture_sha256=sha256(generator/'index.js'),handwritten_playtestr_json=False,
        scope='Actual documented local generator through unmodified yo CLI, real official Generator APIs, terminal adapter and file pipeline. Plugin is synthetic test input, not a replacement CLI or extra project admission.')
    if args.resume_export:
        if json.loads((raw/'first-use-planned.json').read_text(encoding='utf-8'))!=plan:raise ValueError('Original first-use plan changed')
    else:immutable_json(raw/'first-use-planned.json',plan)
    runner=RAW/'candidate/windows/playtestr.exe';env=environment(target);campaign=NextCampaign();attempts=[]
    async def run(argv,label,input=None):
        result=await execute(argv,project,label,cwd=ROOT,env=env,input=input,timeout=180,campaign=campaign)
        attempts.append(result['id']);return result
    if args.resume_export:
        selected={}
        for directory in raw.iterdir():
            if not directory.is_dir() or len(directory.name)!=32 or any(c not in '0123456789abcdef' for c in directory.name):continue
            started=json.loads((RAW/'events'/(directory.name+'-started.json')).read_text(encoding='utf-8'))
            if started['label'] not in {'first-use-runner-version','first-public-record-local-generator'}:continue
            if started['label'] in selected:raise ValueError('Original public invocation selection ambiguous')
            finish=json.loads((RAW/'events'/(directory.name+'-finished.json')).read_text(encoding='utf-8'))
            if finish['category']!='passed' or finish['harness_cleanup']!='harness_process_reaped' or finish['cleanup_errors']:
                raise ValueError('Original public invocation failed or cleanup unconfirmed')
            if sha256(directory/'console.log')!=finish['console_sha256']:raise ValueError('Original public console changed')
            selected[started['label']]=directory.name
        attempts.extend(selected[name] for name in ['first-use-runner-version','first-public-record-local-generator'])
        immutable_json(package/'first-use-wrapper-disposition.json',dict(schema_version=1,
            original_outer_attempt='793f91307ade4cd5b0a09478d0b6ee71',original_successful_public_attempts=list(attempts),
            exported_spec_sha256=sha256(spec),original_plan_sha256=sha256(raw/'first-use-planned.json'),
            reason='The recorder succeeded with independently correct file bytes and exact entry names. The wrapper incorrectly required entry ordering; the public entries predicate sorts both sets. Only the wrapper comparison is repaired; original spec/fixture/controls remain byte identical.',
            next_action='Finish only the remaining third ordinary public replay; do not rerun or overwrite version/record/export.',new_project_admissions=0))
    else:await run([runner,'--version'],'first-use-runner-version')
    declared_env=dict(NO_UPDATE_NOTIFIER='1',NO_COLOR='1',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull,GIT_TERMINAL_PROMPT='0',TZ='UTC')
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home','--temporary-temp',
          '--width','120','--height','32','--timeout-ms','10000','--run-timeout-ms','120000']
    for name,value in declared_env.items():argv+=['--env',name+'='+value]
    for name in ['SYSTEMROOT','WINDIR']:argv+=['--inherit-env',name]
    if not args.resume_export:await run([*argv,'--',*command],'first-public-record-local-generator',input='\n'.join(controls+['']))
    exported=json.loads(spec.read_text(encoding='utf-8'))
    actual={s['state']['path']:s['state'] for s in exported['steps'] if 'state' in s}
    for name,data in [('output/project.json',expected_project),('output/README.md',expected_readme),('sentinel.txt',sentinel)]:
        if base64.b64decode(actual[name]['bytes_base64'])!=data:raise ValueError('Recorder approved bytes differ from independent intended output: '+name)
    if sorted(actual['output']['entries'])!=['README.md','project.json']:raise ValueError('Recorder approved output entry set differs')
    report=raw/'first-ordinary-report.json'
    await run([runner,'test','--report',report.relative_to(ROOT),'--artifacts-dir',(raw/'first-ordinary-evidence').relative_to(ROOT),spec.relative_to(ROOT)],'first-ordinary-replay')
    row=json.loads(report.read_text(encoding='utf-8'))['results'][0]
    if row['status']!='passed' or any(s['status']!='passed' for s in row['steps']) or not row['workspace']['cleaned'] or not row['cleanup']['confirmed_exited']:
        raise ValueError('Missing positive ordinary/cleanup evidence')
    immutable_json(package/'first-use.json',dict(schema_version=1,attempts=attempts,shell_invocations=3,recorder_controls=len(controls),
        spec_sha256=sha256(spec),report_sha256=sha256(report),runner_sha256=sha256(runner),handwritten_playtestr_json=False,
        independently_expected_project_sha256=hashlib.sha256(expected_project).hexdigest(),
        independently_expected_readme_sha256=hashlib.sha256(expected_readme).hexdigest(),human_time='unmeasured',new_project_admissions=0,
        resumed_original_export_after_wrapper_ordering_fix=args.resume_export,
        scope='Prepared familiar-agent public route on actual pinned yo and locked official framework; no human beginner-usability or native qualification claim.'))
    print('Public yo authoring passed:3 commands,',len(controls),'controls; independent exact files and ordinary positive cleanup verified. No admission.')


if __name__=='__main__':asyncio.run(main())
