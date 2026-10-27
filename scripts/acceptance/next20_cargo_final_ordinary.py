"""Execute the frozen twelve-batch native schedule once, stopping on first failure."""
import asyncio
import json
import platform

from next20_jrnl_final import main as batch
from next20_check import RAW,DOC
from readiness_evidence import sha256


async def main():
    package=DOC/'cargo-generate';path=package/'final-series-declaration-native-exit-v1.json'
    declared=json.loads(path.read_text())
    subjects={package/'development-test-freeze.json':declared['canonical_test_freeze_sha256'],
        package/'native-runtime-lock-native-exit-v1.json':declared['native_runtime_lock_sha256'],
        package/'fault-declaration.json':declared['fault_declaration_sha256'],
        DOC/'replacement-candidate-freeze-native-exit-v1.json':declared['candidate_freeze_sha256']}
    if any(sha256(p)!=digest for p,digest in subjects.items()):raise ValueError('final schedule subject changed before native execution')
    if platform.system()=='Windows' and sha256(RAW/'cargo-generate/host-contracts/scenarios.json')!=declared['windows_profile_sha256']:
        raise ValueError('concrete declared local Windows profile changed')
    for selected in range(12):
        await batch(project='cargo-generate',batch=selected,candidate_series='native-exit-v1')


if __name__=='__main__':asyncio.run(main())
