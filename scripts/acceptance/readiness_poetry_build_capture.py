"""Review deterministic sdist bytes through the public recorder and inspect members."""
import asyncio
import base64
import io
import json
import os
import tarfile

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256


async def main():
    package=ROOT/'docs/validation/runner-readiness-ten-project-pass/poetry'
    spec=package/'normal-build-sdist.json'
    if spec.exists():raise RuntimeError('preserve existing build capture')
    env=dict(os.environ)
    env['PATH']=str(RAW/'active/poetry/venv'/('Scripts' if os.name=='nt' else 'bin'))+os.pathsep+env['PATH']
    runner=RAW/'bin'/('playtestr.exe' if os.name=='nt' else 'playtestr')
    argv=[runner,'record','--output',spec.relative_to(ROOT),'--fixture','project-fixture',
          '--temporary-home','--temporary-temp','--timeout-ms','10000','--run-timeout-ms','120000']
    for key,value in [('SOURCE_DATE_EPOCH','946684800'),('POETRY_VIRTUALENVS_CREATE','false'),
                      ('POETRY_KEYRING_ENABLED','false'),('PYTHONDONTWRITEBYTECODE','1'),('PIP_NO_INDEX','1'),
                      ('GIT_CONFIG_NOSYSTEM','1'),('GIT_CONFIG_GLOBAL',os.devnull)]:argv+=['--env',key+'='+value]
    argv+=['--','poetry','--no-plugins','build','--format','sdist','--output','dist','--no-interaction']
    result=await execute(argv,'poetry','record-build-sdist-review-replay',env=env,timeout=180,campaign=Campaign(),
        input='/expect Building sdist\n/expect Built fixture_app-1.2.3.tar.gz\n/exit 0\n/file dist/fixture_app-1.2.3.tar.gz\n/entries dist\n/review\n/replay\n/save\n')
    data=json.loads(spec.read_text())
    archive=base64.b64decode(next(s['state']['bytes_base64'] for s in data['steps'] if s.get('state',{}).get('kind')=='file'))
    members={}
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as bundle:
        for member in bundle:
            if len(members)>=10 or not member.isfile() or member.size>16384 or member.name in members:
                raise RuntimeError('unexpected source archive structure')
            members[member.name]=bundle.extractfile(member).read(16385)
    prefix='fixture_app-1.2.3/'
    assert set(members)=={prefix+name for name in ['README.md','fixture_app/__init__.py','pyproject.toml','PKG-INFO']}
    for name in ['README.md','fixture_app/__init__.py','pyproject.toml']:
        assert members[prefix+name]==(package/'project-fixture'/name).read_bytes()
    metadata=members[prefix+'PKG-INFO'].decode()
    for required in ['Name: fixture-app\n','Version: 1.2.3\n','Summary: Reviewed local fixture\n',
                     'Author: Fixture Author\n','Author-email: author@example.invalid\n','Requires-Python: >=3.10\n']:
        assert required in metadata.replace('\r\n','\n'),required
    immutable_json(package/'build-archive-review.json',dict(id='N08',capture_attempt=result['id'],
        spec_sha256=sha256(spec),archive_bytes=len(archive),member_names=sorted(members),
        source_payloads_equal_reviewed_fixture=True,metadata_required_fields_verified=True,
        capture_and_fresh_replay_passed=True,qualification='development only; native portability pending'))
    print('Reviewed sdist source payloads and metadata independently; public exact-byte fresh replay passed.')


if __name__=='__main__':asyncio.run(main())
