"""Reconstruct actual installed npm files from pinned integrity-checked archives."""
import base64
import hashlib
import json
import posixpath

from next20_verify_node import tar_files


def project_paths(files,platform):
    """Apply the reviewed pacote/tar path projection without changing bytes."""
    projected={};folded={};ignores=set();changes=[]
    for original,data in files.items():
        name=posixpath.normpath(original)
        if name.startswith(('../','/')) or name in {'.','..'}:raise ValueError('unsafe normalized package path')
        if name!=original:changes.append(dict(archive=original,installed=name,kind='normalized-relative-path'))
        base=posixpath.basename(name)
        if base=='.npmignore':ignores.add(name)
        elif base=='.gitignore':
            replacement=posixpath.join(posixpath.dirname(name),'.npmignore')
            if replacement in ignores:
                changes.append(dict(archive=original,installed=replacement,kind='ignored-after-explicit-npmignore'));continue
            changes.append(dict(archive=original,installed=replacement,kind='pacote-ignore-rename'));name=replacement
        if platform=='win32':
            previous=folded.get(name.casefold())
            if previous is not None and previous!=name:
                if posixpath.dirname(previous)!=posixpath.dirname(name):raise ValueError('unreviewed package directory case collision')
                projected.pop(previous)
                changes.append(dict(archive=original,installed=name,replaced=previous,kind='windows-case-insensitive-last-file'))
            folded[name.casefold()]=name
        projected[name]=data
    return projected,changes


def reconstruct(packages,installed,cache,platform):
    if set(installed)-set(packages):raise ValueError('installed npm package absent from canonical lock')
    expected={};reviews=[];sha1_cache=None
    for name,row in sorted(packages.items(),key=lambda item:(item[0].count('/'),item[0])):
        excluded=row.get('optional') and row.get('os') and platform not in row['os']
        actual=installed.get(name)
        if actual is None and not excluded:raise ValueError('required npm package absent from actual hidden lock: '+name)
        if actual is not None and any(actual.get(key)!=row.get(key) for key in ['version','resolved','integrity']):
            raise ValueError('actual npm package differs from pinned canonical identity: '+name)
        if excluded:
            reviews.append(dict(path=name,skip='canonical optional OS exclusion',platforms=row['os']));continue
        if not name.startswith('node_modules/') or not row.get('resolved','').startswith('https://registry.npmjs.org/'):
            raise ValueError('unreviewed npm package physical source: '+name)
        algorithm,encoded=row['integrity'].split('-',1);wanted=base64.b64decode(encoded,validate=True)
        if algorithm=='sha512':
            encoded_hex=wanted.hex();key='_cacache/content-v2/sha512/'+encoded_hex[:2]+'/'+encoded_hex[2:4]+'/'+encoded_hex[4:]
            payload=cache(key)
        elif algorithm=='sha1':
            if sha1_cache is None:sha1_cache={hashlib.sha1(data).digest():data for data in cache(None)}
            payload=sha1_cache[wanted]
        else:raise ValueError('unsupported canonical npm integrity algorithm')
        if len(payload)>16*1024**2 or hashlib.new(algorithm,payload).digest()!=wanted:raise ValueError('actual npm archive integrity differs')
        files,projection=project_paths(tar_files(payload),platform);metadata=json.loads(files['package.json'])
        if metadata['version']!=row['version']:raise ValueError('actual registry package version differs')
        for relative,data in files.items():expected[name+'/'+relative]=hashlib.sha256(data).hexdigest()
        reviews.append(dict(path=name,name=metadata['name'],version=metadata['version'],license=metadata.get('license'),
            integrity=row['integrity'],metadata_sha256=hashlib.sha256(files['package.json']).hexdigest(),
            archive_path_projection=projection,
            lifecycle_scripts={k:v for k,v in metadata.get('scripts',{}).items() if k in {'preinstall','install','postinstall','prepare'}}))
    return expected,reviews
