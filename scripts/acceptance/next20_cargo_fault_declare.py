"""Select three real upstream source faults after the positive twenty-case freeze."""
import difflib
import json

from next20_check import RAW,DOC
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'cargo-generate';target=RAW/'active/cargo-generate';freeze=package/'development-test-freeze.json'
    frozen=json.loads(freeze.read_text());review=json.loads((package/'source-review.json').read_text())
    for name,digest in frozen['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('frozen contract changed before fault selection')
    for name,digest in review['reviewed_inputs'].items():
        if sha256(target/'src'/name)!=digest:raise ValueError('upstream source already changed before fault selection')
    faults=[
        dict(id='F01',path='src/interactive.rs',before='prompt: "Project Name".into(),',after='prompt: "Workspace Name".into(),',
            category='assertion_timeout',meaning='Regression in the real initial prompt prevents the frozen public interaction.'),
        dict(id='F02',path='src/main.rs',before='    Ok(())\n}\n\nfn resolve_args()',after='    std::process::exit(7)\n}\n\nfn resolve_args()',
            category='unexpected_exit',meaning='Ordinary completed generation incorrectly returns exit7 after the successful terminal summary.'),
        dict(id='F03',path='src/template.rs',before='fs::write(new_filename.as_path(), new_contents).with_context',
            after='fs::write(new_filename.as_path(), new_contents.replace(\'=\', ":")).with_context',
            category='state_assertion_failure',meaning='The actual rendered-file writer corrupts equal-sign delimiters without changing saved byte lengths, terminal summary or successful exit. Same-invocation exact saved bytes must reject it.')]
    for fault in faults:
        path=target/'src'/fault['path'];original=path.read_bytes();before=fault['before'].encode();after=fault['after'].encode()
        if original.count(before)!=1:raise ValueError('source fault anchor is not exact and unique: '+fault['id'])
        mutated=original.replace(before,after)
        patch=''.join(difflib.unified_diff(original.decode().splitlines(True),mutated.decode().splitlines(True),
            fromfile='a/'+fault['path'],tofile='b/'+fault['path']))
        destination=package/'fault-patches'/(fault['id']+'.patch');destination.parent.mkdir(exist_ok=True)
        with destination.open('x',encoding='utf-8',newline='\n') as stream:stream.write(patch)
        import hashlib
        fault.update(original_source_sha256=sha256(path),mutated_source_sha256=hashlib.sha256(mutated).hexdigest(),
            patch_sha256=sha256(destination),spec='normal-project.json',spec_sha256=sha256(package/'normal-project.json'))
    immutable_json(package/'fault-declaration.json',dict(schema_version=1,project='cargo-generate',
        selected_after_freeze_sha256=sha256(freeze),faults=faults,
        exposure='Known first-use/contract repairs and general runner native-status repair were exposed before the positive freeze. These concrete source edits were selected only after all20 rc.6 Windows development cases passed and105 contract inputs froze. No mutation compiled/applied yet; no independent-human or untouched-source claim.',
        build_policy='Real locked offline native Rust rebuild per source variant, with reviewed unchanged dependencies. Keep original build/runtime receipts intact. Capture actual mutated executable/source identity separately; unchanged test bytes for baseline, mutated and restored phases.',
        expected_local_probes=9,mandatory_final_native_calibrations=18,project_credits=0))
    print('Selected three exact real upstream source faults after freeze; no mutation applied or executed.')


if __name__=='__main__':main()
