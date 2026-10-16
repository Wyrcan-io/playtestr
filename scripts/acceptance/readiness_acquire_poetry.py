"""Acquire reviewed pinned Poetry source; execute no target/build hooks."""
from readiness_acquire_plop import acquire

if __name__=='__main__':
    acquire('poetry','python-poetry/poetry','38a86661d2ae58694c76d0bb4e628e1400d6dc6f')
