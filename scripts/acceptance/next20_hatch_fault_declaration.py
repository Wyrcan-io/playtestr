"""Select three real Hatch edits after the complete positive contract freeze."""
import json

from next20_check import DOC,RAW
from readiness_evidence import immutable_json,sha256


def main():
    package=DOC/'hatch';freeze=package/'development-test-freeze.json';frozen=json.loads(freeze.read_text())
    for name,digest in frozen['inputs'].items():
        if sha256(package/name)!=digest:raise ValueError('frozen reviewed contract changed')
    faults=[
        dict(id='F01',path='src/hatch/cli/new/__init__.py',
            before='app.prompt("Description", default="")',after='app.prompt("Metadata detail", default="")',
            category='assertion_timeout',meaning='Wrong interactive ready prompt prevents the unchanged approved description workflow.'),
        dict(id='F02',path='src/hatch/cli/new/__init__.py',
            before='app.display_success("Updated: pyproject.toml")\n        return',
            after='app.display_success("Updated: pyproject.toml")\n        raise SystemExit(7)',
            category='unexpected_exit',meaning='A completed metadata update prints the normal success checkpoint but incorrectly exits seven.'),
        dict(id='F03',path='src/hatch/project/core.py',
            before='build_system_config["requires"] = ["hatchling"]',after='build_system_config["requires"] = ["setuptools"]',
            category='state_assertion_failure',meaning='The actual metadata writer saves the wrong build requirement after normal terminal completion, zero exit and matching snapshot.')
    ]
    for fault in faults:
        source=RAW/'active/hatch/src'/fault['path']
        if source.read_bytes().count(fault['before'].encode())!=1:raise ValueError('mutation anchor not unique in actual pinned source')
    immutable_json(package/'fault-declaration.json',dict(schema_version=1,project='hatch',
        selected_after_freeze_sha256=sha256(freeze),primary_spec='n01.json',required_calibrations_per_host=9,
        additional_terminal_only_calibrations_per_host=0,
        exposure='Source and potential fault sites already reviewed; initial authoring/development failures retained. Concrete edits declared after the positive20-case/86-input freeze. No untouched-source, unfamiliar-human or native-transfer claim.',faults=faults))
    print('Selected three unique real source edits after86-input freeze; no mutation applied by declaration.')


if __name__=='__main__':main()
