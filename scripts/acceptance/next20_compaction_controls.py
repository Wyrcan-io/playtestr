"""Exercise historical packing defaults and the explicitly bounded larger option."""
import inspect
import uuid

from next20_check import RAW
from readiness_compact_native import compact
from readiness_evidence import immutable_json, sha256


def main():
    root=RAW/'control-tests'/uuid.uuid4().hex
    if inspect.signature(compact).parameters['max_archive_bytes'].default!=16*1024**2:
        raise ValueError('historical compact default changed')
    packets=[]
    for variant in ['historical-default','explicit24']:
        owned=root/variant;(owned/'native/123456789').mkdir(parents=True);(owned/'control').mkdir()
        (owned/'native/123456789/captured.txt').write_bytes(b'Actual retained packing control\n'*100)
        options=dict(max_archive_bytes=24*1024**2) if variant=='explicit24' else {}
        retained=compact(owned,'control',['123456789'],**options);packets.append(retained)
    if sha256(packets[0]/'packets.tar.gz')!=sha256(packets[1]/'packets.tar.gz'):
        raise ValueError('new explicit limit changed identical packet bytes')
    try:compact(root/'invalid','control',['123456789'],max_archive_bytes=32*1024**2)
    except ValueError as error:
        if str(error)!='unreviewed compressed evidence bound':raise
    else:raise ValueError('unapproved archive bound accepted')
    if (root/'invalid').exists():raise ValueError('invalid limit wrote data before refusal')
    immutable_json(root/'verified.json',dict(schema_version=1,
        default_archive_limit_bytes=16*1024**2,explicit_archive_limit_bytes=24*1024**2,
        actual_archive_sha256=sha256(packets[0]/'packets.tar.gz'),identical_packet_bytes=True,
        unapproved32mib_refused_before_write=True,scenario_credit=0,
        scope='Actual deterministic archive/restore checks preserve historical default behavior; larger option is explicit and bounded.'))
    print('Historical default remains16MiB; actual packet bytes equal under explicit24MiB; unapproved limit refused before writes.')


if __name__=='__main__':main()
