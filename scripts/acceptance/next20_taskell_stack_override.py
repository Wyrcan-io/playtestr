"""Create an owned Stack config that overrides only the Darwin ARM compiler."""
import argparse
import json
from pathlib import Path

from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


SUPPORTED_COMPILERS=('ghc-9.0.2',)


def parse_args(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--compiler',required=True,choices=SUPPORTED_COMPILERS)
    return parser.parse_args(argv)


def main():
    args=parse_args()
    source=RAW/'active/taskell/src'
    package=DOC/'taskell'
    lock=json.loads((package/'native-runtime-lock-native-exit-v1.json').read_text(encoding='utf-8'))
    provenance=json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))
    for name,digest in lock['resolver_files'].items():
        if sha256(source/name)!=digest:raise ValueError('Taskell frozen resolver input changed: '+name)
    if lock['source_pin']!=provenance['pin']:raise ValueError('Taskell source pin changed')
    stack_yaml=(source/'stack.yaml').read_text(encoding='utf-8')
    expected='resolver: nightly-2021-07-14\nallow-newer: true\npvp-bounds: lower\npackages:\n  - .\nextra-deps:\n  - tz-0.1.3.5\n'
    if stack_yaml.replace('\r\n','\n')!=expected:raise ValueError('Taskell Stack configuration differs from frozen shape')
    out=RAW/'toolchain/taskell/arm64-compiler-override'
    out.mkdir(parents=True,exist_ok=True)
    package_path=json.dumps(str(source.resolve()).replace('\\','/'))
    body=('resolver: nightly-2021-07-14\n'
          f'compiler: {args.compiler}\n'
          'compiler-check: match-exact\n'
          'system-ghc: true\n'
          'allow-newer: true\n'
          'pvp-bounds: lower\n'
          'packages:\n'
          f'  - {package_path}\n'
          'extra-deps:\n'
          '  - tz-0.1.3.5\n')
    config=out/'stack.yaml'
    config.write_text(body,encoding='utf-8',newline='\n')
    copied_lock=out/'stack.yaml.lock'
    copied_lock.write_bytes((source/'stack.yaml.lock').read_bytes())
    receipt=out/'override.json'
    immutable_json(receipt,dict(schema_version=1,project='taskell',source_pin=provenance['pin'],
        original_stack_yaml_sha256=sha256(source/'stack.yaml'),original_stack_lock_sha256=sha256(source/'stack.yaml.lock'),
        override_stack_yaml_sha256=sha256(config),copied_stack_lock_sha256=sha256(copied_lock),
        compiler=args.compiler,resolver='nightly-2021-07-14',package_set='unchanged frozen resolver and Stack lock',
        scope=('Apple Silicon uses GHC 9.0.2 and the exact frozen dependency resolver and Stack lock, without modifying pinned source. The compiler needs the Apple SDK ffi include directory in C_INCLUDE_PATH for Stack builds; supply it only to compiler processes.')))
    print(json.dumps(dict(stack_yaml=str(config),receipt=str(receipt),compiler=args.compiler),sort_keys=True))


if __name__=='__main__':main()
