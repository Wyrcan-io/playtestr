"""Read exact logical native evidence from a verified bounded retained packet."""
from functools import lru_cache
import copy
import hashlib
import json
from pathlib import Path
import re
import tarfile

from next20_check import RAW
from next20_packet_archive import archive_path,tar_mode,verify
from readiness_compact_native import physical_members
from readiness_evidence import sha256


def corrected_index(root,index,index_sha):
    path=root/'reference-correction-v1.json'
    if not path.exists():return index,None
    correction=json.loads(path.read_text());result=copy.deepcopy(index);disposition=result['runtime_frame_disposition']
    original=disposition['required_canonical_runtime'];codec=disposition['current_native_executable']['representation']['codec']
    if (correction['original_index_sha256']!=index_sha or correction['wrong_dictionary_sha256']!=original['actual_executable_sha256'] or
        correction['wrong_dictionary_bytes']!=original['actual_executable_bytes'] or original['actual_executable_sha256']!=codec['target_sha256'] or
        correction['correct_dictionary_sha256']!=codec['base_sha256'] or correction['correct_dictionary_bytes']!=codec['base_bytes']):raise ValueError('unsupported/mismatched immutable reference correction')
    original['actual_executable_sha256']=correction['correct_dictionary_sha256'];original['actual_executable_bytes']=correction['correct_dictionary_bytes']
    result['applied_reference_correction']=dict(file=path.name,sha256=sha256(path),original_index_sha256=index_sha,
        scope='Two mistaken dictionary identity fields only; original immutable index retained. Actual dictionary and target bytes still independently decoded/hash-verified.')
    return result,sha256(path)


@lru_cache(maxsize=2)
def _read(project,generation,index_sha,archive_sha,dictionary_identity=None,packet_root=None):
    root=RAW/project/('retained-native-v'+str(generation)) if packet_root is None else Path(packet_root)
    index=json.loads((root/'index.json').read_text())
    if sha256(root/'index.json')!=index_sha or index['project']!=project or index['generation']!=generation or len(index['files'])>10000:raise ValueError('native packet index scope/identity differs')
    index,_=corrected_index(root,index,index_sha)
    archive=archive_path(root,index)
    if sha256(archive)!=archive_sha or archive_sha!=index['archive_sha256'] or archive.stat().st_size>16*1024**2:raise ValueError('required retained native archive missing/changed/bound')
    files=index['files'];physical=physical_members(files)
    if sum(r['bytes'] for r in files.values())>128*1024**2 or any(r['bytes']>16*1024**2 for r in files.values()):raise ValueError('native logical evidence bound')
    verify(archive,files);payloads={}
    with tarfile.open(archive,tar_mode(index,stream=True)) as stream:
        for member in stream:
            if not member.isfile() or member.name not in physical or member.name in payloads or member.size!=physical[member.name]['bytes']:raise ValueError('native physical member coverage/type differs')
            data=stream.extractfile(member).read(16*1024**2+1)
            if len(data)!=member.size or hashlib.sha256(data).hexdigest()!=physical[member.name]['sha256']:raise ValueError('native actual retained member bytes differ')
            payloads[member.name]=data
    if set(payloads)!=set(physical):raise ValueError('native evidence omitted physical member')
    result={name:payloads[row.get('member',name)] for name,row in files.items()}
    external=index.get('external_exact_payloads')
    if external:
        required=index['required_canonical_packet']
        base_generation=required['generation']
        if type(base_generation)!=int or not 1<=base_generation<generation or len(files)+len(external)>10000:
            raise ValueError('unsafe external exact-payload packet reference')
        canonical_index,canonical=read_packet(project,base_generation)
        if (canonical_index.get('external_exact_payloads') or canonical_index.get('runtime_frame_disposition') or canonical_index.get('solid_runtime_disposition') or
                canonical_index['archive_sha256']!=required['archive_sha256'] or
                sha256(RAW/project/('retained-native-v'+str(base_generation))/'index.json')!=required['index_sha256']):
            raise ValueError('required standalone canonical packet differs or reference chain')
        for name,row in external.items():
            if (name in result or name.startswith('/') or any(p in {'','.','..'} or ':' in p or '\\' in p for p in name.split('/')) or
                    row['canonical_logical_path'] not in canonical):raise ValueError('unsafe/missing external logical payload')
            data=canonical[row['canonical_logical_path']]
            if len(data)!=row['bytes'] or hashlib.sha256(data).hexdigest()!=row['sha256']:raise ValueError('external exact bytes differ')
            result[name]=data
        if sum(len(data) for data in result.values())>128*1024**2:raise ValueError('restored logical packet byte bound')
    disposition=index.get('runtime_frame_disposition')
    if disposition:
        from next20_native_runtime_reference import binary_bundle
        required=disposition['required_canonical_runtime'];match=re.fullmatch(re.escape(project)+r'/retained-native-v([0-9]{1,4})/packets\.tar\.gz',required['archive'])
        if not match or int(match[1])>=generation:raise ValueError('native runtime dictionary chain/cycle/escape')
        canonical_index,canonical=read_packet(project,int(match[1]))
        if canonical_index.get('runtime_frame_disposition'):raise ValueError('native runtime dictionary chain forbidden')
        bundle=binary_bundle(canonical[required['logical_frame']],json.loads(canonical[required['logical_frame_index']]))
        base=bundle[required['actual_executable_member']]
        if len(base)!=required['actual_executable_bytes'] or hashlib.sha256(base).hexdigest()!=required['actual_executable_sha256']:raise ValueError('required canonical native executable changed')
        current=disposition['current_native_executable'];representation=current['representation']
        if representation['kind']=='identical-canonical-payload':actual=base
        elif representation['kind']=='copy-insert-v1+xz':
            from next20_archive_delta import decode
            actual=decode(base,result[representation['logical_delta']],representation['codec'])
        elif representation['kind']=='raw-lzma2-preset-dictionary-v1':
            from next20_lzma_dictionary import decode
            actual=decode(base,result[representation['logical_delta']],representation['codec'])
        else:raise ValueError('unknown native runtime payload representation')
        if len(actual)!=current['bytes'] or hashlib.sha256(actual).hexdigest()!=current['sha256']:raise ValueError('actual native executable payload reconstruction differs')
        if disposition['old_compressed_frame_bytes_reconstructible']:raise ValueError('superseded unlike frame cannot claim byte reconstruction')
        for name,reference in disposition['current_exact_metadata'].items():
            data=result[reference['logical_path']]
            if len(data)!=reference['bytes'] or hashlib.sha256(data).hexdigest()!=reference['sha256']:raise ValueError('current actual native build/version metadata differs')
            if name=='build.json' and json.loads(data)['binary_sha256']!=current['sha256']:raise ValueError('current build does not bind retained actual executable')
    if index.get('solid_runtime_disposition'):
        from next20_cargo_solid_reference import restore
        restore(result,index['solid_runtime_disposition'])
    return index,result


