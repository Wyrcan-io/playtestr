"""Download an explicitly reviewed native wheel set without dependency resolution."""
import hashlib
import re
import urllib.parse
import urllib.request


def validate_downloads(rows):
    if not isinstance(rows,list) or not 1<=len(rows)<=64:raise ValueError('frozen wheel count bound')
    names=set();packages=set();total=0
    for row in rows:
        name=row['filename'];package=row['name'];digest=row['sha256'];size=row['bytes']
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z0-9_.+-]{1,240}\.whl',name) or name in names:raise ValueError('unsafe/duplicate frozen wheel filename')
        if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',package) or package in packages:raise ValueError('unsafe/duplicate frozen distribution')
        if not re.fullmatch('[0-9a-f]{64}',digest) or type(size)!=int or not 0<size<=32*1024**2:raise ValueError('frozen wheel digest/size bound')
        parsed=urllib.parse.urlsplit(row['url'])
        if (parsed.scheme!='https' or parsed.hostname!='files.pythonhosted.org' or parsed.username or parsed.password or
            parsed.port not in (None,443) or parsed.query or parsed.fragment or urllib.parse.unquote(parsed.path.rsplit('/',1)[-1])!=name):raise ValueError('frozen wheel primary URL differs')
        names.add(name);packages.add(package);total+=size
    if total>64*1024**2:raise ValueError('frozen wheel total byte bound')
    return total


def download_frozen_wheels(rows,directory):
    total=validate_downloads(rows)
    if any(directory.iterdir()):raise ValueError('preserve existing frozen download directory')
    for row in rows:
        destination=directory/row['filename'];digest=hashlib.sha256();count=0
        request=urllib.request.Request(row['url'],headers={'User-Agent':'Playtestr-validation'})
        with urllib.request.urlopen(request,timeout=30) as response,destination.open('xb') as output:
            final=urllib.parse.urlsplit(response.url)
            if final.scheme!='https' or final.hostname!='files.pythonhosted.org':raise ValueError('unreviewed wheel redirect origin')
            while True:
                data=response.read(1024**2)
                if not data:break
                count+=len(data)
                if count>row['bytes']:raise ValueError('frozen native wheel exceeded declared bytes')
                output.write(data);digest.update(data)
        if count!=row['bytes'] or digest.hexdigest()!=row['sha256']:raise ValueError('downloaded native wheel differs from reviewed primary bytes')
    return dict(files=len(rows),bytes=total)
