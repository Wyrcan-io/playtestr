"""Acquire only the screened immutable Frogmouth source; execute no build hook."""
from readiness_acquire_plop import acquire


if __name__=='__main__':
    acquire('frogmouth','Textualize/frogmouth','15c3e85a6e84b2e4a6845723acf12beb54c81eb2',archive_limit=16*1024**2)