def read_packet(project,generation,*,stage=False):
    if '/' in project or '\\' in project or not 1<=generation<=1000:raise ValueError('invalid native reader scope')
    root=(RAW/'tmp/direct-native-zip'/project if stage else RAW/project)/('retained-native-v'+str(generation));root.resolve(strict=True).relative_to(RAW.resolve(strict=True))
    for ancestor in [root,root.parent,RAW/'tmp/direct-native-zip' if stage else RAW/project,RAW/'tmp' if stage else RAW,RAW,RAW.parent]:
        if ancestor.is_symlink() or getattr(ancestor,'is_junction',lambda:False)():raise ValueError('linked native reader ancestor')
    proof=json.loads((root/'verified.json').read_text());index_sha=sha256(root/'index.json')
    if index_sha!=proof['index_sha256']:raise ValueError('native evidence index changed')
    index=json.loads((root/'index.json').read_text());archive=archive_path(root,index);archive_sha=sha256(archive)
    if archive.is_symlink() or getattr(archive,'is_junction',lambda:False)():raise ValueError('linked retained native archive')
    if archive_sha!=proof['archive_sha256']:raise ValueError('native evidence archive changed')
    index,correction_sha=corrected_index(root,index,index_sha)
    dictionary_identity=correction_sha
    disposition=index.get('runtime_frame_disposition') or index.get('solid_runtime_disposition')
    if index.get('external_exact_payloads'):
        required=index['required_canonical_packet'];number=required['generation']
        if type(number)!=int or not 1<=number<generation:raise ValueError('unsafe external canonical generation')
        base=RAW/project/('retained-native-v'+str(number));base.resolve(strict=True).relative_to((RAW/project).resolve(strict=True))
        if base.is_symlink() or getattr(base,'is_junction',lambda:False)():raise ValueError('linked canonical exact-payload root')
        base_index=json.loads((base/'index.json').read_text());base_archive=archive_path(base,base_index)
        if sha256(base/'index.json')!=required['index_sha256'] or sha256(base_archive)!=required['archive_sha256']:
            raise ValueError('required canonical exact-payload packet missing/changed')
        dictionary_identity=required['index_sha256']+':'+required['archive_sha256']
    if disposition:
        required=disposition['required_canonical_runtime'];match=re.fullmatch(re.escape(project)+r'/retained-native-v([0-9]{1,4})/packets\.tar\.gz',required['archive'])
        if not match or int(match[1])>=generation:raise ValueError('unsafe required native dictionary reference')
        base=RAW/required['archive'];base.resolve(strict=True).relative_to((RAW/project).resolve(strict=True))
        if base.is_symlink() or base.parent.is_symlink() or getattr(base.parent,'is_junction',lambda:False)():raise ValueError('linked native runtime dictionary')
        base_index=sha256(base.parent/'index.json');base_archive=sha256(base)
        if base_index!=required['index_sha256'] or base_archive!=required['archive_sha256']:raise ValueError('required canonical runtime dictionary missing/changed')
        dictionary_identity=base_index+':'+base_archive+':'+str(correction_sha)
    return _read(project,generation,index_sha,archive_sha,dictionary_identity,str(root))
