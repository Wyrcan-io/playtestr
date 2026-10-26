"""Preserve first native failures and declare a complete fresh yo matrix."""
import json

from next20_check import RAW, DOC
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'yo';current=package/'final-series-declaration.json'
    previous=json.loads(current.read_text())
    if previous['revision']!=1:raise ValueError('Preserve existing native replacement')
    retained=[]
    for generation in [1,2]:
        root=RAW/'yo'/('retained-native-v'+str(generation))
        index=json.loads((root/'index.json').read_text());audit=json.loads((root/'rejected-audit.json').read_text())
        removed=json.loads((root/'expanded-removed.json').read_text(encoding='utf-8-sig'))
        if not removed['all_expanded_removed'] or audit['archive_sha256']!=sha256(root/'packets.tar.gz') or audit['index_sha256']!=sha256(root/'index.json') or audit['ordinary_qualification_credit']!=0:
            raise ValueError('Rejected native packet not completely verified/removed')
        retained.append(dict(generation=generation,archive_sha256=index['archive_sha256'],rejected_audit_sha256=sha256(root/'rejected-audit.json'),reports=audit['original_reports'],passed=audit['passed'],failed=audit['failed']))
    immutable_json(package/'final-series-declaration-v1.json',previous)
    original_hash=sha256(current)
    if sha256(package/'final-series-declaration-v1.json')!=original_hash:raise ValueError('Original declaration bytes differ')
    immutable_json(package/'first-native-disposition.json',dict(schema_version=1,run='40301653366',
        source_revision='1199115ba469506034e27177a80face43eb192b2',previous_declaration_sha256=original_hash,
        retained_packets=retained,ordinary_qualification_credit=0,calibration_credit=0,new_project_admissions=0,
        observed='Linux first batch10pass thenE03 expected130 got1, after positive prompt/key and confirmed individual cleanup. Windows115passed plus1cancelled report before stopping the rejected series. No completed qualified matrix or full native source/runtime removal claim.',
        repairs=['Preserve canonical exact cancellation1 on Linux; actual pinned yo error handling produced1. Do not import the older cz-cli self-SIGINT profile.',
                 'Skip only named fixture input trees during report-document parsing; preserve malformed JSON and exact bytes in archive/hash coverage. Invalid report JSON elsewhere still fails closed.',
                 'Account for one exact local sandbox-denied prelaunch report by digest with zero cleanup/ordinary credit;60 other local reports independently verified and checked local source/runtime removed.'],
        regression='Native harness controls cover malformed input preservation, invalid report refusal, explicit cleanup bounds and canonical registry source duplicate refusal. Current old cz-cli cell readback remains required.',
        production_runner_changes=False,canonical_spec_or_fixture_changes=False))
    replacement=dict(previous,revision=2,previous_declaration_sha256=original_hash,rejected_run='40301653366',
        retained_generations=dict(linux=3,windows=4),
        replacement_reason='Complete fresh matrix after two explicit harness/profile corrections; all first rejected/cancelled reports retained, none reused for qualification.',
        native_profile='Linux keeps canonical cancellation1, temporary-home inputs, exact state oracles, devnull/empty Windows inheritance and one previously verified logged path separator change.',
        canonical_registry_source=dict(declaration_sha256=sha256(package/'registry-payloads.json'),
            bytes=json.loads((package/'registry-payloads.json').read_text())['total_bytes'],
            dependency='yo/retained-source/npm-cache: actual canonical package source retained once in local project closure, mandatory for every native packet audit.',
            safety='Native duplicate source removal only after full byte/hash equality and actual source/runtime cleanup; source reference records exact native cleanup inventory and canonical descriptor. Missing/changed local source rejects audit. Counts once against64MiB project gate.'),
        retention_plan='Retain rejectedv1/v2 plus freshv3/v4, local actual reports and canonical source. Exact local catalog duplicates already aliased to unchanged verified archive. Native package source refers to mandatory retained canonical bytes instead of three duplicate copies. Reobserve all-generation64MiB before admission.')
    current.write_text(json.dumps(replacement,sort_keys=True,ensure_ascii=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print('Preserved rejected first series and declared complete fresh yo revision2; canonical87inputs unchanged, zero reused qualification.')


if __name__=='__main__':main()
