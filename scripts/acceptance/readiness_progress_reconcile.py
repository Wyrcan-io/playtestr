"""Validate and preserve the second development admission and incident evidence."""
import hashlib
import json

from readiness_evidence import RAW, ROOT, immutable_json, sha256


def publish(path, value):
    if path.exists():
        if json.loads(path.read_text())!=value:raise RuntimeError('refuse changed progress receipt')
    else:immutable_json(path,value)


def main():
    curated=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    native=RAW/'native/38957159731'
    cells=[]
    for host in sorted(native.iterdir()):
        report=host/'playtestr/results.json'
        if not report.exists():continue
        results=json.loads(report.read_text())['results']
        assert len(results)==20
        assert all(r['status']=='passed' and r['cleanup']['confirmed_exited'] and r['workspace']['cleaned'] for r in results)
        removed=list(host.rglob('retained-source/removed.json'))
        assert len(removed)==1 and json.loads(removed[0].read_text())['removed']
        cells.append(dict(host=host.name,report_sha256=sha256(report),scenarios=20,
            cleanup_receipt_sha256=sha256(removed[0])))
    assert len(cells)==2
    publish(curated/'poetry/development-admission.json',dict(schema_version=1,
        status='development-admitted',runner_source='93bd63df93c2a697ccea4e695afdb9c6a89e5221',
        run='38957159731',cells=cells,real_faults=3,original_fault_parent='109f5ce29a4f4e0b9c22bec6478168fd',
        maintenance_parent='5316cddbc03d44b88049b77f7878203f',
        holdout='original local F03 only; native faults are replicas',
        windows='19/20; repeated quiet resize remains excluded',archive_qualified=False,human_usability='unmeasured'))
    old=curated/'old-control-matrix.json'
    attempt='5605544cfc0d49e8a26a5fb5c74f5a0f'
    console=RAW/'core'/attempt/'console.log'
    records=[]
    for line in console.read_text().splitlines():
        try:records.append(json.loads(line))
        except ValueError:pass
    test='TestAdversarialWindowsWorkspaceExpandsShortTemporaryPath'
    assert any(r.get('Test')==test and r.get('Action')=='pass' for r in records)
    identified=json.loads((RAW/'events'/f'{attempt}-identified.json').read_text())
    manifest=RAW/identified['identity']['manifest']
    assert sha256(manifest)==identified['identity']['sha256']
    finished=json.loads((RAW/'events'/f'{attempt}-finished.json').read_text())
    assert finished['category']=='passed'
    publish(curated/'old-control-matrix-revision-2.json',dict(schema_version=1,
        original_matrix_sha256=sha256(old),correction='Additional actual applicable Windows short-path control evidence',
        test=test,attempt=attempt,console_sha256=sha256(console),identity_sha256=sha256(manifest),
        status='all 88 historical whole controls now have applicable development evidence',
        limitation='Hosted D filesystem still skipped the alias control; local C filesystem supplied actual aliases. No host settings changed.'))
    summaries=list((RAW/'native/38957542544/historical-macos').glob('*/summary.json'))
    assert len(summaries)==1
    history=json.loads(summaries[0].read_text())
    assert len(history['records'])==6 and all(r['actual_passes']==50 for r in history['records'])
    publish(curated/'historical-disposition-development.json',dict(schema_version=1,
        macos_run='38957542544',macos_summary_sha256=sha256(summaries[0]),macos_records=history['records'],
        windows_parent='396e32e495914b2caf3fcd5575e9f065',windows_summary='historical-wizard/be9b10409af94c94b10befcd6a42a446/summary.json',
        windows_passes=150,disposition='bounded current-control observations; original unlogged causal branches remain unresolved',
        fixture_publication='known staging/rename fixture correction is separate from unexplained original exit-code branches',
        final_archive_qualification=False))
    print('Validated Poetry 20x2, actual Windows alias pass, and macOS 3x50 per incident.')


if __name__=='__main__':main()
