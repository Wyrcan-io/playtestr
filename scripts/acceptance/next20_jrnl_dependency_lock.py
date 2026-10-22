"""Lock reviewed common wheels and inspect the two Linux-only keyring dependencies."""
import hashlib
import io
import json
import urllib.request
import zipfile
from email.parser import BytesParser

from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


def fetch(url,limit):
    with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Playtestr-validation'}),timeout=30) as response:
        data=response.read(limit+1)
    if len(data)>limit:raise ValueError('dependency metadata/file limit')
    return data


def main():
    target=RAW/'active/jrnl';locks={};rows=[]
    for p in (target/'dependency-review').glob('*.metadata.txt'):
        meta=BytesParser().parsebytes(p.read_bytes())
        locks[meta['Name'].lower().replace('_','-')]=meta['Version']
    for name in ['SecretStorage','jeepney']:
        metadata=json.loads(fetch('https://pypi.org/pypi/'+name+'/json',2*1024**2))
        wheel=[r for r in metadata['urls'] if r['packagetype']=='bdist_wheel' and r['filename'].endswith('py3-none-any.whl')]
        if len(wheel)!=1:raise ValueError('Linux dependency needs a separately reviewed wheel choice')
        row=wheel[0];data=fetch(row['url'],2*1024**2)
        if hashlib.sha256(data).hexdigest()!=row['digests']['sha256']:raise ValueError('primary package wheel digest mismatch')
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            if any(n.endswith('.pth') or '.data/scripts/' in n for n in bundle.namelist()):raise ValueError('unreviewed dependency startup/script hook')
            names=[n for n in bundle.namelist() if n.endswith('.dist-info/METADATA')]
            meta=BytesParser().parsebytes(bundle.read(names[0]))
            reviewed={n:bundle.read(n).decode('utf-8') for n in bundle.namelist()
                if n in {'secretstorage/__init__.py','jeepney/__init__.py'} or n.endswith(('.dist-info/LICENSE','.dist-info/LICENSE.txt'))}
        path=target/'linux-dependency-review'/row['filename'];path.parent.mkdir(exist_ok=True)
        with path.open('xb') as stream:stream.write(data)
        immutable_json(path.with_suffix('.review.json'),dict(name=meta['Name'],version=meta['Version'],
            license=meta.get('License-Expression',meta.get('License')),requires_dist=meta.get_all('Requires-Dist',[]),
            primary_url=row['url'],sha256=sha256(path),review_inputs=reviewed,approved_for_execution=False))
        locks[meta['Name'].lower().replace('_','-')]=meta['Version']
        rows.append(dict(name=meta['Name'],version=meta['Version'],url=row['url'],sha256=sha256(path),
            license=meta.get('License-Expression',meta.get('License')),startup_hooks=False,
            local_review=path.with_suffix('.review.json').relative_to(RAW).as_posix()))
    immutable_json(target/'dependency-lock-proposed.json',dict(schema_version=1,versions=locks,
        linux_additions=rows,common_windows_wheels_sha256=sha256(target/'wheels.json'),
        scope='Pinned versions across Python 3.12 native hosts; foreign native wheel bytes must be checked against primary release digests and inventoried before installation. No target runtime/network operation approved by metadata alone.'))
    print(json.dumps(dict(versions=locks,linux_additions=rows),indent=2))


if __name__=='__main__':main()
