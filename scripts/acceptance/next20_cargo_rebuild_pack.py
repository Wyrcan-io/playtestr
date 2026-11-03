"""Retain six actual rebuilt Cargo images using mandatory original dictionaries."""
import json
import argparse
import os
from pathlib import Path

from next20_check import DOC, RAW, ROOT
from next20_lzma_dictionary import encode, decode, digest
from readiness_evidence import immutable_json, sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--window',type=int,choices=[1,2,3],default=1);args=parser.parse_args()
    host = 'windows' if os.name == 'nt' else 'linux'
    if args.window!=1 and host!='windows':raise ValueError('replacement image window is Windows-only')
    package = DOC / 'cargo-generate'
    declaration_path = package / 'rebuild-binary-retention-declaration-v1.json'
    declaration = json.loads(declaration_path.read_text())
    target = RAW / 'active/cargo-generate'
    build = json.loads((target / 'build.json').read_text())
    baseline = (target / build['binary_relative_path']).read_bytes()
    if digest(baseline) != declaration['original_images'][host]['original'] or digest(baseline) != build['binary_sha256']:
        raise ValueError('exact original baseline dictionary required')
    suffix='v'+str(args.window)
    root = RAW / ('cargo-generate/rebuild-executables-'+suffix)
    root.mkdir(exist_ok=False)
    records = {}
    compiled = RAW / ('cargo-generate/source-fault-rebuild-recovery-'+suffix)
    for fault in ['F01', 'F02', 'F03']:
        for stage, suffix in [('mutated', '-compiled.json'), ('restored', '-normal-restored-compiled.json')]:
            receipt = compiled / (fault + suffix)
            value = json.loads(receipt.read_text())
            path = ROOT / value['binary']
            path.resolve(strict=True).relative_to(target.resolve(strict=True))
            if path.is_symlink() or not 0 < path.stat().st_size <= 32 * 1024**2 or sha256(path) != value['binary_sha256']:
                raise ValueError('actual compiler image changed or exceeded bound')
            body = path.read_bytes()
            matches = [name for name, expected in declaration['original_images'][host].items() if digest(body) == expected]
            row = dict(bytes=len(body), sha256=digest(body), compile_receipt=receipt.relative_to(ROOT).as_posix(), compile_receipt_sha256=sha256(receipt))
            if matches:
                row.update(encoding='exact-original-image-reference', original_image=matches[0])
            else:
                payload, codec = encode(baseline, body)
                name = fault + '-' + stage + '.lzma2'
                with (root / name).open('xb') as stream:
                    stream.write(payload)
                if decode(baseline, (root / name).read_bytes(), codec) != body:
                    raise ValueError('actual new image full-byte roundtrip failed')
                row.update(encoding='raw-lzma2-preset-dictionary-v1', payload=name, codec=codec)
            records[fault + '-' + stage] = row
            print(host, fault, stage, row['encoding'], flush=True)
    immutable_json(root / 'index.json', dict(schema_version=1, project='cargo-generate', host=host, window=args.window,
        declaration_sha256=sha256(declaration_path), files=records, actual_original_baseline_sha256=digest(baseline),
        original_dictionaries_mandatory=True, independently_decoded_after_retention=False,
        scope='Every actual compiler image matched its receipt and either a declared original image digest or a fully byte-compared bounded delta. Independent readback against mandatory retained original dictionaries still required. No cleanup/admission credit.'))


if __name__ == '__main__':
    main()
