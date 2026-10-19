"""Select real tracked source faults only after the committed two-host freeze."""
import difflib
import hashlib
import subprocess

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    docs=ROOT/'docs/validation/runner-readiness-ten-project-pass/rclone'
    audit=load(docs/'native-authoring-review.json')
    if audit['run']!='39326730110' or {c['host'] for c in audit['cells']}!={'linux','windows'}:
        raise RuntimeError('complete independently reviewed native freeze required')
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    for suffix in ['', 'native-profiles/windows']:
        path=docs/suffix/'reviewed-contract-freeze.json'
        relative=path.relative_to(ROOT).as_posix()
        committed=subprocess.check_output(['git','show',commit+':'+relative],cwd=ROOT)
        if hashlib.sha256(committed).hexdigest()!=sha256(path):raise RuntimeError('freeze is not committed exactly')
    faults=[dict(id='F01',path='fs/config/configfile/configfile.go',spec='N02.json',held_out=False,
        before='\tif err := config.Encrypt(&buf, f); err != nil {',
        after='\tbuf = *bytes.NewBuffer(bytes.Replace(buf.Bytes(), []byte("remote = ."), []byte("remote = wrong"), 1))\n\tif err := config.Encrypt(&buf, f); err != nil {',
        category='state_assertion_failure',state_kind='file',state_path='rclone.conf',
        behavior='Persist the wrong alias destination while the in-memory configuration, reviewed screen and exit0 remain correct.'),
        dict(id='F02',path='fs/config/config.go',spec='E09.json',held_out=False,
        before='\t\t\tfs.Fatalf(nil, "Failed to load config file %q: %v", configPath, err)',
        after='\t\t\tfs.Logf(nil, "Failed to load config file %q: %v", configPath, err)\n\t\t\tos.Exit(0)',
        category='unexpected_exit',behavior='Incorrect actual OS exit0 after reporting a config load failure whose contract requires exit1.'),
        dict(id='F03',path='fs/config/configfile/configfile.go',spec='N02.json',held_out=True,
        before='\tkeepBackup = false // new file was written, no need to keep backup',
        after='\tkeepBackup = false // new file was written, no need to keep backup\n\t_ = os.WriteFile(filepath.Join(configDir, "unreviewed.tmp"), []byte("unwanted\\n"), 0600)',
        category='state_assertion_failure',state_kind='entries',state_path='.',
        behavior='Leave an extra sibling after correctly saving config; reviewed screen, exact config, sentinel and exit0 pass before complete entries reject it.')]
    review=load(docs/'source-review.json');records=[]
    for fault in faults:
        source=RAW/'rclone/retained-source/selected-restore'/fault['path']
        original=source.read_bytes()
        if sha256(source)!=review['reviewed_inputs'][fault['path']] or original.count(fault['before'].encode())!=1:
            raise RuntimeError('original source or unique mutation site differs')
        mutated=original.replace(fault['before'].encode(),fault['after'].encode())
        patch=''.join(difflib.unified_diff(original.decode().splitlines(True),mutated.decode().splitlines(True),
            fromfile='a/'+fault['path'],tofile='b/'+fault['path']))
        destination=docs/'patches'/(fault['id']+'.patch');destination.parent.mkdir(exist_ok=True)
        with destination.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
        records.append(dict(**fault,original_source_sha256=sha256(source),
            mutated_source_sha256=hashlib.sha256(mutated).hexdigest(),patch_sha256=sha256(destination)))
    immutable_json(docs/'fault-selection.json',dict(freeze_commit=commit,selected_after_native_run=audit['run'],
        frozen_contract_sha256=sha256(docs/'reviewed-contract-freeze.json'),native_review_sha256=sha256(docs/'native-authoring-review.json'),
        faults=records,qualifying_faults=3,
        original_heldout='F03 initial execution must be hosted native Linux only. Windows follows a retained original Linux outcome; no local F03 execution.',
        execution='Actual pinned Go application source, compiled with the original owned native compiler and build flags. Unchanged public contracts; no wrapper fault or expectation edits.'))
    print('Selected three real source faults after the committed complete two-host freeze; none executed.')


if __name__=='__main__':main()
