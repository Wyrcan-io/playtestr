"""Capture a reproducible real gem, then independently inspect every payload."""
import asyncio
import base64
import gzip
import hashlib
import io
import json
import tarfile

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_rubygems_cases import PACKAGE, SENTINEL, environment

GEMSPEC=b'''Gem::Specification.new do |s|
  s.name = "fixture_atlas"
  s.version = "1.2.3"
  s.summary = "Reviewed offline fixture"
  s.authors = ["Fixture Author"]
  s.email = "author@example.invalid"
  s.license = "MIT"
  s.homepage = "https://example.invalid/fixture"
  s.files = ["README.md", "lib/fixture_atlas.rb"]
end
'''


def members(data, expected):
    result={}
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:') as archive:
        for item in archive:
            if not item.isfile() or item.name not in expected or item.name in result or item.size>16384:
                raise RuntimeError('unreviewed archive member')
            result[item.name]=archive.extractfile(item).read(16385)
    assert set(result)==set(expected)
    return result


async def main():
    fixture=PACKAGE/'build-fixture';fixture.mkdir(exist_ok=False)
    (fixture/'lib').mkdir();(fixture/'dist').mkdir()
    files={'fixture_atlas.gemspec':GEMSPEC,'README.md':b'Reviewed local gem\n',
           'lib/fixture_atlas.rb':b'module FixtureAtlas\n  VERSION = "1.2.3"\nend\n','sentinel.txt':SENTINEL}
    for name,value in files.items():(fixture/name).write_bytes(value)
    runner=RAW/'bin'/('playtestr.exe' if __import__('os').name=='nt' else 'playtestr')
    spec=PACKAGE/'normal-build-gem.json'
    reference=json.loads((PACKAGE/'normal-gem.json').read_text())
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture','build-fixture',
          '--temporary-home','--temporary-temp','--inherit-env','RUBYLIB','--timeout-ms','10000',
          '--run-timeout-ms','120000']
    for key,value in {**reference['env'],'SOURCE_DATE_EPOCH':'946684800','PROGRAMDATA':'.'}.items():
        argv+=['--env',key+'='+value]
    argv+=['--','ruby','-EUTF-8','-S','gem','build','fixture_atlas.gemspec','--output','dist/fixture_atlas-1.2.3.gem']
    controls='/expect Successfully built RubyGem\n/expect Version: 1.2.3\n/exit 0\n/file dist/fixture_atlas-1.2.3.gem\n'
    controls+=''.join('/file '+name+'\n' for name in files)
    controls+='/entries dist\n/review\n/replay\n/save\n'
    result=await execute(argv,'rubygems','record-reproducible-gem',input=controls,env=environment(),
                         timeout=180,campaign=Campaign())
    saved=json.loads(spec.read_text())
    observed={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in saved['steps'] if s.get('state',{}).get('kind')=='file'}
    for name,value in files.items():assert observed[name]==value
    gem=members(observed['dist/fixture_atlas-1.2.3.gem'],{'metadata.gz','data.tar.gz','checksums.yaml.gz'})
    payload=members(gzip.decompress(gem['data.tar.gz']),{'README.md','lib/fixture_atlas.rb'})
    for name,value in payload.items():assert value==files[name]
    metadata=gzip.decompress(gem['metadata.gz'])
    for line in [b'name: fixture_atlas\n',b'version: 1.2.3\n',b'summary: Reviewed offline fixture\n',b'- Fixture Author\n',b'- MIT\n']:
        assert line in metadata,line
    checksums=gzip.decompress(gem['checksums.yaml.gz'])
    for name in ['metadata.gz','data.tar.gz']:
        assert hashlib.sha256(gem[name]).hexdigest().encode() in checksums
        assert hashlib.sha512(gem[name]).hexdigest().encode() in checksums
    immutable_json(PACKAGE/'build-archive-review.json',dict(capture_attempt=result['id'],
        spec_sha256=sha256(spec),archive_bytes=len(observed['dist/fixture_atlas-1.2.3.gem']),
        members=sorted(gem),source_payloads_equal_reviewed_fixture=True,metadata_fields_verified=True,
        both_internal_checksums_verified=True,fresh_public_replay_passed=True,qualification='development only'))
    print('Real gem reviewed independently; unchanged source, exact binary and fresh public replay pass.')


if __name__=='__main__':asyncio.run(main())
