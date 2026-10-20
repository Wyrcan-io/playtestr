"""Use only owned runtime paths for original superfile's synthetic local workflows."""
import os

from readiness_build_rclone import environment as build_environment
from readiness_evidence import RAW


def environment():
    target=RAW/'active/old-superfile';env=build_environment(target)
    env['PATH']=str(target/'bin')+os.pathsep+env.get('PATH','')
    return env
