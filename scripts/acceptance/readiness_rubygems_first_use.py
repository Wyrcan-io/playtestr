"""Record the actual Bundler prompt and independently calibrate saved scaffolding."""
import asyncio
import base64
import json
import os
from pathlib import Path

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    package=ROOT/'docs/validation/runner-readiness-ten-project-pass/rubygems'
    fixture=package/'fixture';fixture.mkdir(exist_ok=False)
    (fixture/'sentinel.txt').write_bytes(b'reviewed existing work\n')
    active=RAW/'active/rubygems';runtime=json.loads((active/'runtime.json').read_text())
    ruby=active/runtime['ruby_relative_path']
    env=dict(os.environ)
    env['PATH']=str(active/'src/exe')+os.pathsep+str(ruby.parent)+os.pathsep+env['PATH']
    env['RUBYLIB']=str(active/'src/lib')
    env['PYTHONDONTWRITEBYTECODE']='1'
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    spec=package/'normal-gem.json'
    controls=['/expect Enter a test framework.','/text "rspec"','/key Enter',
              "/expect Gem 'atlas' was successfully created.",'/exit 0','/snapshot normal-gem.txt']
    selected=['atlas/Gemfile','atlas/atlas.gemspec','atlas/lib/atlas.rb','atlas/lib/atlas/version.rb',
              'atlas/Rakefile','atlas/spec/atlas_spec.rb','.bundle-user-config','sentinel.txt']
    controls += ['/file '+path for path in selected]
    controls += ['/entries .','/entries atlas','/entries atlas/lib','/review','/replay','/save']
    assert len(controls)==20
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture','fixture','--temporary-home',
          '--temporary-temp','--inherit-env','RUBYLIB','--width','100','--height','28',
          '--timeout-ms','10000','--run-timeout-ms','120000']
    settings={'BUNDLE_USER_CONFIG':'.bundle-user-config','BUNDLE_DISABLE_VERSION_CHECK':'true',
              'BUNDLE_VERSION':'system','GIT_CONFIG_NOSYSTEM':'1','GIT_CONFIG_GLOBAL':os.devnull,
              'GEMRC':os.devnull}
    for key,value in settings.items():argv+=['--env',key+'='+value]
    argv+=['--','ruby','-EUTF-8','-S','bundle','gem','atlas','--no-git','--no-bundle',
           '--no-ci','--no-mit','--no-coc','--no-changelog','--no-linter']
    version=await execute([runner,'--version'],'rubygems','first-use-version-check',env=env,
                          timeout=30,campaign=Campaign())
    capture=await execute(argv,'rubygems','first-use-record-review-replay-export',env=env,
        input='\n'.join(controls)+'\n',timeout=180,campaign=Campaign())
    saved=json.loads(spec.read_text())
    files={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in saved['steps']
           if s.get('state',{}).get('kind')=='file'}
    assert set(files)==set(selected)
    assert files['atlas/lib/atlas/version.rb']==b'# frozen_string_literal: true\n\nmodule Atlas\n  VERSION = "0.1.0"\nend\n'
    assert files['sentinel.txt']==b'reviewed existing work\n'
    assert b'RSpec::Core::RakeTask' in files['atlas/Rakefile']
    assert b'RSpec.describe Atlas' in files['atlas/spec/atlas_spec.rb']
    assert b'module Atlas' in files['atlas/lib/atlas.rb']
    assert b'spec.name = "atlas"' in files['atlas/atlas.gemspec']
    assert b'BUNDLE_GEM__TEST' in files['.bundle-user-config'] and b'rspec' in files['.bundle-user-config']
    root=next(s['state']['entries'] for s in saved['steps'] if s.get('state',{}).get('path')=='.')
    assert set(root)=={'.bundle-user-config','atlas','sentinel.txt'}
    report=RAW/'rubygems/first-ordinary-report.json'
    ordinary=await execute([runner,'test','--report',report.relative_to(ROOT),spec.relative_to(ROOT)],
        'rubygems','first-use-ordinary-public-test',env=env,timeout=130,campaign=Campaign())
    result=json.loads(report.read_text())['results'][0]
    assert result['status']=='passed' and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned']
    immutable_json(package/'first-use.json',dict(schema_version=1,status='development-route-passed',
        shell_invocations=3,recorder_controls=20,handwritten_playtestr_json=False,
        version_attempt=version['id'],capture_attempt=capture['id'],ordinary_attempt=ordinary['id'],
        spec_sha256=sha256(spec),runner_sha256=sha256(runner),target_build_sha256=sha256(active/'build.json'),
        human_time='unmeasured',confounders=['prepared synthetic fixture/options','agent familiarity','runtime already available']))
    print('Bundler first reviewed public test passed: three invocations, twenty controls; human time unmeasured.')


if __name__=='__main__':asyncio.run(main())
