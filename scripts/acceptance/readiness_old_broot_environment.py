"""Owned homes and explicit terminal profile for original Broot workflows."""
from readiness_old_helix_environment import environment as rust_environment


def environment():
    return rust_environment('broot')
