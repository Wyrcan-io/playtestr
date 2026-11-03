"""Independent actual Cargo normal-rebuild audit, outside frozen execution helpers."""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import tarfile

from next20_check import DOC, RAW, NAME
from next20_cargo_source_corpus import Decoder
from next20_cargo_solid_reference import restore
from next20_local_records import read_packet as local_packet
from next20_native_packet_reader import read_packet
from next20_peco_development_readback import git_inputs
from next20_review_input_packet import read as review_packet
from next20_lzma_dictionary import decode
from readiness_evidence import immutable_json, sha256


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(body):
    return hashlib.sha256(body).hexdigest()


def audit(host, revision, generation=None, staged=False, window=1):
    scope = 'artifacts/' + NAME + '/'
    package = DOC / 'cargo-generate'
    if host == 'linux':
        index, records = read_packet('cargo-generate', generation, stage=staged)
        prefix = 'native/41720880957/next20-cargo-linux-rebuild-recovery/'
        root = (RAW / 'tmp/direct-native-zip/cargo-generate' if staged else RAW / 'cargo-generate') / ('retained-native-v' + str(generation))
        provider = json.loads((root / 'provider.json').read_text())
        require(provider['headSha'] == revision and provider['conclusion'] == 'success' and provider['status'] == 'completed', 'provider source/success differs')
    else:
        records = local_packet('cargo-generate')[1]
        prefix = ''

    def logical(name):
        name = name.replace('\\', '/').removeprefix(scope)
        require(name and not name.startswith('/') and all(p not in {'', '.', '..'} and ':' not in p for p in name.split('/')), 'unsafe evidence name')
        return name

    def raw(name):
        name = logical(name)
        if host == 'windows' and (RAW / name).is_file():
            return (RAW / name).read_bytes()
        return records[prefix + name]

    def value(name):
        return json.loads(raw(name).decode('utf-8-sig'))

    def hashed(name):
        return digest(raw(name))

    def manifest(ref):
        require(hashed(ref['manifest']) == ref['sha256'], 'identity manifest changed')
        return value(ref['manifest'])

    helpers = git_inputs(revision)
    if host == 'windows':
        actual = review_packet(RAW / 'cargo-generate/execution-helper-source-rebuild-v1')
        for name, expected in list(helpers.items()):
            body = actual[name]
            normal = body.replace(b'\r\n', b'\n')
            require(expected in {digest(body), digest(normal), digest(normal.replace(b'\n', b'\r\n'))}, 'executed helper changed beyond line endings')
            helpers[name] = digest(body)

    def events(eid, code, phase):
        rows = {k: value('events/' + eid + '-' + k + '.json') for k in ['started', 'identified', 'launched', 'finished']}
        require(all(r['id'] == eid and r['project'] == 'cargo-generate' and r['phase'] == phase for r in rows.values()), 'event identity/phase differs')
        require(rows['started']['ci_run_id'] == ('41720880957' if host == 'linux' else None), 'provider identity differs')
        end = rows['finished']
        require(end['category'] == 'passed' and end['exit_code'] == code and end['harness_cleanup'] == 'harness_process_reaped' and not end['cleanup_errors'] and rows['launched']['pid'] > 0, 'actual command/cleanup differs')
        require(hashed('cargo-generate/' + eid + '/console.log') == end['console_sha256'], 'actual console changed')
        identity = manifest(rows['identified']['identity'])
        base = manifest(identity['base']) if 'base' in identity else identity
        require(all(base['files'].get(n) == h for n, h in helpers.items()), 'actual execution helper identity differs')
        return identity

    target = 'cargo-generate/retained-source-rebuild-v1/' if host == 'linux' or not (RAW / 'active/cargo-generate').exists() else 'active/cargo-generate/'
    build = value(target + 'build.json')
    runtime = value(target + 'runtime.json')
    declaration = json.loads((package / 'rebuild-recovery-declaration-v1.json').read_text())
    require(build['binary_sha256'] == runtime['native_sha256'] == declaration['original_baseline'][host], 'ordinary baseline differs')
    complete = value('cargo-generate/rebuild-recovery-summary-v'+str(window)+'.json')
    plan = value('cargo-generate/rebuild-recovery-execution-plan-v'+str(window)+'.json')
    require(complete['plan_sha256'] == hashed('cargo-generate/rebuild-recovery-execution-plan-v'+str(window)+'.json') and plan['declaration_sha256'] == sha256(package / 'rebuild-recovery-declaration-v1.json'), 'rebuild plan differs')
    require(complete.get('window',1)==window,'cross-window rebuild summary')
    if window==2:
        replacement=package/'rebuild-recovery-replacement-declaration-v2.json'
        changed=json.loads(replacement.read_text())
        require(plan['replacement_declaration_sha256']==sha256(replacement) and plan['preparation_receipt_sha256']==changed['preparation_receipt_sha256']==hashed('cargo-generate/rebuild-preparation-v1/compiled.json'),'replacement preparation/declaration binding differs')
    summary = value(complete['fault_summary'])
    require(hashed(complete['fault_summary']) == complete['fault_summary_sha256'] and summary['normal_restoration_rebuilds'] == 3 and summary['new_compiles'] == 6, 'partial normal rebuild summary')
    packed = value('cargo-generate/rebuild-executables-v'+str(window)+'/index.json')
    retention_path = package / 'rebuild-binary-retention-declaration-v1.json'
    retention = json.loads(retention_path.read_text())
    require(packed['declaration_sha256'] == sha256(retention_path) and len(packed['files']) == 6, 'actual image retention binding differs')
    if host == 'linux':
        old_index, old = read_packet('cargo-generate', 13)
        originals = restore(old, old_index['solid_runtime_disposition'])
    else:
        root = RAW / 'cargo-generate/native-solid-variants/windows'
        old_index = json.loads((root / 'index.json').read_text())
        require(sha256(root / 'executables.tar.xz') == old_index['archive_sha256'], 'mandatory original image archive changed')
        decoder = Decoder(root / 'executables.tar.xz')
        originals = {}
        try:
            with tarfile.open(fileobj=decoder, mode='r|') as stream:
                for member in stream:
                    require(member.isfile() and member.name in old_index['files'] and member.size <= 32 * 1024**2 and member.name not in originals, 'unsafe original image member')
                    body = stream.extractfile(member).read(member.size + 1)
                    require(digest(body) == old_index['files'][member.name]['sha256'], 'original actual image changed')
                    originals[member.name] = body
            while decoder.read(65536):
                pass
        finally:
            decoder.close()
    require({n: digest(b) for n, b in originals.items()} == retention['original_images'][host], 'original image dictionary declaration differs')
    images = {}
    for name, row in packed['files'].items():
        if row['encoding'] == 'exact-original-image-reference':
            body = originals[row['original_image']]
        else:
            require(row['encoding'] == 'raw-lzma2-preset-dictionary-v1', 'unsupported actual image encoding')
            body = decode(originals['original'], raw('cargo-generate/rebuild-executables-v'+str(window)+'/' + row['payload']), row['codec'])
        require(len(body) == row['bytes'] and digest(body) == row['sha256'], 'actual rebuilt image byte recovery differs')
        images[name] = digest(body)
    rules = {f['id']: f for f in json.loads((package / 'fault-declaration.json').read_text())['faults']}
    reviewed = json.loads((package / 'source-review.json').read_text())['reviewed_inputs']
    primary = json.loads((package / 'source-provenance.json').read_text())['files']
    invocations, attempts, compilers = set(), set(), set()
    result = []
    for fault in summary['observations']:
        rule = rules[fault['fault']]
        require(fault['normal_rebuild_recovery_executed'], 'copied image substituted for normal rebuild')
        receipts = {}
        for stage, key in [('mutated', 'compiled_receipt'), ('restored', 'normal_rebuild_receipt')]:
            receipt = value(fault[key])
            require(hashed(fault[key]) == fault[key + '_sha256'], 'compiler receipt changed')
            expected = {scope + 'active/cargo-generate/src/' + n: h for n, h in reviewed.items()}
            if stage == 'mutated':
                expected[scope + 'active/cargo-generate/src/' + rule['path']] = rule['mutated_source_sha256']
            require(receipt['source_inputs'] == expected and receipt['compiler_sha256'] == build['compiler_sha256'] and receipt['cargo_sha256'] == build['cargo_sha256'] and receipt['pristine_build_sha256'] == hashed(target + 'build.json'), 'actual compiler/source binding differs')
            command = [build['cargo_path'], 'rustc', '--locked', '--offline', '--release', '--target', build['native_triple'], '--bin', 'cargo-generate']
            if host == 'windows':
                command += ['--', '-C', 'link-arg=/Brepro']
            require(receipt['command'] == command and receipt['binary_sha256'] == images[fault['fault'] + '-' + stage], 'approved normal compile command/image differs')
            if stage == 'restored':
                require(receipt['purpose'] == 'normal-restored-source-rebuild', 'normal compile receipt purpose missing')
            eid = receipt['compile_attempt']
            require(eid not in compilers, 'duplicate compile execution')
            compilers.add(eid)
            identity = events(eid, 0, 'development')
            actual = manifest(identity['target_catalog'])['files']
            expected_primary = dict(primary)
            if stage == 'mutated':
                expected_primary[rule['path']] = rule['mutated_source_sha256']
            require({n.removeprefix(scope + 'active/cargo-generate/src/'): h for n, h in actual.items() if n.startswith(scope + 'active/cargo-generate/src/')} == expected_primary, 'actual compile prelaunch primary source differs')
            receipts[stage] = receipt
        spec = 'cargo-generate/host-contracts-rebuild-v1/' + rule['spec']
        contract = value(spec)
        for phase in ['baseline', 'mutated', 'restored']:
            outcome = fault[phase]
            report = value(outcome['report'])
            row = report['results'][0]
            require(hashed(outcome['report']) == outcome['report_sha256'] and report['runner_version'] == 'v0.4.0-rc.6' and report['os'] == host, 'actual report candidate/host differs')
            mutant = phase == 'mutated'
            require(row['status'] == ('failed' if mutant else 'passed') and row.get('failure', {}).get('category') == (rule['category'] if mutant else None), 'actual calibration outcome differs')
            require(row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'] and row['invocation_id'] == row['workspace']['id'], 'actual target/workspace cleanup incomplete')
            require(row['invocation_id'] not in invocations and outcome['attempt'] not in attempts, 'duplicate actual invocation')
            invocations.add(row['invocation_id'])
            attempts.add(outcome['attempt'])
            require([s['action'] for s in row['steps']] == [next(iter(s)) for s in contract['steps']], 'omitted actual contract actions')
            identity = events(outcome['attempt'], 1 if mutant else 0, 'final-archive')
            if phase in receipts:
                actual = identity['native_source_fault']
                require(actual['build_receipt_sha256'] == fault[('compiled_receipt' if mutant else 'normal_rebuild_receipt') + '_sha256'] and actual['actual_executable_sha256'] == receipts[phase]['binary_sha256'], 'report did not execute actual compiled image')
            frame = None
            if mutant:
                frame = row['evidence']['screen_path']
                require(raw(frame) and len(raw(frame)) < 1024**2, 'actual mutation frame missing')
                if fault['fault'] == 'F03':
                    first = next(i for i, s in enumerate(row['steps']) if s['status'] == 'failed')
                    require(row['steps'][first]['action'] == 'state' and all(s['status'] == 'passed' for s in row['steps'][:first]) and {'expect', 'exit'} <= {s['action'] for s in row['steps'][:first]}, 'earlier failure substituted for saved corruption')
            else:
                require(all(s['status'] == 'passed' for s in row['steps']), 'normal recovery omitted passing assertions')
            result.append(dict(fault=fault['fault'], phase=phase, report=outcome['report'], report_sha256=outcome['report_sha256'], invocation=row['invocation_id'], frame=frame, frame_sha256=hashed(frame) if frame else None))
    require(len(result) == len(invocations) == len(attempts) == 9 and len(compilers) == 6, 'partial normal-rebuild cell')
    removed = target.startswith('cargo-generate/retained-source-rebuild-v1/')
    if removed:
        proof = value(target + 'removed.json')
        require(proof['removed'] and proof['cleanup_inventory_sha256'] == hashed(target + 'cleanup-inventory.json'), 'source/runtime removal proof differs')
    return dict(schema_version=1, project='cargo-generate', host=host, source_revision=revision,
                calibrations_verified=9, actual_compiler_executions_verified=6, normal_rebuilds_verified=3,
                actual_images_verified=images, actual_phases=result, source_runtime_removed=removed,
                original_ordinary_unchanged=True, ordinary_credit=0, project_admissions=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('host', choices=['windows', 'linux'])
    parser.add_argument('--revision',required=True)
    parser.add_argument('--window',type=int,choices=[1,2],default=1)
    parser.add_argument('--generation', type=int)
    parser.add_argument('--staged', action='store_true')
    parser.add_argument('--verify-existing',action='store_true')
    args = parser.parse_args()
    result = audit(args.host, args.revision, args.generation, args.staged, args.window)
    destination = DOC / 'cargo-generate' / (args.host + '-normal-rebuild-readback-' + ('removed' if result['source_runtime_removed'] else 'before-cleanup') + '.json')
    if args.verify_existing:
        require(json.loads(destination.read_text())==result,'existing immutable readback differs from actual evidence')
    else:
        immutable_json(destination, result)
    print('Actual normal source rebuild audit passed:', args.host, '9phases/6compiler executions/3normal rebuilt images;removed:', result['source_runtime_removed'])
