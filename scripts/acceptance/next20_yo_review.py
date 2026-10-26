"""Verify canonical installed payloads and assemble yo's unmodified ESM runtime."""
import argparse
import hashlib
import json
import os

from next20_check import RAW,ROOT,DOC
from next20_cz_cli_lock import closure
from next20_npm_payloads import reconstruct
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--native-review',action='store_true');args=parser.parse_args()
    target=RAW/'active/yo';source=target/'src';runtime=target/'runtime';package=DOC/'yo'
    provenance=json.loads((package/'source-provenance.json').read_text(encoding='utf-8'))
    fetched=json.loads((target/'dependency-fetch.json').read_text(encoding='utf-8'))
    if not fetched['hooks_disabled'] or not fetched['bin_links_disabled'] or fetched['target_executed'] or fetched['framework_executed']:
        raise ValueError('setup crossed declared hook/target execution boundary')
    if {p.relative_to(source).as_posix():sha256(p) for p in source.rglob('*') if p.is_file()}!=provenance['files']:
        raise ValueError('primary target source changed')
    def cache(relative):
        if relative is None:
            payloads=[];total=0
            for path in (target/'npm-cache/_cacache/content-v2').rglob('*'):
                if path.is_file():
                    total+=path.stat().st_size
                    if total>64*1024**2:raise ValueError('cache audit memory bound')
                    payloads.append(path.read_bytes())
            return payloads
        path=target/'npm-cache'/relative;path.resolve(strict=True).relative_to(target/'npm-cache')
        if path.is_symlink() or path.stat().st_size>16*1024**2:raise ValueError('unsafe package cache payload')
        return path.read_bytes()
    metadata=json.loads((source/'package.json').read_text(encoding='utf-8'))
    canonical=json.loads((source/'package-lock.json').read_text(encoding='utf-8'))
    generator_lock=json.loads((package/'generator-package-lock.json').read_text(encoding='utf-8'))
    scopes=[('app',closure(canonical['packages'],['node_modules/'+n for n in metadata['dependencies']])),
            ('generator-toolchain',{n:r for n,r in generator_lock['packages'].items() if n})]
    reviews=[];all_files={}
    for scope,locked in scopes:
        folder=runtime/scope;hidden=folder/'node_modules/.package-lock.json'
        installed=json.loads(hidden.read_text(encoding='utf-8'))['packages']
        expected,packages=reconstruct(locked,installed,cache,'win32' if os.name=='nt' else 'linux')
        expected['node_modules/.package-lock.json']=sha256(hidden)
        if scope=='app':
            for name,digest in provenance['files'].items():
                if name in {'package.json','package-lock.json'} or name.startswith('lib/'):expected[name]=digest
        else:
            root=dict(name='playtestr-owned-yo-generator',version='0.0.0',private=True,dependencies={'yeoman-generator':'10.2.1'})
            expected['package.json']=hashlib.sha256((json.dumps(root,sort_keys=True,ensure_ascii=True,indent=2)+'\n').encode()).hexdigest()
            expected['package-lock.json']=sha256(package/'generator-package-lock.json')
        actual={p.relative_to(folder).as_posix():sha256(p) for p in folder.rglob('*') if p.is_file()}
        if actual!=expected or actual!=fetched['installed_files'][scope]:
            raise ValueError('actual '+scope+' files differ from exact canonical archives; missing='+str(sorted(set(expected)-set(actual))[:8])+' extra='+str(sorted(set(actual)-set(expected))[:8])+' changed='+str([n for n in expected.keys()&actual.keys() if expected[n]!=actual[n]][:8]))
        for row in packages:reviews.append(dict(scope=scope,**row))
        all_files.update({scope+'/'+n:v for n,v in actual.items()})
    prerequisite=json.loads((target/'node-prerequisite.json').read_text(encoding='utf-8'));node=ROOT/str(prerequisite['node'])
    if sha256(node)!=prerequisite['node_sha256']:raise ValueError('actual reviewed Node changed')
    immutable_json(target/'dependency-review.json',dict(schema_version=1,approved=True,packages=reviews,
        source_provenance_sha256=sha256(package/'source-provenance.json'),dependency_fetch_sha256=sha256(target/'dependency-fetch.json'),
        all_hooks_disabled=True,all_installed_payloads_match_canonical_sri=True,
        source_strategy='Unmodified target lib/package metadata copied byte exactly; no target compilation. Official generator framework published dist files verified to primary registry SRI. Synthetic local generator uses actual public framework APIs.',
        target_execution_scope='Documented local generator with synthetic files, real terminal adapter and file conflict prompts; skip-install, no package.json writes or external services.'))
    if not args.native_review:
        immutable_json(package/'source-review.json',json.loads((target/'dependency-review.json').read_text(encoding='utf-8')))
    immutable_json(target/'installed-inventory.json',dict(schema_version=1,runtime_root=runtime.relative_to(ROOT).as_posix(),files=all_files))
    immutable_json(target/'runtime.json',dict(kind='node',node=str(node),node_sha256=sha256(node),
        source_pin=provenance['pin'],app_relative_path='runtime',entrypoint='app/lib/cli.js',
        installed_inventory_sha256=sha256(target/'installed-inventory.json'),prerequisite_sha256=sha256(target/'node-prerequisite.json')))
    immutable_json(target/'build.json',dict(schema_version=1,pin=provenance['pin'],mode='copied-interpreted-source',
        compiled_files={},source_inputs=provenance['files'],
        copied_source_files={n:'app/'+n for n in provenance['files'] if n.startswith('lib/')},
        runtime_sha256=sha256(target/'runtime.json'),installed_inventory_sha256=sha256(target/'installed-inventory.json'),
        scope='Verified source/module assembly only; no compiler execution or compiled-code claim.'))
    immutable_json(target/'launch-runtime-catalog.json',dict(schema_version=1,runtime_root=runtime.relative_to(ROOT).as_posix(),
        files=all_files,executable=node.relative_to(ROOT).as_posix(),executable_sha256=sha256(node),
        source_inventory_sha256=sha256(target/'installed-inventory.json')))
    print('Reviewed exact installed canonical package payloads:',len(reviews),'packages',len(all_files),'runtime files. Unmodified yo entry ready for declared public authoring; no target execution/admission yet.')


if __name__=='__main__':main()
