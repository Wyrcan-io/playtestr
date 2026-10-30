"""Independently read original native peco development/source/runtime evidence."""
import argparse
import base64
import copy
import hashlib
import io
import json
import posixpath
from pathlib import PurePosixPath
import stat
import subprocess
import tarfile
import uuid
import zipfile

from next20_check import DOC, RAW, ROOT, NAME
from next20_native_packet_reader import read_packet
from readiness_evidence import immutable_json, sha256


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def git_inputs(revision):
    names = subprocess.check_output(['git', 'ls-tree', '-rz', '--name-only', revision, '--',
        'scripts/acceptance', 'scripts/ci', 'schema', 'go.mod', 'go.sum'], cwd=ROOT, timeout=20).decode().split('\0')
    names = [n for n in names if n and (n.endswith('.py') or n.startswith('schema/') and n.endswith('.json') or n in {'go.mod', 'go.sum'})]
    output = subprocess.check_output(['git', 'cat-file', '--batch'], input=('\n'.join(revision+':'+n for n in names)+'\n').encode(), cwd=ROOT, timeout=30)
    result = {}; offset = 0
    for name in names:
        end = output.index(b'\n', offset); header = output[offset:end].split()
        require(len(header)==3 and header[1]==b'blob', 'missing actual helper Git blob')
        size = int(header[2]); start = end+1; body = output[start:start+size]
        require(len(body)==size and output[start+size:start+size+1]==b'\n', 'Git blob framing differs')
        result[name] = digest(body); offset = start+size+1
    require(offset==len(output), 'trailing Git input bytes')
    return result


