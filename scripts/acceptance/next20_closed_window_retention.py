"""Retain the complete closed rejected PDM window before a fresh replacement."""
import hashlib
import json
import tarfile

from next20_check import RAW, DOC
from next20_local_records import safe_path, read_packet
from readiness_evidence import immutable_json, sha256


def main():
    project='pdm';subset='final-series-native-exit-v1';wrapper='76fcc374f4674c2b9774aa75f15b3f06'
    root=RAW/project/subset;destination=RAW/project/'retained-failed-final-v1'
    finished=json.loads((RAW/'events'/(wrapper+'-finished.json')).read_text())
    if finished['category']!='exit_mismatch' or finished['cleanup_errors'] or finished['harness_cleanup']!='harness_process_reaped':raise ValueError('old window is not closed')
    disposition=json.loads((DOC/project/'windows-first-final-rejection.json').read_text())
    if disposition['wrapper']!=wrapper or disposition['ordinary_attempted']!=227 or disposition['final_qualification_credit']!=0:raise ValueError('wrong rejected-window declaration')
    files={};total=0
    for path in sorted(root.rglob('*')):
        if not path.is_file():continue
        name=path.relative_to(RAW).as_posix();safe_path(name,project);size=path.stat().st_size;total+=size
        if len(files)>=4000 or size>16*1024**2 or total>32*1024**2:raise ValueError('closed-window retention bounds')
        files[name]=dict(bytes=size,sha256=sha256(path))
    for row in disposition['observations']:
        if files[row['report']]['sha256']!=row['sha256']:raise ValueError('original failed-window report changed')
        result=json.loads((RAW/row['report']).read_text())['results'][0]
        if not result['cleanup']['confirmed_exited'] or not result['workspace']['cleaned']:raise ValueError('old report cleanup incomplete')
    destination.mkdir(exist_ok=False);archive=destination/'packets.tar.xz'
    with tarfile.open(archive,'w:xz',preset=6) as bundle:
        for name,row in files.items():
            if sha256(RAW/name)!=row['sha256']:raise ValueError('closed window changed during retention')
            member=tarfile.TarInfo(name);member.size=row['bytes'];member.mode=0o644
            with (RAW/name).open('rb') as stream:bundle.addfile(member,stream)
    immutable_json(destination/'index.json',dict(schema_version=1,project=project,compression='tar.xz',files=files,
        archive_sha256=sha256(archive),expanded_bytes=total,closed_subset=subset,closed_wrapper=wrapper,
        scope='Complete original rejected final window, every fixture/spec/plan/report/screen/catalog byte preserved. Parent execution is closed; target source/runtime are outside this subset. Zero final qualification credit.'))
    index,restored=read_packet(project,packet=destination.name)
    if any((RAW/name).read_bytes()!=data for name,data in restored.items()):raise ValueError('complete actual rejected-window byte comparison differs')
    selected=project+'/'+subset+'/11/N07.report.json';(destination/'selected-restore.bin').write_bytes(restored[selected])
    if sha256(destination/'selected-restore.bin')!=files[selected]['sha256']:raise ValueError('selected original failure restore differs')
    immutable_json(destination/'prepared.json',dict(schema_version=1,index_sha256=sha256(destination/'index.json'),archive_sha256=sha256(archive),
        closed_subset=subset,closed_wrapper=wrapper,files_compared_byte_exact=len(restored),
        selected_restore=dict(logical_path=selected,sha256=files[selected]['sha256']),expanded_removal_confirmed=False))
    print('Compared all',len(restored),'closed-window files byte-exactly;',total,'expanded ->',archive.stat().st_size,'XZ bytes. Native checked duplicate removal pending.')


if __name__=='__main__':main()
