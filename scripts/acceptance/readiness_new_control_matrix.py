"""Bind declared whole controls to actual source-matched native outcome events."""
import argparse
import hashlib
import json
from pathlib import Path
import re

from readiness_evidence import RAW, ROOT, immutable_json, sha256


def packet_file(root, reference, maximum):
    """Reject untrusted packet references before opening their payload."""
    if not isinstance(reference,str) or len(reference)>4096:
        raise RuntimeError('unsafe native packet reference')
    parts=reference.replace('\\','/').split('/')
    if not parts or any(p in {'','.','..'} or ':' in p or '\x00' in p for p in parts):
        raise RuntimeError('unsafe native packet reference')
    candidate=root
    for part in parts:
        candidate=candidate/part
        if candidate.is_symlink() or candidate.is_junction():
            raise RuntimeError('linked native packet reference')
    candidate.resolve().relative_to(root.resolve())
    if not candidate.is_file() or candidate.stat().st_size>maximum:
        raise RuntimeError('native evidence byte limit or missing file')
    return candidate


def read_json(path,maximum=1024*1024):
    with path.open('rb') as stream:value=stream.read(maximum+1)
    if len(value)>maximum:raise RuntimeError('native evidence byte limit')
    return json.loads(value.decode('utf-8-sig'))


def canonical_hashes(path):
    value=path.read_bytes().replace(b'\r\n',b'\n')
    return {hashlib.sha256(value).hexdigest(),hashlib.sha256(value.replace(b'\n',b'\r\n')).hexdigest()}


def packet_observations(run):
    root=RAW/'native'/run
    metadata=read_json(root/'run-metadata.json',65536)
    if metadata['status']!='completed' or metadata['conclusion']!='success':raise RuntimeError('native run is not successful')
    result=[]
    for host in sorted(p for p in root.iterdir() if p.is_dir()):
        if host.is_symlink() or host.is_junction():raise RuntimeError('linked native packet host')
        os_name='windows' if 'windows' in host.name.lower() else 'macos' if 'macos' in host.name.lower() else 'linux' if 'ubuntu' in host.name.lower() else None
        if not os_name:continue
        for console in host.glob('core/*/console.log'):
            attempt=console.parent.name
            events=host/'events'
            finished=read_json(events/f'{attempt}-finished.json',65536)
            started=read_json(events/f'{attempt}-started.json',65536)
            read_json(events/f'{attempt}-launched.json',65536)
            if finished['category']!='passed' or finished['exit_code']!=0 or started['expected_exit']!=0:continue
            if finished.get('cleanup_errors') or finished['harness_cleanup']!='harness_process_reaped':raise RuntimeError('native control cleanup unconfirmed')
            identified=read_json(events/f'{attempt}-identified.json',65536)
            manifest=packet_file(host,identified['identity']['manifest'],1024*1024)
            if sha256(manifest)!=identified['identity']['sha256']:raise RuntimeError('native identity manifest changed')
            identity=read_json(manifest)
            if console.stat().st_size>4*1024**2:raise RuntimeError('native console byte bound')
            text=console.read_text(encoding='utf-8',errors='strict')
            whole=set()
            for line in text.splitlines():
                try:event=json.loads(line)
                except ValueError:continue
                if isinstance(event,dict) and event.get('Action')=='pass' and event.get('Test') and '/' not in event['Test']:
                    whole.add((event.get('Package'),event['Test']))
            verbose=set()
            for line in text.splitlines():
                match=re.fullmatch(r'(test_[A-Za-z0-9_]+) \(([^)]+)\) \.\.\. ok',line.strip())
                if match:
                    qualified=match.group(2)
                    if not qualified.endswith('.'+match.group(1)):raise RuntimeError('unittest outcome identity mismatch')
                    verbose.add(qualified)
            if not whole and not verbose:continue
            result.append(dict(host=os_name,artifact=host.name,run=run,attempt=attempt,whole=whole,verbose=verbose,
                files=identity['files'],console_sha256=sha256(console),manifest_sha256=sha256(manifest),
                metadata_sha256=sha256(root/'run-metadata.json'),source_revision=metadata['headSha']))
    if {r['host'] for r in result}!={'linux','macos','windows'}:raise RuntimeError('all three native packets required')
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--core-run',required=True);parser.add_argument('--harness-run',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    for value in [args.core_run,args.harness_run]:
        if not value.isascii() or not value.isdecimal():raise RuntimeError('invalid public native run ID')
    output=args.output.resolve();output.relative_to(ROOT)
    declarations=ROOT/'docs/validation/runner-readiness-ten-project-pass/new-control-declarations.json'
    controls=json.loads(declarations.read_text())['controls']
    if len(controls)!=33 or len({r['id'] for r in controls})!=33:raise RuntimeError('original distinct scope changed')
    observations=packet_observations(args.core_run)+packet_observations(args.harness_run)
    bound=[]
    for control in controls:
        source=ROOT/control['source'];source.relative_to(ROOT)
        hashes=canonical_hashes(source);evidence=[]
        for host in control['hosts']:
            found=[]
            for observed in observations:
                if observed['host']!=host:continue
                if source.suffix=='.go':matched=('github.com/Wyrcan-io/playtestr/'+Path(control['source']).parent.as_posix(),control['test']) in observed['whole']
                else:
                    module=source.stem
                    matched=any(q.startswith(module+'.') and (q.endswith('.'+control['test']) or q.rsplit('.',1)[-1]==control['test']) for q in observed['verbose'])
                if not matched:continue
                if observed['files'].get(control['source']) not in hashes:continue
                found.append({k:observed[k] for k in ['host','artifact','run','attempt','console_sha256','manifest_sha256','metadata_sha256','source_revision']})
            if not found:raise RuntimeError('missing actual source-matched whole control: '+control['id']+' '+host)
            evidence.extend(found)
        bound.append({**control,'status':'development executed; final archive qualification pending',
            'current_source_sha256':sha256(source),'evidence':evidence})
    immutable_json(output,dict(schema_version=1,declarations_sha256=sha256(declarations),controls=bound,
        distinct_whole_controls=33,claim='Development native events only; no final archive credit. No subcase, seed or host-copy inflation.'))
    print('Bound 33 distinct whole controls to actual native source identities and positive outcomes.')


if __name__=='__main__':main()
