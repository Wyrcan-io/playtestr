"""Freeze Taskell's wrapped malformed-input oracle as a separate exact window."""
import json
from pathlib import Path
import shutil

from next20_check import DOC
from readiness_evidence import immutable_json, sha256


def freeze_revision():
    package = DOC/'taskell'
    source = package/'host-contracts'
    destination = package/'host-contracts-native-exit-v2'
    if not source.is_dir() or source.is_symlink():
        raise ValueError('Taskell canonical v1 contract root is missing or linked')
    for path in source.rglob('*'):
        if path.is_symlink() or getattr(path, 'is_junction', lambda: False)():
            raise ValueError('Taskell v1 contract tree contains a linked path')
    if destination.exists():
        raise ValueError('Taskell v2 contract destination already exists; preserve and audit it')
    shutil.copytree(source, destination)
    malformed_path = destination/'taskell-edge-e11-malformed.json'
    malformed = json.loads(malformed_path.read_text(encoding='utf-8'))
    if malformed['steps'][0].get('expect') != 'Could not parse file.':
        raise ValueError('Unexpected E11M base oracle; refusing to revise it')
    malformed['steps'][0]['expect'] = 'not parse file.'
    malformed_path.write_text(json.dumps(malformed, sort_keys=True, ensure_ascii=True, indent=2)+'\n',
                              encoding='utf-8', newline='\n')
    scenario_path = destination/'scenarios.json'
    scenarios = json.loads(scenario_path.read_text(encoding='utf-8'))
    rows = [row for row in scenarios['cases'] if row.get('id') == 'E11M']
    if len(rows) != 1:
        raise ValueError('Taskell v1 scenario catalog does not have exactly one E11M')
    revised_spec_sha = sha256(malformed_path)
    rows[0]['canonical_sha256'] = revised_spec_sha
    rows[0]['spec_sha256'] = revised_spec_sha
    scenario_path.write_text(json.dumps(scenarios, sort_keys=True, ensure_ascii=True, indent=2)+'\n',
                             encoding='utf-8', newline='\n')
    base_declaration_path = package/'final-series-declaration-native-exit-v1.json'
    declaration = json.loads(base_declaration_path.read_text(encoding='utf-8'))
    declaration['revision'] = 2
    declaration['canonical_contracts'] = destination.name
    declaration['canonical_test_freeze_sha256'] = sha256(scenario_path)
    declaration['supersedes'] = dict(path=base_declaration_path.name,
        sha256=sha256(base_declaration_path),
        reason='The provider-read-back Linux V35 report showed the full parser diagnostic wraps between “Could” and “ld” at the canonical 80-column viewport. The revised assertion checks the stable rendered suffix “not parse file.” while preserving the exact exit-1 assertion and unchanged-file state check. Earlier v1 failures remain retained.')
    declaration_path = package/'final-series-declaration-native-exit-v1-v2.json'
    immutable_json(declaration_path, declaration)
    receipt_path = package/'scenario-revision-native-exit-v2.json'
    immutable_json(receipt_path, dict(schema_version=1, project='taskell', candidate='v0.4.0-rc.6',
        base_declaration=base_declaration_path.name, base_declaration_sha256=sha256(base_declaration_path),
        base_contract_tree='host-contracts', base_scenarios_sha256=sha256(source/'scenarios.json'),
        revised_declaration=declaration_path.name, revised_declaration_sha256=sha256(declaration_path),
        revised_contract_tree=destination.name, revised_scenarios_sha256=sha256(scenario_path),
        changed_case='E11M', old_expect='Could not parse file.', new_expect='not parse file.',
        exit_assertion_preserved=malformed['steps'][1] == {'exit': 1},
        unchanged_file_assertion_preserved=malformed['steps'][2].get('state', {}).get('path') == 'board.md',
        scope='Single oracle revision bound to a new 12-batch native window. Earlier attempts and exact v1 hashes remain immutable; no result credit is carried into v2.'))
    return declaration_path, destination, receipt_path


if __name__ == '__main__':
    declaration, contracts, receipt = freeze_revision()
    print('Taskell exact-window v2 frozen:', declaration, contracts, receipt)
