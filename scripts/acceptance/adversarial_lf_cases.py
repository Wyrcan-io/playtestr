"""Reviewed synthetic lf inputs; this generates intentions, never green evidence."""
import json
import shutil
from adversarial_process import DOC


def main():
    directory = DOC / 'lf'
    fixture = directory / 'fixtures'
    fixture.mkdir(exist_ok=True)
    for name in ['00-empty', '01-destination', '02-nested']:
        (fixture / name).mkdir(exist_ok=True)
    files = {'alpha.txt': 'Alpha source retained.\n', 'bravo.txt': 'Bravo move source.\n',
             'charlie.txt': 'Charlie noncontiguous selection.\n',
             'occupied.txt': 'Different occupied destination.\n',
             'protected.txt': 'NEIGHBOR MUST REMAIN EXACT\n',
             '02-nested/notes.txt': 'Nested notes preserved.\n',
             '02-nested/plan.txt': 'NONINITIAL PLAN PREVIEW\nsecond exact line\n',
             'long.txt': ''.join('line %02d: bounded long preview café 雪\n' % i for i in range(40))}
    files.update({'zz-scroll-%02d.txt' % i: 'Scroll item %02d preserved.\n' % i for i in range(35)})
    for name, value in files.items():
        (fixture / name).write_bytes(value.encode('utf-8'))
    config = ('set promptfmt "LF %f"\nset statfmt ""\nset ratios 1:2\n'
              'set info\nset sortby natural\nset preview\nset nohidden\n'
              'set noincsearch\nset noincfilter\n')
    (fixture / 'lfrc').write_bytes(config.encode())
    files['lfrc'] = config
    empty_fixture=directory/'fixtures-empty'
    if not empty_fixture.exists():
        shutil.copytree(fixture,empty_fixture)
        (empty_fixture/'00-empty').rename(empty_fixture/'00-vacant')
    cases = []

    def text(value): return {'text': value}
    def key(value): return {'key': value}
    def expect(value): return {'expect': value}
    def search(name): return [text('/'), text(name), key('Enter'), expect('LF ' + name)]
    def command(value): return [text(':'), text(value), key('Enter')]
    def add(name, kind, purpose, steps, *, changed=None, absent=None):
        expected = dict(files)
        for path in absent or []:
            expected.pop(path, None)
        expected.update(changed or {})
        steps = [expect('LF 00-empty'), *steps]
        position = len(steps)
        cases.append(dict(name=name, kind=kind, purpose=purpose,
            command=['lf', '-single', '-config', 'lfrc', '.'],
            steps=[*steps, text('q'), {'exit': 0}], snapshot_after_step=position,
            snapshot_rows=[1, 20], timeout_ms=10000, expected_files=expected,
            absent_paths=absent or [], expected_exit=0,
            snapshot_exclusion='Rows 21–30: host metadata/status area and long-list lower rows; explicit selected header and exact state remain required'))

    add('normal-project', 'normal', 'Rename a real file to a spaced Unicode name without changing bytes',
        [*search('alpha.txt'), text('r'), expect('rename:'), key('CtrlA'), key('CtrlK'),
         text('renamed café.txt'), key('Enter'), expect('LF renamed'), expect('Alpha source retained.')],
        changed={'renamed café.txt': files['alpha.txt']}, absent=['alpha.txt'])
    add('normal-nested-search', 'normal', 'Navigate into a directory and preview a noninitial searched file',
        [*search('02-nested'), key('ArrowRight'), expect('LF notes.txt'),
         *search('plan.txt'), expect('NONINITIAL PLAN PREVIEW'), expect('second exact line')])
    for name, source, action in [('normal-copy', 'alpha.txt', 'y'), ('normal-move', 'bravo.txt', 'd')]:
        add(name, 'normal', 'Built-in clipboard ' + ('copy' if action == 'y' else 'move') + ' into an empty directory',
            [*search(source), text(action), *search('01-destination'), key('ArrowRight'),
             text('p'), expect('LF ' + source), expect(files[source].strip())],
            changed={'01-destination/' + source: files[source]}, absent=[source] if action == 'd' else [])
    add('normal-noncontiguous-copy', 'normal', 'Copy two nonadjacent selected files and preserve their neighbors',
        [*search('alpha.txt'), text(' '), *search('charlie.txt'), text(' '), text('y'),
         *search('01-destination'), key('ArrowRight'), text('p'),
         expect('LF alpha.txt'), expect('charlie.txt')],
        changed={'01-destination/alpha.txt': files['alpha.txt'], '01-destination/charlie.txt': files['charlie.txt']})
    add('normal-filter-sort-recover', 'normal', 'Filter file names, change ordering and restore the full directory view',
        [*command('setfilter .txt'), expect('LF alpha.txt'), {'expect_not': 'LF 00-empty'},
         {'snapshot_rows':dict(name='filter-intermediate.rows.json',first=1,last=20)},
         *command('set sortby size'), *command('bottom'), expect('LF long.txt'),
         *command('set sortby natural'), *command('setfilter'), *search('protected.txt'), expect('NEIGHBOR MUST REMAIN EXACT')])
    add('edge-empty-directory', 'edge', 'Enter an empty directory and recover to its nonempty parent',
        [key('ArrowRight'), text('r'), expect('rename: empty directory'), key('ArrowLeft'), expect('LF 00-vacant'), *search('protected.txt')])
    cases[-1]['fixture']='fixtures-empty'
    cases[-1]['steps'][0]=expect('LF 00-vacant')
    add('edge-no-match-recovery', 'edge', 'Reject an absent glob selection and recover with a genuine selected result',
        [*command('glob-select absent-never-*'), expect('pattern not found: absent-never-*'),
         *search('bravo.txt'), expect('Bravo move source.')])
    add('edge-cancel-rename', 'edge', 'Cancel rename after editing and preserve original and neighboring files',
        [*search('alpha.txt'), text('r'), expect('rename:'), key('CtrlA'), key('CtrlK'),
         text('abandoned-name.txt'), expect('abandoned-name.txt'), key('Escape'),
         {'expect_not': 'abandoned-name.txt'}], absent=['abandoned-name.txt'])
    add('edge-conflicting-rename', 'edge', 'Decline replacement of an existing different file',
        [*search('alpha.txt'), text('r'), key('CtrlA'), key('CtrlK'), text('occupied.txt'),
         key('Enter'), expect('replace'), text('n'), {'expect_not':'replace'}])
    add('edge-cancel-delete', 'edge', 'Decline destructive delete confirmation and preserve exact selected file',
        [*search('alpha.txt'), *command('delete'), expect("delete '"),
         text('n'), {'expect_not':"delete '"}])
    add('edge-resize-scroll', 'edge', 'Resize repeatedly, search an initially offscreen item, and return to Unicode preview',
        [{'resize': {'width': 80, 'height': 24}}, *search('zz-scroll-34.txt'), expect('Scroll item 34 preserved.'),
         {'resize': {'width': 120, 'height': 35}}, *search('long.txt'), expect('line 00: bounded long preview café 雪'),
         {'resize': {'width': 100, 'height': 30}}, *search('zz-scroll-33.txt'), expect('Scroll item 33 preserved.')])
    (directory / 'scenarios.json').write_text(json.dumps(dict(project='lf', fixture='fixtures',
        environment={'TERM': 'xterm-256color', 'USERNAME': 'synthetic-maintainer'}, cases=cases), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('Declared', len(cases), 'substantive lf cases; no pass or native qualification inferred')


if __name__ == '__main__':
    main()
