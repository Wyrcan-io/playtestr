"""Recheck Peco's actual reports after exact local evidence compaction."""
import json

from next20_check import DOC, RAW
from next20_peco_cell_readback import Evidence, audit as ordinary_audit
from next20_peco_rebuild_readback import audit as rebuild_audit
from readiness_evidence import immutable_json, sha256


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    package = DOC / 'peco'
    evidence = Evidence('windows')
    require(not (RAW / 'active/peco').exists(), 'target remains active')
    proof = evidence.load('peco/retained-local-v1/expanded-removed.json')
    require(proof['all_expanded_removed'], 'local duplicate removal incomplete')
    cells = []
    for host, run, generation in [('windows', None, None), ('linux', '41043810230', 3)]:
        result = ordinary_audit(host, '4d31e08b3d6da92d94f7eb393b43689fd89bbf25', run, generation)
        cells.append(result)
    rebuilt = []
    for host, run, generation in [('windows', None, None), ('linux', '41713430365', 4)]:
        rebuilt.append(rebuild_audit(host, 'ce4012850a43b81fa0968f11cc7f147cd27aa7b2', run, generation))
    count = 0
    for filename, key in [('all-attempt-evidence.json', 'local_reports'), ('normal-rebuild-history-delta-v1.json', 'local_new_reports')]:
        document = json.loads((package / filename).read_text())
        for row in document[key]:
            require(evidence.sha(row['report']) == row['sha256'], 'retained original report changed')
            if row.get('frame'):
                require(evidence.sha(row['frame']) == row['frame_sha256'], 'retained original failure frame changed')
            count += 1
        for row in document['commands']:
            require(evidence.sha(row['console']) == row['console_sha256'], 'retained original command console changed')
    require(count == 357, 'retained report history incomplete')
    require(all(c['source_runtime_removed'] for c in cells + rebuilt), 'source cleanup proof incomplete')
    immutable_json(package / 'complete-retained-readback-v1.json', dict(
        schema_version=1, project='peco', original_ordinary_verified=480,
        qualified_normal_rebuild_calibrations=18, historical_copy_recovery_calibrations=18,
        local_reports_verified=count, normal_rebuilds_verified=6,
        actual_rebuild_compiler_executions_verified=12, source_runtime_removed=True,
        local_index_sha256=sha256(RAW / 'peco/retained-local-v1/index.json'),
        local_removal_sha256=sha256(RAW / 'peco/retained-local-v1/expanded-removed.json'),
        project_admissions=0))
    print('Post-compaction:480 ordinary,18 normal-rebuild calibration phases,357 local reports and command consoles read back exactly.')


if __name__ == '__main__':
    main()
