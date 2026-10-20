"""Independently freeze exact private native archives before reserved transfer."""
import argparse
import hashlib
import subprocess
import tarfile
import zipfile

from readiness_candidate_package import SOURCE as HISTORICAL_SOURCE, VERSION as HISTORICAL_VERSION, MIGRATION_SOURCE, MIGRATION_VERSION
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import packet_file, read_json as load


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--series', choices=['provisional-v1','migration-v2'], default='provisional-v1')
    args = parser.parse_args()
    SOURCE, VERSION = (HISTORICAL_SOURCE, HISTORICAL_VERSION) if args.series=='provisional-v1' else (MIGRATION_SOURCE, MIGRATION_VERSION)
    qualification_name = 'earlier-project-requalification-retention-3d50d81.json' if args.series=='provisional-v1' else 'native-core-129b7a4.json'
    admission_name = 'frogmouth/development-admission.json' if args.series=='provisional-v1' else 'old-migration-status.json'
    require(args.run.isascii() and args.run.isdecimal(), 'invalid candidate run')
    run = RAW / 'native' / args.run
    metadata = load(run / 'run-metadata.json')
    require(metadata['status'] == 'completed' and metadata['conclusion'] == 'success'
            and len(metadata['jobs']) == 3
            and all(j['status'] == 'completed' and j['conclusion'] == 'success' for j in metadata['jobs']),
            'three successful native candidate jobs required')
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass'
    ledger = load(docs / 'candidates.json')
    if args.series=='provisional-v1':
        require(ledger['development_admissions'] == 8, 'eight-project freeze boundary changed')
        for repo, status in [('jondot/hygen', 'provisional-holdout-9'), ('rclone/rclone', 'provisional-holdout-10')]:
            require(next(r for r in ledger['rows'] if r['repository'] == repo)['status'] == status,
                    'reserved transfer target was already consumed')
    else:
        require(ledger['development_admissions']==10, 'ten historical admissions required')
        core=load(docs / qualification_name)
        require(core['source_revision']==SOURCE and str(core['run']).isdecimal() and core['native_hosts']==['linux','macos','windows'] and core['verified_success'], 'source-matched native core proof required')
    tracked = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SOURCE], cwd=ROOT,
                                      text=True, timeout=15).splitlines()
    names = {n for n in tracked if n.endswith('.go') or n in
             {'go.mod', 'go.sum', 'README.md', 'LICENSE', 'THIRD_PARTY_NOTICES.md'}}
    expected = {}
    for name in sorted(names):
        data = subprocess.check_output(['git', 'show', SOURCE + ':' + name], cwd=ROOT, timeout=15)
        require(len(data) < 4*1024**2, 'source member bound')
        # Git text checkout conversion is explicit and confined to build inputs.
        normalized = data.replace(b'\r\n', b'\n')
        expected[name] = {hashlib.sha256(normalized).hexdigest(),
                          hashlib.sha256(normalized.replace(b'\n', b'\r\n')).hexdigest()}
    cells = []
    for artifact, host in [('Linux', 'linux'), ('macOS', 'darwin'), ('Windows', 'windows')]:
        packet = run / ('private-candidate-' + artifact)
        manifests = list((packet / 'candidate-packages' / args.series).glob('*/candidate.json'))
        require(len(manifests) == 1, 'ambiguous native package manifest')
        manifest = manifests[0]
        value = load(manifest)
        arch = value['architecture']
        require(value['source_revision'] == SOURCE and value['version'] == VERSION
                and value['host'] == host and arch in {'amd64', 'arm64'}
                and value['sdk_settings'] == dict(GOOS=host, GOARCH=arch, GOVERSION='go1.25.0')
                and value['ledger_sha256'] == sha256(docs / 'candidates.json')
                and value['source_qualification_index_sha256'] == sha256(docs / qualification_name)
                and value['eighth_admission_sha256' if args.series=='provisional-v1' else 'migration_admission_ledger_sha256'] == sha256(docs / admission_name),
                'wrong native source, compiler settings or qualification gate')
        require(set(value['source_inputs']) == names
                and all(digest in expected[name] for name, digest in value['source_inputs'].items()),
                'build inputs differ from actual frozen Git source')
        sdk = load(packet / 'toolchain/sdk.json')
        require(sdk['version'] == 'go1.25.0' and sdk['host'] == host and sdk['architecture'] == arch,
                'non-native SDK')
        attempts = object.__new__(Campaign)
        attempts.raw = packet
        events = attempts.attempts()
        labels = ['sdk-version', 'native-sdk-settings', 'native-build', 'native-package', 'extracted-version', 'extracted-help']
        witnessed = {}
        for label in labels:
            matches = [(key, row) for key, row in events.items()
                       if row['started']['label'] == 'candidate-' + label]
            require(len(matches) == 1, 'missing or duplicate native package command')
            key, row = matches[0]
            finished = row['finished']
            require('launched' in row and row['started']['expected_exit'] == 0
                    and finished['category'] == 'passed' and finished['exit_code'] == 0
                    and finished['harness_cleanup'] == 'harness_process_reaped' and not finished['cleanup_errors'],
                    'native package command failed or cleanup incomplete')
            reference = row['identified']['identity']
            identity = packet_file(packet, reference['manifest'], 1024**2)
            require(sha256(identity) == reference['sha256'], 'changed native build identity')
            files = load(identity)['files']
            require(all(files['.playtestr-tooling/' + n] == digest for n, digest in value['source_inputs'].items()),
                    'actual command source inputs changed')
            console = packet / 'core' / key / 'console.log'
            require(sha256(console) == finished['console_sha256'], 'changed native command output')
            output = console.read_text(encoding='utf-8-sig')
            if label == 'extracted-version':
                require(output.strip() == 'playtestr ' + VERSION, 'actual extracted version differs')
                binary = value['archive'].rsplit('/dist/', 1)[0] + '/extracted/'
                base = 'playtestr_' + VERSION.removeprefix('v') + '_' + host + '_' + arch
                binary += base + '/playtestr' + ('.exe' if host == 'windows' else '')
                require(files[binary] == value['binary_sha256'] == value['extracted_binary_sha256'],
                        'actual extracted runner bytes differ')
            if label == 'native-build':
                require(files['artifacts/runner-readiness-ten-project-pass/toolchain/go/bin/go' + ('.exe' if host == 'windows' else '')]
                        == value['compiler_sha256'], 'actual compiler differs')
            witnessed[label] = key
        require(witnessed['native-build'] == value['build_attempt']
                and witnessed['extracted-version'] == value['version_attempt'], 'package attempt identity changed')
        archive_reference = 'candidate-packages/' + args.series + '/' + host + '-' + arch + '/dist/'
        archive_reference += 'playtestr_' + VERSION.removeprefix('v') + '_' + host + '_' + arch
        archive_reference += '.zip' if host == 'windows' else '.tar.gz'
        require(value['archive'] == 'artifacts/runner-readiness-ten-project-pass/' + archive_reference,
                'archive reference differs from declared native layout')
        archive = packet_file(packet, archive_reference, 32*1024**2)
        require(sha256(archive) == value['archive_sha256'] and archive.stat().st_size == value['archive_bytes'],
                'candidate archive bytes changed')
        require(archive.with_name(archive.name + '.sha256').read_text().strip()
                == value['archive_sha256'] + '  ' + archive.name, 'candidate checksum differs')
        members = {}
        base = 'playtestr_' + VERSION.removeprefix('v') + '_' + host + '_' + arch
        binary_name = 'playtestr' + ('.exe' if host == 'windows' else '')
        required_members = {base + '/' + n for n in [binary_name, 'LICENSE', 'README.md', 'THIRD_PARTY_NOTICES.md']}
        if host == 'windows':
            with zipfile.ZipFile(archive) as stream:
                require(len(stream.infolist()) == 4, 'candidate member count differs')
                for member in stream.infolist():
                    require(member.file_size <= 32*1024**2 and member.filename in required_members
                            and member.filename not in members, 'candidate member name/bound/duplicate')
                    members[member.filename] = dict(bytes=member.file_size, sha256=hashlib.sha256(stream.read(member)).hexdigest())
        else:
            with tarfile.open(archive, 'r:gz') as stream:
                entries = stream.getmembers()
                require(len(entries) == 4, 'candidate member count differs')
                for member in entries:
                    require(member.isfile() and member.size <= 32*1024**2 and member.name not in members,
                            'candidate member type/bound/duplicate')
                    require(member.name in required_members and member.mode ==
                            (0o755 if member.name == base + '/' + binary_name else 0o644),
                            'candidate member path/permissions differ')
                    members[member.name] = dict(bytes=member.size, sha256=hashlib.sha256(stream.extractfile(member).read(member.size+1)).hexdigest())
        require(set(members) == required_members and members == value['archive_members']
                and members[base + '/' + binary_name]['sha256'] == value['binary_sha256']
                and all(members[base + '/' + name]['sha256'] == value['source_inputs'][name]
                        for name in ['LICENSE', 'README.md', 'THIRD_PARTY_NOTICES.md']),
                'actual archive payload differs')
        cells.append(dict(host=host, architecture=arch, artifact='private-candidate-' + artifact,
                          archive_local_only=archive.relative_to(ROOT).as_posix(), archive_sha256=sha256(archive),
                          archive_bytes=archive.stat().st_size, binary_sha256=value['binary_sha256'],
                          candidate_manifest_sha256=sha256(manifest), command_attempts=witnessed))
    immutable_json(docs / ('provisional-candidate-freeze.json' if args.series=='provisional-v1' else 'migration-candidate-freeze.json'),
                   dict(schema_version=1, run=args.run, tooling_commit=metadata['headSha'],
                        source_revision=SOURCE, version=VERSION, cells=cells,
                        series=args.series, project_admissions_at_freeze=(8 if args.series=='provisional-v1' else 10), reserved_projects_untouched=(args.series=='provisional-v1'),
                        final_archive_credit=0, published=False,
                        residual='fff original Linux exit timeout remains unresolved; provisional builds do not establish stable qualification.'))
    print('Three exact native private archives independently verified:',args.series)


if __name__ == '__main__':
    main()
