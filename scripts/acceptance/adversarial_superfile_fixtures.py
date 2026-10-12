"""Tiny reviewed synthetic state and explicit offline superfile configuration."""
from pathlib import Path
import re
from adversarial_process import ROOT,DOC


def main():
    package=DOC/'superfile'
    fixture=package/'fixtures'
    fixture.mkdir(exist_ok=True)
    files={'alpha.txt':'ALPHA PREVIEW TOKEN\nOriginal alpha bytes.\n',
           'bravo.txt':'BRAVO MOVE TOKEN\nOriginal bravo bytes.\n',
           'charlie.txt':'CHARLIE MULTISELECT TOKEN\nUnselected neighboring bytes.\n',
           'occupied.txt':'OCCUPIED DISTINCT TOKEN\nNever silently replace.\n',
           'protected.txt':'PROTECTED NEIGHBOR TOKEN\nMust remain exact.\n',
           'nested/notes.txt':'NESTED NOTES TOKEN\n',
           'nested/plan.txt':'NONINITIAL PLAN TOKEN\nSecond exact line.\n',
           'long.txt':''.join('line %02d: long preview café 雪\n'%i for i in range(40))}
    files.update({'scroll-%02d.txt'%i:'SCROLL ITEM %02d TOKEN\n'%i for i in range(35)})
    for name,value in files.items():
        relative=name if name.startswith('nested/') else 'source/'+name
        target=fixture/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(value.encode('utf-8'))
        # Remove only the exact earlier exploratory root file, never an
        # unrecognized edit or any directory. No contract was exported yet.
        old=fixture/name
        if relative!=name and old.exists():
            if old.is_symlink() or not old.is_file() or old.read_bytes()!=value.encode('utf-8'):
                raise RuntimeError('Unknown earlier synthetic fixture state')
            old.unlink()
    for name in ['empty','destination']:
        (fixture/name).mkdir(exist_ok=True)
    source=ROOT/'.cache/ten-new-project-apps/superfile/source'
    configuration=(source/'src/superfile_config/config.toml').read_text(encoding='utf-8')
    for old,new in [('auto_check_update = true','auto_check_update = false'),
                    ('show_image_preview = true','show_image_preview = false'),
                    ('show_panel_footer_info = true','show_panel_footer_info = false'),
                    ('nerdfont = true','nerdfont = false'),('sidebar_width = 20','sidebar_width = 0'),
                    ('sidebar_sections = ["home", "pinned", "disks"]','sidebar_sections = []')]:
        configuration,count=re.subn('^'+re.escape(old)+'$',lambda match:new,configuration,flags=re.MULTILINE)
        if count!=1:
            raise RuntimeError('Pinned configuration anchor is not unique: '+old)
    config=fixture/'.configuration/config.toml'
    config.parent.mkdir(exist_ok=True)
    config.write_bytes(configuration.encode('utf-8'))
    print('Synthetic fixture and explicitly offline configuration prepared')


if __name__=='__main__':
    main()
