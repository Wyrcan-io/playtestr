"""Declare additive Windows readiness while preserving every existing oracle."""
import json
from next20_check import DOC
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'pdm';linux=json.loads((package/'native-profile-v2.json').read_text())
    immutable_json(package/'windows-profile-v1.json',dict(schema_version=1,host='windows',
        canonical_freeze_sha256=sha256(package/'development-test-freeze.json'),
        native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),
        case_profiles={'N01':linux['case_profiles']['N01']},
        scope='Add the five reviewed prompt-readiness expectations before original N01 inputs. Every original input, native exit, exact fixture/generated file and snapshot remains unchanged. No target/runner source change or historical-screen waiver.'))
    print('Declared Windows additive readiness, zero execution credit.')


if __name__=='__main__':main()
