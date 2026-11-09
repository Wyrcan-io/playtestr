"""Remove only verified Taskell executable copies left by the public-route job."""
import argparse
import json
import os
from pathlib import Path

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


PROJECT = 'taskell'
COPIES = ('project', 'diagnosis', 'maintenance', 'relocated space café')


def cleanup(output, expected_sha256, *, root=ROOT):
    root = Path(root).resolve(strict=True)
    output = Path(output)
    if not output.is_absolute():
        output = root/output
    resolved = output.resolve(strict=False)
    resolved.relative_to(root)
    if not output.exists():
        return []
    if output.is_symlink() or getattr(output, 'is_junction', lambda: False)():
        raise ValueError('refusing linked public-route evidence root')
    removed = []
    binary_name = 'taskell.exe' if os.name == 'nt' else 'taskell'
    for name in COPIES:
        copy_root = output/name
        copy_path = copy_root.resolve(strict=False)
        copy_path.relative_to(resolved)
        if copy_root.is_symlink() or getattr(copy_root, 'is_junction', lambda: False)():
            raise ValueError('refusing linked Taskell public-route copy')
        if not copy_root.exists():
            removed.append(dict(path=(copy_root/'bin'/binary_name).relative_to(root).as_posix(), absent=True))
            continue
        bin_dir = copy_root/'bin'
        if bin_dir.is_symlink() or getattr(bin_dir, 'is_junction', lambda: False)():
            raise ValueError('refusing linked Taskell public-route bin directory')
        if not bin_dir.exists():
            removed.append(dict(path=(bin_dir/binary_name).relative_to(root).as_posix(), absent=True))
            continue
        binary = bin_dir/binary_name
        if binary.is_symlink() or getattr(binary, 'is_junction', lambda: False)():
            raise ValueError('refusing linked Taskell public-route executable')
        if binary.exists():
            if sha256(binary) != expected_sha256:
                raise ValueError('Taskell public-route executable identity changed; refusing removal')
            entries = list(bin_dir.iterdir())
            if len(entries) != 1 or entries[0].name != binary_name:
                raise ValueError('Taskell public-route bin directory contains unexpected entries')
            binary.unlink()
            bin_dir.rmdir()
            removed.append(dict(path=binary.relative_to(root).as_posix(), sha256=expected_sha256, absent=True))
        else:
            if any(bin_dir.iterdir()):
                raise ValueError('Taskell public-route bin directory contains unexpected entries')
            bin_dir.rmdir()
            removed.append(dict(path=binary.relative_to(root).as_posix(), absent=True))
    return removed


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=RAW/PROJECT/'public-route-native-exit-v1')
    args = parser.parse_args()
    output = args.output
    if not output.exists():
        print(json.dumps(dict(status='no-public-route-copies-created', removed=[]), sort_keys=True))
        return
    planned_path = output/'planned.json'
    planned = json.loads(planned_path.read_text(encoding='utf-8')) if planned_path.is_file() else {}
    if planned:
        expected_sha256 = planned['target_binary_sha256']
    else:
        build = json.loads((RAW/'active'/PROJECT/'build.json').read_text(encoding='utf-8'))
        expected_sha256 = build['binary_sha256']
    removed = cleanup(output, expected_sha256)
    immutable_json(output/'cleanup-final-v1.json', dict(schema_version=1, project=PROJECT,
                   target_binary_sha256=expected_sha256, planned_record_present=bool(planned), removed=removed,
                   scope='Only the four known public-route executable copies were inspected and removed by exact binary hash. Specs, fixtures, reports and other evidence remain.'))
    print(json.dumps(dict(status='checked', removed=len(removed), output=str(output)), sort_keys=True))


if __name__ == '__main__':
    main()
