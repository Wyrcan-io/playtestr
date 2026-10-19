"""Acquire reserved Rclone source only after nine admissions and archive freeze."""
from readiness_acquire_plop import acquire
from readiness_evidence import ROOT
from readiness_new_control_matrix import read_json as load


def main():
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass'
    freeze = load(docs / 'provisional-candidate-freeze.json')
    ledger = load(docs / 'candidates.json')
    if (freeze['project_admissions_at_freeze'] != 8 or not freeze['reserved_projects_untouched']
            or len(freeze['cells']) != 3 or ledger['development_admissions'] < 9):
        raise RuntimeError('reserved Rclone transfer requires frozen native archives and nine admissions')
    acquire('rclone', 'rclone/rclone', 'd369079a1448c487d09d85bfe11382e16ea4e345',
            archive_limit=32*1024**2, expanded_limit=192*1024**2,
            entry_limit=25000, member_limit=16*1024**2)


if __name__ == '__main__':
    main()
