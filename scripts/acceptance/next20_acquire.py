"""Acquire one declared pinned target; reuse the checked historical extractor."""
import argparse
import json
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

from next20_check import NAME,RAW,ROOT,DOC
from readiness_acquire_plop import extract_source
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure
from next20_storage_baseline import prior_campaign_usage


def download_source(url, opener=urllib.request.urlopen, pause=time.sleep):
    """Download one bounded source archive with limited transient retries."""
    attempts=[]
    for number in range(1,4):
        request=urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'})
        try:
            with opener(request,timeout=30) as response:
                data=response.read(8*1024**2+1)
                status=response.getcode()
            if len(data)>8*1024**2:
                attempts.append(dict(attempt=number,outcome='oversized',http_status=status,
                                     bytes=len(data)))
                raise ValueError('compressed source exceeds declaration')
            attempts.append(dict(attempt=number,outcome='downloaded',http_status=status,
                                 bytes=len(data)))
            return data,attempts
        except (urllib.error.HTTPError,urllib.error.URLError,TimeoutError,OSError) as error:
            status=error.code if isinstance(error,urllib.error.HTTPError) else None
            if isinstance(error,urllib.error.HTTPError):
                retryable=500<=error.code<=599
            else:
                retryable=isinstance(error,(urllib.error.URLError,TimeoutError,ConnectionError))
            attempts.append(dict(attempt=number,outcome='transient_error' if retryable else 'error',
                http_status=status,error_type=type(error).__name__,message=str(error)[:512]))
            if not retryable or number==3:
                failure=RuntimeError('pinned source download failed after bounded attempts')
                failure.attempts=attempts
                raise failure from error
            pause(number)
    raise AssertionError('bounded source download loop fell through')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');parser.add_argument('--resume-source-archive',action='store_true')
    parser.add_argument('--omitted-documentation-links',type=Path);args=parser.parse_args()
    declaration=json.loads((DOC/'selection-declaration.json').read_text())
    matches=[p for p in declaration['selected'] if p['id']==args.project]
    if len(matches)!=1:raise ValueError('not a selected target')
    selected=matches[0]
    if selected['late_transfer']:raise ValueError('late transfer target cannot be acquired before provisional freeze')
    rows=json.loads((DOC/'screening-decisions.json').read_text())['rows']
    row=next(r for r in rows if r.get('repository')==selected['repository'])
    active=RAW/'active';active.mkdir(exist_ok=True)
    # Preserve prior target trees when their checked removal packet is
    # incomplete. Acquisition remains exclusive at the selected project path.
    if (active/args.project).exists() and not args.resume_source_archive:raise ValueError('active target already exists; resume/clean it before acquisition')
    before=measure(RAW);old_size=prior_campaign_usage(DOC,ROOT)['raw']
    if before['total_bytes']+64*1024**2>4*1024**3 or before['total_bytes']+old_size+64*1024**2>6*1024**3:
        raise ValueError('insufficient declared acquisition headroom')
    target=active/args.project;links=None;link_policy=None
    if args.omitted_documentation_links:
        from next20_source_links import policy
        link_policy,links=policy(args.omitted_documentation_links,args.project,row['pin'])
    if args.resume_source_archive:
        if link_policy is None or set(active.iterdir())!={target} or {p.name for p in target.iterdir()}!={'task-owned.json','source.tar.gz'}:raise ValueError('resume requires one refused source-only archive and explicit policy')
        owner=json.loads((target/'task-owned.json').read_text())
        if owner['workspace']!=str(ROOT) or owner['campaign']!=NAME or owner['slug']!=args.project or owner['pin']!=row['pin'] or sha256(target/'source.tar.gz')!=link_policy['original_archive_sha256']:raise ValueError('refused source archive ownership/bytes differ')
    url='https://api.github.com/repos/'+selected['repository']+'/tarball/'+row['pin']
    if args.resume_source_archive:
        data=(target/'source.tar.gz').read_bytes();download_attempts=[]
    else:
        try:
            data,download_attempts=download_source(url)
        except RuntimeError as error:
            failure_root=RAW/args.project/'acquisition-fetch-failures'
            immutable_json(failure_root/(uuid.uuid4().hex+'.json'),dict(schema_version=1,
                project=args.project,pin=row['pin'],attempts=getattr(error,'attempts',[]),
                scope='Bounded source acquisition failed before creating an active target tree.'))
            raise
        target.mkdir()
        immutable_json(target/'task-owned.json',dict(workspace=str(ROOT),campaign=NAME,
            project=selected['repository'],slug=args.project,pin=row['pin'],
            storage_before_bytes=before['total_bytes'],source_only=True))
    archive=target/'source.tar.gz'
    if not args.resume_source_archive:
        with archive.open('xb') as stream:stream.write(data)
    count,total=extract_source(data,target/'src',expanded_limit=64*1024**2,
        entry_limit=10000,member_limit=8*1024**2,omitted_links=links)
    immutable_json(target/'acquisition.json',dict(repository=selected['repository'],pin=row['pin'],url=url,
        archive_sha256=sha256(archive),compressed_bytes=len(data),expanded_bytes=total,entries=count,
        download_attempts=download_attempts,
        build_hooks_executed=False,**(dict(omitted_documentation_links=links,documentation_link_policy_sha256=sha256(args.omitted_documentation_links),reused_refused_archive=args.resume_source_archive) if links else {}),source_files={p.relative_to(target/'src').as_posix():sha256(p)
            for p in sorted((target/'src').rglob('*')) if p.is_file()}))
    print('Acquired source only:',args.project,row['pin'],'files',count,'bytes',total)


if __name__=='__main__':main()
