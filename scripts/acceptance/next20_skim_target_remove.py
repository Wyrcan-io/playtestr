"""Remove Skim's target only after independently rechecking its cleanup receipt."""
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from next20_check import RAW
from next20_target_cleanup import prepare_native_directory_permissions, target_inventory, source_inventory
from readiness_evidence import immutable_json, sha256


def remove():
    target = RAW / 'active' / 'skim'
    retained = RAW / 'skim' / 'retained-source'
    package = Path('docs/validation/runner-readiness-next-twenty-project-pass/skim')
    provenance_path = package / 'source-provenance.json'
    prepared_path = retained / 'prepared.json'
    inventory_path = retained / 'cleanup-inventory.json'
    proof_path = RAW / 'skim' / 'process-proof.json'

    for path in (RAW, RAW / 'active', target, RAW / 'skim', retained):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('linked Skim removal ancestor')
    if target.resolve(strict=True) != (RAW / 'active' / 'skim').resolve(strict=True):
        raise ValueError('Skim target identity changed')
    prepared = json.loads(prepared_path.read_text(encoding='utf-8'))
    inventory = json.loads(inventory_path.read_text(encoding='utf-8'))
    proof = json.loads(proof_path.read_text(encoding='utf-8'))
    owner_path = target / 'task-owned.json'
    owner = json.loads(owner_path.read_text(encoding='utf-8'))
    provenance = json.loads(provenance_path.read_text(encoding='utf-8'))

    if (prepared.get('removed') is not False or prepared.get('source_restored_exact') is not True or
            prepared.get('source_archive_sha256') != sha256(target / 'source.tar.gz') or
            prepared.get('cleanup_inventory_sha256') != sha256(inventory_path) or
            prepared.get('process_proof_sha256') != sha256(proof_path)):
        raise ValueError('Skim prepared removal receipt is stale or incomplete')
    if (inventory.get('project') != 'skim' or inventory.get('owned_target') != str(target) or
            inventory.get('owner_sha256') != sha256(owner_path) or
            inventory.get('process_proof_sha256') != sha256(proof_path) or
            inventory.get('source_restored_exact') is not True or
            (inventory.get('actual_reports_with_confirmed_cleanup') == 0 and inventory.get('no_case_evidence') is not True)):
        raise ValueError('Skim cleanup inventory is not a no-case verified receipt')
    if (owner.get('workspace') != str(Path.cwd()) or
            owner.get('campaign') != 'runner-readiness-next-twenty-project-pass' or owner.get('slug') != 'skim'):
        raise ValueError('foreign Skim target ownership marker')
    if (proof.get('owned_target') != str(target) or
            proof.get('confirmed_no_matching_live_processes') is not True or
            proof.get('matching_live_processes') != []):
        raise ValueError('Skim process proof is missing or failed')
    acquisition = json.loads((target / 'acquisition.json').read_text(encoding='utf-8'))
    if acquisition.get('pin') != provenance.get('pin') or acquisition.get('source_files') != provenance.get('files'):
        raise ValueError('Skim source acquisition differs from reviewed provenance')
    if source_inventory(target / 'src') != provenance['files']:
        raise ValueError('Skim source differs from the exact pinned source manifest')

    max_files = inventory.get('max_files', 40000)
    max_bytes = inventory.get('max_bytes', 1024**3)
    current = target_inventory(target, max_files=max_files, max_bytes=max_bytes)
    expected = {key: inventory[key] for key in ('files', 'owned_links', 'total_bytes')}
    if current != expected:
        raise ValueError('Skim target changed after cleanup preparation')
    for relative in current['owned_links']:
        (target / Path(relative)).unlink()
    changed = prepare_native_directory_permissions(target, RAW / 'active')
    shutil.rmtree(target)
    if target.exists():
        raise ValueError('Skim target remains after checked removal')
    immutable_json(retained / 'removed.json', dict(
        schema_version=1, removed=True, owned_relative_path='active/skim',
        cleanup_inventory_sha256=sha256(inventory_path), source_restored_exact=True,
        process_proof_sha256=sha256(proof_path), native_directory_permissions_prepared=changed,
        checked_at_utc=datetime.now(timezone.utc).isoformat()))
    print('Removed Skim target after exact source, process, ownership, and prepared-inventory checks.')


if __name__ == '__main__':
    remove()
