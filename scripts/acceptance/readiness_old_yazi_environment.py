"""Owned homes and original terminal profile for Yazi migration."""
from readiness_old_helix_environment import environment as rust_environment


def environment():
    return rust_environment("yazi")
