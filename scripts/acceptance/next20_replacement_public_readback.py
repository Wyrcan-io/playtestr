"""Bind105 audited public reexecutions to candidate and retained-packet hashes separately."""
import json
import tarfile

from next20_check import RAW,ROOT,DOC
from readiness_compact_native import verify
from readiness_evidence import immutable_json,sha256


def main():
    freeze_path=DOC/'replacement-candidate-freeze-native-exit-v1.json';freeze=json.loads(freeze_path.read_text());cells=[]
    for host,generation,label in [('linux',7,'Linux'),('darwin',8,'macOS'),('windows',9,'Windows')]:
        candidate=next(r for r in freeze['cells'] if r['host']==host)
        retained=RAW/'product-controls'/('retained-native-v'+str(generation));index_path=retained/'index.json'
        index=json.loads(index_path.read_text());archive=retained/'packets.tar.gz'
        audit_path=retained/'public-control-audit.json';audit=json.loads(audit_path.read_text())
        removed_path=retained/'expanded-removed.json';removed=json.loads(removed_path.read_text(encoding='utf-8-sig'))
        if sha256(index_path)!=audit['index_sha256'] or sha256(archive)!=index['archive_sha256'] or sha256(archive)!=audit['archive_sha256']:
            raise ValueError('retained public-control archive/index/audit changed')
        if not removed['all_expanded_removed'] or removed['index_sha256']!=sha256(index_path) or removed['archive_sha256']!=sha256(archive):raise ValueError('checked expansion removal missing')
        if audit['run']!='40428498259' or audit['revision']!='83f8950c9b512da8e19b88ef502dda39d6369f9f' or audit['public_reexecutions']!=35 or audit['runner_sha256']!=candidate['binary_sha256']:raise ValueError('wrong public-control native qualification')
        verify(archive,index['files']);prefix='native/40428498259/next20-archive-controls-'+label+'/'
        with tarfile.open(archive,'r:gz') as stream:
            def read(name):
                row=index['files'][name];return json.loads(stream.extractfile(row.get('member',name)).read(row['bytes']+1))
            installed=read(prefix+'candidate-native-exit-v1/'+host+'/installed.json')
            results=[n for n in index['files'] if n.startswith(prefix+'product-controls/') and n.endswith('/results.json')]
            if len(results)!=1:raise ValueError('missing/ambiguous completed public-control run')
            result=read(results[0]);build=read(results[0].removesuffix('results.json')+'build.json')
            if result['observed']!=35 or len(result['controls'])!=35:raise ValueError('incomplete actual public control outcomes')
            for value in [installed,result,build]:
                if value.get('binary_sha256',value.get('runner_sha256'))!=candidate['binary_sha256'] or value['archive_sha256']!=candidate['archive_sha256']:
                    raise ValueError('actual installed/build/result candidate identities differ')
        cells.append(dict(host=host,run=audit['run'],qualification_revision=audit['revision'],public_reexecutions=35,
            candidate_archive_sha256=candidate['archive_sha256'],candidate_binary_sha256=candidate['binary_sha256'],
            retained_archive_sha256=sha256(archive),retained_index_sha256=sha256(index_path),
            independent_audit_sha256=sha256(audit_path),checked_removal_sha256=sha256(removed_path),
            retained_generation=generation,retained_local_only=retained.relative_to(ROOT).as_posix()))
    immutable_json(DOC/'replacement-public-controls-readback.json',dict(schema_version=1,candidate_series='native-exit-v1',
        candidate_freeze_sha256=sha256(freeze_path),cells=cells,total_public_reexecutions=105,
        project_credits=0,new_unique_whole_control_credits=0,
        scope='Fresh actual35 public controls per exact native archive, independently audited before compaction and read back from fully verified retained packets after checked cleanup. Raw public-control audit archive_sha256 denotes the retention packet; candidate archive hashes are separately bound here from actual installed/build/result payloads.'))
    print('Read back105 actual audited controls; exact candidate and retained-packet hashes separately bound.')


if __name__=='__main__':main()
