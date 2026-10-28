"""Admit Cargo only from both actual cells and complete retained journey evidence."""
import base64
import argparse
import copy
import hashlib
import json
import lzma
import uuid

from next20_check import RAW,DOC,ROOT,NAME
from next20_cargo_cell_model import validate,challenge,require
from next20_local_records import read_packet as local_packet
from next20_native_packet_reader import read_packet
from readiness_evidence import immutable_json,sha256
from readiness_storage import measure


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--verify-existing',action='store_true');args=parser.parse_args()
    package=DOC/'cargo-generate';raw=RAW/'cargo-generate';subjects={}
    require(not (RAW/'active/cargo-generate').exists(),'Cargo target remains active locally')
    local_index,local=local_packet('cargo-generate');native_index,native=read_packet('cargo-generate',13)
    def data(path):
        if path.is_file():value=path.read_bytes()
        else:value=local[path.relative_to(RAW).as_posix()]
        subjects[path.relative_to(ROOT).as_posix()]=hashlib.sha256(value).hexdigest();return value
    def load(path):return json.loads(data(path).decode('utf-8-sig'))
    def digest(path):return hashlib.sha256(data(path)).hexdigest()
    def command(eid):
        events={event:load(RAW/'events'/(eid+'-'+event+'.json')) for event in ['started','identified','launched','finished']}
        require(all(r['id']==eid and r['campaign']==NAME for r in events.values()),'wrong/incomplete original engineering attempt')
        finish=events['finished']
        require(finish['category']=='passed' and finish['exit_code']==events['started']['expected_exit'] and not finish['cleanup_errors'] and finish['harness_cleanup']=='harness_process_reaped','original command result/reaping differs')
        reference=events['identified']['identity'];depth=0
        while True:
            manifest=RAW/reference['manifest'];require(digest(manifest)==reference['sha256'],'public/maintenance actual prelaunch identity changed')
            identity=load(manifest);depth+=1;require(depth<=5,'identity reference chain bound')
            if 'base' not in identity:break
            reference=identity['base']
        require(identity['files'].get('artifacts/'+NAME+'/candidate-native-exit-v1/windows/playtestr.exe')==windows['binary_sha256'],'public/maintenance command launched another runner')
        return events
    provenance=load(package/'source-provenance.json');freeze=load(package/'development-test-freeze.json');scenarios=load(package/'scenarios.json')
    for name,value in freeze['inputs'].items():require(digest(package/name)==value,'frozen canonical input changed')
    require(len(scenarios['cases'])==20 and sum(c['kind']=='normal' for c in scenarios['cases'])==8 and sum(c['kind']=='edge' for c in scenarios['cases'])==12 and sum(bool(c['combined_risks']) for c in scenarios['cases'])>=4,'canonical scenario/risk boundary differs')
    candidate=load(DOC/'replacement-candidate-freeze-native-exit-v1.json');windows=next(c for c in candidate['cells'] if c['host']=='windows')
    source_paths=sorted(raw.glob('source-closure-*.json'));require(bool(source_paths),'complete actual source/executable readback absent')
    source_path=source_paths[-1];source=load(source_path)
    require(source['registry_inner_tars']==341 and source['registry_source_files']==15270 and {c['host'] for c in source['cells']}=={'windows','linux'},'partial actual source closure')
    for path,key in [(raw/'registry-source-corpus-v1/index.json','required_corpus_index_sha256'),(raw/'registry-source-corpus-v1/sources.tar.xz','required_corpus_archive_sha256'),
        (raw/'retained-native-v13/index.json','current_linux_index_sha256'),(raw/'retained-native-v13/packets.tar.xz','current_linux_archive_sha256'),
        (raw/'native-solid-variants/windows/index.json','windows_executable_index_sha256'),(raw/'native-solid-variants/windows/executables.tar.xz','windows_executable_archive_sha256')]:require(digest(path)==source[key],'required actual source/executable corpus changed')
    source_marker=load(package/'registry-source-corpus-reference-v1.json');require(source_marker['required_dictionary_index_sha256']==source['required_corpus_index_sha256'],'required source dictionary reference changed')
    # Native packet history is still fully readable, including first failures.
    for generation in [1,2,3,4,5,9,11,13]:
        index,records=read_packet('cargo-generate',generation)
        for name in ['index.json','verified.json']:data(raw/('retained-native-v'+str(generation))/name)
        data(raw/('retained-native-v'+str(generation))/('packets.'+index.get('compression','tar.gz')))
    history=load(raw/'retained-native-v12/retention-promotion.json')
    require(history['only_superseded_generated_encoding_removed'] and history['all_actual_report_input_metadata_and_four_executable_bytes_preserved'] and
        history['required_replacement_index_sha256']==digest(raw/'retained-native-v13/index.json') and history['required_replacement_archive_sha256']==digest(raw/'retained-native-v13/packets.tar.xz'),'successful packet supersession unbound')
    public_path=package/'candidate-authoring/native-exit-v1/1/requalification.json';public=load(public_path)
    require(public['runner_sha256']==windows['binary_sha256'] and public['shell_invocations']==3 and public['recorder_controls']==20 and not public['first_attempt'] and not public['handwritten_playtestr_json'],'replacement public authoring metrics differ')
    require(public['historical_first_use_sha256']==digest(package/'first-use.json'),'historical first-use misses lost')
    for eid in public['attempts']:command(eid)
    report=ROOT/public['ordinary_report'];require(digest(report)==public['ordinary_report_sha256'],'public ordinary report changed')
    row=load(report)['results'][0];require(row['status']=='passed' and all(s['status']=='passed' for s in row['steps']) and row['cleanup']['confirmed_exited'] and row['workspace']['cleaned'],'public route not positive/clean')
    require(digest(public_path.parent/'normal-project.json')==public['spec_sha256'],'public approved spec changed')
    public_spec=load(public_path.parent/'normal-project.json')
    for step in public_spec['steps']:
        state=step.get('state',{})
        if state.get('kind')=='file':require(hashlib.sha256(base64.b64decode(state['bytes_base64'],validate=True)).hexdigest()==public['independent_expected_file_sha256'][state['path']],'public file approval differs from independent expected bytes')
    journey_root=raw/'maintenance-38db8dec0d474f7c9f8eda890ec39c1e';journey=load(journey_root/'journey.json')
    require(journey['runner_sha256']==windows['binary_sha256'] and journey['unrelated_assertions_preserved'] and journey['maintained_spec_sha256']==journey['relocated_spec_sha256'],'maintenance archive/relocation scope differs')
    for item in journey['attempts']:command(item['id'])
    require(digest(journey_root/'actual-source-fault.html')==journey['html_sha256'] and digest(journey_root/'cargo-diagnosis-relative-actual-source-fault.report.json')==journey['actual_fault_report_sha256'],'actual source-fault HTML diagnosis changed')
    maintained=load(journey_root/'route/maintained.json');expected=copy.deepcopy(load(package/'normal-project.json'));expected['command'][0]=maintained['command'][0]
    expected['steps'][journey['selected_state_step']-1]['state']['bytes_base64']=base64.b64encode(b'project=synthetic-notes\nowner=Ada\nmode=basic\nreadme=true\nreviewed=yes\n').decode()
    require(maintained==expected and digest(journey_root/'route/maintained.json')==journey['maintained_spec_sha256'],'selected update changed unrelated original oracle')
    for filename in ['maintained.json','suffix.json']:require(data(journey_root/'route'/filename)==data(journey_root/'relocated caf\u00e9 \u96ea'/filename),'relocated contract bytes differ')
    suffix=load(journey_root/'route/suffix.json');states={s['state']['path']:s['state'] for s in suffix['steps'] if s.get('state',{}).get('kind')=='file'}
    require(not any(s.get('text')=='Ada' for s in suffix['steps']) and base64.b64decode(states['synthetic-notes/profile.txt']['bytes_base64'])==b'project=synthetic-notes\nowner=Grace\nmode=basic\nreadme=true\nreviewed=yes\n','suffix rerecord did not replace actual owner outcome')
    data(raw/'generated-source-workflow.yml');command('afc6a8e901db4d78bf10dbb237a7d349')
    # No remote execution is inferred from a generated/linted workflow.
    controls=list((raw/'audit-controls').glob('*/results.json'));require(len(controls)==1,'missing/ambiguous actual complete cell-model challenges')
    result=load(controls[0]);require(result['semantic_corruptions_rejected']==24 and len(result['cells'])==2,'incomplete semantic model controls')
    cells=[]
    for cell in result['cells']:
        path=RAW/cell['model'];require(digest(path)==cell['model_sha256'],'actual model encoding changed')
        encoded=lzma.decompress(data(path),memlimit=64*1024**2);require(hashlib.sha256(encoded).hexdigest()==cell['decoded_model_sha256'],'actual decoded model changed')
        model=json.loads(encoded);require(validate(model)==cell['counts'] and challenge(model)==cell['controls'],'actual model corruption controls not reproducible')
        readback=load(RAW/model['independent_readback']['path']);require(digest(RAW/model['independent_readback']['path'])==model['independent_readback']['sha256'] and readback['ordinary_readbacks']==240 and readback['calibration_readbacks']==9,'independent complete actual readback changed')
        expected=next(c for c in candidate['cells'] if c['host']==cell['host'])
        source_cell=next(c for c in source['cells'] if c['host']==cell['host'])
        cells.append(dict(host=cell['host'],run=readback['run'],source_revision=readback['revision'],ordinary=240,calibrations=9,
            candidate_archive_sha256=expected['archive_sha256'],runner_sha256=expected['binary_sha256'],actual_target_binary_sha256=source_cell['actual_executable_sha256']['original'],
            actual_model=cell['model'],actual_model_sha256=cell['model_sha256'],execution_host='ubuntu-24.04' if cell['host']=='linux' else 'Windows-11-10.0.26300-SP0'))
    require({c['host'] for c in cells}=={'windows','linux'},'native host breadth incomplete')
    for name in ['invalid-spec-refusal-disposition.json','development-key-disposition.json','development-outcome-disposition.json','native-linux-first-final-rejection.json','native-linux-second-final-rejection.json','native-linux-backspace-trace-v1.json','native-linux-input-echo-trace-v1.json','native-linux-readiness-profile-v4.json','final-linux-replacement-declaration-native-exit-v1-v3.json','fault-declaration.json']:load(package/name)
    size=measure(raw)['total_bytes'];require(size<=64*1024**2,'complete project retained evidence exceeds64MiB')
    value=dict(schema_version=1,project='cargo-generate',repository=provenance['repository'],pin=provenance['pin'],admitted=True,
        candidate='v0.4.0-rc.6',native_cells=cells,canonical_scenarios=20,normal=8,edge=12,ordinary=480,calibrations=18,real_source_faults=3,
        cell_model_negative_controls=24,local_target_absent=True,retained_bytes=size,source_closure=source_path.relative_to(RAW).as_posix(),
        public_repaired_repeat=dict(shell_invocations=3,recorder_controls=20,first_attempt=False),maintenance_suffix_relocation=True,generated_workflow=True,delivered_ci_observations=0,
        initial_usability_target_met=False,human_participants=0,human_usability='unmeasured',paid_admissions=0,subjects=subjects,
        limitations=['Unpublished private engineering qualification of exact rc.6 archives; no stable/public release claim.',
            'Two rejected complete Linux windows and two diagnostics preserve actual upstream termios/input-consumption races. Additive Linux checkpoints retain every original action/oracle; no zero-flake or untouched-holdout claim.',
            'Original generated compression wrappers are explicitly superseded, not byte-reconstructible. Every actual compiled source/executable/report/input byte remains verified and requires the physical declared dictionaries.',
            'A transient per-project retained-evidence cap breach during earlier experiments remains recorded; current cap compliance does not erase that breach.',
            'Generated free workflow is retained but not dispatched; global delivered-source/archive CI qualification remains outstanding.'],
        scope='One new project admission on current candidate from two complete actual native cells,480ordinary/18fresh mandatory calibrations,real source faults,source/executable retention,public authoring/maintenance and24negative evidence challenges. Historical rc.5 admissions and global next-twenty closure remain separate.')
    if args.verify_existing:
        existing=load(package/'admission.json')
        for key in ['project','repository','pin','admitted','candidate','native_cells','ordinary','calibrations','canonical_scenarios','real_source_faults','cell_model_negative_controls']:
            require(existing[key]==value[key],'original admission differs from complete current readback: '+key)
        for name,expected in existing['subjects'].items():require(digest(ROOT/name)==expected,'original admission subject changed: '+name)
        immutable_json(raw/('admission-readback-'+uuid.uuid4().hex+'.json'),dict(schema_version=1,admission_sha256=digest(package/'admission.json'),
            original_subjects_rechecked=len(existing['subjects']),additional_verified_subjects=subjects,public_and_maintenance_actual_runner_launches_rechecked=True,
            scope='Complete existing admission reproduced, including original public/maintenance runner prelaunch manifests. Immutable original admission unchanged.'))
        print('Original Cargo admission reproduced with every subject and actual public/maintenance runner identity verified; immutable receipt unchanged');return
    immutable_json(package/'admission.json',value)
    print('Admitted cargo-generate on exactrc.6:480ordinary,18calibrations,3real faults,2native cells; whole next-twenty campaign remains incomplete')


if __name__=='__main__':main()
