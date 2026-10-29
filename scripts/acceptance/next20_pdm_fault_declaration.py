"""Select three concrete PDM source faults after the reviewed development freeze."""
import json

from next20_check import DOC, RAW
from readiness_evidence import immutable_json, sha256


def main():
    package=DOC/'pdm';freeze=package/'development-test-freeze.json'
    frozen=json.loads(freeze.read_text())
    for name,digest in frozen['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('reviewed input changed after freeze')
    faults=[dict(id='F01',path='src/pdm/cli/commands/init.py',
        before='"Project version"',after='"Workspace version"',category='assertion_timeout',
        meaning='Wrong ready prompt prevents the approved input sequence.'),
        dict(id='F02',path='src/pdm/__main__.py',before='    main()\n',
        after='    main()\n    raise SystemExit(7)\n',category='unexpected_exit',
        meaning='Completed successful initialization incorrectly exits seven.'),
        dict(id='F03',path='src/pdm/cli/templates/__init__.py',
        before='fp.write(tomlkit.dumps(content))',
        after='fp.write(tomlkit.dumps(content).replace(\'name = "synthetic-notes"\', \'name = "wrong-notes"\', 1))',
        category='state_assertion_failure',
        meaning='The real TOML writer saves the wrong project name after normal terminal completion and zero exit.')]
    for fault in faults:
        path=RAW/'active/pdm/src'/fault['path']
        if path.read_bytes().count(fault['before'].encode())!=1:raise ValueError('mutation anchor not unique')
    immutable_json(package/'fault-declaration.json',dict(schema_version=1,project='pdm',
        selected_after_freeze_sha256=sha256(freeze),primary_spec='normal-minimal-runtime-v2.json',
        required_calibrations_per_host=9,additional_terminal_only_calibrations_per_host=0,
        exposure='Reviewed source and development failures known; concrete edits selected after the frozen 20/0 development run. Historical screen gap remains open; no admission.',
        faults=faults))
    print('Declared three unique source faults after the freeze; none applied by this command.')


if __name__=='__main__':main()
