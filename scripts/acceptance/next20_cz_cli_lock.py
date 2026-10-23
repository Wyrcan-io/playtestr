"""Select the reviewed Babel build closure from cz-cli's exact upstream lock."""
import copy
import argparse
import base64
import json
from pathlib import PurePosixPath

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


BUILD_ROOTS=['@babel/cli','@babel/core','@babel/plugin-proposal-object-rest-spread',
             '@babel/preset-env','babel-plugin-istanbul']


def closure(packages,roots):
    selected={};pending=list(roots)
    def resolve(parent,name):
        parts=PurePosixPath(parent).parts
        for length in range(len(parts),-1,-1):
            prefix=parts[:length]
            if prefix and prefix[-1]=='node_modules':continue
            candidate='/'.join((*prefix,'node_modules',name))
            if candidate in packages:return candidate
        return None
    while pending:
        path=pending.pop()
        if path in selected:continue
        row=packages[path];selected[path]=copy.deepcopy(row)
        for name in set(row.get('dependencies',{}))|set(row.get('optionalDependencies',{}))|set(row.get('peerDependencies',{})):
            found=resolve(path,name)
            optional=name in row.get('optionalDependencies',{}) or row.get('peerDependenciesMeta',{}).get(name,{}).get('optional')
            if not found:
                if optional:continue
                raise ValueError('Pinned build dependency unresolved: '+path+' '+name)
            pending.append(found)
    return dict(sorted(selected.items()))


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-declaration',action='store_true');args=parser.parse_args()
    target=RAW/'active/cz-cli';source=target/'src';package=DOC/'cz-cli';package.mkdir(exist_ok=True)
    original=json.loads((source/'package-lock.json').read_text(encoding='utf-8'))
    metadata=json.loads((source/'package.json').read_text(encoding='utf-8'))
    chosen=closure(original['packages'],['node_modules/'+name for name in BUILD_ROOTS])
    root=dict(name='playtestr-owned-cz-cli-build',version='0.0.0',private=True,
        dependencies={name:metadata['devDependencies'][name] for name in BUILD_ROOTS})
    selected={}
    for name,row in chosen.items():
        integrity=row.get('integrity','');algorithm,separator,encoded=integrity.partition('-')
        if not row.get('resolved','').startswith('https://registry.npmjs.org/') or algorithm not in {'sha1','sha512'} or not separator:
            raise ValueError('Unreviewed build package provenance: '+name)
        if len(base64.b64decode(encoded,validate=True))!=({'sha1':20,'sha512':64}[algorithm]):raise ValueError('Invalid upstream package integrity: '+name)
        row.pop('dev',None);row.pop('devOptional',None)
        selected[name]=row
    builder=target/'build-toolchain';builder.mkdir()
    immutable_json(builder/'package.json',root)
    immutable_json(builder/'package-lock.json',dict(name=root['name'],version=root['version'],
        lockfileVersion=3,requires=True,packages={'':root,**selected}))
    (builder/'babel.config.js').write_bytes((source/'babel.config.js').read_bytes())
    receipt=dict(schema_version=1,
        canonical_package_sha256=sha256(source/'package.json'),canonical_lock_sha256=sha256(source/'package-lock.json'),
        roots=BUILD_ROOTS,upstream_locked_packages=len(original['packages'])-1,
        selected_build_packages=len(selected),packages={name:row['integrity'] for name,row in selected.items()},
        derived_package_sha256=sha256(builder/'package.json'),derived_lock_sha256=sha256(builder/'package-lock.json'),
        transformation='Select exact upstream physical resolution closure including required peers; retain every selected version/resolved/integrity. Remove development flags for the separate build-only root. Do not execute unrelated dev/release/hook packages.',
        canonical_config_sha256=sha256(source/'babel.config.js'),new_project_credit=0)
    if args.verify_declaration:
        if json.loads((package/'build-lock-derivation.json').read_text(encoding='utf-8'))!=receipt:
            raise ValueError('Native derived build closure differs from reviewed canonical declaration')
        immutable_json(target/'build-lock-derivation.json',receipt)
    else:immutable_json(package/'build-lock-derivation.json',receipt)
    print('Exact upstream Babel closure:',len(selected),'of',len(original['packages'])-1,'locked dependencies; no package execution.')


if __name__=='__main__':main()
