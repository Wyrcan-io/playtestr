"""Independent bounded synthetic sdist format, with explicit reviewed metadata.

No Poetry builder/output function is imported. Inputs are the reviewed fixture,
fixed package metadata and declared native filename ordering. Compression uses
the host's standard gzip runtime before executing the target scenario.
"""
import gzip
import io
import tarfile


METADATA=('Metadata-Version: 2.4\nName: fixture-app\nVersion: 1.2.3\n'
          'Summary: Reviewed local fixture\nAuthor: Fixture Author\n'
          'Author-email: author@example.invalid\nRequires-Python: >=3.10\n'
          'Classifier: Programming Language :: Python :: 3\n'+
          ''.join(f'Classifier: Programming Language :: Python :: 3.{minor}\n' for minor in range(10,16))+
          'Description-Content-Type: text/markdown\n\nReviewed package\n\n').encode()


def reviewed_archive(fixture,windows):
    files=['README.md','fixture_app/__init__.py','pyproject.toml']
    files.sort(key=str.casefold if windows else str)
    buffer=io.BytesIO()
    with gzip.GzipFile(filename='fixture_app-1.2.3.tar.gz',mode='wb',fileobj=buffer,mtime=946684800) as compressed:
        with tarfile.TarFile(mode='w',fileobj=compressed,format=tarfile.PAX_FORMAT) as bundle:
            for name in [*files,'PKG-INFO']:
                value=METADATA if name=='PKG-INFO' else (fixture/name).read_bytes()
                if len(value)>16384:raise ValueError('reviewed fixture member byte bound')
                entry=tarfile.TarInfo('fixture_app-1.2.3/'+name)
                entry.mode=0o644;entry.uid=entry.gid=0;entry.uname=entry.gname=''
                entry.mtime=946684800;entry.size=len(value)
                bundle.addfile(entry,io.BytesIO(value))
    result=buffer.getvalue()
    if len(result)>65536:raise ValueError('reviewed archive byte bound')
    return result
