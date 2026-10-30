import io
import tarfile
import unittest
import uuid

from next20_check import RAW
from next20_source_links import validate_links
from readiness_acquire_plop import extract_source


class SourceLinkTests(unittest.TestCase):
    def test_only_explicit_sibling_documentation_alias_is_omitted_and_never_followed(self):
        root=RAW/'control-tests'/('source-link-'+uuid.uuid4().hex);root.mkdir(parents=True)
        data=io.BytesIO()
        with tarfile.open(fileobj=data,mode='w:gz') as archive:
            info=tarfile.TarInfo('source/CLAUDE.md');body=b'original reviewed documentation\n';info.size=len(body);archive.addfile(info,io.BytesIO(body))
            info=tarfile.TarInfo('source/AGENTS.md');info.type=tarfile.SYMTYPE;info.linkname='CLAUDE.md';archive.addfile(info)
        options=dict(expanded_limit=1024,entry_limit=10,member_limit=1024)
        with self.assertRaises(RuntimeError):extract_source(data.getvalue(),root/'refused',**options)
        self.assertFalse((root/'refused').exists())
        extract_source(data.getvalue(),root/'approved',omitted_links={'AGENTS.md':'CLAUDE.md'},**options)
        self.assertEqual((root/'approved/CLAUDE.md').read_bytes(),body)
        self.assertFalse((root/'approved/AGENTS.md').exists())
        with self.assertRaises(RuntimeError):extract_source(data.getvalue(),root/'changed',omitted_links={'AGENTS.md':'OTHER.md'},**options)
        pin='a'*40
        self.assertEqual(validate_links(dict(schema_version=1,pin=pin,omitted_documentation_links={'AGENTS.md':'CLAUDE.md'}),pin),{'AGENTS.md':'CLAUDE.md'})
        for name,target in [('AGENTS.md','../outside.md'),('code.go','CLAUDE.md'),('AGENTS.md','code.go'),('AGENTS.md','AGENTS.md')]:
            with self.assertRaises(ValueError):validate_links(dict(schema_version=1,pin=pin,omitted_documentation_links={name:target}),pin)


if __name__=='__main__':unittest.main()
