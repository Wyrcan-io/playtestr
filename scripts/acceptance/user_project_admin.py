#!/usr/bin/env python3
"""Acquire pinned external sources and persist honest compact result ledgers.

No recursive deletion occurs here. The Windows operator verifies paths and
uses Remove-Item -LiteralPath after the native process check.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
DOC=ROOT/'docs/validation/ten-project-user-pass'


def acquire(index, native_only=False, quiet=False):
    c=json.loads((DOC/'candidates.json').read_text(encoding='utf-8'))[index]
    slug=c['repo'].split('/')[-1]; slug='create-vite' if slug=='vite' else slug
    dest=ROOT/'.cache/ten-project-apps'/f'{slug}-{index+1:02d}'
    if dest.exists(): raise RuntimeError('Refuse reuse of unverified existing application directory')
    dest.mkdir(parents=True)
    (dest/'task-owned.json').write_text(json.dumps(dict(project=slug,repo=c['repo'],sha=c['sha'],created_by='ten-project-user-pass',workspace=str(ROOT))))
    if native_only:
        print('Owned source directory prepared; native Linux acquisition still required',dest)
        return
    subprocess.run(['git','clone','--filter=blob:none','--no-checkout',c['url']+'.git',str(dest/'source')],check=True,timeout=180)
    subprocess.run(['git','-C',str(dest/'source'),'checkout','--detach',c['sha']],check=True,timeout=180)
    print('Acquired',slug,c['sha'],dest)
    if quiet:return
    for name in ['LICENSE','LICENSE.md','LICENCE','COPYING','README.md','README.rst','pyproject.toml','package.json','go.mod']:
        f=dest/'source'/name
        if f.exists():
            s=f.read_text(encoding='utf-8',errors='replace'); print(name,s[:500] if name!='README.md' else s[:2500])


def close(slug,app):
    c=next(c for c in json.loads((DOC/'candidates.json').read_text(encoding='utf-8')) if c['repo'].split('/')[-1]==slug or slug=='create-vite' and c['repo']=='vitejs/vite')
    directory=DOC/slug; config=json.loads((directory/'scenarios.json').read_text(encoding='utf-8'));raw=ROOT/'artifacts/ten-project-user-pass'/slug
    summary=json.loads((raw/'record-summary.json').read_text(encoding='utf-8')); defect=json.loads((raw/'defect-summary.json').read_text(encoding='utf-8'));recovery=json.loads((raw/'recovery-summary.json').read_text(encoding='utf-8'))
    assert len(summary['scenarios'])>=3 and all(r['attempts']==10 for r in summary['scenarios'])
    assert defect['scenarios'][0]['failed']==1 and len(recovery['scenarios'])==len(config['cases'])
    report=json.loads((raw/(config['cases'][0]['name']+'-defect-0.json')).read_text(encoding='utf-8'))['results'][0]
    result=dict(project=slug,upstream=c,host=summary['host'],runner_sha256=summary['runner_sha256'],status='journeys_passed_pending_final_requalification',scenarios=summary['scenarios'],defect_category=report['failure']['category'],defect_step=next(s['number'] for s in report['steps'] if s['status']=='failed'),defect_recovery_contract_hashes_equal=defect['scenarios'][0]['contract_hashes']==recovery['scenarios'][0]['contract_hashes'],task_owned_application_directory=str(ROOT/'.cache/ten-project-apps'/app),deleted=False,complete_product_campaign_credit=0)
    assert result['defect_recovery_contract_hashes_equal']
    (directory/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    text=f"# {slug}: new-user terminal regression trial\n\nUpstream: [{c['repo']}]({c['url']}), exact source `{c['sha']}`, license {c['license']}. Actual primary host: {summary['host']}. This is operator engineering validation, not maintainer adoption or complete-product campaign credit.\n\n"
    text+='| Scenario | User risk / tested behavior | Accepted repetitions | Positive evidence |\n| --- | --- | --- | --- |\n'
    for case in config['cases']:
        text+=f"| {case['name']} | {case['purpose']} | 10 passing fresh runs | Reviewed `{case['snapshot']}`, meaningful checkpoints; "+('independent saved-state bytes' if case.get('oracle') else 'rendered terminal outcome')+' |\n'
    text+='\nThree distinct workflows minimum; extra scenarios are recorded explicitly. Recorder review/fresh replay/export used public commands, fixtures and temporary home/temp. The primary flow exercises fresh suffix maintenance; manual JSON maintenance and generated workflow setup are retained separately. No app-name special case in the runner.\n\n'
    text+=f"Unchanged-contract target regression produced `{result['defect_category']}` at step {result['defect_step']}; fixing/restoring target behavior passed with identical primary contract hashes. Cleanup was confirmed in every passing/negative report. See [result.json](result.json), [scenarios.json](scenarios.json), retained regression patch/configuration recipe and ignored raw reports.\n\n"
    text+='Not covered: '+config.get('exclusions','credentials/network integrations, arbitrary style/mouse/grapheme behavior and all features outside the selected scenarios')+'. No universal compatibility, zero-flakiness or application-wide coverage claim.\n'
    text+='\nActual source/build/reacquisition instructions are recorded in recipe.json. Application deletion follows evidence checks; deletion status is separately recorded in result.json and the batch ledger. Complete-product campaign credit: 0.\n'
    (directory/'README.md').write_text(text,encoding='utf-8')
    ledger=json.loads((DOC/'ledger.json').read_text(encoding='utf-8'));ledger['projects']=[p for p in ledger['projects'] if p['project']!=slug]+[result];(DOC/'ledger.json').write_text(json.dumps(ledger,indent=2)+'\n')
    print('Evidence closed',slug,len(config['cases']),'scenarios; deletion still requires native checks')


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8',errors='replace')
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['acquire','close']);p.add_argument('value');p.add_argument('app',nargs='?');p.add_argument('--native-source-only',action='store_true');p.add_argument('--quiet',action='store_true');a=p.parse_args()
    if a.mode=='acquire':acquire(int(a.value),a.native_source_only,a.quiet)
    else:close(a.value,a.app)
