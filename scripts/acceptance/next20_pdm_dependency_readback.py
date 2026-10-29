"""Bind actual installed dependency code to reviewed primary-release wheel bytes."""
from email.parser import BytesParser
import hashlib
import io
import json
import uuid
import zipfile

from next20_check import DOC, RAW
from next20_native_packet_reader import read_packet
from next20_python_runtime import python_runtime_root
from readiness_evidence import immutable_json, sha256


def require(value,message):
    if not value:raise ValueError(message)


def main():
    package=DOC/'pdm';target=RAW/'active/pdm'
    local=target if target.is_dir() else RAW/'pdm/retained-source'
    retained=None
    def local_data(path):
        nonlocal retained
        if path.is_file():return path.read_bytes()
        if retained is None:
            from next20_local_records import read_packet as read_local
            _,retained=read_local('pdm')
        name=path.relative_to(RAW).as_posix()
        require(name in retained,'retained dependency metadata missing: '+name)
        return retained[name]
    def local_json(path):return json.loads(local_data(path).decode('utf-8-sig'))
    review=json.loads((package/'source-review.json').read_text())
    extra_root=RAW/'pdm/runtime-revision/v2';extra=local_json(extra_root/'reviewed-wheels.json')
    primary={}
    for rows,root in [(review['dependencies'],local/'dependency-review/primary'),(extra['wheels'],extra_root/'primary')]:
        for row in rows:
            path=root/(row['wheel']+'.json')
            require(hashlib.sha256(local_data(path)).hexdigest()==row['primary_metadata_sha256'],'reviewed primary release body changed')
            for item in local_json(path)['urls']:
                if item['packagetype']=='bdist_wheel':primary[item['filename']]=item['digests']['sha256']
    _,native=read_packet('pdm',3);prefix='native/40869293414/next20-pdm-linux-final/'
    def native_data(relative):return native[prefix+relative]
    lock=json.loads((package/'native-runtime-lock.json').read_text())['versions'];results=[]
    for host in ['windows','linux']:
        if host=='windows':
            runtime=local_json(local/'runtime.json');inventory=local_json(local/'installed-inventory.json')['files']
            wheel_paths=[*sorted((local/'wheels').glob('*.whl')),*sorted((extra_root/'wheels').glob('*.whl'))]
            wheels={p.name:p.read_bytes() for p in wheel_paths}
        else:
            runtime=json.loads(native_data('pdm/retained-source/runtime.json'))
            inventory=json.loads(native_data('pdm/retained-source/installed-inventory.json'))['files']
            wheel_rows=json.loads(native_data('pdm/retained-source/wheels.json'))
            wheels={name:native_data('pdm/retained-source/wheels/'+name) for name in wheel_rows}
            for name,row in wheel_rows.items():require(hashlib.sha256(wheels[name]).hexdigest()==row['sha256'],'retained native wheel changed')
        prefixes={n.split('/site-packages/')[0]+'/site-packages/' for n in inventory if '/site-packages/' in n}
        require(len(prefixes)==1,'ambiguous installed package root');site=prefixes.pop()
        metadata={n[len(site):]:d for n,d in inventory.items() if n.startswith(site) and n.endswith('.dist-info/METADATA')}
        selected=[];covered=set();code_files=0
        for filename,raw in wheels.items():
            require(primary.get(filename)==hashlib.sha256(raw).hexdigest(),'actual wheel absent from reviewed primary digest bodies')
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                names=archive.namelist();metafiles=[n for n in names if n.endswith('.dist-info/METADATA')]
                require(len(metafiles)==1,'wheel metadata ambiguous');meta=metafiles[0]
                info=BytesParser().parsebytes(archive.read(meta));distribution=info['Name'].lower().replace('_','-')
                if meta not in metadata:continue
                require(lock.get(distribution)==info['Version'],'installed dependency differs from reviewed version lock')
                require(metadata[meta]==hashlib.sha256(archive.read(meta)).hexdigest(),'actual installed distribution metadata differs')
                require(meta not in covered,'duplicate actual installed dependency');covered.add(meta)
                for entry in archive.infolist():
                    if entry.is_dir() or entry.filename.endswith('.dist-info/RECORD'):continue
                    require('.data/' not in entry.filename and not entry.filename.endswith('.pth'),'unexpected startup or relocated dependency wheel payload')
                    body=archive.read(entry)
                    require(inventory.get(site+entry.filename)==hashlib.sha256(body).hexdigest(),'actual installed package payload differs: '+entry.filename)
                    if entry.filename.endswith(('.py','.so','.pyd','.dll')):code_files+=1
                selected.append(dict(name=distribution,version=info['Version'],wheel=filename,wheel_sha256=hashlib.sha256(raw).hexdigest()))
        bootstrap={n for n in metadata if n.startswith(('pip-','setuptools-','pdm-'))}
        require(set(metadata)==covered|bootstrap and len(selected)==38,'installed dependency coverage differs')
        hooks={n:d for n,d in inventory.items() if n.endswith('.pth')}
        require(set(hooks)=={site+'_editable_impl_pdm.pth'},'unexpected actual interpreter startup path hook')
        generated=json.loads(native_data('pdm/native-generated-source.json')) if host=='linux' else json.loads((package/'runtime-generated-source.json').read_text())
        require(hooks[site+'_editable_impl_pdm.pth']==generated['generated_files']['.pdm-build/_editable_impl_pdm.pth']['sha256'],'installed editable path differs from independently reviewed generated source path')
        if host=='windows' and target.is_dir():
            runtime_root=python_runtime_root(target,runtime)
            for name,digest in inventory.items():require(sha256(runtime_root/name)==digest,'actual current Windows installed bytes changed')
        elif host=='windows':
            cleanup=local_json(local/'cleanup-inventory.json');directory=runtime.get('runtime_directory','venv')+'/'
            for name,digest in inventory.items():require(cleanup['files'][directory+name]['sha256']==digest,'actual removed Windows installed bytes differed')
        if host=='linux':
            cleanup=json.loads(native_data('pdm/retained-source/cleanup-inventory.json'))
            for name,digest in inventory.items():require(cleanup['files']['venv/'+name]['sha256']==digest,'actual removed Linux installed bytes differed')
        results.append(dict(host=host,reviewed_dependencies=len(selected),code_files=code_files,selected=selected,
            installed_inventory_files=len(inventory),editable_path_verified=True,source_runtime_removed=host=='linux' or not target.is_dir()))
    destination=RAW/'pdm/dependency-readbacks'/uuid.uuid4().hex
    immutable_json(destination/'verified.json',dict(schema_version=1,results=results,primary_release_bodies=42,
        original_review_sha256=sha256(package/'source-review.json'),runtime_revision_review_sha256=hashlib.sha256(local_data(extra_root/'reviewed-wheels.json')).hexdigest(),
        scope='Every actual selected dependency wheel matches retained reviewed primary-release digest bodies. Installed package payloads,including Python/native extension code,match those wheels. Windows actual selected runtime rehashed; Linux actual removal inventory binds bytes. Read-only installed Python SDK/bootstrap remain separately identified prerequisites,not a retained SDK or security-isolation claim.',project_admissions=0))
    print('Independently verified38 actual dependencies per host against42 retained primary-release bodies and complete installed code payloads; no admission.')


if __name__=='__main__':main()
