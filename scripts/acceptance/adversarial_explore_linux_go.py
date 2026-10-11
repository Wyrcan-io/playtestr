"""Explicit WSL-only exploratory build/replay, with no native qualification credit."""
import argparse
import os
from pathlib import Path
import platform
import sys
from adversarial_process import ROOT, run

parser=argparse.ArgumentParser()
parser.add_argument('--project',required=True)
args=parser.parse_args()
if 'microsoft' not in platform.release().lower():
    raise RuntimeError('This recipe is specifically labeled WSL exploration')
runtime=Path('/var/tmp/playtestr-adversarial-runtime')
env=dict(os.environ,PLAYTESTR_GO=str(runtime/'go/bin/go'))
for name,folder in [('GOCACHE','product-build-cache'),('GOMODCACHE','product-mod-cache'),('GOPATH','product-go-path')]:
    target=runtime/folder
    target.mkdir(exist_ok=True)
    env[name]=str(target)
env['GOTOOLCHAIN']='local'
binary=ROOT/'bin/playtestr-linux'
run([runtime/'go/bin/go','build','-trimpath','-o',binary,'./cmd/playtestr'],
    'core','wsl-exploratory-product-build',env=env,timeout=300)
for mode in ['test','state']:
    run([sys.executable,ROOT/'scripts/acceptance/adversarial_journey.py',mode,args.project,
         '--runtime','/var/tmp/playtestr-adversarial-'+args.project,'--binary',binary],
        args.project,'wsl-exploratory-'+mode,env=env,timeout=480)
print('WSL exploratory ordinary and state cases passed; native Linux still required')
