"""Check compiled Node evidence against retained source and registry payloads."""
import base64
import copy
import hashlib
import io
import json
import posixpath
import tarfile


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tar_files(data):
    require(len(data) <= 16*1024**2, 'Node package archive size bound')
    result = {}; expanded = entries = 0
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:gz') as archive:
        for member in archive:
            entries += 1; expanded += member.size
            require(entries <= 10000 and expanded <= 64*1024**2, 'Node package expansion bound')
            name = member.name
            require(not name.startswith('/') and '..' not in name.split('/'), 'unsafe Node package path')
            require(member.isdir() or member.isfile(), 'unreviewed Node package special entry')
            if not member.isfile():
                continue
            require(member.size <= 4*1024**2 and '/' in name, 'Node package member bound/root')
            relative = name.split('/', 1)[1]
            require(relative not in result, 'duplicate Node package member')
            result[relative] = archive.extractfile(member).read(4*1024**2+1)
    return result


def dependencies(get, raw, hash_of, host, provenance):
    """Reconstruct installed module bytes from canonical SRI-checked packages."""
    from next20_cz_cli_lock import BUILD_ROOTS, closure
    source = tar_files(raw('cz-cli/retained-source/source.tar.gz'))
    require({n:digest(v) for n,v in source.items()} == provenance['files'], 'retained Node source is not canonical')
    canonical = json.loads(source['package-lock.json'])
    metadata = json.loads(source['package.json'])
    fetched = get('cz-cli/retained-source/dependency-fetch.json')
    require(fetched['hooks_disabled'] and fetched['bin_links_disabled'], 'Node install hooks/bin links enabled')
    require(fetched['source_lock_sha256'] == digest(source['package-lock.json']), 'Node source lock changed')
    # Cache index metadata is not evidence of downloaded package contents.
    # Locate actual retained content, then check canonical upstream SRI bytes.
    cache = raw(None)
    cache = [v for n,v in cache.items() if '/retained-source/npm-cache/_cacache/content-v2/' in n]
    sri_cache = {}
    for algorithm in ('sha512', 'sha1'):
        for data in cache:
            sri_cache[(algorithm, hashlib.new(algorithm, data).digest())] = data
    scopes = [('build-toolchain', BUILD_ROOTS), ('app', list(metadata['dependencies']))]
    reconstructed = {}
    for scope, roots in scopes:
        selected = closure(canonical['packages'], ['node_modules/'+n for n in roots])
        lock_name = 'cz-cli/retained-source/npm-installed-locks/'+scope+'.json'
        installed = get(lock_name)
        require(hash_of(lock_name) == fetched['installed_files'][scope]['node_modules/.package-lock.json'], 'installed Node lock byte mismatch')
        require(set(installed['packages']) == set(selected), 'installed Node closure differs from canonical lock')
        expected = {}
        # Outer packages precede nested physical dependencies, which replace
        # files only at their exact canonical physical node_modules paths.
        for name, row in sorted(selected.items(), key=lambda item:(item[0].count('/'),item[0])):
            actual = installed['packages'][name]
            require(actual['version'] == row['version'] and actual.get('integrity') == row.get('integrity') and actual.get('resolved') == row.get('resolved'), 'installed Node package provenance differs')
            os_name = 'win32' if host == 'windows' else host
            if row.get('optional') and row.get('os') and os_name not in row['os']:
                require(not any(n.startswith(name+'/') for n in fetched['installed_files'][scope]), 'OS-excluded optional package installed')
                continue
            algorithm, encoded = row['integrity'].split('-',1)
            require(algorithm in {'sha1','sha512'} and row['resolved'].startswith('https://registry.npmjs.org/'), 'unreviewed Node package registry/integrity')
            payload = sri_cache.get((algorithm,base64.b64decode(encoded,validate=True)))
            require(payload is not None, 'missing actual canonical Node package payload: '+name)
            files = tar_files(payload)
            package = json.loads(files['package.json'])
            require(package['version'] == row['version'], 'registry package version differs from lock')
            for relative, data in files.items():
                expected[name+'/'+relative] = digest(data)
        # npm synthesizes its hidden lock; all other files must come from
        # canonical upstream packages or the explicitly prepared root.
        expected['node_modules/.package-lock.json'] = hash_of(lock_name)
        if scope == 'app':
            expected.update({n:digest(v) for n,v in source.items() if n in {'package.json','package-lock.json'} or n.startswith('bin/')})
        else:
            root = dict(name='playtestr-owned-cz-cli-build',version='0.0.0',private=True,
                        dependencies={n:metadata['devDependencies'][n] for n in BUILD_ROOTS})
            chosen = copy.deepcopy(selected)
            for row in chosen.values():
                row.pop('dev',None); row.pop('devOptional',None)
            build_lock = dict(name=root['name'],version=root['version'],lockfileVersion=3,requires=True,packages={'':root,**chosen})
            encode = lambda value:(json.dumps(value,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()
            expected.update({'package.json':digest(encode(root)), 'package-lock.json':digest(encode(build_lock)), 'babel.config.js':digest(source['babel.config.js'])})
            require(expected['package-lock.json'] == fetched['build_lock_sha256'], 'derived canonical build lock mismatch')
        actual = fetched['installed_files'][scope]
        require(actual == expected, 'installed '+scope+' bytes differ from canonical package payloads; missing='+str(sorted(set(expected)-set(actual))[:8])+' extra='+str(sorted(set(actual)-set(expected))[:8])+' changed='+str([n for n in expected.keys() & actual.keys() if expected[n]!=actual[n]][:8]))
        reconstructed[scope] = expected
    inventory = get('cz-cli/retained-source/installed-inventory.json')
    require(inventory['files'] == reconstructed['app'], 'executed Node inventory differs from independently reconstructed packages')
    return reconstructed


def compiled_payloads(proof, raw, expected_names):
    files = proof['compiled_files']; payloads = proof['compiled_payloads']
    require(set(files) == set(payloads) == set(expected_names), 'incomplete actual compiled Node output set')
    for name, sha in files.items():
        reference = payloads[name]
        require(reference == 'artifacts/runner-readiness-next-twenty-project-pass/cz-cli/compiled-payloads/'+sha+'.js', 'unsafe compiled Node payload reference')
        require(digest(raw(reference.split('/runner-readiness-next-twenty-project-pass/',1)[1])) == sha, 'compiled Node code payload differs from executed hash')


def host_contract(spec, runtime, host):
    result = copy.deepcopy(spec)
    old = '../app-v2/bin/git-cz'
    require(result['command'][2].count(old) == 1, 'canonical Node standard entry changed')
    result['command'][2] = result['command'][2].replace(old, '../'+runtime['app_relative_path']+'/'+runtime['entrypoint'])
    if host == 'linux':
        result['env'].update(PATH='/usr/bin:/bin', GIT_CONFIG_GLOBAL='/dev/null')
        result['inherit_env'] = []
        # Only the two declared interruption cases have a CtrlC input.
        if any(s.get('key') == 'CtrlC' for s in result['steps']):
            for step in result['steps']:
                if 'exit' in step:
                    require(step['exit'] == 1, 'canonical Windows interruption exit differs')
                    step['exit'] = 130
    return result


def main():
    import argparse
    import os
    import uuid
    from next20_check import RAW, DOC
    from readiness_evidence import immutable_json, sha256
    parser = argparse.ArgumentParser()
    parser.add_argument('--local-dependencies', action='store_true', required=True)
    parser.add_argument('--challenge-local', action='store_true')
    args = parser.parse_args()
    target = RAW/'active/cz-cli'
    def get(relative):
        return json.loads((target/relative.removeprefix('cz-cli/retained-source/')).read_text(encoding='utf-8'))
    cache = {'cz-cli/retained-source/'+p.relative_to(target).as_posix():p.read_bytes()
             for p in (target/'npm-cache/_cacache/content-v2').rglob('*') if p.is_file()}
    def raw(relative):
        if relative is None:
            return cache
        return (target/relative.removeprefix('cz-cli/retained-source/')).read_bytes()
    def hash_of(relative):
        return sha256(target/relative.removeprefix('cz-cli/retained-source/'))
    provenance = json.loads((DOC/'cz-cli/source-provenance.json').read_text(encoding='utf-8'))
    result = dependencies(get, raw, hash_of, 'windows' if os.name=='nt' else 'linux', provenance)
    controls = []
    if args.challenge_local:
        for name in ['changed-source-lock','changed-installed-module','missing-registry-payloads']:
            def changed_get(relative):
                value = get(relative)
                if relative.endswith('/dependency-fetch.json'):
                    value = copy.deepcopy(value)
                    if name == 'changed-source-lock':value['source_lock_sha256'] = '0'*64
                    if name == 'changed-installed-module':value['installed_files']['app']['node_modules/cz-conventional-changelog/index.js'] = '0'*64
                return value
            def changed_raw(relative):
                return {} if relative is None and name == 'missing-registry-payloads' else raw(relative)
            try:
                dependencies(changed_get,changed_raw,hash_of,'windows' if os.name=='nt' else 'linux',provenance)
            except ValueError as error:
                controls.append(dict(control=name,rejected=True,reason=str(error)))
            else:
                raise ValueError('Altered actual Node dependency evidence accepted: '+name)
        # Check exact actual compiled bytes, then challenge one recorded hash.
        build = get('cz-cli/retained-source/build.json')
        supplement = json.loads((RAW/'cz-cli/compiled-byte-supplement.json').read_text(encoding='utf-8'))
        proof = dict(compiled_files=build['compiled_files'],compiled_payloads=supplement['original_payloads'])
        def code_raw(relative):return (RAW/relative).read_bytes()
        compiled_payloads(proof,code_raw,proof['compiled_files'])
        changed = copy.deepcopy(proof)
        changed['compiled_files'][next(iter(changed['compiled_files']))] = '0'*64
        try:compiled_payloads(changed,code_raw,proof['compiled_files'])
        except ValueError as error:controls.append(dict(control='changed-compiled-module-hash',rejected=True,reason=str(error)))
        else:raise ValueError('Altered actual compiled module accepted')
    destination = RAW/'cz-cli/dependency-audits'/uuid.uuid4().hex
    immutable_json(destination/'verified.json', dict(schema_version=1,
        scopes={k:len(v) for k,v in result.items()}, controls=controls,source_provenance_sha256=sha256(DOC/'cz-cli/source-provenance.json'),
        scope='Local dependency byte reconstruction from actual canonical SRI-checked cache packages. No native or project admission credit.'))
    print('Independently reconstructed actual Node dependency bytes:', {k:len(v) for k,v in result.items()})


if __name__ == '__main__':
    main()
