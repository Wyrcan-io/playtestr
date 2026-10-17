"""Acquire the next reviewed RubyGems/Bundler source; run no build hooks."""
from readiness_acquire_plop import acquire, extract_source
from readiness_evidence import RAW, ROOT, immutable_json, sha256
import argparse
import json
from pathlib import Path

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--resume',action='store_true')
    parser.add_argument('--archive-proof',type=Path);args=parser.parse_args()
    pin='f033df93676007227d1ae0bd7326008e6396b3e9'
    if args.archive_proof:
        args.archive_proof.resolve(strict=True).relative_to(ROOT)
        target=RAW/'active/rubygems';archive=target/'source.tar.gz'
        owner=json.loads((target/'task-owned.json').read_text())
        proof=json.loads(args.archive_proof.read_text())
        if owner!=dict(workspace=str(ROOT),campaign='runner-readiness-ten-project-pass',project='ruby/rubygems',pin=pin):
            raise RuntimeError('partial source ownership mismatch')
        if archive.stat().st_size>32*1024**2 or sha256(archive)!=proof['archive_sha256'] or proof['pin']!=pin:
            raise RuntimeError('partial archive identity mismatch')
        count,total=extract_source(archive.read_bytes(),target/'src',expanded_limit=192*1024**2,
                                   entry_limit=20000,member_limit=32*1024**2)
        immutable_json(target/'acquisition.json',dict(pin=pin,archive_sha256=sha256(archive),
            compressed_bytes=archive.stat().st_size,extracted_source_bytes=total,entries=count,
            build_hooks_executed=False,completed_after_preserved_guard_failure=True))
        print('Completed reviewed pinned RubyGems source:',count,'members,',total,'expanded bytes')
    else:
        acquire('rubygems','ruby/rubygems',pin,archive_limit=32*1024**2,
                expanded_limit=192*1024**2,entry_limit=20000,member_limit=32*1024**2,resume=args.resume)
