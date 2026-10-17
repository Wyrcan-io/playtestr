"""Acquire project six's screened immutable Bash source; execute no hooks."""
from readiness_acquire_plop import acquire


if __name__ == '__main__':
    acquire('fff', 'dylanaraps/fff', '6f2dc6f3a003d24e8b3fd48b046241b486022ad5',
            archive_limit=8*1024**2, expanded_limit=16*1024**2, entry_limit=2000, member_limit=8*1024**2)
