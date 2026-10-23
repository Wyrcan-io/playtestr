"""Preserve the first setup refusal and declare a fresh complete native series."""
import json

from next20_check import DOC, RAW
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'cz-cli'
    current=package/'final-series-declaration.json'
    previous=json.loads(current.read_text(encoding='utf-8'))
    if previous['revision']!=1:raise ValueError('native replacement already declared; preserve it')
    for generation in [1,2]:
        retained=RAW/'cz-cli'/('retained-native-v'+str(generation))
        if not json.loads((retained/'expanded-removed.json').read_text(encoding='utf-8-sig'))['all_expanded_removed']:
            raise ValueError('first failed native packet not checked/retained/removed')
    immutable_json(package/'final-series-declaration-v1.json',previous)
    original_hash=sha256(current)
    if sha256(package/'final-series-declaration-v1.json')!=original_hash:raise ValueError('first declaration bytes changed')
    disposition=dict(schema_version=1,run='40025853402',revision='3643f67b1b89e7de46fd15cec3dd71e4e9ced84c',
        native_jobs=2,setup_failures=2,ordinary_executions=0,calibrations=0,
        observed='Both build reviews refused the hidden npm lock physical package set before compiling or running the application. The original guard did not log individual missing entries; no claim that the absent package name was directly observed.',
        repair='Permit omitted hidden-lock entries only when the canonical lock marks them optional and explicitly excludes this actual OS. Retain exact installed-byte reconstruction; every required package and all hashes stay mandatory. Log exact missing/extra entries on further refusal. Capture actual bounded setup metadata before the build review.',
        verification='Actual package reconstruction positives plus four byte-corruption rejections, alternate optional OS lock representation positive and missing-required-package rejection. An initial representation control omitted updating its companion inventory hash and was correctly refused; retained attempt f9941a116c47413090f4c371d0afb728. Correct complete controls f6ac2d82e312476895d7b93cefe91637.',
        previous_declaration_sha256=original_hash,
        retained_failed_packets=[dict(generation=g,archive_sha256=sha256(RAW/'cz-cli'/('retained-native-v'+str(g))/'packets.tar.gz')) for g in [1,2]],
        cleanup_scope='Nested command processes were reaped and hosted VMs disposed; no application execution or explicit native source/runtime removal receipt. Local packet expansions removed only after complete archive/index verification.',
        contract_or_fixture_changes=False,production_runner_changes=False,new_project_admissions=0)
    immutable_json(package/'first-native-setup-disposition.json',disposition)
    replacement=dict(previous,revision=2,retained_generations=dict(linux=3,windows=4),
        previous_declaration_sha256=original_hash,rejected_run='40025853402',
        replacement_reason='Fresh complete native matrix after the explicit hidden-lock representation guard correction; no reuse of failed setup as scenario coverage.')
    current.write_text(json.dumps(replacement,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Preserved first refused native setup and declared complete fresh revision2; canonical scenarios unchanged.')


if __name__=='__main__':main()
