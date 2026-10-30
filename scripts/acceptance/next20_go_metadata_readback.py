"""Independently bind cached module metadata to the reviewed Go checksum records."""
import argparse
import base64
import hashlib
import json
from pathlib import Path

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


def main():
    parser=argparse.ArgumentParser();parser.add_argument('project');args=parser.parse_args();project=args.project
    if '/' in project or '\\' in project:raise ValueError('unsafe Go metadata project')
    target=RAW/'active'/project;fetch=json.loads((target/'module-fetch.json').read_text());review=json.loads((DOC/project/'dependency-source-review-declaration.json').read_text());rows=[];files={}
    for module in fetch['modules']:
        rule=review['modules'][module['Path']+'@'+module['Version']]
        path=Path(module['GoMod']);path.resolve(strict=True).relative_to(target.resolve(strict=True));body=path.read_bytes()
        digest=hashlib.sha256(body).hexdigest();go_digest='h1:'+base64.b64encode(hashlib.sha256((digest+'  go.mod\n').encode()).digest()).decode()
        if go_digest!=module['GoModSum'] or go_digest!=rule['go_mod_sum']:raise ValueError('actual cached go.mod differs from reviewed Go checksum')
        files[path.relative_to(target).as_posix()]=digest
        info=Path(module['Info']);info.resolve(strict=True).relative_to(target.resolve(strict=True));metadata=json.loads(info.read_text())
        if metadata['Version']!=module['Version']:raise ValueError('actual cached module version metadata differs')
        files[info.relative_to(target).as_posix()]=sha256(info)
        rows.append(dict(path=module['Path'],version=module['Version'],go_mod_relative_path=path.relative_to(target).as_posix(),go_mod_sha256=digest,go_mod_sum=go_digest,info_relative_path=info.relative_to(target).as_posix(),info_sha256=sha256(info)))
    immutable_json(target/'module-metadata-readback.json',dict(schema_version=1,modules=rows,files=files,source_review_sha256=sha256(DOC/project/'dependency-source-review-declaration.json'),
        scope='Actual cached module go.mod bytes independently match Go h1 single-file checksums and reviewed values;version info matches locked versions. Binds graph metadata in addition to actual ZIP/installed-source readback. No build or target execution.'))
    print('Verified actual go.mod checksums and cached version info for',len(rows),'modules.')


if __name__=='__main__':main()
