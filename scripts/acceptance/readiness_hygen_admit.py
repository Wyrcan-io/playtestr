"""Admit the ninth development package after native and checked retention gates."""
import json
import shutil

from readiness_compact_native import verify
from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_hygen_verify_first_use import require
from readiness_new_control_matrix import packet_observations, read_json as load


def main():
    project = RAW / 'hygen'
    docs = ROOT / 'docs/validation/runner-readiness-ten-project-pass/hygen'
    candidate = load(docs.parent / 'provisional-candidate-freeze.json')
    source = candidate['source_revision']
    core = RAW / 'native/39103715410/run-metadata.json'
    metadata = load(core)
    require(metadata['headSha'] == source and metadata['status'] == 'completed'
            and metadata['conclusion'] == 'success' and len(metadata['jobs']) == 3
            and all(j['conclusion'] == 'success' for j in metadata['jobs']), 'native core source unqualified')
    observations = packet_observations('39103715410')
    for host in ['linux', 'macos']:
        require(sum(row['host'] == host and
                    ('github.com/Wyrcan-io/playtestr/internal/runner', 'TestPrimaryReplyRealPTYStartupAndExactExit')
                    in row['whole'] for row in observations) >= 2, 'ordinary/race real PTY evidence missing')
    require(not (RAW / 'active/hygen').exists(), 'local active target remains')
    retained = project / 'retained-source'
    removed = load(retained / 'removed.json')
    index = load(retained / 'verified-index.json')
    reviewed = load(docs / 'source-review.json')
    require(removed['removed'] and removed['owned_relative_path'] == 'active/hygen'
            and removed['source_archive_sha256'] == reviewed['archive_sha256'] == sha256(retained / 'source.tar.gz'),
            'local source archive/removal identity differs')
    for name in index['selected_restore']:
        require(sha256(retained / 'selected-restore' / name) == index['files'][name]['sha256'], 'local selected source restore differs')
    native_path = project / 'native-development-verification.json'
    native = load(native_path)
    require(native['runner_source'] == source and native['candidate_version'] == candidate['version']
            and native['real_faults'] == 3 and len(native['cells']) == 2
            and native['original_heldout'] == dict(host='Linux', run='39154095409', fault='F03'),
            'wrong native qualification/holdout scope')
    directory = project / 'retained-native-v1'
    inventory = load(directory / 'index.json', 4*1024**2)
    verified = load(directory / 'verified.json')
    expanded = load(directory / 'expanded-removed.json')
    require(set(inventory['runs']) == {'39151379008', '39151639480', '39152550656', '39153221631', '39154095409', '39154521534'}
            and sha256(directory / 'index.json') == verified['index_sha256']
            and sha256(directory / 'packets.tar.gz') == inventory['archive_sha256'] == verified['archive_sha256'],
            'native retained archive coverage/identity differs')
    verify(directory / 'packets.tar.gz', inventory['files'])
    require(expanded['all_expanded_removed'] and expanded['archive_sha256'] == inventory['archive_sha256']
            and set(expanded['removed_runs']) == set(inventory['runs'])
            and all(not (RAW / 'native' / run).exists() for run in inventory['runs']), 'expanded cleanup incomplete')
    for cell in native['cells']:
        require(cell['scenarios'] == 20, 'native scenario scope differs')
        prefix = 'native/' + cell['run'] + '/' + cell['host'] + '/'
        for key in ['report_sha256', 'source_fault_summary_sha256', 'maintenance_sha256', 'cleanup_receipt_sha256']:
            require(any(name.startswith(prefix) and record['sha256'] == cell[key]
                        for name, record in inventory['files'].items()), 'verified native payload missing from archive')
    original = docs / 'original-source-faults/summary.json'
    original_faults = load(original)['faults']
    require(len(original_faults) == 3 and {r['id'] for r in original_faults} == {'F01', 'F02', 'F03'}
            and [r['id'] for r in original_faults if r['held_out']] == ['F03']
            and all(r['restored_exact'] for r in original_faults), 'original fault detection/restoration incomplete')
    require(any(name.startswith('native/39154095409/playtestr-Linux/hygen/faults/')
                and record['sha256'] == sha256(original) for name, record in inventory['files'].items()),
            'original fault payload not retained')
    first_path = docs / 'first-use-native-39151639480.json'
    first = load(first_path)
    require(first['shell_invocations'] == 3 and first['recorder_controls'] == 20 and len(first['cells']) == 2,
            'first-use engineering budget unmet')
    for cell in first['cells']:
        prefix = 'native/39151639480/playtestr-' + ('Linux' if cell['host'] == 'linux' else 'macOS') + '/'
        for key in ['journey_sha256', 'spec_sha256', 'cleanup_sha256']:
            require(any(name.startswith(prefix) and record['sha256'] == cell[key]
                        for name, record in inventory['files'].items()), 'first-use verified payload not retained')
    observed = sum(p.stat().st_size for p in project.rglob('*') if p.is_file())
    require(observed < 64*1024**2, 'project retained evidence cap exceeded')
    candidate_path = docs.parent / 'candidates.json'
    before = candidate_path.read_bytes()
    ledger = load(candidate_path)
    require(ledger['project_admissions'] == ledger['development_admissions'] == 8, 'unexpected development counter')
    row = next(r for r in ledger['rows'] if r['repository'] == 'jondot/hygen')
    require(row['status'] == 'reserved-transfer-active', 'wrong reserved-project stage')
    row.update(status='development-admitted', qualified_hosts=['linux-amd64', 'darwin-arm64'],
               qualification='Twenty frozen real generation/overwrite/injection/dry-run/Unicode/resize workflows, three real source faults/restorations and thirteen-command public maintenance pass both native hosts on exact provisional archives. Initial hosted Linux F03 only is heldout. Original setup/authoring/maintenance failures retained; final archive repetition matrix remains open.')
    ledger['project_admissions'] = ledger['development_admissions'] = 9
    record = dict(schema_version=1, project='jondot/hygen', pin=reviewed['pin'], status='development-admitted',
                  runner_source=source, candidate_version=candidate['version'], normal_scenarios=8, edge_scenarios=12,
                  real_faults=3, cells=native['cells'], native_verification_sha256=sha256(native_path),
                  provisional_candidate_freeze_sha256=sha256(docs.parent / 'provisional-candidate-freeze.json'),
                  original_fault_summary_sha256=sha256(original), first_use_sha256=sha256(first_path),
                  reviewed_freeze_sha256=sha256(docs / 'reviewed-contract-freeze.json'),
                  local_removal_receipt_sha256=sha256(retained / 'removed.json'), core_metadata_sha256=sha256(core),
                  retained_native_archive_sha256=inventory['archive_sha256'], retained_native_index_sha256=sha256(directory / 'index.json'),
                  observed_project_retained_bytes=observed, archive_qualified=False, final_runner_admissions=0,
                  human_usability='unmeasured', original_heldout=native['original_heldout'],
                  limitations='Trusted local EJS/prompt/config inputs only. No remote template setup, shell actions, arbitrary plugins or general Unicode compatibility claim. Windows is exploratory and excluded from admitted cells. Generated workflow preparation is verified, actual generated CI/final archive repetitions remain open.')
    shutil.copyfile(native_path, docs / native_path.name)
    immutable_json(docs / 'development-admission.json', record)
    data = (json.dumps(ledger, indent=2, ensure_ascii=True) + '\n').encode()
    candidate_path.write_bytes(data.replace(b'\n', b'\r\n') if b'\r\n' in before else data)
    print('Hygen development admitted: nine projects/eighteen native cells; final archive credit zero.')


if __name__ == '__main__':
    main()