def audit(generation, run, revision, require_removed=True):
    index, records = read_packet('peco', generation)
    retained = RAW/'peco'/('retained-native-v'+str(generation))
    acquisition = json.loads((retained/'acquisition.json').read_text())
    provider = json.loads((retained/'provider.json').read_text())
    require(acquisition['run']==run and acquisition['revision']==revision and provider['headSha']==revision and provider['status']=='completed', 'provider run/source differs')
    require(provider['conclusion']==('success' if require_removed else 'failure'), 'unexpected original provider conclusion')
    prefix = 'native/'+run+'/next20-peco-linux-development/'
    scope = 'artifacts/'+NAME+'/'
    def logical(name):
        name = str(name).replace('\\', '/').removeprefix(scope)
        require(name and not name.startswith('/') and ':' not in name and all(p not in {'', '.', '..'} for p in name.split('/')), 'unsafe logical evidence path')
        return name
    def data(name):
        name = prefix+logical(name)
        require(name in records, 'actual retained payload missing: '+name)
        return records[name]
    def load(name):
        return json.loads(data(name).decode('utf-8-sig'))
    def sha(name):
        return digest(data(name))
    package = DOC/'peco'; target = 'peco/retained-source/'
    owner = load(target+'task-owned.json'); build = load(target+'build.json'); runtime = load(target+'runtime.json')
    provenance = json.loads((package/'source-provenance.json').read_text()); primary = provenance['files']
    require(owner['slug']=='peco' and owner['campaign']==NAME and owner['pin']==provenance['pin'], 'foreign original target ownership')
    owned = owner['workspace']+'/'+scope+'active/peco/'
    def owned_relative(name):
        require(name.startswith(owned) and '..' not in PurePosixPath(name).parts, 'native input escapes owned target')
        return name.removeprefix(owned)
    acquired = load(target+'acquisition.json')
    require(acquired['source_files']==primary and acquired['archive_sha256']==sha(target+'source.tar.gz'), 'original source acquisition differs')
    source = {}; links = {}
    with tarfile.open(fileobj=io.BytesIO(data(target+'source.tar.gz')), mode='r:gz') as archive:
        for member in archive:
            if member.isdir():continue
            name = member.name.split('/', 1)[1]
            require(name not in source and name not in links and all(p not in {'', '.', '..'} for p in name.split('/')), 'unsafe/duplicate primary source member')
            if member.issym():
                links[name] = member.linkname; continue
            require(member.isfile() and name in primary and member.size<=8*1024**2, 'unreviewed primary source member')
            body = archive.extractfile(member).read(member.size+1)
            require(len(body)==member.size and digest(body)==primary[name], 'original primary source bytes differ')
            source[name] = body
    policy = json.loads((package/'source-link-policy.json').read_text())
    require(set(source)==set(primary) and links==policy['omitted_documentation_links'], 'primary source/link coverage differs')
    review = json.loads((package/'dependency-source-review-declaration.json').read_text())
    fetch = load(target+'module-fetch.json'); catalog = load(target+'dependency-source-catalog.json')
    package_inputs = load(target+'native-package-inputs.json'); corpus = 'peco/go-module-corpus/'
    corpus_index = load(corpus+'index.json')
    for name, row in corpus_index['files'].items():
        require(len(data(corpus+name))==row['bytes'] and sha(corpus+name)==row['sha256'], 'retained module/metadata/proof body differs')
    installed = {'src/'+n:h for n,h in primary.items()}; members = 0
    require(len(fetch['modules'])==len(review['modules'])==26, 'module closure coverage differs')
    for module in fetch['modules']:
        key = module['Path']+'@'+module['Version']; rule = review['modules'][key]
        base = 'archives/'+module['Path']+'/@v/'+module['Version']
        body = data(corpus+base+'.zip')
        require(digest(body)==rule['zip_sha256'] and module['Sum']==rule['go_sum'] and module['GoModSum']==rule['go_mod_sum'], 'actual module archive/checksum differs')
        rows = []; license_seen = {}; directory = owned_relative(module['Dir'])
        with zipfile.ZipFile(io.BytesIO(body)) as archive:
            names = set()
            for member in sorted(archive.infolist(), key=lambda m:m.filename):
                if member.is_dir():continue
                require(member.filename.startswith(key+'/') and member.filename not in names and not stat.S_ISLNK(member.external_attr>>16) and member.file_size<=8*1024**2, 'unsafe module source entry')
                names.add(member.filename); name = member.filename.removeprefix(key+'/')
                require(all(p not in {'', '.', '..'} and ':' not in p and '\\' not in p for p in name.split('/')), 'module source path escapes')
                raw = archive.read(member); hashed = digest(raw); members += 1
                installed[directory+'/'+name] = hashed
                rows.append(hashed+'  '+member.filename+'\n')
                if name in rule['licenses']:license_seen[name] = hashed
        h1 = 'h1:'+base64.b64encode(hashlib.sha256(''.join(rows).encode()).digest()).decode()
        mod = data(corpus+base+'.mod')
        mod_h1 = 'h1:'+base64.b64encode(hashlib.sha256((digest(mod)+'  go.mod\n').encode()).digest()).decode()
        require(h1==rule['go_sum'] and mod_h1==rule['go_mod_sum'] and license_seen==rule['licenses'], 'independent module h1/license readback differs')
        require(json.loads(data(corpus+base+'.info'))['Version']==module['Version'], 'module version metadata differs')
    require(installed==catalog['files'], 'actual installed primary/module catalog differs')
    require(package_inputs['files']==catalog['actual_native_compile_inputs'] and all(installed.get(n)==h for n,h in package_inputs['files'].items()), 'actual native compile inputs differ')
    require(catalog['native_package_inputs_sha256']==sha(target+'native-package-inputs.json') and build['source_catalog_sha256']==sha(target+'dependency-source-catalog.json') and build['actual_package_inputs_sha256']==sha(target+'native-package-inputs.json'), 'actual build source bindings differ')
    require(build['source_review_sha256']==sha256(package/'dependency-source-review-declaration.json') and build['compiler_sha256']==fetch['compiler_sha256'] and fetch['settings']['GOOS']=='linux' and fetch['settings']['GOVERSION']==review['compiler_version'] and fetch['settings']['CGO_ENABLED']=='0', 'native build prerequisite/source review differs')
    binary_index = load(corpus+'executables-index.json'); binary_archive = data(corpus+'executables.tar.xz')
    require(digest(binary_archive)==binary_index['archive_sha256'], 'actual executable archive differs')
    binaries = {}
    with tarfile.open(fileobj=io.BytesIO(binary_archive), mode='r:xz') as archive:
        for member in archive:
            require(member.isfile() and member.name not in binaries and member.name in binary_index['files'] and member.size<=16*1024**2, 'unsafe actual executable member')
            binaries[member.name] = archive.extractfile(member).read(member.size+1)
    for name, row in binary_index['files'].items():
        require(len(binaries[row.get('member', name)])==row['bytes'] and digest(binaries[row.get('member', name)])==row['sha256'], 'actual executable bytes differ')
    require(build['compiled_files']=={name.removeprefix('bin/'):digest(body) for name,body in binaries.items() if name.startswith('bin/')}, 'actual app/capture binaries differ from build')
    require(runtime['native_sha256']==build['binary_sha256'] and runtime['target_sha256']==build['actual_target_sha256'] and owned_relative(runtime['native'])==build['binary_relative_path'] and owned_relative(runtime['target'])==build['actual_target_relative_path'], 'actual native app/capture routing differs')
    linked = load(target+'binary-buildinfo.json')
    require(linked['actual_target_sha256']==build['actual_target_sha256'] and linked['linked_modules']=={m['path']:m['version'] for m in package_inputs['actual_module_versions'] if m['version']!='primary-source'}, 'actual linked module versions differ')
    frozen = load('peco/host-contracts/development-test-freeze.json'); cases = load('peco/host-contracts/scenarios.json')['cases']
    canonical = json.loads((package/'scenarios.json').read_text())['cases']
    require(frozen['canonical_freeze_sha256']==sha256(package/'development-test-freeze.json') and len(cases)==len(canonical)==20, 'canonical host freeze differs')
    for name, hashed in frozen['inputs'].items():require(sha('peco/host-contracts/'+name)==hashed, 'frozen host input changed')
    by_id = {c['id']:c for c in cases}
    for case in canonical:
        host = by_id[case['id']]; value = load('peco/host-contracts/'+case['spec'])
        expected = json.loads((package/case['spec']).read_text())
        expected['command'][0] = posixpath.relpath(runtime['native'], owner['workspace']+'/'+scope+'peco/host-contracts')
        expected['command'][expected['command'].index('--app')+1] = 'peco'
        require(value==expected and host['canonical_sha256']==case['spec_sha256'] and host['spec_sha256']==sha('peco/host-contracts/'+case['spec']), 'host changed reviewed action or oracle')
    summaries = [n.removeprefix(prefix) for n in records if n.startswith(prefix+'peco/development/') and n.endswith('/summary.json')]
    require(len(summaries)==1, 'one original development window required')
    summary = load(summaries[0]); require(summary['passed']==20 and summary['failed']==0 and len(summary['results'])==20 and {r['case'] for r in summary['results']}==set(by_id), 'partial development window')
    helper_inputs = git_inputs(revision); invocations = set(); attempts = set()
    candidate = next(c for c in json.loads((DOC/'replacement-candidate-freeze-native-exit-v1.json').read_text())['cells'] if c['host']=='linux')
    for observed in summary['results']:
        report_name = logical(observed['report']); report = load(report_name); row = report['results'][0]
        case = by_id[observed['case']]; spec = 'peco/host-contracts/'+case['spec']; value = load(spec)
        require(report['report_version']==3 and report['runner_version']=='v0.4.0-rc.6' and report['os']=='linux' and len(report['results'])==1, 'wrong report schema/candidate/platform')
        require(sha(report_name)==observed['report_sha256'] and sha(spec)==observed['spec_sha256'] and row['status']=='passed' and all(s['status']=='passed' for s in row['steps']), 'nonpositive actual development outcome')
        require([s['action'] for s in row['steps']]==[next(iter(s)) for s in value['steps']], 'omitted actual action')
        require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'] and row['invocation_id']==row['workspace']['id'] and row['invocation_id'] not in invocations, 'missing/cross-invocation cleanup')
        invocations.add(row['invocation_id'])
        exits = [s['exit'] for s in value['steps'] if 'exit' in s]
        require(len(exits)==1 and row['target']['exited'] and row['target']['exit_code']==exits[0], 'actual exact exit differs')
        for step in row['steps']:
            if 'state' in step:require(step['state']['invocation_id']==row['invocation_id'] and step['state']['workspace_id']==row['workspace']['id'], 'cross-invocation saved state')
        eid = observed['attempt']; require(eid not in attempts, 'duplicate actual attempt'); attempts.add(eid)
        events = {kind:load('events/'+eid+'-'+kind+'.json') for kind in ['started','identified','launched','finished']}
        require(all(v['id']==eid and v['campaign']==NAME and v['phase']=='development' and v['project']=='peco' for v in events.values()) and events['started']['ci_run_id']==run, 'actual event source/phase differs')
        finished = events['finished']; require(finished['category']=='passed' and finished['harness_cleanup']=='harness_process_reaped' and not finished['cleanup_errors'] and events['launched']['pid']>0 and sha('peco/'+eid+'/console.log')==finished['console_sha256'], 'incomplete harness launch/cleanup/console')
        def manifest(reference):
            require(sha(reference['manifest'])==reference['sha256'], 'changed actual identity manifest')
            return load(reference['manifest'])
        combined = manifest(events['identified']['identity']); base = manifest(combined['base']); actual = manifest(combined['target_catalog'])['files']
        require(all(base['files'].get(name)==hashed for name,hashed in helper_inputs.items()), 'actual helper inputs differ from exact Git revision')
        require(base['files'].get(scope+spec)==sha(spec) and base['files'].get(scope+'candidate-native-exit-v1/linux/playtestr')==candidate['binary_sha256'], 'actual spec/candidate launch differs')
        require({n.removeprefix(scope+'active/peco/src/'):h for n,h in actual.items() if n.startswith(scope+'active/peco/src/')}==primary and actual.get(scope+'active/peco/runtime.json')==sha(target+'runtime.json'), 'actual prelaunch source/runtime differs')
        for name,hashed in build['compiled_files'].items():require(actual.get(scope+'active/peco/bin/'+name)==hashed or load(target+'launch-runtime-catalog.json')['files'].get(name)==hashed, 'actual app/capture catalog differs')
    cleanup = load(target+'cleanup-inventory.json'); proof = load('peco/process-proof.json')
    require(cleanup['source_restored_exact'] and cleanup['actual_reports_with_confirmed_cleanup']==20 and cleanup['process_proof_sha256']==sha('peco/process-proof.json') and proof['confirmed_no_matching_live_processes'] and not proof['matching_live_processes'], 'original cleanup preparation differs')
    require({n.removeprefix('src/'):r['sha256'] for n,r in cleanup['files'].items() if n.startswith('src/')}==primary, 'actual cleanup source differs')
    removed = prefix+target+'removed.json' in records
    require(removed==require_removed, 'original source/runtime removal classification differs')
    if removed:
        removal = load(target+'removed.json')
        require(removal['removed'] and removal['cleanup_inventory_sha256']==sha(target+'cleanup-inventory.json'), 'actual source/runtime removal proof differs')
    return dict(schema_version=1, project='peco', host='linux', provider_run=run, helper_source_revision=revision, generation=generation,
        provider_conclusion=provider['conclusion'], retained_index_sha256=sha256(retained/'index.json'), actual_ordinary_readbacks=20,
        actual_attempts_verified=len(attempts), source_blobs_verified=len(primary), omitted_documentation_links=len(links), modules_verified=26,
        module_source_members_verified=members, actual_compile_inputs_verified=len(package_inputs['files']), helper_inputs_verified=len(helper_inputs),
        app_and_capture_exact=True, all_target_workspace_cleanup=True, source_runtime_removed=removed, project_admissions=0, final_ordinary_credit=0,
        scope='All original development reports, prelaunch source/spec/helper/candidate bindings, independently hashed module archives/licenses/source/compile inputs and actual executable bytes. Failed cleanup remains failed; no final or admission credit.')


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--generation', type=int, required=True); parser.add_argument('--run', required=True); parser.add_argument('--revision', required=True)
    parser.add_argument('--original-cleanup-failed', action='store_true'); args = parser.parse_args()
    result = audit(args.generation, args.run, args.revision, not args.original_cleanup_failed)
    destination = DOC/'peco'/('linux-development-readback-v'+str(args.generation)+'.json')
    immutable_json(destination, result)
    print('Read back20 actual development reports, primary/module/code/runtime identities; source/runtime removed:', result['source_runtime_removed'])


if __name__=='__main__':main()
