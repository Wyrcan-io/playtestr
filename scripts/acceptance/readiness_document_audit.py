"""Check campaign narrative UTF-8 and local Markdown links against Git paths."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import urllib.parse

from readiness_evidence import ROOT, immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',choices=['document-audit.json','closing-document-audit.json','closing-document-audit-v2.json'],default='document-audit.json');args=parser.parse_args()
    tracked=subprocess.run(['git','-c','core.quotePath=false','ls-files','-z'],cwd=ROOT,check=True,stdout=subprocess.PIPE).stdout.decode().split('\x00')
    files={n for n in tracked if n}
    # Staging the reviewable closing documents makes their public link targets
    # concrete without requiring a commit before validation.
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    selected=[p for p in docs.rglob('*.md') if not any(q in p.relative_to(docs).parts for q in ['fixtures','snapshots','contracts','human-study'])]
    selected+=[ROOT/n for n in ['README.md','roadmap.md','docs/plans/README.md','docs/plans/16-runner-stability-and-usability.md']]
    failures=[];links=0;hashes={}
    for path in sorted(set(selected)):
        data=path.read_bytes();source=data.decode('utf-8-sig');hashes[path.relative_to(ROOT).as_posix()]=sha256(path)
        source=re.sub(r'^(```|~~~).*?^\1[^\n]*$', '',source,flags=re.M|re.S)
        for match in re.finditer(r'(?<!!)\[[^\]\n]+\]\((<[^>]+>|[^\s)]+)(?:\s+"[^"]*")?\)',source):
            href=match.group(1).strip('<>')
            if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:',href) or href.startswith('#'):continue
            target=urllib.parse.unquote(href.split('#',1)[0].split('?',1)[0])
            if not target:continue
            resolved=(ROOT/target.lstrip('/') if target.startswith('/') else path.parent/target).resolve()
            try:name=resolved.relative_to(ROOT).as_posix()
            except ValueError:failures.append(dict(source=str(path.relative_to(ROOT)),target=href,reason='outside workspace'));continue
            links+=1
            if name not in files or not resolved.is_file():failures.append(dict(source=path.relative_to(ROOT).as_posix(),target=href,reason='not a tracked public file'))
    if failures:
        print(json.dumps(failures,ensure_ascii=True,indent=2));raise RuntimeError('public documentation link failures')
    immutable_json(docs/args.output,dict(markdown_files=len(hashes),local_links=links,files=hashes,
        scope='Strict UTF-8 narrative Markdown and local file links resolved to actual Git-index tracked files. Fixture/contract/snapshot payloads are exact-byte data, not narrative; fenced code and remote URLs are not local file links. Remote link availability and heading anchors are outside this local check.'))
    print('Verified narrative UTF-8 and tracked local links:',len(hashes),'documents,',links,'links.')


if __name__=='__main__':main()
