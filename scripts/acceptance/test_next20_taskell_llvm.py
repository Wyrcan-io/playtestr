import io
import base64
import hashlib
import os
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from next20_check import RAW
from next20_taskell_llvm import (PUBLIC_KEY,PUBLIC_KEY_GIT_BLOB,SIGNATURE_COMMENT,
    MACPORTS_LIBEDIT_DYLIB,MACPORTS_NCURSES_DYLIB,MACPORTS_LIBXML2_DYLIB,MACPORTS_ZLIB_DYLIB,
    MACPORTS_ICU_DYLIB,MACPORTS_LIBICONV_DYLIB,
    MACPORTS_LIBCHARSET_DYLIB,
    checked_version,decode_signify_signature,
    safe_extract,safe_extract_dylib_family,safe_extract_libffi,tool_inventory,
    verify_macos_link_closure,verify_tool_inventory,github_environment)


class TaskellLLVMTests(unittest.TestCase):
    def setUp(self):
        (RAW/'tmp').mkdir(parents=True,exist_ok=True)
        self.temp=tempfile.TemporaryDirectory(dir=RAW/'tmp')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)

    def test_github_environment_keeps_dyld_loader_path_command_scoped(self):
        values=github_environment(self.root/'llvm',self.root/'manifest.json')
        self.assertIn('TASKELL_LLVM_LIBRARY_PATH',values)
        self.assertNotIn('DYLD_LIBRARY_PATH',values)

    def test_pinned_archive_key_matches_signify_envelope_and_mismatch_rejects(self):
        public=base64.b64decode(PUBLIC_KEY,validate=True)
        content=('untrusted comment: signify public key\n'+PUBLIC_KEY+'\n').encode()
        self.assertEqual(hashlib.sha1(b'blob '+str(len(content)).encode()+b'\0'+content).hexdigest(),
                         PUBLIC_KEY_GIT_BLOB)
        self.assertEqual(public[:2],b'Ed')
        self.assertEqual(public[2:10].hex(),'7e3e18ab04272542')
        self.assertEqual(SIGNATURE_COMMENT,'untrusted comment: verify with macports-archives-2025.pub')
        signature=self.root/'archive.sig'
        signature.write_text(SIGNATURE_COMMENT+'\n'+base64.b64encode(b'Ed'+public[2:10]+b'0'*64).decode()+'\n',encoding='ascii')
        parsed,decoded=decode_signify_signature(signature)
        self.assertEqual(parsed,public)
        self.assertEqual(decoded[2:10],public[2:10])
        signature.write_text('untrusted comment: verify with another-key.pub\n'+
            base64.b64encode(decoded).decode()+'\n',encoding='ascii')
        with self.assertRaisesRegex(ValueError,'unexpected signify envelope'):
            decode_signify_signature(signature)

    def test_failed_native_version_probe_preserves_bounded_diagnostics(self):
        with patch('next20_taskell_llvm.subprocess.run',return_value=type('Result',(),{
                'returncode':-6,'stdout':'short stdout','stderr':'LLVM abort detail'})()):
            with self.assertRaisesRegex(RuntimeError,'LLVM abort detail'):
                checked_version('owned/opt',{})

    def test_macos_link_closure_follows_owned_transitive_dependencies_and_rejects_missing(self):
        prefix=self.root/'owned-llvm';(prefix/'bin').mkdir(parents=True);(prefix/'lib').mkdir()
        opt=prefix/'bin/opt';llc=prefix/'bin/llc';opt.write_bytes(b'opt');llc.write_bytes(b'llc')
        for name in ['libLLVM.dylib','libffi.8.dylib','libedit.0.dylib','libncurses.6.dylib',
                     'libxml2.16.dylib','libz.1.dylib','libicui18n.78.dylib',
                     'libicuuc.78.dylib','libicudata.78.dylib','libiconv.2.dylib','libcharset.1.dylib']:
            (prefix/'lib'/name).write_bytes(name.encode())
        def probe(args,**_):
            source=Path(args[2]).name
            references={
                'opt':['/opt/local/lib/libLLVM.dylib'],
                'llc':['/opt/local/lib/libLLVM.dylib'],
                'libLLVM.dylib':['/opt/local/lib/libffi.8.dylib','/opt/local/lib/libedit.0.dylib',
                                 '/opt/local/lib/libxml2.16.dylib'],
                'libedit.0.dylib':['/opt/local/lib/libncurses.6.dylib'],
                'libxml2.16.dylib':['/opt/local/lib/libz.1.dylib','/opt/local/lib/libicui18n.78.dylib',
                                     '/opt/local/lib/libiconv.2.dylib'],
                'libicui18n.78.dylib':['/opt/local/lib/libicuuc.78.dylib','/opt/local/lib/libicudata.78.dylib'],
                'libicuuc.78.dylib':['/opt/local/lib/libicudata.78.dylib'],
                'libffi.8.dylib':[],'libncurses.6.dylib':[],'libz.1.dylib':[],
                'libicudata.78.dylib':[],'libiconv.2.dylib':['/opt/local/lib/libcharset.1.dylib'],
                'libcharset.1.dylib':[],
            }[source]
            output=str(args[2])+'\n'+''.join('    '+path+' (compatibility version 1.0.0, current version 1.0.0)\n' for path in references)
            return subprocess.CompletedProcess(args,0,stdout=output,stderr='')
        with patch('next20_taskell_llvm.subprocess.run',side_effect=probe):
            rows=verify_macos_link_closure(prefix,[opt,llc])
        self.assertTrue(any(row['source']=='lib/libedit.0.dylib' and row['library']=='/opt/local/lib/libncurses.6.dylib' for row in rows))
        self.assertTrue(any(row['source']=='lib/libxml2.16.dylib' and row['library']=='/opt/local/lib/libz.1.dylib' for row in rows))
        self.assertTrue(any(row['source']=='lib/libicuuc.78.dylib' and row['library']=='/opt/local/lib/libicudata.78.dylib' for row in rows))
        (prefix/'lib/libiconv.2.dylib').unlink()
        with patch('next20_taskell_llvm.subprocess.run',side_effect=probe):
            with self.assertRaisesRegex(RuntimeError,'libiconv.2.dylib'):
                verify_macos_link_closure(prefix,[opt,llc])
        (prefix/'lib/libiconv.2.dylib').write_bytes(b'libiconv.2.dylib')
        (prefix/'lib/libncurses.6.dylib').unlink()
        with patch('next20_taskell_llvm.subprocess.run',side_effect=probe):
            with self.assertRaisesRegex(RuntimeError,'libncurses.6.dylib'):
                verify_macos_link_closure(prefix,[opt,llc])

    def archive(self,entries,name='fixture.tbz2'):
        package=self.root/name
        with tarfile.open(package,'w:bz2') as archive:
            for name,data in entries:
                member=tarfile.TarInfo(name)
                if data is None:
                    member.type=tarfile.DIRTYPE
                    member.size=0
                    archive.addfile(member)
                else:
                    member.size=len(data)
                    member.mode=0o755
                    archive.addfile(member,io.BytesIO(data))
        return package

    def test_bounded_extraction_and_tool_inventory_bind_bytes(self):
        package=self.archive([
            ('opt/local/libexec/llvm-12/bin/opt',b'opt-fixture'),
            ('opt/local/libexec/llvm-12/bin/llc',b'llc-fixture'),
        ])
        prefix=self.root/'llvm-12'
        expanded,opt,llc=safe_extract(package,prefix)
        self.assertEqual(expanded,len(b'opt-fixture')+len(b'llc-fixture'))
        self.assertEqual(opt.read_bytes(),b'opt-fixture')
        self.assertEqual(llc.read_bytes(),b'llc-fixture')
        inventory=tool_inventory(prefix)
        verify_tool_inventory(prefix,inventory)
        opt.write_bytes(b'tampered')
        with self.assertRaisesRegex(ValueError,'file changed'):
            verify_tool_inventory(prefix,inventory)

    def test_archive_path_escape_is_rejected_before_extraction(self):
        package=self.archive([('opt/local/libexec/llvm-12/../escape',b'no')])
        with self.assertRaisesRegex(ValueError,'Unsafe MacPorts LLVM archive member path'):
            safe_extract(package,self.root/'llvm-12')
        self.assertFalse((self.root/'escape').exists())

    def test_macports_layout_allows_only_bounded_ignored_versioned_bin_wrappers(self):
        package=self.root/'layout.tbz2'
        with tarfile.open(package,'w:bz2') as archive:
            for name in ('opt','opt/local','opt/local/bin','opt/local/libexec',
                         'opt/local/libexec/llvm-12','opt/local/libexec/llvm-12/bin'):
                member=tarfile.TarInfo(name);member.type=tarfile.DIRTYPE;archive.addfile(member)
            for name,data in [('opt/local/bin/opt-mp-12',b'#!/bin/sh\n'),
                              ('opt/local/bin/llc-mp-12',b'#!/bin/sh\n'),
                              ('opt/local/libexec/llvm-12/bin/opt',b'opt'),
                              ('opt/local/libexec/llvm-12/bin/llc',b'llc')]:
                member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o755
                archive.addfile(member,io.BytesIO(data))
        prefix=self.root/'selected-llvm'
        safe_extract(package,prefix)
        self.assertEqual((prefix/'bin/opt').read_bytes(),b'opt')
        self.assertEqual((prefix/'bin/llc').read_bytes(),b'llc')
        self.assertFalse((self.root/'opt').exists())

    def test_signed_xml_and_zlib_families_select_only_required_runtime_libraries(self):
        xml=self.archive([
            ('opt/local/etc',None),
            ('opt/local/etc/xml/.turd_libxml2',b''),
            ('opt/local/lib/libxml2.16.0.4.dylib',b'xml-runtime'),
            ('opt/local/lib/libxml2.16.dylib',b'xml-alias'),
            ('opt/local/include/libxml/parser.h',b'header'),
        ],'libxml2.tbz2')
        zlib=self.archive([
            ('opt/local/lib/libz.1.3.2.dylib',b'zlib-runtime'),
            ('opt/local/lib/libz.1.dylib',b'zlib-alias'),
            ('opt/local/lib/libz.a',b'static'),
        ],'zlib.tbz2')
        icu=self.archive([
            ('opt/local/sbin/gennorm2',b'build-time ICU utility'),
            ('opt/local/lib/libicui18n.78.3.dylib',b'icu-i18n'),
            ('opt/local/lib/libicui18n.78.dylib',b'i18n-alias'),
            ('opt/local/lib/libicuuc.78.3.dylib',b'icu-common'),
            ('opt/local/lib/libicuuc.78.dylib',b'common-alias'),
            ('opt/local/lib/libicudata.78.3.dylib',b'icu-data'),
            ('opt/local/lib/libicudata.78.dylib',b'data-alias'),
        ],'icu.tbz2')
        iconv=self.archive([
            ('opt/local/lib/libiconv.2.7.dylib',b'iconv-runtime'),
            ('opt/local/lib/libiconv.2.dylib',b'iconv-alias'),
            ('opt/local/lib/libcharset.1.0.0.dylib',b'charset-runtime'),
            ('opt/local/lib/libcharset.1.dylib',b'charset-alias'),
        ],'libiconv.tbz2')
        prefix=self.root/'runtime'
        xml_bytes,xml_files=safe_extract_dylib_family(xml,prefix,MACPORTS_LIBXML2_DYLIB,
            ['libxml2.16.dylib'],'libxml2')
        zlib_bytes,zlib_files=safe_extract_dylib_family(zlib,prefix,MACPORTS_ZLIB_DYLIB,
            ['libz.1.dylib'],'zlib')
        icu_bytes,icu_files=safe_extract_dylib_family(icu,prefix,MACPORTS_ICU_DYLIB,
            ['libicui18n.78.dylib','libicuuc.78.dylib','libicudata.78.dylib'],'ICU',
            cap=128*1024**2,archive_cap=512*1024**2)
        iconv_bytes,iconv_files=safe_extract_dylib_family(iconv,prefix,MACPORTS_LIBICONV_DYLIB,
            ['libiconv.2.dylib'],'libiconv')
        charset_bytes,charset_files=safe_extract_dylib_family(iconv,prefix,MACPORTS_LIBCHARSET_DYLIB,
            ['libcharset.1.dylib'],'libcharset')
        self.assertEqual(xml_bytes,len(b'xml-runtime')+len(b'xml-alias'))
        self.assertEqual(set(xml_files),{'libxml2.16.0.4.dylib','libxml2.16.dylib'})
        self.assertFalse((prefix/'lib/.turd_libxml2').exists())
        self.assertEqual(zlib_bytes,len(b'zlib-runtime')+len(b'zlib-alias'))
        self.assertEqual(set(zlib_files),{'libz.1.3.2.dylib','libz.1.dylib'})
        self.assertEqual(icu_bytes,len(b'icu-i18n')+len(b'i18n-alias')+len(b'icu-common')+
                         len(b'common-alias')+len(b'icu-data')+len(b'data-alias'))
        self.assertEqual(set(icu_files),{'libicui18n.78.3.dylib','libicui18n.78.dylib',
            'libicuuc.78.3.dylib','libicuuc.78.dylib','libicudata.78.3.dylib','libicudata.78.dylib'})
        self.assertFalse((prefix/'sbin/gennorm2').exists())
        self.assertEqual(iconv_bytes,len(b'iconv-runtime')+len(b'iconv-alias'))
        self.assertEqual(set(iconv_files),{'libiconv.2.7.dylib','libiconv.2.dylib'})
        self.assertEqual(charset_bytes,len(b'charset-runtime')+len(b'charset-alias'))
        self.assertEqual(set(charset_files),{'libcharset.1.0.0.dylib','libcharset.1.dylib'})
        self.assertFalse((prefix/'lib/libz.a').exists())

    def test_dylib_family_archive_and_selected_bytes_obey_separate_caps(self):
        oversized_archive=self.archive([
            ('opt/local/lib/libz.1.dylib',b'x'*101),
        ],'oversized-archive.tbz2')
        with self.assertRaisesRegex(ValueError,'archive expansion exceeded its byte cap'):
            safe_extract_dylib_family(oversized_archive,self.root/'archive-limit',MACPORTS_ZLIB_DYLIB,
                ['libz.1.dylib'],'zlib',cap=200,archive_cap=100)
        oversized_library=self.archive([
            ('opt/local/lib/libz.1.dylib',b'x'*11),
        ],'oversized-library.tbz2')
        with self.assertRaisesRegex(ValueError,'dylib expansion exceeded 10 bytes'):
            safe_extract_dylib_family(oversized_library,self.root/'library-limit',MACPORTS_ZLIB_DYLIB,
                ['libz.1.dylib'],'zlib',cap=10,archive_cap=100)

    def test_nonempty_macports_activation_marker_is_rejected(self):
        package=self.archive([
            ('opt/local/etc/xml/.turd_libxml2',b'not-empty'),
            ('opt/local/lib/libxml2.16.dylib',b'xml-runtime'),
        ],'nonempty-marker.tbz2')
        with self.assertRaisesRegex(ValueError,'Unexpected path in MacPorts libxml2 archive'):
            safe_extract_dylib_family(package,self.root/'nonempty-marker',MACPORTS_LIBXML2_DYLIB,
                ['libxml2.16.dylib'],'libxml2')

    @unittest.skipIf(os.name=='nt','native Windows symlink creation unavailable under this token')
    def test_signed_libffi_layout_selects_versioned_dylib_and_safe_alias(self):
        package=self.root/'libffi.tbz2'
        with tarfile.open(package,'w:bz2') as archive:
            for name,data in [('opt/local/lib/libffi.8.1.2.dylib',b'ffi-binary'),
                              ('opt/local/include/ffi.h',b'header')]:
                member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o755
                archive.addfile(member,io.BytesIO(data))
            alias=tarfile.TarInfo('opt/local/lib/libffi.8.dylib');alias.type=tarfile.SYMTYPE
            alias.linkname='libffi.8.1.2.dylib';archive.addfile(alias)
        prefix=self.root/'selected-llvm'
        expanded,selected=safe_extract_libffi(package,prefix)
        self.assertEqual(expanded,len(b'ffi-binary'))
        self.assertEqual(set(selected),{'libffi.8.dylib','libffi.8.1.2.dylib'})
        self.assertEqual((prefix/'lib/libffi.8.dylib').read_bytes(),b'ffi-binary')
        self.assertEqual((prefix/'lib/libffi.8.dylib').resolve(),(prefix/'lib/libffi.8.1.2.dylib').resolve())

    def test_libffi_extraction_refuses_escaping_link(self):
        package=self.root/'libffi-escape.tbz2'
        with tarfile.open(package,'w:bz2') as archive:
            alias=tarfile.TarInfo('opt/local/lib/libffi.8.dylib');alias.type=tarfile.SYMTYPE
            alias.linkname='../../outside.dylib';archive.addfile(alias)
        with self.assertRaisesRegex(ValueError,'Escaping symlink'):
            safe_extract_libffi(package,self.root/'selected-llvm')

    def test_libedit_documentation_symlink_escape_is_rejected_without_extraction(self):
        package=self.root/'libedit-man-escape.tbz2'
        with tarfile.open(package,'w:bz2') as archive:
            alias=tarfile.TarInfo('opt/local/share/man/man3/el_tok_end.3.gz')
            alias.type=tarfile.SYMTYPE;alias.linkname='../../../../../../outside'
            archive.addfile(alias)
            library=tarfile.TarInfo('opt/local/lib/libedit.0.dylib');library.size=4
            archive.addfile(library,io.BytesIO(b'edit'))
        with self.assertRaisesRegex(ValueError,'Escaping link'):
            safe_extract_dylib_family(package,self.root/'untrusted-docs',MACPORTS_LIBEDIT_DYLIB,
                                      ['libedit.0.dylib'],'libedit')
        self.assertFalse((self.root/'untrusted-docs').exists())

    @unittest.skipIf(os.name=='nt','native Windows symlink creation unavailable under this token')
    def test_signed_libedit_and_ncurses_dylib_families_extract_only_runtime_links(self):
        edit=self.root/'libedit.tbz2'
        with tarfile.open(edit,'w:bz2') as archive:
            member=tarfile.TarInfo('opt/local/lib/libedit.0.1.dylib');member.size=len(b'edit-binary');member.mode=0o755
            archive.addfile(member,io.BytesIO(b'edit-binary'))
            alias=tarfile.TarInfo('opt/local/lib/libedit.0.dylib');alias.type=tarfile.SYMTYPE
            alias.linkname='libedit.0.1.dylib';archive.addfile(alias)
            ignored=tarfile.TarInfo('opt/local/bin/editline');ignored.size=3
            archive.addfile(ignored,io.BytesIO(b'bin'))
            man_alias=tarfile.TarInfo('opt/local/share/man/man3/el_tok_end.3.gz')
            man_alias.type=tarfile.SYMTYPE;man_alias.linkname='el_gets.3.gz';archive.addfile(man_alias)
        ncurses=self.root/'ncurses.tbz2'
        with tarfile.open(ncurses,'w:bz2') as archive:
            for name,data in [('opt/local/lib/libncurses.6.6.dylib',b'ncurses'),
                              ('opt/local/lib/libform.6.6.dylib',b'form'),
                              ('opt/local/lib/libcurses.6.6.dylib',b'curses')]:
                member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o755
                archive.addfile(member,io.BytesIO(data))
            static=tarfile.TarInfo('opt/local/lib/libncurses++w.a')
            static_bytes=b'x'*(4*1024**2+1);static.size=len(static_bytes)
            archive.addfile(static,io.BytesIO(static_bytes))
            static_alias=tarfile.TarInfo('opt/local/lib/libncurses++w.a.link')
            static_alias.type=tarfile.SYMTYPE;static_alias.linkname='libncurses++w.a'
            archive.addfile(static_alias)
            for name,target in [('opt/local/lib/libncurses.6.dylib','libncurses.6.6.dylib'),
                                ('opt/local/lib/libform.6.dylib','libform.6.6.dylib'),
                                ('opt/local/lib/libcurses.dylib','libcurses.6.6.dylib')]:
                alias=tarfile.TarInfo(name);alias.type=tarfile.SYMTYPE;alias.linkname=target;archive.addfile(alias)
        prefix=self.root/'runtime'
        expanded,files=safe_extract_dylib_family(edit,prefix,MACPORTS_LIBEDIT_DYLIB,['libedit.0.dylib'],'libedit')
        self.assertEqual(expanded,len(b'edit-binary'))
        self.assertEqual(set(files),{'libedit.0.dylib','libedit.0.1.dylib'})
        expanded,files=safe_extract_dylib_family(ncurses,prefix,MACPORTS_NCURSES_DYLIB,
            ['libncurses.6.dylib'],'ncurses',cap=32*1024**2)
        self.assertEqual(expanded,len(b'ncurses')+len(b'form')+len(b'curses'))
        self.assertEqual(set(files),{'libncurses.6.6.dylib','libncurses.6.dylib','libform.6.6.dylib','libform.6.dylib',
                                     'libcurses.6.6.dylib','libcurses.dylib'})
        self.assertFalse((prefix/'lib/libncurses++w.a').exists())
        self.assertFalse((prefix/'lib/libncurses++w.a.link').exists())


if __name__=='__main__':
    unittest.main()
