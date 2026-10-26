"""Independently reconstruct yo interpreted runtime and declared source copies."""
import base64
import copy
import hashlib
import json
import posixpath

from next20_check import DOC, NAME
from next20_verify_node import digest, require, tar_files


def projected_files(payload, host):
    # Independent npm extraction model: normalize leading ./, honor npm's
    # gitignore rename, then serialize case-insensitive Windows file writes.
    original=tar_files(payload);result={};folded={}
    for name,data in original.items():
        name=posixpath.normpath(name)
        require(not name.startswith(('/', '../')) and name!='..','escaping package path')
        if posixpath.basename(name)=='.gitignore':
            renamed=posixpath.join(posixpath.dirname(name),'.npmignore')
            if renamed in result:continue
            name=renamed
        if host=='windows':
            previous=folded.get(name.casefold())
            if previous is not None:result.pop(previous)
            folded[name.casefold()]=name
        result[name]=data
    return result


def dependencies(get, raw, hash_of, host, provenance):
    from next20_cz_cli_lock import closure
    source=tar_files(raw('yo/retained-source/source.tar.gz'))
    require({n:digest(v) for n,v in source.items()}==provenance['files'],'yo retained source differs from canonical Git blobs')
    canonical=json.loads(source['package-lock.json']);metadata=json.loads(source['package.json'])
    framework=json.loads((DOC/'yo/generator-package-lock.json').read_text())
    source_framework=framework['packages']['node_modules/yeoman-generator']
    require(source_framework['version']=='10.2.1' and source_framework['integrity']=='sha512-Fhs5a10HofaiJEai1dRuFiWbqiLX0njzXlkBsExnQSCsHdu2FHsSa9tBvT86nRkcR/XgRHq4Z/1Qe/5kmaN+zg==','yo framework differs from reviewed primary source')
    fetched=get('yo/retained-source/dependency-fetch.json')
    require(fetched['hooks_disabled'] and fetched['bin_links_disabled'] and not fetched['target_executed'] and not fetched['framework_executed'],'yo setup executed hooks or target')
    require(fetched['source_lock_sha256']==digest(source['package-lock.json']),'yo canonical lock changed')
    require(fetched['framework_lock_sha256']==digest((DOC/'yo/generator-package-lock.json').read_bytes()),'yo frozen framework lock changed')
    cache=[v for n,v in raw(None).items() if '/retained-source/npm-cache/_cacache/content-v2/' in n]
    sri={}
    for data in cache:
        for algorithm in ('sha512','sha1'):sri[(algorithm,hashlib.new(algorithm,data).digest())]=data
    scopes=[('app',closure(canonical['packages'],['node_modules/'+n for n in metadata['dependencies']])),
            ('generator-toolchain',{n:r for n,r in framework['packages'].items() if n})]
    reconstructed={}
    for scope,selected in scopes:
        hidden='yo/retained-source/npm-installed-locks/'+scope+'.json';installed=get(hidden)['packages']
        require(set(installed)==set(selected),'yo hidden lock package membership differs')
        expected={}
        for name,row in sorted(selected.items(),key=lambda item:(item[0].count('/'),item[0])):
            actual=installed[name]
            require(all(actual.get(k)==row.get(k) for k in ('version','integrity','resolved')),'yo installed package provenance differs')
            algorithm,encoded=row['integrity'].split('-',1)
            require(algorithm in {'sha512','sha1'} and row['resolved'].startswith('https://registry.npmjs.org/'),'unreviewed yo dependency registry')
            payload=sri.get((algorithm,base64.b64decode(encoded,validate=True)))
            require(payload is not None,'missing actual yo canonical package payload: '+name)
            files=projected_files(payload,host)
            require(json.loads(files['package.json'])['version']==row['version'],'yo package version differs')
            expected.update({name+'/'+n:digest(v) for n,v in files.items()})
        expected['node_modules/.package-lock.json']=hash_of(hidden)
        if scope=='app':
            expected.update({n:digest(v) for n,v in source.items() if n in {'package.json','package-lock.json'} or n.startswith('lib/')})
        else:
            root=dict(name='playtestr-owned-yo-generator',version='0.0.0',private=True,dependencies={'yeoman-generator':'10.2.1'})
            expected['package.json']=digest((json.dumps(root,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode())
            expected['package-lock.json']=digest((DOC/'yo/generator-package-lock.json').read_bytes())
        require(expected==fetched['installed_files'][scope],'yo installed '+scope+' differs from canonical SRI bytes')
        reconstructed[scope]=expected
    inventory=get('yo/retained-source/installed-inventory.json')
    require(inventory['files']=={scope+'/'+n:v for scope,files in reconstructed.items() for n,v in files.items()},'yo executed inventory differs from reconstructed complete runtime')
    return reconstructed


def host_contract(spec, runtime, host):
    result=copy.deepcopy(spec)
    require(result['command'][2].count('../runtime/app/lib/cli.js')==1,'yo standard entry route changed')
    if host=='linux':
        result['env']['GIT_CONFIG_GLOBAL']='/dev/null';result['inherit_env']=[]
        if any(s.get('key')=='CtrlC' for s in result['steps']):
            for step in result['steps']:
                if 'exit' in step:
                    require(step['exit']==1,'yo canonical Windows interrupt differs');step['exit']=130
    return result


def assembly(proof, get, raw, hash_of, source, inventory):
    receipt=proof['assembly_receipt'].removeprefix('artifacts/'+NAME+'/')
    require(hash_of(receipt)==proof['assembly_receipt_sha256'],'yo source assembly receipt changed')
    value=get(receipt);planned=posixpath.dirname(receipt)+'/planned.json'
    require(value['mode']==proof['mode']=='copied-interpreted-source' and value['compiler_execution'] is proof['compiler_execution'] is False,'yo falsely claims compiled source')
    require(value['source_inputs']==get(planned)['source_inputs']==source and value['planned_sha256']==hash_of(planned),'yo source copy plan differs')
    mapping={n:'app/'+n for n in source if n.startswith('lib/')}
    require(value['copied_source_files']==get(planned)['copied_source_files']==mapping,'yo declared copied module membership differs')
    require(value['copied_payloads']==proof['copied_payloads'] and set(proof['copied_payloads'])==set(mapping.values()),'yo source payload set differs')
    expected=dict(inventory)
    for original,copied in mapping.items():
        payload=proof['copied_payloads'][copied]
        require(payload['sha256']==source[original] and payload['path']=='artifacts/'+NAME+'/yo/interpreted-payloads/'+source[original],'yo source payload reference differs')
        require(digest(raw(payload['path'].removeprefix('artifacts/'+NAME+'/')))==source[original],'yo executed interpreted source bytes differ')
        expected[copied]=source[original]
    require(value['runtime_catalog']==proof['catalog_path'] and value['runtime_catalog_sha256']==proof['catalog_sha256'],'yo assembly launch catalog reference differs')
    return expected
