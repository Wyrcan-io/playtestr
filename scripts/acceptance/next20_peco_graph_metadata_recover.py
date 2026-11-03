"""Recover only exact historical Go graph metadata recorded before cleanup."""
import hashlib
import json
import urllib.request

from next20_check import DOC, RAW, ROOT
from readiness_evidence import immutable_json, sha256


def main():
    target=RAW/'active/peco';retained=RAW/'peco/retained-source'
    inventory=json.loads((retained/'cleanup-inventory.json').read_text());prepared=json.loads((retained/'prepared.json').read_text())
    if sha256(retained/'cleanup-inventory.json')!=prepared['cleanup_inventory_sha256'] or inventory['owned_target']!=str(target) or sha256(target/'task-owned.json')!=inventory['owner_sha256']:
        raise ValueError('original checked metadata inventory/ownership differs')
    root=RAW/'peco/graph-metadata-recovery-v1';root.mkdir(exist_ok=False)
    prefix='gopath/pkg/mod/cache/download/'
    entries={n:r for n,r in inventory['files'].items() if n.startswith(prefix) and '/@v/' in n and n.endswith(('.mod','.info'))}
    if not entries or len(entries)>128 or sum(r['bytes'] for r in entries.values())>4*1024**2:raise ValueError('historical graph metadata count/byte bound')
    immutable_json(root/'planned.json',dict(schema_version=1,original_inventory_sha256=sha256(retained/'cleanup-inventory.json'),entries=entries,
        source='https://proxy.golang.org/',scope='Only original pinned .mod/.info bodies,each exact original SHA/length. No ZIP/source-code acquisition,build,dependency hook or target execution.'))
    acquired=[];existing=[]
    for name,row in sorted(entries.items()):
        if any(p in {'','.','..'} or any(c in p for c in ':\\?#%') for p in name.split('/')) or row['bytes']>65536:raise ValueError('unsafe historical metadata path/member bound')
        path=target/name;path.resolve().relative_to(target.resolve())
        if path.is_file():
            if path.stat().st_size!=row['bytes'] or sha256(path)!=row['sha256']:raise ValueError('existing historical metadata differs')
            existing.append(name);continue
        url='https://proxy.golang.org/'+name.removeprefix(prefix)
        with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-owned-metadata-review'}),timeout=20) as response:
            if response.status!=200 or not response.geturl().startswith('https://proxy.golang.org/'):raise ValueError('historical metadata origin/status differs')
            body=response.read(65537)
        saved=root/name;saved.parent.mkdir(parents=True,exist_ok=True);saved.open('xb').write(body)
        if len(body)!=row['bytes'] or hashlib.sha256(body).hexdigest()!=row['sha256']:raise ValueError('fresh historical metadata differs from actual original bytes; retain for review')
        path.parent.mkdir(parents=True,exist_ok=True);path.open('xb').write(body)
        acquired.append(dict(path=name,url=url,bytes=len(body),sha256=row['sha256']))
    immutable_json(root/'complete.json',dict(schema_version=1,original_inventory_sha256=sha256(retained/'cleanup-inventory.json'),acquired=acquired,existing_verified=existing,
        original_bytes_recovered_exact=True,source_code_changed=False,target_executed=False,scope='Actual immutable registry metadata bytes reobtained and independently compared to the original checked inventory. Original failed offline verification remains failed.'))
    print('Recovered',len(acquired),'exact original historical metadata bodies;',len(existing),'existing bodies verified. No target/source-code execution.')


if __name__=='__main__':main()
