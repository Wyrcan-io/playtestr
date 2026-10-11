"""Synthetic reviewed Copier templates and independently specified outcomes."""
import json
from adversarial_process import DOC

def main():
    package=DOC/'copier'
    root=package/'fixtures'
    if (package/'scenarios.json').exists():
        raise RuntimeError('Refuse replacing declared or approved scenarios')
    def write(relative,text):
        path=root/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(text,encoding='utf-8',newline='\n')
    common='_envops:\n  keep_trailing_newline: true\n'
    answers='{{ _copier_answers | to_nice_yaml }}'
    basic=common+'''project_name:
  type: str
  default: Example
  help: Project name
project_slug:
  type: str
  default: "{{ project_name | lower | replace(' ', '-') }}"
  help: Project slug
license:
  type: str
  choices: [MIT, Apache-2.0]
  default: MIT
  help: License
'''
    write('templates/basic/copier.yml',basic)
    write('templates/basic/.copier-answers.yml.jinja',answers)
    write('templates/basic/README.md.jinja','# {{ project_name }}\nslug={{ project_slug }}\nlicense={{ license }}\n')
    write('templates/basic/data/config.json.jinja','{"project_name": {{ project_name | tojson }}, "project_slug": {{ project_slug | tojson }}, "license": {{ license | tojson }}}\n')
    write('templates/conditional/copier.yml',common+'''include_docs:
  type: bool
  default: false
  help: Include documentation
module_name:
  type: str
  default: core
  when: "{{ include_docs }}"
  help: Documentation module
''')
    write('templates/conditional/config.json.jinja','{"include_docs": {{ include_docs | tojson }}, "module_name": {{ module_name | tojson }}}\n')
    write('templates/conditional/{% if include_docs %}docs.txt{% endif %}.jinja','module={{ module_name }}\n')
    write('templates/features/copier.yml',common+'''features:
  type: str
  multiselect: true
  choices: [lint, tests, docs]
  default: []
  help: Optional features
''')
    write('templates/features/features.json.jinja','{{ features | tojson }}\n')
    write('templates/hooked/copier.yml',common+'''component:
  type: str
  default: core
  help: Component name
_tasks:
  - [python, hooks/write-marker.py]
''')
    write('templates/hooked/component.txt.jinja','component={{ component }}\n')
    write('templates/hooked/hooks/write-marker.py',"from pathlib import Path\nPath('task-marker.txt').write_bytes(b'reviewed task executed\\n')\n")
    write('templates/validated/copier.yml',common+'''slug:
  type: str
  default: valid
  help: Lowercase slug
  validator: "{% if slug != slug | lower %}Slug must be lowercase{% endif %}"
''')
    write('templates/validated/slug.txt.jinja','slug={{ slug }}\n')
    write('templates/integer/copier.yml',common+'''workers:
  type: int
  default: 1
  help: Worker count
''')
    write('templates/integer/workers.txt.jinja','workers={{ workers }}\n')
    write('templates/json/copier.yml',common+'''metadata:
  type: json
  default: {}
  multiline: false
  help: Project metadata
''')
    write('templates/json/metadata.json.jinja','{{ metadata | tojson }}\n')
    write('neighbor.txt','protected neighboring state\n')
    write('existing/README.md','protected local README\n')
    write('existing/.copier-answers.yml','_src_path: templates/basic\nproject_name: Existing\nproject_slug: existing\nlicense: MIT\n')
    cases=[]
    def expect(value): return {'expect':value}
    def key(value): return {'key':value}
    def text(value): return {'text':value}
    def replace(value): return [key('CtrlA'),key('CtrlK'),text(value),key('Enter')]
    def case(name,kind,purpose,command,steps,files=None,absent=None):
        files=dict(files or {})
        files['neighbor.txt']='protected neighboring state\n'
        cases.append(dict(name=name,kind=kind,purpose=purpose,command=command,
            steps=steps,expected_files=files,absent_paths=absent or [],timeout_ms=10000))
    basic_steps=[expect('Project name'),*replace('Atlas'),expect('Project slug'),key('Enter'),
        expect('License'),key('ArrowDown'),key('Enter'),{'exit':0}]
    case('normal-project','normal','Dependent project files and nondefault keyboard-selected license',
        ['copier','copy','templates/basic','project'],basic_steps,
        {'project/README.md':'# Atlas\nslug=atlas\nlicense=Apache-2.0\n',
         'project/data/config.json':'{"project_name": "Atlas", "project_slug": "atlas", "license": "Apache-2.0"}\n'})
    case('normal-conditional','normal','Conditional question and actual optional file creation',
        ['copier','copy','templates/conditional','project'],
        [expect('Include documentation'),text('y'),expect('Documentation module'),*replace('docs'),{'exit':0}],
        {'project/config.json':'{"include_docs": true, "module_name": "docs"}\n','project/docs.txt':'module=docs\n'})
    case('normal-features','normal','Checkbox navigation and ordered multi-feature saved state',
        ['copier','copy','templates/features','project'],
        [expect('Optional features'),text(' '),key('ArrowDown'),key('ArrowDown'),text(' '),key('Enter'),{'exit':0}],
        {'project/features.json':'["lint", "docs"]\n'})
    case('normal-recopy-protected','normal','Recopy from saved answers while preserving a local README',
        ['copier','recopy','--skip-answered','--ask','project_name','existing'],
        [expect('Project name'),*replace('Recopied'),expect('Overwrite'),text('n'),key('Enter'),{'exit':0}],
        {'existing/README.md':'protected local README\n',
         'existing/data/config.json':'{"project_name": "Recopied", "project_slug": "existing", "license": "MIT"}\n'})
    case('normal-reviewed-task','normal','Explicit trust for one reviewed local marker-writing task',
        ['copier','copy','--trust','templates/hooked','project'],
        [expect('Component name'),*replace('engine'),{'exit':0}],
        {'project/component.txt':'component=engine\n','project/task-marker.txt':'reviewed task executed\n'})
    case('edge-validator-recovery','edge','Actual slug validator rejection and correction before generation',
        ['copier','copy','templates/validated','project'],
        [expect('Lowercase slug'),*replace('INVALID'),expect('Slug must be lowercase'),*replace('corrected'),{'exit':0}],
        {'project/slug.txt':'slug=corrected\n'})
    case('edge-integer-recovery','edge','Invalid integer input rejected and corrected to an exact numeric state',
        ['copier','copy','templates/integer','project'],
        [expect('Worker count'),*replace('abc'),expect('Invalid input'),*replace('7'),{'exit':0}],
        {'project/workers.txt':'workers=7\n'})
    case('edge-json-recovery','edge','Malformed JSON rejected then corrected without losing the prompt',
        ['copier','copy','templates/json','project'],
        [expect('Project metadata'),*replace('{'),expect('Invalid input'),*replace('{"team": "core", "active": true}'),{'exit':0}],
        {'project/metadata.json':'{"active": true, "team": "core"}\n'})
    case('edge-cancel-after-edit','edge','Cancellation after editing leaves no generated project',
        ['copier','copy','templates/basic','project'],
        [expect('Project name'),key('CtrlA'),key('CtrlK'),text('Abandoned'),key('CtrlC'),
         expect('Execution stopped by user'),{'exit':1}],absent=['project'])
    case('edge-unsafe-task-refused','edge','Reviewed task template is refused without explicit trust',
        ['copier','copy','templates/hooked','project'],
        [expect('unsafe'),{'exit':4}],absent=['project','project/task-marker.txt'])
    (package/'scenarios.json').write_text(json.dumps(dict(project='copier',fixture='fixtures',
        phase='Declared initial contracts; Git update case added after synthetic repository preparation',
        cases=cases),indent=2)+'\n',encoding='utf-8')
    print('Declared ten initial Copier workflows; substantive Git update preparation remains mandatory')

if __name__=='__main__': main()
