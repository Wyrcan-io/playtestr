"""Declare meaningful cases and tiny reviewed synthetic Cookiecutter templates."""
import json
from pathlib import Path
from adversarial_process import DOC

def text(value): return {'text':value}
def expect(value): return {'expect':value}
def enter(): return {'key':'Enter'}
def reply(anchor,value): return [expect(anchor),text(value),enter()]

def main():
    directory=DOC/'cookiecutter'
    directory.mkdir(parents=True,exist_ok=True)
    fixtures=directory/'fixtures'
    fixtures.mkdir(exist_ok=True)
    variables=dict(project_name='Terminal Sample',
                   project_slug='{{ cookiecutter.project_name.lower().replace(" ", "-") }}',
                   license=['MIT','BSD-3-Clause'],include_docs=True,
                   metadata={'owner':'maintainer'},_new_lines='\n')
    def template(relative,values,files,hooks=None):
        root=fixtures/relative
        root.mkdir(parents=True,exist_ok=True)
        (root/'cookiecutter.json').write_text(json.dumps(values,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        for name,value in files.items():
            file=root/'{{cookiecutter.project_slug}}'/name
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_text(value,encoding='utf-8',newline='\n')
        if hooks:
            hook=root/'hooks/post_gen_project.py'
            hook.parent.mkdir(exist_ok=True)
            hook.write_text(hooks,encoding='utf-8',newline='\n')
    files={'README.md':'# {{cookiecutter.project_name}}\nLicense={{cookiecutter.license}}\nDocs={{cookiecutter.include_docs}}\n',
           'data/config.json':'{"owner":"{{cookiecutter.metadata.owner}}","slug":"{{cookiecutter.project_slug}}"}\n'}
    template('basic',variables,files)
    structured=dict(variables,_copy_without_render=['literal.txt'])
    template('structured',structured,dict(files,
        **{'literal.txt':'{{ cookiecutter.project_name }} remains literal\n',
           'payload.bin':'\x00\x01SYNTHETIC-BINARY\n'}))
    template('nested/templates/component',dict(project_name='Component',project_slug='component',_new_lines='\n'),
             {'src/component.txt':'component={{cookiecutter.project_name}}\n'})
    template('hooked',dict(project_name='Hooked',project_slug='hooked',_new_lines='\n'),
             {'README.md':'# {{cookiecutter.project_name}}\n'},
             "from pathlib import Path\nPath('hook-result.txt').write_text('hook executed\\n',encoding='utf-8',newline='\\n')\nprint('Reviewed local generation hook completed')\n")
    (fixtures/'existing').mkdir(exist_ok=True)
    (fixtures/'existing/README.md').write_text('original protected bytes\n',newline='\n')
    (fixtures/'existing/neighbor.txt').write_text('neighbor preserved\n',newline='\n')
    (fixtures/'sentinel.txt').write_text('outside output preserved\n',newline='\n')
    base=['cookiecutter','--default-config','--accept-hooks','no','basic']
    def flow(name='Investor Fixture',slug='investor-fixture',license='2',docs='no',metadata='{"owner":"reviewer"}'):
        return (reply('project_name',name)+reply('project_slug',slug)+
                reply('Select license',license)+reply('include_docs',docs)+reply('metadata',metadata))
    def state(slug,name='Investor Fixture',license='BSD-3-Clause',docs=False,owner='reviewer'):
        return {slug+'/README.md':f'# {name}\nLicense={license}\nDocs={docs}\n',
                slug+'/data/config.json':json.dumps({'owner':owner,'slug':slug},ensure_ascii=False,separators=(',',':'))+'\n',
                'sentinel.txt':'outside output preserved\n'}
    cases=[]
    def add(name,kind,risk,command,steps,oracle,exit_code=0,absent=None):
        cases.append(dict(name=name,kind=kind,purpose=risk,command=command,steps=steps+[{'exit':exit_code}],
                          expected_files=oracle,absent_paths=absent or [],
                          qualified_hosts=['linux','windows'],timeout_ms=8000,run_timeout_ms=120000,
                          output_cap=2000000,expected_exit=exit_code))
    add('normal-project','normal','Generate a nondefault two-file project with dependent slug, chosen license and exact state',base,
        flow(),state('investor-fixture'))
    add('normal-structured-data','normal','Structured metadata and Unicode render while declared literal text and binary payload are copied exactly',
        ['cookiecutter','--default-config','--accept-hooks','no','structured'],
        flow('Café Project','unicode-project','1','yes','{"owner":"café"}'),
        dict(state('unicode-project','Café Project','MIT',True,'café'),
            **{'unicode-project/literal.txt':'{{ cookiecutter.project_name }} remains literal\n',
               'unicode-project/payload.bin':'\x00\x01SYNTHETIC-BINARY\n'}))
    add('normal-nested-template','normal','Select a template below an aggregate directory; generated nested source is exact',
        ['cookiecutter','--default-config','--accept-hooks','no','--directory','templates/component','nested'],
        reply('project_name','Nested Component')+[expect('project_slug'),
            {'resize':{'width':80,'height':24}},text('nested-component'),enter()],
        {'nested-component/src/component.txt':'component=Nested Component\n','sentinel.txt':'outside output preserved\n'})
    add('normal-reviewed-hook','normal','Explicitly approve a reviewed local hook and verify its separate saved effect',
        ['cookiecutter','--default-config','--accept-hooks','ask','hooked'],
        reply('Do you want to execute hooks?','y')+reply('project_name','Hooked Fixture')+reply('project_slug','hook-result')+
        [expect('Reviewed local generation hook completed')],
        {'hook-result/README.md':'# Hooked Fixture\n','hook-result/hook-result.txt':'hook executed\n'})
    add('normal-preserve-existing','normal','Overwrite directory with skip-existing policy preserves protected bytes and adds missing generated file',
        ['cookiecutter','--default-config','--accept-hooks','no','--overwrite-if-exists','--skip-if-file-exists','basic'],
        flow(slug='existing'),{'existing/README.md':'original protected bytes\n',
        'existing/neighbor.txt':'neighbor preserved\n','existing/data/config.json':'{"owner":"reviewer","slug":"existing"}\n'})
    add('edge-choice-recovery','edge','Out-of-range choice is visibly rejected before valid correction',base,
        reply('project_name','Investor Fixture')+reply('project_slug','investor-fixture')+
        reply('Select license','99')+[expect('Please select one of the available options')]+[text('2'),enter()]+
        reply('include_docs','no')+reply('metadata','{"owner":"reviewer"}'),state('investor-fixture'))
    add('edge-boolean-recovery','edge','Invalid Boolean cannot silently become true; correction reaches exact output',base,
        reply('project_name','Investor Fixture')+reply('project_slug','investor-fixture')+
        reply('Select license','2')+reply('include_docs','maybe')+[expect('Please enter Y or N')]+
        [text('no'),enter()]+reply('metadata','{"owner":"reviewer"}'),state('investor-fixture'))
    add('edge-json-recovery','edge','Array is rejected for dict metadata and valid object then persists',base,
        reply('project_name','Investor Fixture')+reply('project_slug','investor-fixture')+
        reply('Select license','2')+reply('include_docs','no')+reply('metadata','[]')+
        [expect('Requires JSON dict.')]+[text('{"owner":"reviewer"}'),enter()],state('investor-fixture'))
    add('edge-cancel-after-edit','edge','Cancel after entering name; no output directory or protected file mutation',base,
        reply('project_name','Unsaved Fixture')+[expect('project_slug'),{'key':'CtrlC'},expect('Aborted!')],
        {'existing/README.md':'original protected bytes\n','sentinel.txt':'outside output preserved\n'},1,
        ['unsaved-fixture','investor-fixture'])
    add('edge-existing-rejected','edge','Existing destination is rejected at exact nonzero exit and all original bytes survive',base,
        flow(slug='existing')+[expect('already exists')],
        {'existing/README.md':'original protected bytes\n','existing/neighbor.txt':'neighbor preserved\n'},1,
        ['existing/data/config.json'])
    config=dict(project='cookiecutter',fixture='fixtures',cases=cases,
        environment={'PYTHONIOENCODING':'utf-8','PYTHONUTF8':'1','TERM':'xterm-256color'},
        scope_exclusions=['remote template acquisition','unreviewed hooks','real credentials','every template extension'],
        oracle='Independent exact UTF-8 files and absence checks in the current managed workspace before teardown')
    (directory/'scenarios.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    scope='# Cookiecutter scope declared before recording\n\nPinned source and local synthetic templates; Linux/Windows qualification planned. No host credit until executed.\n\n| Case | Kind | User risk |\n| --- | --- | --- |\n'
    scope+=''.join(f"| {c['name']} | {c['kind']} | {c['purpose']} |\n" for c in cases)
    scope+='\nAll cases use fresh fixture/home/temp, 8-second steps, 120-second whole runs, two MiB target output, four MiB harness capture. Expected files are constructed independently in this recipe, not derived from target-generated output.\n'
    (directory/'scope.md').write_text(scope,encoding='utf-8')
    print('Declared five normal and five distinct edge cases')

if __name__=='__main__':
    main()
