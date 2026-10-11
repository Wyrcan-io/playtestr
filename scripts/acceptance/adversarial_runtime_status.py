"""Read-only status for exactly the campaign-owned active runtime."""
import argparse
import json
import os
from pathlib import Path
import sys
from adversarial_process import ROOT

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project')
    parser.add_argument('--native-source',action='store_true')
    args=parser.parse_args()
    if not args.project or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in args.project):
        raise RuntimeError('Invalid project identity')
    root=(Path('/var/tmp')/('playtestr-adversarial-'+args.project)) if args.native_source else ROOT/'.cache/ten-new-project-apps'/args.project
    result=dict(root=str(root),exists=root.exists(),runtime=(root/'runtime.json').is_file(),source=(root/'source').is_dir(),processes=[])
    if (root/'task-owned.json').is_file():
        result['owner']=json.loads((root/'task-owned.json').read_text(encoding='utf-8'))
    if (root/'runtime.json').is_file():
        result['identity']=json.loads((root/'runtime.json').read_text(encoding='utf-8'))
    if Path('/proc').exists():
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit() or int(proc.name)==os.getpid(): continue
            try:
                command=[v.decode(errors='replace') for v in (proc/'cmdline').read_bytes().split(b'\0') if v]
                if any(value.startswith(str(root)+'/') for value in command):
                    result['processes'].append(dict(pid=int(proc.name),owned_arguments=[v for v in command if v.startswith(str(root)+'/')]))
                elif args.project in command and any('scripts/acceptance/adversarial_' in v for v in command):
                    result['processes'].append(dict(pid=int(proc.name),kind='owned campaign helper'))
            except OSError: pass
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
