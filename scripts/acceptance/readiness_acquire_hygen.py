"""Acquire reserved Hygen only after the exact provisional archive freeze."""
from readiness_acquire_plop import acquire
from readiness_evidence import ROOT, RAW
from readiness_new_control_matrix import read_json as load


def main():
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass'
    freeze = load(docs / 'provisional-candidate-freeze.json')
    if (freeze['project_admissions_at_freeze'] != 8 or not freeze['reserved_projects_untouched']
            or len(freeze['cells']) != 3 or freeze['published']):
        raise RuntimeError('reserved transfer requires actual private provisional archive freeze')
    acquire('hygen', 'jondot/hygen', '26f76d8dede565b2bf38d0b9e9f3009ee2c8f9ae',
            archive_limit=16*1024**2, expanded_limit=96*1024**2,
            entry_limit=12000, member_limit=8*1024**2)


if __name__ == '__main__':
    main()
