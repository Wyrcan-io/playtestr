"""Freeze three independently audited native archives without rebuilding any cell."""
import argparse
import json
import re

from next20_check import RAW,ROOT,DOC
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--linux-run',required=True)
    parser.add_argument('--windows-run',required=True);parser.add_argument('--revision',required=True)
    parser.add_argument('--windows-revision');args=parser.parse_args()
    if any(not re.fullmatch('[0-9]{1,20}',r) for r in [args.linux_run,args.windows_run]) or not re.fullmatch('[0-9a-f]{40}',args.revision):raise ValueError('invalid exact source/run')
    declaration=DOC/'replacement-candidate-retry-v3.json';retry=json.loads(declaration.read_text())
    cells=[]
    for host,run,revision,source in [
        ('darwin','40420820491','dbb4d13cafb5ed834410788121ef98ca85937ac7',retry['original_production_revision']),
        ('linux',args.linux_run,args.revision,retry['retry_source_revision']),
        ('windows',args.windows_run,args.windows_revision or args.revision,retry['retry_source_revision'])]:
        audit_path=DOC/('replacement-native-'+host+'-'+run+'.json');row=json.loads(audit_path.read_text())
        if row['host']!=host or row['run']!=run or row['source_revision']!=source or row['qualification_revision']!=revision or len(row['commands'])!=12:
            raise ValueError('native cell audit does not bind exact required execution')
        readback_path=DOC/('replacement-source-readback-'+host+'-'+run+'.json')
        readback=json.loads(readback_path.read_text())
        if readback['host']!=host or readback['run']!=run or readback['qualification_revision']!=revision or {c['attempt'] for c in readback['commands']}!={c['id'] for c in row['commands'].values()}:
            raise ValueError('complete qualification-source readback does not match native commands')
        archive=ROOT/row['archive_local_only'];archive.resolve(strict=True).relative_to((RAW/'replacement-archives/native-exit-v1').resolve(strict=True))
        if sha256(archive)!=row['archive_sha256'] or archive.stat().st_size!=row['archive_bytes']:raise ValueError('audited candidate archive missing/changed')
        cells.append(dict(row,audit=audit_path.relative_to(ROOT).as_posix(),audit_sha256=sha256(audit_path),
            qualification_source_readback=readback_path.relative_to(ROOT).as_posix(),qualification_source_readback_sha256=sha256(readback_path)))
    immutable_json(DOC/'replacement-candidate-freeze-native-exit-v1.json',dict(schema_version=1,series='native-exit-v1',version='v0.4.0-rc.6',
        original_production_revision=retry['original_production_revision'],retry_source_revision=retry['retry_source_revision'],
        source_equivalence_declaration=declaration.relative_to(ROOT).as_posix(),source_equivalence_sha256=sha256(declaration),
        cells=cells,project_credits=0,publication=False,
        qualification='Three real native source/test/vet/race and single-build archive cells independently audited. Exact source/test revisions differ by one reviewed test-only fixture; all production/package inputs identical. No rc.5 project results transferred. External project, old migration, archive public controls and whole-campaign qualification remain open.'))
    print('Froze three exact distinct private archives; no rebuild, no project credit.')


if __name__=='__main__':main()
