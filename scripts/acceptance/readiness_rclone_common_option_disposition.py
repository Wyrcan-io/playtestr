"""Bind the observed alias failure to reviewed shared option registration."""
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass'
    review=load(docs/'rclone/source-review.json')
    registration=RAW/'rclone/option-source-review/fs/registry.go'
    if sha256(registration)!=review['reviewed_inputs']['fs/registry.go']:
        raise RuntimeError('shared option source differs')
    text=registration.read_text()
    if 'info.Options = append(info.Options, optDescription)' not in text or 'Advanced: true' not in text:
        raise RuntimeError('shared advanced-option registration differs')
    run=RAW/'native/39279953091'
    metadata=load(run/'run-metadata.json')
    if metadata['conclusion']!='failure':raise RuntimeError('original native alias outcome differs')
    cells=[]
    for artifact in ['Linux','Windows']:
        target=run/('playtestr-'+artifact)/'rclone'
        retained=target/'retained-source'
        index=load(retained/'verified-index.json')
        if ({n:r['sha256'] for n,r in index['files'].items()}!=review['reviewed_inputs']
                or not load(retained/'removed.json')['removed']
                or not load(retained/'removal-prepared.json')['runtime_processes_verified']):
            raise RuntimeError('actual native source restoration/cleanup incomplete')
        build=load(retained/'build.json')
        capture=[load(p) for p in (target.parent/'events').glob('*-finished.json')
                 if load(p)['label']=='first-use-public-record-review-replay-save']
        if len(capture)!=1 or capture[0]['category']!='exit_mismatch':raise RuntimeError('alias capture failure differs')
        cells.append(dict(host=artifact,failed_capture=capture[0]['id'],build_sha256=sha256(retained/'build.json'),
            target_binary_sha256=build['binary_sha256'],source_cleanup_sha256=sha256(retained/'removed.json')))
    immutable_json(docs/'rclone/common-option-disposition.json',dict(original_run='39279953091',cells=cells,
        source=dict(path='fs/registry.go',sha256=sha256(registration),pin=review['pin']),
        cause='Review missed Register appending the shared advanced description option to every backend, including alias.',
        observed='Both alias routes reach the remote value, then time out waiting for Keep this remote. Replay/export correctly refuse unresolved controls.',
        correction='All alias creation/edit controls now explicitly observe and decline the advanced prompt. A prepared rename workflow provides a useful sixteen-control first route without backend-option configuration.',
        scenario_revision='scenario-declaration-v2.json; still before any twenty-case authoring or source fault selection.',
        first_use_accounting='Initial Linux local-config route succeeded in 3 commands/20 controls. Windows has two failed available-target routes (4 commands/40 controls); a successful 3-command/16-control rename would total 7/56, missing both cumulative engineering targets.',
        production_go_changed=False,provisional_archives_changed=False,development_admission=False,final_archive_credit=0))
    print('Shared option omission and actual successful native cleanup retained; first-use qualification remains open.')


if __name__=='__main__':main()
