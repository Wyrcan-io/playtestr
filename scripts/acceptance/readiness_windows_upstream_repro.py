"""Bounded original-pin Windows race investigation; never application admission."""
import argparse
import asyncio
import json
import os
from pathlib import Path
import shutil
import sys

from adversarial_process import execute
from readiness_acquire_plop import extract_source
from readiness_build_rclone import environment
from readiness_build_plop import usage
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import runner
from readiness_new_control_matrix import read_json as load


class Investigation(Campaign):
    def __init__(self, target, tools):
        super().__init__()
        self.target, self.tools = target, tools

    def identity(self, project, argv):
        inputs = [p for p in (self.target/'src').rglob('*') if p.is_file()]
        inputs += [self.target/'task-owned.json', *self.tools]
        binary = self.target/'bin/target.exe'
        if binary.exists():
            inputs.append(binary)
        return super().identity(project, [*argv, *inputs])


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', choices=['superfile', 'glow'], required=True)
    parser.add_argument('--phase', choices=['prepare', 'build', 'run', 'startup', 'logged'], required=True)
    args = parser.parse_args()
    if os.name != 'nt':
        raise RuntimeError('native Windows investigation only')
    project = args.project
    slug = 'r3-windows-'+project
    target = RAW/'active'/slug
    docs = ROOT/'docs/validation/runner-readiness-ten-project-pass'
    review = load(docs/'old-migration'/project/'source-review.json')
    canonical = RAW/('old-'+project)/'retained-source/source.tar.gz'
    if sha256(canonical) != review['archive_sha256']:
        raise RuntimeError('canonical reviewed original source changed')
    owner = dict(workspace=str(ROOT), campaign='runner-readiness-ten-project-pass',
                 project=review['repository'], pin=review['pin'], scope='R3-04 diagnostic only')
    if args.phase == 'prepare':
        if any((RAW/'active').iterdir()):
            raise RuntimeError('another local application is active')
        target.mkdir()
        immutable_json(target/'task-owned.json', owner)
        omitted = None
        if project == 'superfile':
            omitted = load(docs/'old-migration'/project/'source-acquisition-review.json')['omitted_links']
        extract_source(canonical.read_bytes(), target/'src', expanded_limit=192*1024**2,
                       entry_limit=25000, member_limit=8*1024**2, omitted_links=omitted)
        immutable_json(target/'declaration.json', dict(project=project, pin=review['pin'],
            canonical_archive_sha256=sha256(canonical), source_review_sha256=sha256(docs/'old-migration'/project/'source-review.json'),
            schedule='At most ten unchanged real-PTY attempts; stop at the first target race, failed outcome or unconfirmed cleanup.',
            build='Read-only installed Go1.27.0 and existing project-local GCC; direct -race build, no installer/generator hooks.',
            ordinary_deadlines='Original spec deadlines; each independent command bounded to 150 seconds.',
            scope='Current diagnostic observations do not explain every old failure or qualify Windows application compatibility.'))
        print('Prepared reviewed original source for Windows race diagnosis:', project)
        return
    if load(target/'task-owned.json') != owner:
        raise RuntimeError('investigation ownership differs')
    actual = {p.relative_to(target/'src').as_posix(): sha256(p) for p in (target/'src').rglob('*') if p.is_file()}
    if actual != review['reviewed_inputs']:
        raise RuntimeError('reviewed original source changed')
    go = Path(shutil.which('go')).resolve(strict=True)
    gcc = ROOT/'.tools/winlibs/mingw64/bin/gcc.exe'
    env = environment(target)
    env.update(CGO_ENABLED='1', CC=str(gcc), PATH=str(gcc.parent)+os.pathsep+env['PATH'])
    campaign = Investigation(target, [go, gcc])
    async def call(label, argv, timeout=30):
        return await execute(argv, slug, label, env=env, cwd=ROOT,
                             timeout=timeout, campaign=campaign)
    if args.phase == 'build':
        version = await call('readonly-go-version', [go, 'version'])
        if 'go1.27.0 windows/amd64' not in version['output']:
            raise RuntimeError('unreviewed Go compiler version')
        await call('readonly-gcc-version', [gcc, '--version'])
        binary = target/'bin/target.exe'
        binary.parent.mkdir(exist_ok=True)
        operation=asyncio.create_task(call('original-native-race-build',
            [go, '-C', target/'src', 'build', '-race', *review['build_flags'], '-o', binary, '.'], 900))
        sizes=[]
        try:
            while not operation.done():
                size=await asyncio.to_thread(usage,target)
                sizes.append(size)
                if size>review['active_stop_mib']*1024**2:
                    raise RuntimeError('owned diagnostic build storage stop')
                await asyncio.sleep(2)
            built=await operation
        finally:
            if not operation.done():
                operation.cancel()
                try:
                    await operation
                except asyncio.CancelledError:
                    pass
            immutable_json(target/'build-storage.json',dict(observed_bytes=sizes,
                scope='Periodic logical bytes; not exact peak or an OS quota.'))
        immutable_json(target/'build.json', dict(attempt=built['id'], pin=review['pin'],
            binary_sha256=sha256(binary), go=str(go), go_sha256=sha256(go), gcc_sha256=sha256(gcc), race=True))
        return
    build = load(target/'build.json')
    if sha256(target/'bin/target.exe') != build['binary_sha256']:
        raise RuntimeError('diagnostic binary changed')
    if args.phase == 'startup':
        env['GORACE'] = 'halt_on_error=1 exitcode=66'
        outcome = await execute([target/'bin/target.exe', *review.get('version_arguments', ['-version'])],
            slug, 'independent-direct-startup-race', env=env, cwd=target, timeout=30,
            expected=66, campaign=campaign)
        if 'WARNING: DATA RACE' not in outcome['output']:
            raise RuntimeError('exit66 alone does not prove a race report')
        immutable_json(target/'startup-race.json', dict(attempt=outcome['id'],
            binary_sha256=build['binary_sha256'], race_report=True,
            scope='Direct startup diagnosis; separate from real-PTY input attempt and historical unlogged causes.'))
        print(outcome['output'][-10000:])
        return
    original = ROOT/'docs/validation/ten-new-project-adversarial-pass'/project
    name = 'normal-panel-copy' if project == 'superfile' else 'normal-project'
    source_spec = original/(name+'.json')
    spec = load(source_spec)
    package = target/('logged-package' if args.phase == 'logged' else 'package')
    package.mkdir()
    shutil.copytree(original/spec['workspace']['fixture'], package/spec['workspace']['fixture'])
    shutil.copytree(original/'snapshots', package/'snapshots')
    spec['command'][0] = str(target/'bin/target.exe')
    # Race diagnostics go through the real target's terminal/stderr; no outside log path.
    spec.setdefault('env', {})['GORACE'] = 'halt_on_error=1 exitcode=66'+(' log_path=.diagnostic-race-log' if args.phase == 'logged' else '')
    contract = package/(name+'.json')
    immutable_json(contract, spec)
    binary, frozen, cell = runner('migration-v2')
    records = []
    if args.phase == 'logged':
        immutable_json(target/'logged-declaration.json', dict(
            attempts=3, reason='Separate bounded log-capture diagnosis after the initial terminal viewport retained only the tail of a race stack. Direct version probe did not reproduce (exit0); it remains a failed expected66 experiment.',
            variation='GORACE writes a relative log in the owned managed fixture; retain failed workspace explicitly for evidence. Original actions and deadlines unchanged.',
            no_qualification_credit=True))
    for repetition in range(3 if args.phase == 'logged' else 10):
        label=('logged-' if args.phase == 'logged' else '')+str(repetition)
        report = target/('attempt-'+label+'.json')
        try:
            result = await call('original-input-race-'+label,
                [binary, 'test', *(['--keep-workspace-on-failure'] if args.phase == 'logged' else []),
                 '--report', report, '--artifacts-dir', target/('evidence-'+label), contract], 150)
            identity = result['id']
        except RuntimeError as error:
            identity = getattr(error, 'evidence_id', None)
            if not identity or not report.exists():
                raise
        row = load(report)['results'][0]
        record = dict(repetition=repetition, attempt=identity, status=row['status'],
                      report_sha256=sha256(report), cleanup=row['cleanup'], workspace=row.get('workspace'))
        records.append(record)
        if args.phase == 'logged' and row['status'] != 'passed':
            retained=Path(row['workspace']['retained_path']).resolve(strict=True)
            retained.relative_to((target/'tmp').resolve(strict=True))
            logs=[]
            for path in retained.rglob('.diagnostic-race-log.*'):
                if path.is_symlink() or path.stat().st_size>4*1024**2:
                    raise RuntimeError('unsafe diagnostic race log')
                destination=target/('captured-'+path.name)
                shutil.copyfile(path,destination)
                logs.append(dict(path=destination.name,sha256=sha256(destination)))
            record['race_logs']=logs
        if not row['cleanup'].get('confirmed_exited') or not (row.get('workspace', {}).get('cleaned') or
                (args.phase=='logged' and row['workspace'].get('retained'))):
            raise RuntimeError('diagnostic target/workspace cleanup unconfirmed')
        if row['status'] != 'passed':
            break
    immutable_json(target/('logged-observations.json' if args.phase=='logged' else 'observations.json'), dict(project=project, pin=review['pin'],
        original_spec_sha256=sha256(source_spec), executed_spec_sha256=sha256(contract),
        binary_sha256=build['binary_sha256'], runner_sha256=cell['binary_sha256'], records=records,
        scope='Diagnostic race-instrumented target; no application or final-archive credit. Inspect actual race stack before causal disposition.'))
    print('Bounded original-pin Windows observations:', project, len(records))


if __name__ == '__main__':
    asyncio.run(main())
