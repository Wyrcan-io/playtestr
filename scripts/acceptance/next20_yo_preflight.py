"""Check declared yo inputs and executable helper syntax before remote work."""
import ast
import json

from next20_check import ROOT, DOC, RAW
from readiness_evidence import sha256


def main():
    paths=sorted((ROOT/'scripts/acceptance').glob('next20_*.py'))
    for path in paths:ast.parse(path.read_text(encoding='utf-8-sig'),filename=str(path))
    package=DOC/'yo';target=RAW/'active/yo'
    frozen=json.loads((package/'development-test-freeze.json').read_text())
    for name,digest in frozen['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('Frozen yo input changed: '+name)
    provenance=json.loads((package/'source-provenance.json').read_text())
    if {p.relative_to(target/'src').as_posix():sha256(p) for p in (target/'src').rglob('*') if p.is_file()}!=provenance['files']:
        raise ValueError('Actual yo source not exactly restored')
    installed=json.loads((target/'installed-inventory.json').read_text())
    for name,digest in installed['files'].items():
        if sha256(ROOT/installed['runtime_root']/name)!=digest:raise ValueError('Actual yo runtime not restored: '+name)
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
