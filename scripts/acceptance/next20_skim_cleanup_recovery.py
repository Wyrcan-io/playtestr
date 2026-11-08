"""Prepare and audit the later local Skim tree that postdated its first removal."""
import argparse
import json
from pathlib import Path

from next20_check import DOC, RAW, ROOT
from next20_target_cleanup import source_inventory, target_inventory
from readiness_evidence import immutable_json, sha256


PROJECT = DOC / 'skim'
TARGET = RAW / 'active' / 'skim'
PACKAGE = DOC / 'skim'
PREPARED = PACKAGE / 'local-residual-cleanup-v1-prepared.json'
REMOVED = PACKAGE / 'local-residual-cleanup-v1-removed.json'
PROOF = RAW / 'skim' / 'process-proof-final-cleanup.json'


def snapshot():
    """Bind every remaining byte to retained pinned source and V22 evidence."""
    for path in (ROOT / 'artifacts', RAW, RAW / 'active', TARGET, RAW / 'skim'):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('linked Skim recovery ancestor')
    if TARGET.resolve(strict=True) != (RAW / 'active' / 'skim').resolve(strict=True):
        raise ValueError('Skim recovery root changed')
    owner = json.loads((TARGET / 'task-owned.json').read_text(encoding='utf-8'))
    acquisition = json.loads((TARGET / 'acquisition.json').read_text(encoding='utf-8'))
    provenance_path = PACKAGE / 'source-provenance.json'
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))
    archive = TARGET / 'source.tar.gz'
    if (owner.get('workspace') != str(ROOT) or owner.get('campaign') != 'runner-readiness-next-twenty-project-pass' or
            owner.get('slug') != 'skim' or acquisition.get('pin') != provenance.get('pin') or
            acquisition.get('archive_sha256') != sha256(archive) or acquisition.get('source_files') != provenance.get('files')):
        raise ValueError('restored Skim owner/archive differs from retained provenance')
    if source_inventory(TARGET / 'src') != provenance['files']:
        raise ValueError('restored Skim source differs from all 819 retained hashes')
    build_path = TARGET / 'build.json'
    build = json.loads(build_path.read_text(encoding='utf-8'))
    binary = TARGET / build['binary_relative_path']
    if build.get('pin') != provenance['pin'] or sha256(binary) != build.get('binary_sha256'):
        raise ValueError('Skim executable differs from retained build identity')

    attempts_path = PACKAGE / 'candidate-native-attempts-v11.json'
    attempts = json.loads(attempts_path.read_text(encoding='utf-8'))
    if (attempts.get('workflow_run_id') != 42440742894 or attempts.get('new_qualification_credit') != 0 or
            any(h.get('target_cleanup', '').find('owned target removal') < 0 for h in attempts.get('hosts', []))):
        raise ValueError('hosted Skim final cleanup evidence is incomplete')

    local_receipt_path = PACKAGE / 'local-residual-case-evidence-v1.json'
    local_receipt = json.loads(local_receipt_path.read_text(encoding='utf-8'))
    original = {p.relative_to(TARGET / 'case-evidence').as_posix(): sha256(p)
                for p in (TARGET / 'case-evidence').rglob('*') if p.is_file()}
    retained_root = PACKAGE / 'local-residual-case-evidence-v1'
    retained = {p.relative_to(retained_root).as_posix(): sha256(p)
                for p in retained_root.rglob('*') if p.is_file()}
    if len(original) != 6 or original != retained or local_receipt.get('files') != original:
        raise ValueError('post-removal local Skim reports were not retained byte-identically')

    proof = json.loads(PROOF.read_text(encoding='utf-8-sig'))
    if (proof.get('owned_target') != str(TARGET) or proof.get('confirmed_no_matching_live_processes') is not True or
            proof.get('matching_live_processes') != []):
        raise ValueError('fresh native Skim process proof missing or failed')
    inventory = target_inventory(TARGET, max_files=40000, max_bytes=1024**3)
    if inventory['owned_links']:
        raise ValueError('unexpected linked Skim cleanup entry')
    non_source = {name: row for name, row in inventory['files'].items() if not name.startswith('src/')}
    return dict(schema_version=1, project='skim', pin=provenance['pin'],
        owned_relative_path='active/skim', source_provenance_sha256=sha256(provenance_path),
        acquisition_sha256=sha256(TARGET / 'acquisition.json'), source_archive_sha256=sha256(archive),
        owner_sha256=sha256(TARGET / 'task-owned.json'), source_blobs_verified=len(provenance['files']),
        process_proof_sha256=sha256(PROOF), final_series_attempts_sha256=sha256(attempts_path),
        local_report_retention_sha256=sha256(local_receipt_path),
        source_file_count=len(provenance['files']), other_file_count=len(non_source),
        other_total_bytes=sum(row['bytes'] for row in non_source.values()),
        other_files=non_source, whole_target_file_count=len(inventory['files']),
        whole_target_total_bytes=inventory['total_bytes'], removed_links=[])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'verify', 'finalize'])
    args = parser.parse_args()
    if args.action == 'prepare':
        if PREPARED.exists():
            raise ValueError('preserve existing Skim recovery cleanup preparation')
        record = snapshot()
        immutable_json(PREPARED, record)
        print('Prepared exact Skim residual cleanup:', record['whole_target_file_count'], 'files,',
              record['whole_target_total_bytes'], 'bytes.')
    elif args.action == 'verify':
        expected = json.loads(PREPARED.read_text(encoding='utf-8'))
        actual = snapshot()
        if actual != expected:
            raise ValueError('Skim tree or cleanup evidence changed after preparation')
        print('Reverified exact Skim target and all retained source/process/fault evidence.')
    else:
        if TARGET.exists():
            raise ValueError('Skim target remains after native PowerShell removal')
        prepared = json.loads(PREPARED.read_text(encoding='utf-8'))
        proof = json.loads(PROOF.read_text(encoding='utf-8-sig'))
        if proof.get('confirmed_no_matching_live_processes') is not True or proof.get('matching_live_processes') != []:
            raise ValueError('Skim process proof failed during finalization')
        immutable_json(REMOVED, dict(schema_version=1, project='skim', removed=True,
            owned_relative_path='active/skim', prepared_sha256=sha256(PREPARED),
            process_proof_sha256=sha256(PROOF), final_series_attempts_sha256=prepared['final_series_attempts_sha256'],
            local_report_retention_sha256=prepared['local_report_retention_sha256'],
            source_restored_exact=True, target_absent=True))
        print('Finalized checked Skim target removal receipt.')


if __name__ == '__main__':
    main()
