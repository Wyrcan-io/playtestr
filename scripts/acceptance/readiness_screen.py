"""Acquire bounded upstream metadata only; never build or execute target hooks."""
import base64
import json
from pathlib import Path
import subprocess

from readiness_evidence import RAW, ROOT, immutable_json

LEADS = [
 'rclone/rclone', 'twpayne/chezmoi', 'antonmedv/walk', 'sayanarijit/xplr',
 'mgunyho/tere', 'andmarti1424/sc-im', 'jarun/nnn',
 'plopjs/plop', 'jondot/hygen', 'python-poetry/poetry', 'pdm-project/pdm',
 'rubygems/rubygems', 'microsoft/edit', 'dooit-org/dooit', 'Textualize/frogmouth',
 'jdx/usage', 'nelsonenzo/tmux-appimage', 'joshmedeski/sesh', 'sc-im/sc-im',
 'martanne/vis', 'jarun/nnn', 'Canop/bacon', 'sxyazi/yazi',
 'o2sh/onefetch', 'PaulJuliusMartinez/jless', 'jqnatividad/qsv', 'charmbracelet/mods',
 'charmbracelet/vhs', 'charmbracelet/huh', 'papis/papis', 'dylanaraps/fff',
 'alichtman/tere', 'samtay/sd', 'antonmedv/fx', 'zellij-org/zellij',
 'https://github.com/GothenburgBitFactory/taskwarrior', 'gokcehan/lf',
]


def api(route):
    result = subprocess.run(['gh','api',route], cwd=ROOT, capture_output=True, timeout=30)
    if len(result.stdout)>1024*1024 or len(result.stderr)>16384:
        raise ValueError('metadata output bound')
    if result.returncode: raise RuntimeError(result.stderr.decode(errors='replace')[:1024])
    return json.loads(result.stdout)


def main():
    output = RAW/'screening'
    output.mkdir(parents=True, exist_ok=True)
    prior = json.loads((ROOT/'corpus/manifest.json').read_text(encoding='utf-8'))
    exclusions = {p['repository'].removeprefix('https://github.com/').lower() for p in prior['projects']}
    exclusions.update(['cookiecutter/cookiecutter','copier-org/copier','gokcehan/lf',
                       'yorukot/superfile','helix-editor/helix','charmbracelet/glow',
                       'canop/broot','sxyazi/yazi','ranger/ranger','jarun/nnn',
                       'dundee/gdu','saulpw/visidata','tconbeer/harlequin'])
    for lead in LEADS:
        lead = lead.removeprefix('https://github.com/')
        path = output/(lead.replace('/','--')+'.json')
        if path.exists(): continue
        if lead.lower() in exclusions:
            immutable_json(path,dict(repository=lead,status='excluded-previously-represented'))
            print(lead, 'excluded previous',flush=True);continue
        try:
            meta = api('repos/'+lead)
            commit = api('repos/'+lead+'/commits/'+meta['default_branch'])
            pin = commit['sha']
            readme = api('repos/'+lead+'/readme?ref='+pin)
            data = base64.b64decode(readme['content'])
            if len(data)>256*1024: raise ValueError('README exceeds bound')
            row = dict(repository=meta['full_name'],pin=pin,license=(meta.get('license') or {}).get('spdx_id'),
                       language=meta['language'],archived=meta['archived'],
                       upstream_url=meta['html_url'],source_url=meta['html_url']+'/tree/'+pin,
                       readme_url=readme['html_url'],readme=data.decode('utf-8',errors='strict'),
                       status='metadata-acquired-not-yet-reviewed')
            immutable_json(path,row)
            print(lead,pin,row['license'],flush=True)
        except Exception as error:
            immutable_json(path,dict(repository=lead,status='metadata-error',error=str(error)))
            print(lead,'metadata-error',flush=True)


if __name__ == '__main__': main()
