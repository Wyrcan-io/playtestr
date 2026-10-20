"""Use only owned runtime paths for original glow's synthetic local workflows."""
import os

from readiness_build_rclone import environment as build_environment
from readiness_evidence import RAW


def environment():
    target=RAW/'active/old-glow';env=build_environment(target)
    env['PATH']=str(target/'bin')+os.pathsep+env.get('PATH','')
    env.update(TERM='screen-256color',GLAMOUR_STYLE='dark',GLOW_TEXT_SIZING='off')
    return env
