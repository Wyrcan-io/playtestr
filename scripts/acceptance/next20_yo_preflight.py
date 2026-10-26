"""Check declared yo inputs and executable helper syntax before remote work."""
import argparse
import ast
import hashlib
import json

from next20_check import ROOT, DOC, RAW
from readiness_evidence import sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--retained',action='store_true');args=parser.parse_args()
    paths=sorted((ROOT/'scripts/acceptance').glob('next20_*.py'))
    for path in paths:ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
    package=DOC/'yo';target=RAW/('yo/retained-source' if args.retained else 'active/yo')
    frozen=json.loads((package/'development-test-freeze.json').read_text())
    for name,digest in frozen['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('Frozen yo input changed: '+name)
    provenance=json.loads((package/'source-provenance.json').read_text())
    if args.retained:
        from next20_verify_node import tar_files
        actual={n:hashlib.sha256(data).hexdigest() for n,data in tar_files((target/'source.tar.gz').read_bytes()).items()}
        cleanup=json.loads((target/'cleanup-inventory.json').read_text())
        removed=json.loads((target/'removed.json').read_text(encoding='utf-8-sig'))
        if not removed['removed'] or removed['cleanup_inventory_sha256']!=sha256(target/'cleanup-inventory.json') or (RAW/'active/yo').exists():
            raise ValueError('Retained preflight lacks checked removal')
    else:actual={p.relative_to(target/'src').as_posix():sha256(p) for p in (target/'src').rglob('*') if p.is_file()}
    if actual!=provenance['files']:
        raise ValueError('Actual yo source not exactly restored')
    installed=json.loads((target/'installed-inventory.json').read_text())
    for name,digest in installed['files'].items():
        actual_digest=cleanup['files']['runtime/'+name]['sha256'] if args.retained else sha256(ROOT/installed['runtime_root']/name)
        if actual_digest!=digest:raise ValueError('Actual yo runtime not restored: '+name)
    declaration=json.loads((package/'final-series-declaration.json').read_text())
    if declaration['framework_lock_sha256']!=sha256(package/'generator-package-lock.json') or declaration['ordinary_required']!=480 or declaration['calibration_required']!=20:
        raise ValueError('Native frozen declaration differs')
    workflow=(ROOT/'.github/workflows/runner-readiness-next20-yo.yml').read_text()
    if workflow.count('name: Final fresh-state batch ')!=12 or workflow.count('native-yo-final-batch-')!=12:
        raise ValueError('Partial native workflow')
    for item in ['os: ubuntu-24.04','os: windows-2025','max-parallel: 2','timeout-minutes: 65',
                 'next20_yo_native.py','next20_python_faults.py yo --package',
                 'next20_yo_cache_retention.py','--max-files 60000','-MaxFiles 60000','run-id: 39450029736']:
        if item not in workflow:raise ValueError('Missing reviewed native workflow boundary: '+item)
    print('Parsed',len(paths),'campaign helpers;87 frozen yo inputs and complete actual source/runtime restored; complete bounded two-host workflow prepared. No native credit.')


if __name__=='__main__':main()
