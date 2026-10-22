"""Deduplicate actual local and retained hosted command journals without expansion."""
from collections import Counter
import hashlib
import json
import re
import tarfile
import uuid

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_final_batch_verify import require
from readiness_new_control_matrix import read_json as load

PATTERN=re.compile(r'(?:^|/)events/([a-f0-9]{32})-(started|identified|launched|finished)\.json$')


def main():
    commands={};sources=[];duplicate_copies=0
    def add(identity,kind,data,location):
        nonlocal duplicate_copies
        require(len(data)<=2*1024**2,'command event byte bound')
        value=json.loads(data.decode('utf-8-sig'))
        require(value['id']==identity and value['event']==kind,'command journal identity differs')
        digest=hashlib.sha256(data).hexdigest();row=commands.setdefault(identity,{})
        if kind in row:
            require(row[kind]['sha256']==digest,'conflicting command journal copies')
            duplicate_copies+=1
        else:row[kind]=dict(sha256=digest,value=value,source=location)
    for path in sorted((RAW/'events').glob('*.json')):
        match=PATTERN.search('events/'+path.name)
        if match:add(*match.groups(),path.read_bytes(),path.relative_to(RAW).as_posix())
    # Include still-expanded native packets, and standalone archive-experience
    # packets. Exclude selected-restore copies; their archives are read below.
    for parent in [RAW/'native',RAW/'delivered-ci-generation']:
        if not parent.exists():continue
        for directory in parent.rglob('events'):
            if 'selected-restore' in directory.parts:continue
            for path in directory.glob('*.json'):
                match=PATTERN.search('events/'+path.name)
                if match:add(*match.groups(),path.read_bytes(),path.relative_to(RAW).as_posix())
    for index_path in sorted(RAW.glob('*/retained-native-v*/index.json')):
        root=index_path.parent;index=load(index_path,maximum=8*1024**2)
        archive=root/'packets.tar.gz';expected=index['archive_sha256']
        if not archive.exists():
            encoded=load(root/'reencoded.json');archive=root/'packets.tar.xz';expected=encoded['replacement_archive_sha256']
            require(encoded['original_index_sha256']==sha256(index_path),'journal reencoded index differs')
        require(sha256(archive)==expected,'journal retained archive differs')
        wanted={}
        for name,record in index['files'].items():
            match=PATTERN.search(name)
            if match:wanted.setdefault(record.get('member',name),[]).append((name,record,match.groups()))
        found=set()
        with tarfile.open(archive,'r|*') as bundle:
            for member in bundle:
                if member.name not in wanted:continue
                require(member.isfile() and member.size<=2*1024**2,'unsafe retained journal event')
                data=bundle.extractfile(member).read(2*1024**2+1)
                for name,record,groups in wanted[member.name]:
                    require(len(data)==record['bytes'] and hashlib.sha256(data).hexdigest()==record['sha256'],'actual retained command event changed')
                    add(*groups,data,archive.relative_to(RAW).as_posix()+'::'+name);found.add(name)
        require(found=={n for group in wanted.values() for n,_,_ in group},'retained command journal missing')
        sources.append(dict(index= index_path.relative_to(RAW).as_posix(),index_sha256=sha256(index_path),archive_sha256=expected,event_paths=len(found)))
    groups=Counter();incomplete=[];cleanup=Counter();finished=0
    for identity,events in commands.items():
        start=events.get('started',{}).get('value',{})
        end=events.get('finished',{}).get('value')
        if end:
            finished+=1
            require(start,'finished command lacks actual start')
            require(all(e['value'].get('project')==start.get('project') and e['value'].get('label')==start.get('label')
                for e in events.values()),'command envelope mismatch')
            groups[(end.get('phase','unspecified'),end.get('project','unspecified'),end.get('category','unspecified'))]+=1
            cleanup[(end.get('harness_cleanup','unspecified'),bool(end.get('cleanup_errors')))]+=1
        else:incomplete.append(dict(id=identity,events=sorted(events),project=start.get('project'),label=start.get('label'),
            disposition='Retained unfinished command envelope; no successful completion credit. This may be the currently running closing auditor or an interrupted historical attempt.'))
    root=RAW/'closing-journal'/uuid.uuid4().hex;root.mkdir(parents=True)
    immutable_json(root/'commands.json',commands)
    immutable_json(root/'sources.json',sources)
    receipt=dict(unique_command_ids=len(commands),finished_commands=finished,incomplete_commands=incomplete,
        duplicate_event_copies_merged=duplicate_copies,retained_packet_archives=len(sources),
        outcomes=[dict(phase=p,project=j,category=c,commands=n) for (p,j,c),n in sorted(groups.items())],
        harness_cleanup=[dict(outcome=c,has_cleanup_errors=e,commands=n) for (c,e),n in sorted(cleanup.items())],
        command_inventory_local_only=(root/'commands.json').relative_to(ROOT).as_posix(),command_inventory_sha256=sha256(root/'commands.json'),
        retained_sources_local_only=(root/'sources.json').relative_to(ROOT).as_posix(),retained_sources_sha256=sha256(root/'sources.json'),
        scope='Deduplicated actual command envelopes, including setup/build/authoring/harness and failed commands, from current local events and self-contained retained hosted packets. Commands are not scenarios or project admissions. Final series, old-migration report outcomes and bounded R3 repetitions have separate nonoverlapping denominators. Repeated identical event copies add no credit. This is a point-in-time observation; later closing commands are not backfilled.')
    immutable_json(ROOT/'docs/validation/runner-readiness-ten-project-pass/all-command-accounting.json',receipt)
    print('Actual unique command IDs:',len(commands),'; completed:',finished,'; incomplete:',len(incomplete),'; retained packet archives:',len(sources))


if __name__=='__main__':main()
