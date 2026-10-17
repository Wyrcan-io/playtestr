"""Preserve explicit reviewed corrections to initially authored expectations."""
import base64
import json
from readiness_evidence import immutable_json, sha256
from readiness_rubygems_cases import PACKAGE


def main():
    receipt=PACKAGE/'contract-revision-2.json'
    if receipt.exists():raise RuntimeError('preserve revision')
    changes=[]
    for filename,step,value in [
        ('normal-set-path.json',2,b'---\r\nBUNDLE_PATH: vendor/reviewed\r\n'),
        ('normal-unset-path.json',2,b'---\r\nBUNDLE_WITHOUT: development\r\n'),
        ('normal-lock.json',3,b'GEM\n  specs:\n\nPLATFORMS\n  ruby\n\nDEPENDENCIES\n\nCHECKSUMS\n\nBUNDLED WITH\n  4.1.0.beta2\n')]:
        p=PACKAGE/filename;before=sha256(p);spec=json.loads(p.read_text())
        spec['steps'][step-1]['state']['bytes_base64']=base64.b64encode(value).decode()
        p.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8',newline='\n')
        changes.append(dict(spec=filename,before=before,after=sha256(p),reason='public unsaved selected review; YAML plain strings/CRLF or current beta lock CHECKSUMS and version indentation'))
    p=PACKAGE/'edge-build-missing.json';before=sha256(p);spec=json.loads(p.read_text())
    assert spec['command'][3]=='bundle';spec['command'][3]='gem'
    p.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8',newline='\n')
    changes.append(dict(spec=p.name,before=before,after=sha256(p),reason='RubyGems gem build command; bundle has no build subcommand; original failed attempt retained'))
    p=PACKAGE/'edge-wrong-type.json';before=sha256(p);spec=json.loads(p.read_text())
    spec['width']=160;spec['height']=100;spec['steps'][0]['expect']='rb_file_s_stat'
    p.write_text(json.dumps(spec,indent=2)+'\n',encoding='utf-8',newline='\n')
    changes.append(dict(spec=p.name,before=before,after=sha256(p),reason='actual pinned beta emits filesystem backtrace plus friendly-error TypeError; larger viewport retains original stat diagnosis; no clean upstream error UX claimed'))
    spec=json.loads((PACKAGE/'normal-extension.json').read_text())
    files={s['state']['path']:base64.b64decode(s['state']['bytes_base64']) for s in spec['steps'] if s.get('state',{}).get('kind')=='file'}
    assert files['native_atlas/ext/native_atlas/native_atlas.c']==b'#include "native_atlas.h"\n\nVALUE rb_mNativeAtlas;\n\nRUBY_FUNC_EXPORTED void\nInit_native_atlas(void)\n{\n  rb_mNativeAtlas = rb_define_module("NativeAtlas");\n}\n'
    assert files['native_atlas/ext/native_atlas/native_atlas.h']==b'#ifndef NATIVE_ATLAS_H\n#define NATIVE_ATLAS_H 1\n\n#include "ruby.h"\n\n#endif /* NATIVE_ATLAS_H */\n'
    assert files['native_atlas/lib/native_atlas/version.rb']==b'# frozen_string_literal: true\n\nmodule NativeAtlas\n  VERSION = "0.1.0"\nend\n'
    assert b'create_makefile("native_atlas/native_atlas")' in files['native_atlas/ext/native_atlas/extconf.rb']
    assert b'require "native_atlas/native_atlas"' in files['native_atlas/lib/native_atlas.rb']
    immutable_json(receipt,dict(changes=changes,extension_independent_literal_review=True,
        qualification='authored correction only; ordinary replay required; Windows resize unresolved'))
    print('Reviewed explicit expectation corrections and exact C/header/version payloads.')


if __name__=='__main__':main()
