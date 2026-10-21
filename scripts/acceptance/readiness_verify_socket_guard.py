"""Verify actual process-scoped offline archive commands and positive controls."""
import argparse
import asyncio
from pathlib import Path
import sys

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load


def require(value,message):
    if not value:
        raise RuntimeError(message)


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--canonical-archive',type=Path,required=True)
    parser.add_argument('--packet',type=Path)
    parser.add_argument('--check-only',action='store_true')
    args=parser.parse_args()
    base=args.packet.resolve(strict=True) if args.packet else RAW
    base.relative_to(RAW.resolve(strict=True))
    guard=base/'offline-guard'
    proof=load(guard/'verified.json')
    require(sha256(guard/'guard')==proof['binary_sha256'] and sha256(guard/'main.go')==proof['source_sha256']
            ==sha256(ROOT/'scripts/acceptance/readiness_socket_guard.go.txt'), 'actual socket policy source/binary differs')
    def witness(identity):
        events={k:load(base/'events'/(identity+'-'+k+'.json')) for k in ['started','identified','launched','finished']}
        require(all(e['id']==identity and e['event']==k and e['project']=='core' for k,e in events.items()), 'actual socket experiment identity differs')
        end=events['finished']
        require(end['category']=='passed' and end['harness_cleanup']=='harness_process_reaped' and not end['cleanup_errors'], 'guarded command or cleanup failed')
        ref=events['identified']['identity'];manifest=packet_file(base,ref['manifest'].replace('\\','/'),2*1024**2)
        require(sha256(manifest)==ref['sha256'] and sha256(base/'core'/identity/'console.log')==end['console_sha256'], 'guard command evidence changed')
        return events,load(manifest)['files']
    events,files=witness(proof['build_attempt'])
    require(files['artifacts/runner-readiness-ten-project-pass/offline-guard/main.go']==proof['source_sha256']
            and files['artifacts/runner-readiness-ten-project-pass/toolchain/go/bin/go']==proof['compiler_sha256'], 'actual guard build inputs differ')
    for name,expected in [('baseline','socket-created-and-closed; no connection attempted'),('guarded','socket-denied=EPERM')]:
        identity=proof['probes'][name];events,files=witness(identity)
        require(files['artifacts/runner-readiness-ten-project-pass/offline-guard/guard']==proof['binary_sha256']
                and events['finished']['exit_code']==0 and (base/'core'/identity/'console.log').read_text().strip()==expected,
                'socket policy positive control differs')
    roots=[p for p in (base/'archive-experience').glob('*/experience.json') if load(p).get('socket_guard')]
    require(len(roots)==1,'one actual guarded archive experience required')
    root=roots[0].parent;receipt=load(roots[0]);policy=receipt['socket_guard']
    require(receipt['host']=='linux' and receipt['architecture']=='amd64' and policy['sha256']==proof['binary_sha256'], 'offline proof is native Linux amd64 only')
    labels=set(receipt['attempts'])-{n for n in receipt['attempts'] if n.startswith('fixture-build-')}
    require(len(labels)==16 and set(policy['receipts'])==labels and {'record','current-clean','current-reads-previous-report'}<=labels,
            'required public commands did not all use the socket policy')
    rows=[]
    for label in sorted(labels):
        events,files=witness(receipt['attempts'][label])
        relative=policy['receipts'][label]
        prefix='artifacts/runner-readiness-ten-project-pass/'
        require(relative.startswith(prefix),'applied policy receipt escapes campaign')
        path=packet_file(base,relative.removeprefix(prefix),65536);actual=load(path)
        selected='previous' if label.startswith('previous-') else 'rollback' if label.startswith('rollback-') else 'current'
        require(actual['filter_applied'] is True and actual['architecture']=='linux-amd64'
                and actual['denied_syscalls']==['socket','socketpair','connect']
                and actual['pid']==events['launched']['pid']
                and actual['target_sha256']==receipt['installed_binary_sha256'][selected]
                and files[policy['binary']]==proof['binary_sha256'], 'actual applied socket policy or exec target differs')
        rows.append(dict(label=label,attempt=receipt['attempts'][label],policy_sha256=sha256(path),
            applied_to_actual_pid=True,target_sha256=actual['target_sha256']))
    argv=[sys.executable,ROOT/'scripts/acceptance/readiness_verify_archive_experience.py','--series','migration-v2',
          '--id',root.name,'--check-only','--canonical-archive',args.canonical_archive]
    if args.packet:argv+=['--packet',base]
    checked=await execute(argv,'core','offline-independent-archive-outcomes',timeout=120,campaign=Campaign())
    if not args.check_only:
        immutable_json(guard/'application-verified.json',dict(experience=root.name,
            experience_sha256=sha256(root/'experience.json'),guard_source_sha256=proof['source_sha256'],
            guard_binary_sha256=proof['binary_sha256'],guard_control_sha256=sha256(guard/'verified.json'),
            archive_outcomes_audit=checked['id'],actual_guarded_commands=rows,
            scope='Actual native Linux amd64 source-free record/test/report and upgrade/rollback commands succeeded under a per-process inherited socket/socketpair/connect refusal. Positive baseline socket creation and actual guarded EPERM are recorded separately. No firewall or host setting was changed. No OS-level network isolation, adversarial sandbox or macOS/Windows offline coverage is claimed.',
            final_archive_credit=0))
    print('Verified sixteen actual public archive commands under the applied socket policy and all nineteen archive journey outcomes.')


if __name__=='__main__':asyncio.run(main())
