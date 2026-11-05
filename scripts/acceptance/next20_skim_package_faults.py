"""Bundle Skim source-fault receipts and case reports for artifact upload."""
import json
from pathlib import Path
import zipfile

from next20_check import RAW, ROOT
from readiness_evidence import immutable_json, sha256


def main():
    project_ids = ('skim-exit-empty-01-v5', 'skim-match-count-01-v5',
                   'skim-multi-count-01-v5')
    matrix = RAW / 'active/fault-matrix-v1.json'
    if not matrix.is_file():
        raise ValueError('completed Skim fault matrix is missing')
    archive = RAW / 'active/skim/fault-matrix-evidence.zip'
    included = []
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        paths = [matrix]
        for project_id in project_ids:
            project = RAW / 'active' / project_id
            project.resolve(strict=True).relative_to((RAW / 'active').resolve(strict=True))
            for name in ('fault-started.json', 'fault-finished.json', 'task-owned.json',
                         'build.json', 'runtime.json'):
                path = project / name
                if path.is_file():
                    paths.append(path)
            evidence = project / 'case-evidence'
            if evidence.is_dir():
                paths.extend(path for path in evidence.rglob('*')
                             if path.is_file() and not path.is_symlink())
        for path in sorted(set(paths)):
            if path.is_symlink():
                raise ValueError('linked fault evidence is refused')
            path.resolve(strict=True).relative_to(RAW.resolve(strict=True))
            if path.stat().st_size > 4 * 1024 * 1024:
                raise ValueError('single fault evidence member exceeds 4 MiB')
            relative = path.relative_to(RAW).as_posix()
            output.write(path, relative)
            included.append(dict(path=relative, sha256=sha256(path), size=path.stat().st_size))
    if archive.stat().st_size > 32 * 1024 * 1024:
        raise ValueError('fault evidence archive exceeds 32 MiB')
    immutable_json(RAW / 'active/skim/fault-matrix-evidence-archive.json', dict(
        schema_version=1, matrix_sha256=sha256(matrix), archive=str(archive.relative_to(ROOT)),
        archive_sha256=sha256(archive), archive_size=archive.stat().st_size,
        members=included))
    print('Bundled', len(included), 'Skim fault evidence files:', archive.relative_to(ROOT))


if __name__ == '__main__':
    main()

