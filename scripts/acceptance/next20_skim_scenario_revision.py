"""Create the reviewed v6 delta for Skim's CLI parser early-exit case."""
import json
from pathlib import Path

from next20_check import ROOT
from readiness_evidence import sha256


def write_json(path, value):
    lines = json.dumps(value, indent=2, ensure_ascii=False).splitlines()
    path.write_bytes(b'\r\n'.join(line.encode('utf-8') for line in lines) + b'\r\n')


def main():
    package = ROOT / 'docs/validation/runner-readiness-next-twenty-project-pass/skim'
    base_path = package / 'scenario-declaration-v5.json'
    base = json.loads(base_path.read_text(encoding='utf-8'))
    spec = json.loads((package / 'E03-v2.json').read_text(encoding='utf-8'))
    spec.pop('startup_timeout_ms', None)
    spec['name'] = 'Skim E03 parser early-exit exact-code scenario v3'
    spec_path = package / 'E03-v3.json'
    write_json(spec_path, spec)
    replacement = next(row.copy() for row in base['scenarios'] if row['id'] == 'E03')
    replacement['contract'] = spec_path.name
    replacement['contract_sha256'] = sha256(spec_path)
    replacement['positive_evidence'] = (
        'Exact target exit code 2 and confirmed workspace cleanup; '
        'this CLI parser exits before entering terminal mode.')
    base_digest = sha256(base_path)
    revision = dict(schema_version=6, project='skim',
        base_declaration=base_path.name, base_sha256=base_digest,
        supersedes_sha256=base_digest, scenario_count=20,
        normal_count=8, edge_count=12, replacements=[replacement])
    write_json(package / 'scenario-declaration-v6.json', revision)
    assert sha256(spec_path) == replacement['contract_sha256']
    assert sha256(base_path) == revision['base_sha256']
    print('Created E03-v3 and scenario-declaration-v6 with bound hashes.')


if __name__ == '__main__':
    main()

