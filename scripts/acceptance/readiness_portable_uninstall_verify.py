"""Audit actual native portable archive execution and four-file uninstall."""
import argparse
import hashlib
from pathlib import Path
import tarfile

from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_identity_manifest import load_manifest
from readiness_new_control_matrix import read_json as load


def require(value,message):
    if not value:raise RuntimeError(message)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);args=parser.parse_args()
    require(args.run.isascii() and args.run.isdecimal(),'invalid run')
    parent=RAW/'native'/args.run;metadata=load(parent/'run-metadata.json')
    require(metadata['status']=='completed' and metadata['conclusion']=='success' and len(metadata['jobs'])==2
        and all(j['conclusion']=='success' and j['status']=='completed' for j in metadata['jobs']),'incomplete native portable jobs')
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    candidate=load(docs/'migration-candidate-freeze.json')
    for artifact,host,machine in [('Linux','linux','x86_64'),('macOS','darwin','arm64')]:
        packet=parent/('portable-uninstall-'+artifact)
        cell=next(c for c in candidate['cells'] if c['host']==host)
        roots=list((packet/'portable-uninstall').glob('*/verified.json'));require(len(roots)==1,'ambiguous uninstall proof')
        path=roots[0];root=path.parent;proof=load(path);declared=load(root/'declared.json')
        require(proof['host']==declared['host']==host and proof['native_machine']==machine
            and proof['architecture']==declared['architecture']==cell['architecture']
            and proof['archive_sha256']==declared['archive_sha256']==cell['archive_sha256']
            and proof['binary_sha256']==declared['binary_sha256']==cell['binary_sha256']
            and proof['declaration_sha256']==sha256(root/'declared.json') and proof['installed_directory_removed'],
            'actual native proof identity/removal differs')
        canonical=ROOT/cell['archive_local_only']
        require(canonical.stat().st_size==cell['archive_bytes'] and sha256(canonical)==cell['archive_sha256'],'canonical exact archive changed')
        with tarfile.open(canonical,'r:gz') as archive:
            members=archive.getmembers();require(len(members)==4 and all(m.isfile() and m.size<=32*1024**2 for m in members),'archive member bounds')
            expected={Path(m.name).name:hashlib.sha256(archive.extractfile(m).read(m.size+1)).hexdigest() for m in members}
        require(set(expected)=={'LICENSE','README.md','THIRD_PARTY_NOTICES.md','playtestr'}
            and proof['installed_files_verified']==declared['files']==expected,'four installed files differ from exact archive')
        installed=declared['installed_relative'];prefix='artifacts/runner-readiness-ten-project-pass/'
        require(installed.startswith(prefix+'portable-uninstall/'+root.name+'/') and installed.endswith('/installed caf\u00e9 \u96ea'),
            'different owned Unicode install path')
        require(not (packet/installed.removeprefix(prefix)).exists(),'expanded portable installation remains')
        ledger=object.__new__(Campaign);ledger.raw=packet;events=ledger.attempts()[proof['version_attempt']]
        require(all(e['phase']=='final-archive' for e in events.values()) and 'launched' in events,'missing actual final launch')
        end=events['finished'];require(events['started']['expected_exit']==0 and end['exit_code']==0 and end['category']=='passed'
            and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'],'actual launch/cleanup failed')
        manifest=load_manifest(packet,events['identified']['identity'])
        require(manifest['host']==('Linux' if host=='linux' else 'Darwin') and manifest['architecture']==machine
            and manifest['files'][installed+'/playtestr']==cell['binary_sha256'],'different actual native executable')
        console=packet/'core'/proof['version_attempt']/'console.log'
        require(sha256(console)==end['console_sha256'] and console.read_text(encoding='utf-8-sig').strip()=='playtestr '+candidate['version'],
            'actual portable version output differs')
        immutable_json(docs/'archive-experience'/(host+'-portable-uninstall.json'),dict(run=args.run,host=host,
            architecture=cell['architecture'],archive_sha256=cell['archive_sha256'],binary_sha256=cell['binary_sha256'],
            proof_sha256=sha256(path),declaration_sha256=sha256(root/'declared.json'),version_attempt=proof['version_attempt'],
            privileged_role_enabled=proof['privileged_role_enabled'],installed_directory_removed=True,final_archive_credit=0,
            scope='Actual native Unicode/spaces portable launch and checked four-file removal; prelaunch executable and all installed members independently match canonical exact candidate archive.'))
        print('Independently verified portable uninstall:',host)


if __name__=='__main__':main()
