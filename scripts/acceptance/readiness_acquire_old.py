"""Reacquire one original project into this campaign's owned namespace."""
import argparse

from readiness_acquire_plop import acquire,extract_source
from readiness_evidence import RAW,ROOT,immutable_json,sha256
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--project',required=True)
    parser.add_argument('--resume-archive',action='store_true')
    parser.add_argument('--resume-download',action='store_true');args=parser.parse_args()
    if args.resume_archive and args.resume_download:parser.error('select one explicit acquisition resume route')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    ledger=load(docs/'candidates.json');inventory=load(docs/'old-migration-inventory.json')
    if ledger['development_admissions']!=10:raise RuntimeError('old target execution follows all ten new development packages')
    selected=[p for p in inventory['projects'] if p['project']==args.project]
    if len(selected)!=1:raise RuntimeError('undeclared original project')
    project=selected[0]
    archive_limit=(24 if args.project=='superfile' else 16)*1024**2
    omitted=({'docs/'+name:'../'+name for name in ['AUTHORS.md','CODE_OF_CONDUCT.md','CONTRIBUTING.md','README.md']}
             if args.project=='cookiecutter' else
             {'docs/changelog.md':'../CHANGELOG.md','docs/contributing.md':'../CONTRIBUTING.md',
              'docs/index.md':'../README.md','tests/demo/symlink.txt':'aaaa.txt'}
             if args.project=='copier' else
             {'website/src/content/docs/notice.md':'../../../../NOTICE.md'}
             if args.project=='superfile' else
             {'contrib/themes':'../runtime/themes'} if args.project=='helix' else None)
    expected=None
    if omitted:
        reviewed=load(docs/'old-migration'/args.project/'source-acquisition-review.json')
        if reviewed['pin']!=project['pin'] or reviewed['repository']!=project['repository'] or reviewed['omitted_links']!=omitted:
            raise RuntimeError('source-link disposition differs from reviewed pin')
        expected=reviewed['archive_sha256']
    if args.resume_archive:
        target=RAW/'active'/('old-'+args.project)
        owner=load(target/'task-owned.json')
        if (owner!=dict(workspace=str(ROOT),campaign='runner-readiness-ten-project-pass',project=project['repository'],pin=project['pin'])
                or {p.name for p in target.iterdir()}!={'task-owned.json','source.tar.gz'}):
            raise RuntimeError('resume requires only exact original owned marker and failed-extraction archive')
        archive=target/'source.tar.gz'
        if archive.stat().st_size>archive_limit:raise RuntimeError('archive byte bound')
        if expected is not None and sha256(archive)!=expected:raise RuntimeError('original retained archive changed')
        count,total=extract_source(archive.read_bytes(),target/'src',expanded_limit=192*1024**2,
            entry_limit=25000,member_limit=8*1024**2,omitted_links=omitted)
        immutable_json(target/'acquisition.json',dict(pin=project['pin'],archive_sha256=sha256(archive),
            compressed_bytes=archive.stat().st_size,extracted_source_bytes=total,entries=count,
            build_hooks_executed=False,omitted_links=omitted or {},resumed_original_archive=True))
        print('Extracted original retained archive with exactly reviewed documentation links omitted; no hook executed.')
        return
    acquire('old-'+args.project,project['repository'],project['pin'],archive_limit=archive_limit,
        expanded_limit=192*1024**2,entry_limit=25000,member_limit=8*1024**2,omitted_links=omitted,
        expected_archive_sha256=expected,resume=args.resume_download)


if __name__=='__main__':main()
