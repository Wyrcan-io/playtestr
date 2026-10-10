"""Screen primary upstream metadata before acquiring any campaign application."""
import base64
import json
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/validation/ten-new-project-adversarial-pass'
RAW = ROOT / 'artifacts/ten-new-project-adversarial-pass/screening'
CANDIDATES = [
    ('cookiecutter/cookiecutter', 'selected', ['linux','windows'], 'Prompt CLI; local synthetic templates, choices, hooks and generated manifests'),
    ('copier-org/copier', 'selected', ['linux','windows'], 'Prompt CLI; template defaults, validation, overwrite and update workflows'),
    ('gokcehan/lf', 'selected', ['linux','windows'], 'Full-screen file manager; copy, move, rename, search, nested command mode'),
    ('yorukot/superfile', 'selected', ['linux','windows'], 'Full-screen file manager; multi-panel operations, clipboard and cancellation'),
    ('helix-editor/helix', 'selected', ['linux','windows'], 'Full-screen modal editor; save, search, selections, undo and invalid commands'),
    ('charmbracelet/glow', 'selected', ['linux','macos'], 'Markdown browser/pager; long scrolling, search, navigation and local documents'),
    ('Canop/broot', 'selected', ['linux','macos'], 'Tree explorer; filtering, verb mode and bounded synthetic filesystem changes'),
    ('sxyazi/yazi', 'selected', ['linux','macos'], 'Full-screen file manager; bulk selection, tabs, nested modes and file operations'),
    ('ranger/ranger', 'selected', ['linux','macos'], 'Curses file manager; console commands, bookmarks, rename and preview'),
    ('mirror/nano', 'rejected', [], 'Unavailable GitHub identity; no canonical source or new-project credit'),
    ('jarun/nnn', 'selected', ['linux','macos'], 'C file manager; contexts, filtering, archives and file operations'),
    ('joshuto-rs/joshuto', 'reserve', ['linux','macos'], 'Rust file manager; alternative nested modes and file operations'),
    ('Textualize/oterm', 'rejected', [], 'Core workflows require model service; unsuitable AI-free offline campaign'),
    ('dandavison/delta', 'reserve', ['linux','macos','windows'], 'Rust interactive pager through pager integration; must prove direct useful interactions'),
    ('paulirish/git-open', 'rejected', [], 'Browser-launch workflow lacks ten meaningful terminal interactions'),
    ('pypa/hatch', 'reserve', ['linux','macos','windows'], 'Python environment/project utility; verify adequate interactive workflows'),
    ('nushell/nushell', 'reserve', ['linux','macos','windows'], 'Rust interactive shell; structured data, filesystem and error recovery'),
    ('vifm/vifm', 'reserve', ['linux','macos','windows'], 'C modal file manager; platform-specific build prerequisites'),
]

def api(route):
    return json.loads(subprocess.check_output(['gh','api',route], timeout=40))

def main():
    DOC.mkdir(parents=True, exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    if (DOC/'candidates.json').exists():
        raise SystemExit('Refuse overwriting original pre-acquisition screening')
    records=[]
    existing=DOC/'screening-attempts.jsonl'
    if existing.exists():
        records=[json.loads(line) for line in existing.read_text(encoding='utf-8').splitlines()]
    for repo, decision, hosts, reason in CANDIDATES:
        if any(r['repo']==repo for r in records):
            continue
        try:
            meta=api('repos/'+repo)
        except subprocess.CalledProcessError as error:
            record=dict(repo=repo,disposition='rejected',reason=reason,
                        metadata_error=str(error),acquired=False,
                        screened_at=datetime.now(timezone.utc).isoformat())
            records.append(record)
            with existing.open('a',encoding='utf-8') as out:
                out.write(json.dumps(record)+'\n')
            continue
        branch=meta['default_branch']
        commit=api('repos/'+repo+'/commits/'+branch)
        sha=commit['sha']
        record=dict(repo=repo,url=meta['html_url'],sha=sha,default_branch=branch,
                    archived=meta['archived'],pushed_at=meta['pushed_at'],
                    language=meta['language'],license=(meta.get('license') or {}).get('spdx_id'),
                    disposition=decision,planned_hosts=hosts,reason=reason,
                    screened_at=datetime.now(timezone.utc).isoformat(),
                    acquired=False,host_claim='provisional until pinned documentation and actual execution',
                    canonical_identity_pending=repo=='mirror/nano')
        try:
            readme=api('repos/'+repo+'/readme?ref='+sha)
            data=base64.b64decode(readme['content'])
            (RAW/(repo.replace('/','--')+'-README.txt')).write_bytes(data)
            record['readme_source']=readme['html_url']
            record['readme_bytes']=len(data)
        except subprocess.CalledProcessError:
            record['readme_missing']=True
        records.append(record)
        with (DOC/'screening-attempts.jsonl').open('a',encoding='utf-8') as out:
            out.write(json.dumps(record)+'\n')
        print(repo,sha,decision,flush=True)
    (DOC/'candidates.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
