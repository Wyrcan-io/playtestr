"""Prepare only synthetic local Git history for actual public Copier update."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
from adversarial_process import ROOT,DOC,run

def main():
    package=DOC/'copier'
    fixture=package/'fixtures'
    template=fixture/'templates/update'
    destination=fixture/'updated'
    archive=package/'synthetic-git-metadata.tar.gz'
    if archive.exists():
        # Restore only reviewed synthetic .git metadata. No upstream app source
        # or downloaded program is carried in this archive.
        expected=json.loads((package/'synthetic-git-identity.json').read_text(encoding='utf-8'))['archive_sha256']
        if archive.stat().st_size>2*1024*1024 or hashlib.sha256(archive.read_bytes()).hexdigest()!=expected:
            raise RuntimeError('Synthetic Git archive identity differs')
        with tarfile.open(archive) as tar:
            members=tar.getmembers()
            if len(members)>1000 or sum(member.size for member in members)>4*1024*1024:
                raise RuntimeError('Synthetic Git archive total bound')
            for member in members:
                path=Path(member.name)
                if path.is_absolute() or '..' in path.parts or '.git' not in path.parts or not member.isfile():
                    raise RuntimeError('Unsafe synthetic Git archive')
                if member.size>1024*1024:
                    raise RuntimeError('Synthetic Git member bound')
            tar.extractall(package,filter='data')
        print('Restored reviewed synthetic Git metadata')
        return
    if destination.exists():
        raise RuntimeError('Refuse overwriting unknown or partially prepared destination')
    identity=json.loads((ROOT/'.cache/ten-new-project-apps/copier/runtime.json').read_text(encoding='utf-8'))
    env=dict(os.environ,PATH=identity['path']+os.pathsep+os.environ['PATH'],
        GIT_AUTHOR_NAME='Synthetic validation',GIT_AUTHOR_EMAIL='synthetic@example.invalid',
        GIT_COMMITTER_NAME='Synthetic validation',GIT_COMMITTER_EMAIL='synthetic@example.invalid',
        GIT_AUTHOR_DATE='2020-01-01T00:00:00Z',GIT_COMMITTER_DATE='2020-01-01T00:00:00Z')
    def command(argv,label,cwd): return run(argv,'copier','git-fixture-'+label,cwd=cwd,env=env,timeout=30)
    def write(path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(value,encoding='utf-8',newline='\n')
    def initialize(path):
        command(['git','init','--initial-branch','main'],'init',path)
        for key,value in [('core.autocrlf','false'),('core.filemode','false'),('user.name','Synthetic validation'),('user.email','synthetic@example.invalid')]:
            command(['git','config',key,value],'local-config',path)
    def commit(path,label):
        command(['git','add','.'],'add-'+label,path)
        command(['git','commit','-m',label],'commit-'+label,path)
    common='_envops:\n  keep_trailing_newline: true\nproject_name:\n  type: str\n  default: UpdateSeed\n'
    if template.exists():
        if (template/'copier.yml').read_text(encoding='utf-8')!=common or (template/'README.md.jinja').read_text(encoding='utf-8')!='# {{ project_name }}\nversion=v1\n':
            raise RuntimeError('Unknown partial synthetic template')
        if command(['git','status','--porcelain'],'verify-partial-pristine',template)['output'].strip():
            raise RuntimeError('Partial template modified unexpectedly')
        if command(['git','log','-1','--format=%s'],'verify-partial-commit',template)['output'].strip()!='synthetic-template-v1':
            raise RuntimeError('Unknown partial template history')
    else:
        template.mkdir(parents=True)
        write(template/'copier.yml',common)
        write(template/'.copier-answers.yml.jinja','{{ _copier_answers | to_nice_yaml }}')
        write(template/'README.md.jinja','# {{ project_name }}\nversion=v1\n')
        initialize(template)
        commit(template,'synthetic-template-v1')
        command(['git','tag','v1.0.0'],'tag-v1',template)
    executable=Path(identity['path'])/('copier.exe' if os.name=='nt' else 'copier')
    command([executable,'copy','--defaults','--vcs-ref','v1.0.0','templates/update','updated'],'seed-upstream-v1',fixture)
    initialize(destination)
    commit(destination,'synthetic-generated-v1')
    write(destination/'local.txt','committed local customization\n')
    commit(destination,'synthetic-local-customization')
    write(template/'copier.yml',common+'support_level:\n  type: str\n  default: basic\n  help: Support level\n')
    write(template/'README.md.jinja','# {{ project_name }}\nversion=v2\nsupport={{ support_level }}\n')
    write(template/'new.txt.jinja','new file for {{ project_name }}\n')
    commit(template,'synthetic-template-v2')
    command(['git','tag','v2.0.0'],'tag-v2',template)
    dirty=package/'fixtures-dirty'
    if dirty.exists(): raise RuntimeError('Unknown dirty fixture destination')
    shutil.copytree(fixture,dirty)
    write(dirty/'updated/local.txt','uncommitted local change\n')
    with tarfile.open(archive,'w:gz') as tar:
        for path in [template/'.git',destination/'.git',dirty/'templates/update/.git',dirty/'updated/.git']:
            for member in sorted(path.rglob('*')):
                if member.is_symlink(): raise RuntimeError('Synthetic Git link refused')
                if member.is_file():
                    info=tar.gettarinfo(member,arcname=member.relative_to(package).as_posix())
                    info.uid=info.gid=info.mtime=0
                    info.uname=info.gname=''
                    with member.open('rb') as data: tar.addfile(info,data)
    if archive.stat().st_size>2*1024*1024:
        raise RuntimeError('Synthetic Git archive bound')
    config=json.loads((package/'scenarios.json').read_text(encoding='utf-8'))
    config['baseline_suffix_by_host']={'Linux':'-unix','Darwin':'-unix'}
    config['phase']='Twelve declared substantive flows; exact approved host variants required'
    config['cases'] += [dict(name='normal-git-update',kind='normal',
        purpose='Actual v1 to v2 template update with a new answer and preserved committed local file',
        command=['copier','update','--skip-answered','updated'],
        steps=[{'expect':'Support level'},{'key':'CtrlA'},{'key':'CtrlK'},{'text':'premium'},{'key':'Enter'},{'exit':0}],
        expected_files={'updated/README.md':'# UpdateSeed\nversion=v2\nsupport=premium\n',
            'updated/new.txt':'new file for UpdateSeed\n','updated/local.txt':'committed local customization\n',
            'neighbor.txt':'protected neighboring state\n'},absent_paths=[],timeout_ms=10000,
        timeout_ms_by_host={'Windows':20000}),
        dict(name='edge-dirty-update-refused',kind='edge',fixture='fixtures-dirty',
        purpose='Dirty Git project refuses update and preserves actual uncommitted local state',
        command=['copier','update','--skip-answered','updated'],
        steps=[{'expect':'Destination repository is dirty; cannot continue.'},{'exit':1}],
        expected_files={'updated/README.md':'# UpdateSeed\nversion=v1\n',
            'updated/local.txt':'uncommitted local change\n','neighbor.txt':'protected neighboring state\n'},
        absent_paths=['updated/new.txt'],timeout_ms=10000)]
    (package/'scenarios.json').write_text(json.dumps(config,indent=2)+'\n',encoding='utf-8')
    (package/'synthetic-git-identity.json').write_text(json.dumps(dict(
        archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        contents='Only synthetic Git metadata; generated templates and state are ordinary reviewed fixture files',
        author='synthetic@example.invalid',no_upstream_source=True),indent=2)+'\n',encoding='utf-8')
    print('Prepared actual synthetic v1/v2 Git update and independent dirty-update refusal')

if __name__=='__main__': main()
