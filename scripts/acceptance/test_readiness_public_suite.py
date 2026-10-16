import tempfile
from pathlib import Path
import unittest

from readiness_evidence import RAW, ROOT
from readiness_public_suite import SelectedCampaign


class PublicSelectionTests(unittest.TestCase):
    def setUp(self):
        RAW.mkdir(parents=True,exist_ok=True)
        self.folder=tempfile.TemporaryDirectory(dir=RAW)
        self.addCleanup(self.folder.cleanup)
        self.root=Path(self.folder.name)
        self.selection=self.root/'selected.txt'

    def test_selection_directory_does_not_omit_contracts(self):
        fixture=self.root/'fixture';fixture.mkdir()
        (fixture/'seed').write_bytes(b'reviewed')
        spec=self.root/'case.json'
        spec.write_text('{"version":3,"command":["must-not-launch"],"workspace":{"fixture":"fixture"},"steps":[{"expect":"ready"}]}')
        self.selection.write_text('Selected 1 specs:\n'+spec.relative_to(ROOT).as_posix()+'\n')
        campaign=SelectedCampaign(self.selection)
        identity=campaign.identity('selection-control',['public-runner','test',self.root])
        import json
        stored=json.loads((campaign.raw/identity['manifest']).read_text())
        self.assertIn(spec.relative_to(ROOT).as_posix(),stored['files'])
        self.assertIn((fixture/'seed').relative_to(ROOT).as_posix(),stored['files'])

    def test_bad_and_duplicate_selection_rejects_before_launch(self):
        for content in ['', 'Selected 1 specs:\nmissing.json\n', 'Selected 2 specs:\na.json\na.json\n']:
            self.selection.write_text(content)
            with self.assertRaises((ValueError,FileNotFoundError)):
                SelectedCampaign(self.selection).identity('selection-control',['must-not-launch'])

    def test_selected_owned_executable_mutation_changes_identity(self):
        import json
        binary=self.root/'owned-target.exe';binary.write_bytes(b'reviewed target binary')
        spec=self.root/'case.json'
        spec.write_text(json.dumps(dict(version=3,command=[str(binary)],steps=[dict(exit=0)])))
        self.selection.write_text('Selected 1 specs:\n'+spec.relative_to(ROOT).as_posix()+'\n')
        campaign=SelectedCampaign(self.selection)
        before=campaign.identity('selection-control',['public-runner','test',self.root])
        binary.write_bytes(b'changed target binary')
        after=campaign.identity('selection-control',['public-runner','test',self.root])
        self.assertNotEqual(before['sha256'],after['sha256'])


if __name__=='__main__':unittest.main()
