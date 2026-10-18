"""Bind seven earlier-project requalifications to checked retained native bytes."""
import argparse
import hashlib
import json
import tarfile

from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load

SOURCE = '3d50d81aae8f1d24f7a718e6e05b39069697b1a6'
PROJECTS = {'plop', 'poetry', 'rubygems', 'edit', 'vis', 'fff', 'papis'}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--entry', action='append', required=True,
                        help='project:run:generation, once for each earlier project')
    args = parser.parse_args()
    entries = [value.split(':') for value in args.entry]
    require(all(len(row) == 3 for row in entries), 'invalid requalification entry')
    require(len(entries) == 7 and {r[0] for r in entries} == PROJECTS,
            'exactly seven distinct earlier projects required')
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass'
    rows = []
    for project, run, generation in sorted(entries):
        require(run.isascii() and run.isdecimal() and generation.isascii()
                and generation.isdecimal() and 1 <= int(generation) <= 1000,
                'invalid run/generation')
        receipt = RAW / project / ('requalification-' + run + '.json')
        outcome = load(receipt)
        require(outcome['runner_source'] == SOURCE and len(outcome['cells']) == 2,
                'wrong source or incomplete project verification')
        retained = RAW / project / ('retained-native-v' + generation)
        index = load(retained / 'index.json', 4 * 1024**2)
        checked = load(retained / 'verified.json')
        removed = load(retained / 'expanded-removed.json')
        archive = retained / 'packets.tar.gz'
        require(index['project'] == project and index['generation'] == int(generation)
                and index['runs'] == [run], 'wrong retained native series')
        require(sha256(retained / 'index.json') == checked['index_sha256']
                and sha256(archive) == index['archive_sha256'] == checked['archive_sha256'],
                'retained archive identity changed')
        verify(archive, index['files'])
        require(removed['all_expanded_removed'] and removed['removed_runs'] == [run]
                and removed['archive_sha256'] == index['archive_sha256']
                and not (RAW / 'native' / run).exists(), 'expanded cleanup unconfirmed')
        with tarfile.open(archive, 'r:gz') as stream:
            name = 'native/' + run + '/run-metadata.json'
            record = index['files'][name]
            require(record['bytes'] <= 65536, 'run metadata bound')
            data = stream.extractfile(record.get('member', name)).read(65537)
            require(hashlib.sha256(data).hexdigest() == record['sha256'],
                    'retained run metadata changed')
            metadata = json.loads(data.decode('utf-8-sig'))
        require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success'
                and len(metadata['jobs']) == 2
                and all(j['status'] == 'completed' and j['conclusion'] == 'success'
                        for j in metadata['jobs']), 'native jobs not successful')
        expected_hosts = {'playtestr-Linux', 'playtestr-Windows' if project in
                          {'rubygems', 'edit', 'papis'} else 'playtestr-macOS'}
        require({c['host'] for c in outcome['cells']} == expected_hosts,
                'incorrect project/native boundary')
        for cell in outcome['cells']:
            require(cell['scenarios'] == 20 and cell.get('run', run) == run,
                    'wrong scenario count or cell run')
            prefix = 'native/' + run + '/' + cell['host'] + '/'
            for key in ['report_sha256', 'source_fault_summary_sha256',
                        'maintenance_sha256', 'cleanup_receipt_sha256']:
                require(any(name.startswith(prefix) and r['sha256'] == cell[key]
                            for name, r in index['files'].items()),
                        'independently verified payload absent from retained archive')
        rows.append(dict(project=project, run=run, cells=outcome['cells'],
                         requalification_sha256=sha256(receipt),
                         retention=dict(local_only_reference=retained.relative_to(ROOT).as_posix(),
                                        archive_sha256=sha256(archive),
                                        index_sha256=sha256(retained / 'index.json'),
                                        expanded_removed_receipt_sha256=sha256(retained / 'expanded-removed.json'))))
    # Validate every project before publishing any new immutable curated receipts.
    for row in rows:
        immutable_json(docs / row['project'] / 'requalification-3d50d81.json',
                       load(RAW / row['project'] / ('requalification-' + row['run'] + '.json')))
    immutable_json(docs / 'earlier-project-requalification-retention-3d50d81.json',
                   dict(schema_version=1, runner_source=SOURCE, projects=rows,
                        new_project_credit=0, new_native_cell_credit=0, final_archive_credit=0))
    print('Seven earlier projects independently requalified and retained at exact repaired source.')


if __name__ == '__main__':
    main()
