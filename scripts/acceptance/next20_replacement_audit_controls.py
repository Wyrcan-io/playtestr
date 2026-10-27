"""Positive readback and deliberate tampering against the actual retained Mac packet."""
import copy
import json
import tarfile
import uuid

from next20_check import RAW
from next20_replacement_audit import audit
from readiness_compact_native import verify
from readiness_evidence import immutable_json,sha256


def main():
    retained=RAW/'replacement-candidate/retained-native-v6'
    index=json.loads((retained/'index.json').read_text());archive=retained/'packets.tar.gz'
    if sha256(archive)!=index['archive_sha256']:raise ValueError('retained packet digest differs')
    verify(archive,index['files'])
    root=RAW/'control-tests'/uuid.uuid4().hex;root.mkdir(parents=True)
    root.resolve(strict=True).relative_to((RAW/'control-tests').resolve(strict=True))
    # Only audited, bounded regular members; resolve aliases from the verified index.
    with tarfile.open(archive,'r:gz') as stream:
        for name,row in index['files'].items():
            destination=root/name;destination.resolve().relative_to(root.resolve())
            data=stream.extractfile(row.get('member',name)).read(row['bytes']+1)
            if len(data)!=row['bytes']:raise ValueError('restored control member length differs')
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(data)
    run='40420820491';packet=root/'native'/run/'next20-private-replacement-macOS'
    provider=json.loads((root/'native'/run/'run-metadata.json').read_text())
    args=('darwin','dbb4d13cafb5ed834410788121ef98ca85937ac7','515ffc3612f9bf4c53a4e26f0baafee1c48dcf89',run)
    receipt,_=audit(packet,provider,*args);observed=['actual-retained-packet-positive']
    def reject(label,metadata):
        try:audit(packet,metadata,*args)
        except (ValueError,KeyError):observed.append(label);return
        raise ValueError('auditor accepted tampering: '+label)
    wrong=copy.deepcopy(provider);wrong['headSha']='0'*40;reject('wrong-provider-source-rejected',wrong)
    wrong=copy.deepcopy(provider)
    next(j for j in wrong['jobs'] if 'macos-15' in j['name'])['conclusion']='failure'
    reject('failed-provider-cell-rejected',wrong)
    label='replacement-focused-native-status-controls';eid=receipt['commands'][label]['id']
    console=packet/'core'/eid/'console.log';original=console.read_bytes()
    console.write_bytes(original+b'changed original console\n');reject('changed-console-rejected',provider);console.write_bytes(original)
    native=packet/'replacement-candidate/native-exit-v1/darwin-arm64'
    manifest=native/'candidate.json';original=manifest.read_bytes();value=json.loads(original)
    value['archive_sha256']='0'*64;manifest.write_text(json.dumps(value))
    reject('changed-archive-digest-rejected',provider);manifest.write_bytes(original)
    audit(packet,provider,*args);observed.append('restored-original-positive')
    immutable_json(root/'replacement-audit-controls.json',dict(schema_version=1,controls=observed,
        original_packet_archive_sha256=sha256(archive),original_receipt=receipt,
        project_credits=0,scope='Auditor controls using an exact verified retained native packet; no target or candidate rebuild. Owned bounded control fixture retained for audit.'))
    print('Actual-packet auditor controls passed:',len(observed),'fixture:',root)


if __name__=='__main__':main()
