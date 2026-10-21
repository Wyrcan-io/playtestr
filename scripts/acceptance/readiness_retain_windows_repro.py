"""Retain small diagnostic evidence before checked owned-root removal."""
import argparse
import shutil

from readiness_evidence import RAW, ROOT, immutable_json, sha256
from readiness_new_control_matrix import read_json as load


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',choices=['superfile','glow'],required=True)
    args=parser.parse_args()
    slug='r3-windows-'+args.project
    target=RAW/'active'/slug
    owner=load(target/'task-owned.json')
    review=load(ROOT/'docs/validation/runner-readiness-ten-project-pass/old-migration'/args.project/'source-review.json')
    if owner['workspace']!=str(ROOT) or owner['pin']!=review['pin'] or owner['scope']!='R3-04 diagnostic only':
        raise RuntimeError('diagnostic owner differs')
    actual={p.relative_to(target/'src').as_posix():sha256(p) for p in (target/'src').rglob('*') if p.is_file()}
    if actual!=review['reviewed_inputs']:
        raise RuntimeError('original source changed')
    output=RAW/slug/'retained-evidence'
    output.mkdir()
    selected=list(target.glob('*.json'))+list(target.glob('captured-*'))
    for folder in target.iterdir():
        if folder.is_dir() and (folder.name.endswith('package') or folder.name.startswith('evidence-')):
            selected.extend(p for p in folder.rglob('*') if p.is_file())
    files={};total=0
    for source in selected:
        if source.is_symlink() or source.stat().st_size>4*1024**2:
            raise RuntimeError('unsafe diagnostic evidence')
        total+=source.stat().st_size
        if total>8*1024**2 or len(files)>=2000:
            raise RuntimeError('diagnostic retention bound')
        relative=source.relative_to(target).as_posix()
        destination=output/relative
        destination.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,destination)
        if sha256(source)!=sha256(destination):
            raise RuntimeError('diagnostic evidence copy differs')
        files[relative]=sha256(destination)
    immutable_json(output/'retention-index.json',dict(project=args.project,owned_relative_path='active/'+slug,
        owner_sha256=sha256(target/'task-owned.json'),original_source_catalog=actual,
        canonical_archive_sha256=review['archive_sha256'],files=files,bytes=total,
        scope='Original canonical source archive already retained once; diagnostic binary/caches are expendable after identity capture. Complete reports, contracts, snapshots, fixtures and race captures retained; global immutable command events/identities remain unchanged.'))
    print('Verified small diagnostic retention:',args.project,total,'bytes')


if __name__=='__main__':main()
