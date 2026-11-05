"""Verify each frozen Git Town spec's exact bytes before any target launch."""
import argparse
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def verify(catalog_path):
    catalog_path = Path(catalog_path).resolve(strict=True)
    catalog_path.relative_to(ROOT)
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    scenarios = catalog.get('scenarios')
    if not isinstance(scenarios, list) or len(scenarios) != catalog.get('declared_distinct_scenarios'):
        raise ValueError('scenario catalog count does not match its frozen declaration')
    seen = set()
    for scenario in scenarios:
        name = scenario.get('spec')
        if not isinstance(name, str) or Path(name).name != name or name in seen:
            raise ValueError('scenario catalog contains an invalid or duplicate spec path')
        seen.add(name)
        path = (catalog_path.parent / name).resolve(strict=True)
        path.relative_to(catalog_path.parent)
        raw = path.read_bytes()
        actual = hashlib.sha256(raw).hexdigest()
        if actual != scenario.get('spec_sha256'):
            raise ValueError(f'{name}: frozen spec SHA-256 mismatch ({actual})')
        parsed = json.loads(raw.decode('utf-8'))
        if parsed.get('version') != 3 or parsed.get('command', [None])[0] != 'git-town':
            raise ValueError(f'{name}: expected a public Git Town spec v3')
        print(f'VERIFIED {name} {len(raw)} {actual}')
    print(f'VERIFIED {len(seen)} exact Git Town public specs from {catalog_path.name}')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('catalog')
    args = parser.parse_args()
    verify(args.catalog)


if __name__ == '__main__':
    main()
