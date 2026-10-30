"""Retain peco native artifacts with exact references to the original packet."""
import argparse
import asyncio
import io
import json
import re
import zipfile

from adversarial_process import execute
from next20_check import RAW, ROOT, NextCampaign, owned_environment
from next20_native_zip_packet import download
from next20_referenced_native_zip import retain
from readiness_evidence import immutable_json


async def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);parser.add_argument('--revision',required=True)
    parser.add_argument('--artifact',default='next20-peco-linux-development');parser.add_argument('--generation',type=int,required=True)
    parser.add_argument('--base-generation',type=int,default=1);args=parser.parse_args()
    if not re.fullmatch('[0-9]{1,20}',args.run) or not re.fullmatch('[0-9a-f]{40}',args.revision) or args.artifact not in {'next20-peco-linux-development','next20-peco-linux-final'}:
        raise ValueError('undeclared exact peco native acquisition')
    output=RAW/'peco'/('retained-native-v'+str(args.generation))
    if output.exists():raise ValueError('preserve original native generation')
    result=await execute(['gh','run','view',args.run,'--repo','Wyrcan-io/playtestr','--json','status,conclusion,headSha,jobs'],
        'core','peco-exact-reference-provider-'+args.run,cwd=ROOT,env=owned_environment(),timeout=60,campaign=NextCampaign())
    provider=json.loads(result['output'])
    if provider['headSha']!=args.revision or provider['status']!='completed':raise ValueError('native provider source/status differs')
    metadata=json.loads(await asyncio.to_thread(download,['gh','api','repos/Wyrcan-io/playtestr/actions/runs/'+args.run+'/artifacts'],1024**2))
    matches=[a for a in metadata['artifacts'] if a['name']==args.artifact and not a['expired']]
    if len(matches)!=1 or matches[0]['size_in_bytes']>32*1024**2:raise ValueError('peco artifact count/32MiB bound')
    payload=await asyncio.to_thread(download,['gh','api','repos/Wyrcan-io/playtestr/actions/artifacts/'+str(matches[0]['id'])+'/zip'],32*1024**2)
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if any(p.file_size>16*1024**2 for p in archive.infolist()):raise ValueError('peco original member16MiB bound')
    index=await asyncio.to_thread(retain,payload,output,'peco',args.run,args.artifact,args.base_generation)
    immutable_json(output/'provider.json',provider)
    immutable_json(output/'acquisition.json',dict(schema_version=1,run=args.run,revision=args.revision,artifact=args.artifact,artifact_id=matches[0]['id'],
        provider_zip_bytes=len(payload),provider_zip_sha256=index['provider_zip_sha256'],expanded_native_payload_written=False,
        mandatory_standalone_generation=args.base_generation,qualification_credit=0))
    print('Retained peco original native artifact:',index['logical_files'],'logical files;',len(index.get('external_exact_payloads',{})),'exact original references;',index['archive_bytes'],'new XZ bytes; no admission.')


if __name__=='__main__':asyncio.run(main())
