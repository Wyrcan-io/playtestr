"""Execute the frozen twelve-batch native schedule once, stopping on first failure."""
import asyncio
import argparse
import json
import platform

from next20_jrnl_final import main as batch
from next20_check import RAW,DOC
from readiness_evidence import sha256,immutable_json


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--linux-replacement',action='store_true');args=parser.parse_args()
    package=DOC/'cargo-generate';path=package/'final-series-declaration-native-exit-v1.json'
    declared=json.loads(path.read_text())
    subjects={package/'development-test-freeze.json':declared['canonical_test_freeze_sha256'],
        package/'native-runtime-lock-native-exit-v1.json':declared['native_runtime_lock_sha256'],
        package/'fault-declaration.json':declared['fault_declaration_sha256'],
        DOC/'replacement-candidate-freeze-native-exit-v1.json':declared['candidate_freeze_sha256']}
    if any(sha256(p)!=digest for p,digest in subjects.items()):raise ValueError('final schedule subject changed before native execution')
    if platform.system()=='Windows' and sha256(RAW/'cargo-generate/host-contracts/scenarios.json')!=declared['windows_profile_sha256']:
        raise ValueError('concrete declared local Windows profile changed')
    if args.linux_replacement:
        if platform.system()!='Linux':raise ValueError('Linux replacement flag cannot relabel another host')
        replacement_path=package/'final-linux-replacement-declaration-native-exit-v1-v2.json';replacement=json.loads(replacement_path.read_text())
        profile_path=RAW/'cargo-generate/host-contracts/scenarios.json';profile=json.loads(profile_path.read_text())
        review_path=package/'native-linux-readiness-profile-v3.json'
        if replacement['base_final_declaration_sha256']!=sha256(path) or replacement['native_readiness_review_sha256']!=sha256(review_path) or profile.get('native_readiness_review_sha256')!=sha256(review_path):raise ValueError('replacement native input profile is not exact predeclared review')
        if sha256(RAW/'cargo-generate/host-contracts/normal-project.json')!=replacement['actual_native_N01_sha256']:raise ValueError('replacement concrete native N01 differs')
        immutable_json(RAW/'cargo-generate/final-linux-window-2.json',dict(schema_version=1,window=2,replacement_declaration_sha256=sha256(replacement_path),native_profile_sha256=sha256(profile_path),native_readiness_review_sha256=sha256(review_path),base_final_declaration_sha256=sha256(path)))
    for selected in range(12):
        await batch(project='cargo-generate',batch=selected,candidate_series='native-exit-v1')


if __name__=='__main__':asyncio.run(main())
