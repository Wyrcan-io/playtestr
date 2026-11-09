"""Read the frozen first-batch storage baseline without rescanning its raw tree."""
import json

from readiness_evidence import sha256


def prior_campaign_usage(docs_root, workspace_root):
    """Return prior raw/retained/curated byte totals bound to reviewed receipts."""
    next_docs = docs_root
    old_docs = workspace_root / 'docs/validation/runner-readiness-ten-project-pass'
    checkpoint_path = next_docs / 'storage-checkpoint-v42.json'
    closing_path = old_docs / 'closing-storage.json'
    current_path = next_docs / 'storage-checkpoint-v43.json'
    current = json.loads(current_path.read_text(encoding='utf-8'))
    checkpoint = json.loads(checkpoint_path.read_text(encoding='utf-8'))
    closing = json.loads(closing_path.read_text(encoding='utf-8'))
    record = current.get('prior_campaign_snapshots', {})
    checkpoint_new = checkpoint['actual_bytes']['new_campaign_raw']
    checkpoint_combined = checkpoint['actual_bytes']['combined_raw']
    old_raw = checkpoint_combined - checkpoint_new
    if (record.get('v42_sha256') != sha256(checkpoint_path) or
            record.get('first_ten_closing_storage_sha256') != sha256(closing_path) or
            record.get('v42_new_raw_bytes') != checkpoint_new or
            record.get('v42_combined_raw_bytes') != checkpoint_combined or
            record.get('first_ten_raw_bytes') != old_raw or
            record.get('first_ten_retained_bytes') != closing['retained_bytes'] or
            record.get('first_ten_curated_bytes') != closing['curated_bytes'] or
            closing.get('active_projects') != []):
        raise ValueError('frozen prior-campaign storage baseline differs from its receipts')
    return dict(raw=old_raw, retained=closing['retained_bytes'], curated=closing['curated_bytes'])
