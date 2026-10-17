"""Acquire project seven's screened pinned source without executing build hooks."""
from readiness_acquire_plop import acquire


if __name__ == '__main__':
    acquire('papis', 'papis/papis', 'c744b5efe9b307b9664f3e96c154cb620e140a8f',
            archive_limit=16*1024**2, expanded_limit=64*1024**2,
            entry_limit=10000, member_limit=8*1024**2)
