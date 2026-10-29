"""Approve exact reviewed Linux wheel closure before any hosted Hatch build."""
from email.parser import BytesParser
import hashlib
import json
import re
import tomllib
import urllib.parse
import zipfile

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'hatch';target=RAW/'active/hatch';linux=target/'linux-review-inputs'
    common_inputs=target/'wheel-review-inputs/index-v2.json';native_inputs=linux/'index.json'
    common=json.loads(common_inputs.read_text(encoding='utf-8'))['wheels'];native=json.loads(native_inputs.read_text(encoding='utf-8'))['wheels']
    normalize=lambda name:re.sub(r'[-_.]+','-',name.lower())
    rows={};metadata={};approvals={}
    for row in common+native:
        name=normalize(row['name']);is_native=row in native
        wheel=(linux/'wheels' if is_native else target/'wheels')/row['wheel']
        if sha256(wheel)!=row['sha256']:raise ValueError('reviewed wheel changed')
        primary=(linux/(name+'-'+row['version']+'.json')) if is_native else target/'wheel-review-inputs'/(row['wheel']+'.pypi.json')
        body=json.loads(primary.read_text(encoding='utf-8'));matches=[f for f in body['urls'] if f['filename']==row['wheel'] and f['digests']['sha256']==row['sha256'] and f['size']==row['bytes']]
        if len(matches)!=1:raise ValueError('reviewed primary wheel differs')
        url=matches[0]['url'];parsed=urllib.parse.urlsplit(url)
        if parsed.scheme!='https' or parsed.hostname!='files.pythonhosted.org' or parsed.username or parsed.password:raise ValueError('unexpected primary wheel origin')
        with zipfile.ZipFile(wheel) as archive:
            names=archive.namelist();selected=[n for n in names if n.endswith('.dist-info/METADATA') and len(n.split('/'))==2]
            if len(selected)!=1 or any(n in {'sitecustomize.py','usercustomize.py'} for n in names):raise ValueError('unexpected startup/metadata input')
            info=BytesParser().parsebytes(archive.read(selected[0]));metadata[name]=info
            if normalize(info['Name'])!=name or info['Version']!=row['version']:raise ValueError('actual dependency metadata differs')
            hooks={n:hashlib.sha256(archive.read(n)).hexdigest() for n in names if n.endswith('.pth') or '.data/scripts/' in n}
            if hooks:
                scripts={n:d for n,d in hooks.items() if '.data/scripts/' in n};startup={n:d for n,d in hooks.items() if n.endswith('.pth')}
                if name=='uv' and is_native:
                    if startup or {n.rsplit('/',1)[1] for n in scripts}!={'uv','uvx'} or any(not archive.read(n).startswith(b'\x7fELF') for n in scripts):raise ValueError('unreviewed Linux native uv scripts')
                else:
                    original=json.loads((target/'wheel-script-approval.json').read_text(encoding='utf-8')).get(row['wheel'])
                    if original!=dict(wheel_sha256=row['sha256'],scripts=scripts,startup_hooks=startup):raise ValueError('common startup/script review differs')
                approvals[row['wheel']]=dict(wheel_sha256=row['sha256'],scripts=scripts,startup_hooks=startup)
        rows[name]=dict(name=name,version=row['version'],filename=row['wheel'],sha256=row['sha256'],bytes=row['bytes'],url=url,primary_metadata_sha256=sha256(primary))
    # Evaluate actual distribution metadata against explicit intended Linux/Python
    # markers, then bind only the complete reachable closure. No pip resolution
    # on a future host is allowed to silently select a different binary wheel.
    env=default_environment();env.update(sys_platform='linux',os_name='posix',platform_system='Linux',platform_machine='x86_64',
        implementation_name='cpython',platform_python_implementation='CPython',python_version='3.12',python_full_version='3.12.0',extra='')
    source=tomllib.loads((target/'src/pyproject.toml').read_text(encoding='utf-8'))
    pending=[Requirement(r) for r in source['project']['dependencies']+source['build-system']['requires']+['editables~=0.3']]
    used=set();expanded=set()
    while pending:
        req=pending.pop()
        if req.marker and not req.marker.evaluate(env):continue
        name=normalize(req.name)
        if name not in rows or not req.specifier.contains(rows[name]['version'],prereleases=True):raise ValueError('Linux closure version missing/incompatible: '+str(req))
        info=metadata[name]
        if info.get('Requires-Python') and not SpecifierSet(info['Requires-Python']).contains('3.12.0'):raise ValueError('Linux dependency excludes intended Python3.12')
        used.add(name)
        for extra in sorted({*req.extras,''}):
            key=(name,extra)
            if key in expanded:continue
            expanded.add(key);markers=dict(env,extra=extra)
            for text in info.get_all('Requires-Dist',[]):
                child=Requirement(text)
                if not child.marker or child.marker.evaluate(markers):
                    child.marker=None;pending.append(child)
    if len(used)!=48 or 'pywin32-ctypes' in used:raise ValueError('reviewed Linux closure differs from expected48 distributions')
    setup=json.loads((package/'setup-declaration.json').read_text(encoding='utf-8'));generated=target/'src/src/hatch/_version.py'
    lock=dict(schema_version=1,module='hatch',expected_version=setup['built_source_version'],version_args=['--version'],
        versions={n:r['version'] for n,r in sorted(rows.items())},reviewed_linux_additions=sorted({normalize(r['name']) for r in native}-{'uv','backports-zstd'}),
        source_review_sha256=sha256(package/'source-review.json'),common_wheels_sha256=sha256(target/'wheels.json'),
        common_primary_inputs_sha256=sha256(common_inputs),linux_review_inputs_sha256=sha256(native_inputs),
        frozen_wheel_downloads=[rows[n] for n in sorted(used)],wheel_hook_approvals=approvals,
        additional_build_requirements=['editables~=0.3'],build_environment=setup['version_environment'],
        generated_source_files=['src/hatch/_version.py'],generated_source_normalized_sha256={'src/hatch/_version.py':hashlib.sha256(generated.read_bytes().replace(b'\r\n',b'\n')).hexdigest()},
        explicit_python_application_profile=True,
        native_profile='Actual native copied interpreter argv; only case-declared generated-text state expectations convert CRLF to LF. All input fixture/cache/sentinel bytes, actions, exact exits, snapshots and semantics preserved. No --python target argument or wizard EOF/cancellation translation.',
        native_installed_dependency_count=48,
        scope='Exactly reviewed primary-release wheels downloaded by frozen URL/digest; no source distributions or resolver-selected alternative native binaries. Setuptools startup .pth matches Windows review; Linux uv/uvx exact primary-bound ELF scripts are installed but not executed. No environment creation or credential/network route in target scenarios.')
    immutable_json(package/'native-runtime-lock.json',lock)
    immutable_json(package/'linux-dependency-review.json',dict(schema_version=1,approved=True,native_runtime_lock_sha256=sha256(package/'native-runtime-lock.json'),
        linux_review_inputs_sha256=sha256(native_inputs),common_primary_inputs_sha256=sha256(common_inputs),
        actual_dependency_closure=sorted(used),new_linux_versions={n:rows[n]['version'] for n in lock['reviewed_linux_additions']},
        native_hooks={n:r for n,r in approvals.items() if n.startswith('uv-') and not n.endswith('win_amd64.whl')},
        license_review='distro Apache2, SecretStorage BSD3, jeepney MIT, cryptography Apache2 OR BSD3, cffi MIT-0, pycparser BSD3; actual retained wheel licenses inspected. Existing uv MIT OR Apache2 and backports.zstd PSF2 native payloads are primary-bound.',
        execution_boundary='Owned offline build and synthetic declared workflows only. No uv/native utility invocation, credentials, publishing, generated CI execution or isolation claim. Read-only installed Python SDK/venv bootstrap remains an explicit prerequisite.'))
    print('Approved exact48-distribution Linux wheel closure, hooks and private-version/generated-source profile before any hosted target build.')


if __name__=='__main__':main()
