"""Declare bounded yo development cases from the two actual public exports."""
import base64
import copy
import json
import shutil

from next20_check import DOC
from readiness_evidence import immutable_json, sha256


def main():
    package = DOC/'yo'
    if (package/'scenarios.json').exists():
        raise ValueError('Preserve declared first development inputs')
    base = json.loads((package/'normal-project.json').read_text())
    cases = []

    def state(path, value):
        return {'state': {'path': path, 'kind': 'file', 'bytes_base64': base64.b64encode(value).decode()}}

    def route(label, language='TypeScript', readme=True, prefix=None, selection=None):
        steps = [{'expect': 'Project label'}]
        steps += prefix if prefix is not None else [{'text': label}, {'key': 'Enter'}]
        steps += [{'expect': 'Project language'}]
        steps += selection if selection is not None else ([{'key': 'ArrowDown'}] if language == 'JavaScript' else [])
        steps += [{'key': 'Enter'}, {'expect': 'Include README'}]
        if not readme:
            steps += [{'text': 'n'}]
        return steps + [{'key': 'Enter'}]

    def result(label, language='TypeScript', readme=True, old=None):
        files = {'output/project.json': (json.dumps(dict(label=label, language=language), ensure_ascii=False, indent=2)+'\n').encode()}
        if readme:
            files['output/README.md'] = ('# '+label+'\n\nLanguage: '+language+'\n').encode()
        files.update(old or {})
        steps = [state(path, value) for path, value in files.items()]
        if not readme and 'output/README.md' not in files:
            steps += [{'state': {'path': 'output/README.md', 'kind': 'absent'}}]
        steps += [state('sentinel.txt', (package/'fixture/sentinel.txt').read_bytes()),
                  {'state': {'path': 'output', 'kind': 'entries', 'entries': sorted(p[7:] for p in files)}}]
        return steps

    def add(cid, task, label=None, language='TypeScript', readme=True, prefix=None,
            selection=None, initial=None, extra=None, after=None, exit_code=0, width=120,
            combined=(), public=None, command=None):
        if public:
            spec = json.loads((package/public).read_text())
            name = public
        else:
            spec = copy.deepcopy(base)
            fixture = package/'fixtures'/cid.lower()
            shutil.copytree(package/'fixture', fixture)
            for path, value in (initial or {}).items():
                dest = fixture/path
                if value is None:
                    dest.mkdir(parents=True)
                else:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(value)
            spec['workspace']['fixture'] = fixture.relative_to(package).as_posix()
            spec['name'] = cid+' '+task
            spec['width'] = width
            if command:
                spec['command'] = command
            spec['steps'] = route(label, language, readme, prefix, selection) if label is not None else []
            spec['steps'] += extra or []
            spec['steps'] += ([{'expect': 'Scaffold complete'}] if exit_code == 0 else [])
            spec['steps'] += [{'exit': exit_code}]
            spec['steps'] += after if after is not None else result(label.strip(), language, readme)
            name = cid.lower()+'.json'
            immutable_json(package/name, spec)
        cases.append(dict(id=cid, kind='normal' if cid[0]=='N' else 'edge', task=task,
                          risk=task, combined_risks=list(combined), expected_exit=exit_code,
                          hosts=['linux', 'windows'], spec=name, spec_sha256=sha256(package/name),
                          initial_fixture=spec['workspace']['fixture']))

    add('N01', 'Generate TypeScript and README through public authoring', public='normal-project.json')
    add('N02', 'Generate JavaScript without README and compare approved screen', public='normal-javascript.json')
    add('N03', 'Trim surrounding input whitespace', '  Synthetic trimmed  ')
    add('N04', 'Preserve Unicode label in JSON and Markdown', 'Synthetic café 東京')
    add('N05', 'Generate JavaScript and README', 'Synthetic browser', language='JavaScript')
    same = (json.dumps(dict(label='Synthetic identical', language='TypeScript'), indent=2)+'\n').encode()
    add('N06', 'Preserve identical existing project and unrelated output', 'Synthetic identical', readme=False,
        initial={'output/project.json': same, 'output/keep.txt': b'Preserved output\n'},
        after=result('Synthetic identical', readme=False, old={'output/keep.txt': b'Preserved output\n'}))
    conflict = [{'expect': 'Overwrite'}, {'text': 'y'}, {'key': 'Enter'}]
    add('N07', 'Approve replacement of existing project', 'Synthetic overwrite', readme=False,
        initial={'output/project.json': b'original project\n'}, extra=conflict)
    add('N08', 'Decline replacement and preserve original project', 'Synthetic skipped', readme=False,
        initial={'output/project.json': b'original project\n'},
        extra=[{'expect': 'Overwrite'}, {'text': 'n'}, {'key': 'Enter'}],
        after=result('Synthetic skipped', readme=False, old={'output/project.json': b'original project\n'}))
    recovery = [{'key': 'Enter'}, {'expect': 'Project label is required'}, {'text': 'Synthetic recovered'}, {'key': 'Enter'}]
    add('E01', 'Recover from empty label validation', 'Synthetic recovered', prefix=recovery)
    add('E02', 'Recover from whitespace-only validation', 'Synthetic recovered',
        prefix=[{'text': '   '}, *recovery])
    absent = [{'state': {'path': 'output', 'kind': 'absent'}}, state('sentinel.txt', (package/'fixture/sentinel.txt').read_bytes())]
    add('E03', 'Cancel before any answer without writes', prefix=None,
        extra=[{'expect': 'Project label'}, {'key': 'CtrlC'}], exit_code=1, after=absent)
    add('E04', 'Cancel after label before language answer',
        extra=[{'expect': 'Project label'}, {'text': 'Synthetic cancelled'}, {'key': 'Enter'},
               {'expect': 'Project language'}, {'key': 'CtrlC'}], exit_code=1, after=absent)
    add('E05', 'Resize during Unicode input and decline README', 'Synthetic café 東京', readme=False, width=48,
        prefix=[{'text': 'Synthetic café 東京'}, {'resize': {'width': 72, 'height': 24}}, {'key': 'Enter'}],
        combined=('Unicode input', 'resize', 'declined README'))
    long = 'Synthetic '+('wrapped ' * 12).strip()
    add('E06', 'Edit long wrapped label before saving', long, width=48,
        prefix=[{'text': long+'X'}, {'key': 'Backspace'}, {'key': 'Enter'}],
        combined=('wrapped input', 'backspace', 'exact saved bytes'))
    add('E07', 'Save shell metacharacters as literal JSON data', 'Synthetic $(no-command); & < > " \\', readme=False,
        combined=('literal metacharacters', 'JSON escaping', 'no README'))
    add('E08', 'Wrap list selection upward to JavaScript', 'Synthetic reverse', language='JavaScript',
        selection=[{'key': 'ArrowUp'}], width=60, combined=('list wrap', 'narrow viewport', 'saved language'))
    add('E09', 'Abort conflicting write and preserve original bytes', 'Synthetic aborted', readme=False,
        initial={'output/project.json': b'original project\n'},
        extra=[{'expect': 'Overwrite'}, {'text': 'x'}, {'key': 'Enter'}, {'expect': 'Process aborted by user'}],
        exit_code=1, after=result('Synthetic aborted', readme=False, old={'output/project.json': b'original project\n'}))
    add('E10', 'Approve all conflicting files with one decision', 'Synthetic force',
        initial={'output/project.json': b'original project\n', 'output/README.md': b'original readme\n'},
        extra=[{'expect': 'Overwrite'}, {'text': 'a'}, {'key': 'Enter'}],
        combined=('multiple conflicts', 'approve all', 'two exact saved files'))
    add('E11', 'Reject a file occupying the output directory', 'Synthetic blocked', readme=False,
        initial={'output': b'blocked directory\n'}, extra=[{'expect': 'ENOTDIR'}], exit_code=1,
        after=[state('output', b'blocked directory\n'), state('sentinel.txt', (package/'fixture/sentinel.txt').read_bytes())])
    add('E12', 'Reject malformed local generator configuration', initial={'.yo-rc.json': b'{invalid json\n'},
        extra=[{'expect': 'Unexpected'}], exit_code=1,
        after=absent+[state('.yo-rc.json', b'{invalid json\n')])
    immutable_json(package/'scenarios.json', dict(schema_version=1, project='yo', development_revision=1,
        normal=8, edge=12, cases=cases,
        scope='Actual pinned yo and official locked Generator; unchanged trusted local fixture, no installations/services. First predictions retained even on failure.'))
    print('Declared twenty yo cases; first development has no qualification credit.')


if __name__ == '__main__':
    main()
