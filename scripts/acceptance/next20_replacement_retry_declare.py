"""Bind the test-only retry source and remaining native budget before dispatch."""
import json
import subprocess
from datetime import datetime

from next20_check import ROOT,RAW,DOC
from readiness_evidence import immutable_json


def tree(revision):
    data=subprocess.check_output(['git','ls-tree','-r',revision],cwd=ROOT,timeout=30).decode()
    return {line.split('\t',1)[1]:line.split('\t',1)[0].split()[2] for line in data.splitlines()}


def main():
    original='515ffc3612f9bf4c53a4e26f0baafee1c48dcf89'
    revised='24029291cd0221d7611f07d27b464ec0936a815f'
    def selected(name):
        return name.endswith('.go') or name.startswith('schema/') and name.endswith('.json') or name in {'go.mod','go.sum','README.md','LICENSE','THIRD_PARTY_NOTICES.md'}
    old={n:h for n,h in tree(original).items() if selected(n)}
    new={n:h for n,h in tree(revised).items() if selected(n)}
    changed=sorted(n for n in set(old)|set(new) if old.get(n)!=new.get(n))
    if changed!=['internal/setupaction/install_integration_test.go']:raise ValueError('retry changes more than the reviewed fixture')
    if {n:h for n,h in old.items() if not n.endswith('_test.go')}!={n:h for n,h in new.items() if not n.endswith('_test.go')}:
        raise ValueError('production/package inputs changed; completed Mac archive cannot carry')
    provider=json.loads((RAW/'core/4a4210f3735b4a15b597a82d15db4312/console.log').read_text())
    seconds=sum((datetime.fromisoformat(j['completedAt'].replace('Z','+00:00'))-datetime.fromisoformat(j['startedAt'].replace('Z','+00:00'))).total_seconds() for j in provider['jobs'])
    allocated=3+(int(seconds)+59)//60+2*29
    if allocated>90:raise ValueError('retry ceiling exceeds original native allocation')
    immutable_json(DOC/'replacement-candidate-retry-v3.json',dict(schema_version=1,series='native-exit-v1',version='v0.4.0-rc.6',
        status='declared-before-two-host-retry',original_production_revision=original,retry_source_revision=revised,
        changed_source_inputs=changed,unchanged_production_package_git_blobs={n:h for n,h in old.items() if not n.endswith('_test.go')},
        source_equivalence='Git blob equality for every non-test Go file, all schemas, module files and packaged documents. Actual per-cell test/source revisions remain explicit; macOS is not relabelled.',
        preserved_mac_run='40420820491',preserved_mac_qualification_revision='dbb4d13cafb5ed834410788121ef98ca85937ac7',
        mac_archive_audit='replacement-native-darwin-40420820491.json',first_attempt_conservative_minutes=3,
        second_run_actual_job_seconds=seconds,second_run_conservative_minutes=(int(seconds)+59)//60,
        retry_hosts=['ubuntu-24.04','windows-2025'],retry_job_minutes_ceiling=29,retry_total_minutes_ceiling=58,
        maximum_parallel_jobs=2,aggregate_conservative_native_minutes=allocated,original_native_minutes_ceiling=90,
        automatic_harness_allocation='Separate original 15-minute per-push ceiling; wait for completion before native retry. Earlier legacy concurrency exception remains recorded.',
        local_controls='7d94d94986c34fe8996217052d08011c',project_credits=0,publication=False))
    print('Production/package inputs identical; changed one test fixture; conservative native minutes:',allocated,'of90')


if __name__=='__main__':main()
