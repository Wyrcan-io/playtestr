"""Measure inherited Git discovery in a real public managed workspace."""
import asyncio
import os
from pathlib import Path
import shutil
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


async def main():
    git=shutil.which('git')
    if git is None:raise RuntimeError('read-only Git prerequisite missing')
    git=Path(git);original_git=sha256(git)
    root=RAW/'old-broot/git-discovery-calibration'/uuid.uuid4().hex
    fixture=root/'fixture';fixture.mkdir(parents=True)
    synthetic=root/'parent-repository';synthetic.mkdir()
    temporary=synthetic/'tmp';temporary.mkdir()
    env=dict(os.environ,TEMP=str(temporary),TMP=str(temporary),TMPDIR=str(temporary),
             GIT_CEILING_DIRECTORIES=str(temporary),GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull)
    initialized=await execute([git,'init','--quiet','--template=',synthetic],
        'core','git-managed-fixture-initialize-synthetic-parent',env=env,timeout=30,campaign=Campaign())
    binary,candidate,cell=runner('migration-v2');calls={}
    for label,inherit,code,text in [('ambient-parent',False,0,'true'),
                                  ('explicit-fixture-boundary',True,128,'fatal: not a git repository')]:
        contract=dict(version=3,name=label,command=[str(git),'rev-parse','--is-inside-work-tree'],
            workspace=dict(fixture='fixture',home='temporary',temp='temporary'),
            env=dict(LC_ALL='C',LANG='C',GIT_CONFIG_NOSYSTEM='1',GIT_CONFIG_GLOBAL=os.devnull),
            width=100,height=12,timeout_ms=3000,run_timeout_ms=15000,
            steps=[dict(expect=text),dict(exit=code),dict(state=dict(kind='absent',path='.git'))])
        if inherit:contract['inherit_env']=['GIT_CEILING_DIRECTORIES']
        spec=root/(label+'.json');report=root/(label+'-report.json');immutable_json(spec,contract)
        result=await execute([binary,'test','--report',report.relative_to(ROOT),'--artifacts-dir',
            (root/(label+'-evidence')).relative_to(ROOT),spec.relative_to(ROOT)],
            'core','git-managed-fixture-'+label,env=env,timeout=60,campaign=Campaign())
        row=load(report)['results'][0]
        if (row['status']!='passed' or row['target']['exit_code']!=code or not row['cleanup']['confirmed_exited']
                or not row['workspace']['cleaned'] or row['steps'][-1]['state']['invocation_id']!=row['invocation_id']):
            raise RuntimeError('Git boundary observation or same-run cleanup differs')
        calls[label]=dict(attempt=result['id'],report_sha256=sha256(report),spec_sha256=sha256(spec))
    if sha256(git)!=original_git:raise RuntimeError('read-only Git prerequisite changed')
    immutable_json(root/'verified.json',dict(calls=calls,synthetic_parent_setup=initialized['id'],git_sha256=original_git,runner_sha256=cell['binary_sha256'],
        provisional_archive_sha256=cell['archive_sha256'],
        result='An undeclared parent Git ceiling is filtered by the public contract, so owned temp placement beneath a checkout permits parent discovery. Explicit inherit_env passes the caller-defined ceiling and restores fixture-local discovery; exact exit128 and positive diagnostic are observed before cleanup.',
        scope='General explicit environment profile control, no Broot runtime or final-archive credit. No product behavior, original snapshots or expected files changed.'))
    print('Public real-PTY Git discovery control confirms explicit fixture boundary:',root.relative_to(ROOT))


if __name__=='__main__':asyncio.run(main())
