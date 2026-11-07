"""Curate full Git Town V20 packets without losing independently checked identity."""
import json
import hashlib
import os
from pathlib import Path
import zipfile

from git_town_artifact_audit import read_archive, require
from readiness_evidence import immutable_json, sha256

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / 'artifacts/runner-readiness-next-twenty-project-pass'
DOC = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass'


def sha256_bytes(body):
    return hashlib.sha256(body).hexdigest()


def curate_final_packet(files, host, output, source_sha256):
    rows = []
    kept = 0
    with zipfile.ZipFile(output, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for name in sorted(files):
            reason = None
            if '/retained-source/fault-binaries/' in name:
                reason = 'native binaries independently hash-checked against build/launch receipts by V20 auditor; per-binary hashes retained in the complete index'
            elif host == 'windows' and '/retained-source/src/' in name:
                reason = 'canonical pinned source payload retained once in the Linux packet'
            elif host == 'windows' and name.startswith('docs/validation/'):
                reason = 'tracked qualification documents retained once in the Linux packet'
            row = dict(path=name, bytes=len(files[name]), sha256=sha256_bytes(files[name]), retained=reason is None)
            if reason:
                row['omitted_after_independent_verification'] = reason
            else:
                archive.writestr(name, files[name])
                kept += 1
            rows.append(row)
        index = dict(schema_version=1, project='git-town', host=host,
            provider_archive_sha256=source_sha256, provider_members=len(files),
            retained_members=kept, omitted_members=len(files)-kept,
            scope='Complete original-provider member path/size/SHA index. Final reports, planned case contracts, summaries, pinned source/provenance, fault receipts/events and cleanup evidence are retained. Rebuilt native fault binaries are omitted after the V20 independent auditor verified them against build and launch receipts.',
            members=rows)
        archive.writestr('retention-index-v1.json', json.dumps(index, ensure_ascii=True, sort_keys=True,
            separators=(',', ':')).encode('utf-8'))
    return dict(bytes=os.path.getsize(output), retained_members=kept, indexed_members=len(rows))


def main():
    audit = json.loads((DOC / 'git-town/final-series-audit-v20.json').read_text(encoding='utf-8'))
    staging = RAW / 'tmp/git-town-final-v20-staging'
    destination = RAW / 'retained/git-town-final-v20-v2'
    require(staging.is_dir() and not staging.is_symlink() and destination.is_dir() and not destination.is_symlink(),
            'owned staging/retention roots are missing or linked')
    rows = []
    for cell in audit['hosts']:
        host = cell['host']
        archive_path = staging / f'{host}.zip'
        require(archive_path.is_file() and not archive_path.is_symlink(), 'verified provider packet is missing')
        require(archive_path.stat().st_size == cell['artifact_bytes'] and sha256(archive_path) == cell['artifact_sha256'],
                'provider artifact size/SHA differs from immutable V20 audit')
        payload = archive_path.read_bytes()
        files = read_archive(payload)
        require(len(files) == cell['artifact_members'] and sum(map(len, files.values())) == cell['expanded_bytes'],
                'provider archive bounded readback differs from the recorded inventory')
        output = destination / f'{host}-evidence-v1.zip'
        curated = curate_final_packet(files, host, output, cell['artifact_sha256'])
        require(curated['bytes'] <= 50 * 1024 * 1024, 'one host retention packet exceeds reserved headroom')
        index_digest = None
        with zipfile.ZipFile(output) as retained:
            names = retained.namelist()
            require(len(names) == curated['retained_members'] + 1 and len(set(names)) == len(names),
                    'curated member count or uniqueness differs')
            index = json.loads(retained.read('retention-index-v1.json'))
            index_digest = sha256_bytes(retained.read('retention-index-v1.json'))
            require(index['provider_archive_sha256'] == cell['artifact_sha256'] and
                    index['provider_members'] == cell['artifact_members'] and
                    index['retained_members'] == curated['retained_members'] and
                    len(index['members']) == cell['artifact_members'], 'retention index coverage differs')
            rows_by_path = {r['path']: r for r in index['members']}
            require(set(rows_by_path) == set(files), 'retention index lost or invented provider paths')
            for name in names:
                if name == 'retention-index-v1.json':
                    continue
                item = rows_by_path[name]
                body = retained.read(name)
                require(item['retained'] is True and len(body) == item['bytes'] and sha256_bytes(body) == item['sha256'],
                        'curated packet member failed exact readback')
            selected = next((n for n in names if n.endswith('/final-execution-summary.json')), None)
            require(selected is not None, 'final execution summary is not retained')
            require(sha256_bytes(retained.read(selected)) == rows_by_path[selected]['sha256'],
                    'selected final summary restore failed')
        rows.append(dict(host=host, provider_sha256=cell['artifact_sha256'], provider_bytes=cell['artifact_bytes'],
            provider_members=cell['artifact_members'], expanded_bytes=cell['expanded_bytes'],
            retained_packet=output.relative_to(RAW).as_posix(), retained_sha256=sha256(output),
            retained_bytes=curated['bytes'], retained_members=curated['retained_members'],
            omitted_members=curated['indexed_members'] - curated['retained_members'],
            retention_index='retention-index-v1.json', retention_index_sha256=index_digest))
        del files, payload
    require(sum(row['retained_bytes'] for row in rows) <= 50 * 1024 * 1024,
            'combined project retention exceeds reserved headroom')
    immutable_json(destination / 'readback-v1.json', dict(schema_version=1, project='git-town',
        source_audit='git-town/final-series-audit-v20.json', hosts=rows,
        combined_retained_bytes=sum(row['retained_bytes'] for row in rows),
        scope='Provider ZIPs matched original GitHub size/SHA, passed bounded full-member CRC/path checks, were curated with a complete omission/retention index, and every retained member was hash-checked after write. Full provider ZIPs remain in task-owned tmp staging until native checked cleanup.'))
    print('Git Town V20 retention readback passed:', [(r['host'], r['retained_bytes']) for r in rows],
          'combined', sum(row['retained_bytes'] for row in rows))


if __name__ == '__main__':
    main()
