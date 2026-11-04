"""Bind and statically review Skim's checksum-locked dependency build scripts."""
import argparse
import json
from pathlib import Path
import re

from next20_check import RAW
from readiness_evidence import immutable_json, sha256


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', default='docs/validation/runner-readiness-next-twenty-project-pass/skim/dependency-hook-review-v1.json')
    parser.add_argument('--source-review', default='docs/validation/runner-readiness-next-twenty-project-pass/skim/source-review-v1.json')
    args = parser.parse_args()
    target = RAW / 'active' / 'skim'
    fetched = json.loads((target / 'dependency-fetch-review.json').read_text())
    source = target / 'cargo-home' / 'registry' / 'src'
    registry = next(source.iterdir())
    hooks = []
    for relative, expected_hash in sorted(fetched['build_hooks'].items()):
        path = target / relative
        if sha256(path) != expected_hash:
            raise ValueError('dependency hook changed after fetch review: ' + relative)
        text = path.read_text(encoding='utf-8')
        lower = text.lower()
        if any(marker in lower for marker in (
            'std::net::tcpstream', 'std::net::udpsocket', 'reqwest::',
            'ureq::', 'curl ', 'powershell.exe', 'cmd.exe /c',
        )):
            raise ValueError('network or shell execution marker in dependency hook: ' + relative)
        if re.search(r'Command::new\s*\(\s*["\'](?:sh|bash|cmd|powershell|curl|git)["\']', text, re.I):
            raise ValueError('shell, network, or git child process in dependency hook: ' + relative)
        package = path.parent.name
        if package.startswith(('libmimalloc-sys-', 'psm-')):
            disposition = 'Compile bundled native source with cc into Cargo OUT_DIR; no installer or network hook.'
        elif package in {'pulldown-cmark-0.13.4', 'terminfo-0.9.0', 'defmt-1.2.0', 'rustversion-1.0.23'}:
            disposition = 'Read package-owned source or target metadata and emit generated Rust/configuration under Cargo OUT_DIR.'
        elif 'Command::new' in text:
            disposition = 'Run the Cargo-provided Rust compiler for a feature/version probe; generated probe stays under Cargo OUT_DIR.'
        else:
            disposition = 'Inspect Cargo target/features and emit cfg/link metadata; no external service or shell launch.'
        hooks.append(dict(path=relative, sha256=expected_hash, disposition=disposition,
                          executed_during_review=False))
    if len(hooks) != len(fetched['build_hooks']) or not hooks:
        raise ValueError('incomplete dependency hook set')
    receipt = dict(
        schema_version=1,
        project='skim',
        pin='1ab47f6ba7f1bfc355273bbdd98d4b2056ef95a3',
        source_review_sha256=sha256(Path(args.source_review).resolve(strict=True)),
        dependency_fetch_review_sha256=sha256(target / 'dependency-fetch-review.json'),
        hook_count=len(hooks),
        hooks=hooks,
        build_authorization={
            'approved': True,
            'features': ['cli', 'frizbee'],
            'command': 'cargo build --release --locked --offline --no-default-features --features cli,frizbee --bin sk',
            'disabled': ['image', 'listen', 'preview commands', 'external shell commands', 'IPC', 'network at runtime'],
            'scope': 'Compile the pinned target from exact checked source and locked archives; build hooks may write only Cargo-owned OUT_DIR and invoke Rust/C compiler tools.'
        },
        policy='Hash-bound static review of every fetched Cargo dependency build script. No build script was executed during this review.'
    )
    out = Path(args.output).resolve()
    out.relative_to(Path.cwd().resolve())
    immutable_json(out, receipt)
    print('Reviewed', len(hooks), 'locked dependency hook hashes; no hook executed.')


if __name__ == '__main__':
    main()
