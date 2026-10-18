"""Author twenty declared real Hygen workflows through public recorder controls."""
import argparse
import asyncio
import base64
import hashlib
import json
from pathlib import PurePosixPath
import uuid

from adversarial_process import execute
from readiness_evidence import Campaign, RAW, ROOT, immutable_json, sha256
from readiness_hygen_first_use import environment, runner
from readiness_new_control_matrix import read_json as load


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def text(value):
    return '/text ' + json.dumps(value, ensure_ascii=True)


def template(to, body, **attributes):
    header = {'to': to, **attributes}
    return ('---\n' + ''.join(k + ': ' + json.dumps(v, ensure_ascii=False) + '\n'
                             for k, v in header.items()) + '---\n').encode() + body


def entry_sets(files):
    directories = {'.'}
    for name in files:
        parent = PurePosixPath(name).parent
        while str(parent) != '.':
            directories.add(parent.as_posix())
            parent = parent.parent
    nodes = set(files) | (directories - {'.'})
    return {directory: sorted(PurePosixPath(name).name for name in nodes
                             if PurePosixPath(name).parent.as_posix() == directory)
            for directory in sorted(directories)}


def rows():
    default_question = dict(type='input', name='message', message='Message for file?')

    def row(identity, title, templates, outputs, *, initial=None, question=None,
            answer='reviewed', controls=None, after=None, args=None, missing=()):
        question = question or default_question
        seed = {'.hygen.js': b'module.exports = {};\n', 'sentinel.bin': b'preserve\x00existing\r\n',
                '_templates/work/new/prompt.js': ('module.exports = ' + json.dumps([question], ensure_ascii=True) + ';\n').encode(),
                **{'_templates/work/new/' + name: value for name, value in templates.items()}, **(initial or {})}
        expected = {**seed, **outputs}
        actions = ['/expect ' + question['message'], '/snapshot-rows prompt.rows.json 1 1']
        actions += controls if controls is not None else [text(answer), '/expect ' + answer, '/key Enter']
        actions += after or ['/expect added: ' + next(iter(outputs))]
        actions += ['/exit 0']
        return dict(id=identity, title=title, kind='normal' if identity.startswith('N') else 'edge',
                    args=args or [], files=seed, expected=expected, missing=list(missing), actions=actions,
                    entry_sets=entry_sets(expected))

    simple = template('generated/result.txt', b'Hello, <%= message %>!\n')
    existing = {'generated/result.txt': b'keep existing\r\n'}
    question_select = dict(type='select', name='flavor', message='Choose flavor', choices=['plain', 'spiced', 'sweet'])
    question_multi = dict(type='multiselect', name='features', message='Choose features', choices=['cache', 'tests', 'docs'])
    inject = lambda body, **attrs: template('document.txt', body, inject=True, eof_last=False, **attrs)
    return [
        row('N01', 'render prompted input into a new file', {'output.ejs.t': simple},
            {'generated/result.txt': b'Hello, reviewed!\n'}),
        row('N02', 'confirm selected existing-file overwrite', {'output.ejs.t': simple},
            {'generated/result.txt': b'Hello, reviewed!\n'}, initial=existing,
            after=['/expect Overwrite?', text('y'), '/expect added: generated/result.txt']),
        row('N03', 'decline selected existing-file overwrite', {'output.ejs.t': simple}, {}, initial=existing,
            after=['/expect Overwrite?', text('n'), '/expect skipped: generated/result.txt']),
        row('N04', 'select a nondefault template value',
            {'output.ejs.t': template('generated/flavor.txt', b'Flavor: <%= flavor %>\n')},
            {'generated/flavor.txt': b'Flavor: spiced\n'}, question=question_select,
            controls=['/key ArrowDown', '/key Enter']),
        row('N05', 'select two nonadjacent feature values',
            {'output.ejs.t': template('generated/features.txt', b'Features: <%= features.join(",") %>\n')},
            {'generated/features.txt': b'Features: cache,docs\n'}, question=question_multi,
            controls=[text(' '), '/key ArrowDown', '/key ArrowDown', text(' '), '/key Enter']),
        row('N06', 'inject a prompted line after an existing marker',
            {'output.ejs.t': inject(b'<%= message %>\n', after='^# marker$')},
            {'document.txt': b'header\n# marker\nreviewed\nfooter\n'},
            initial={'document.txt': b'header\n# marker\nfooter\n'}, after=['/expect inject: document.txt']),
        row('N07', 'append a prompted line preserving the old prefix',
            {'output.ejs.t': inject(b'<%= message %>\n', append=True)},
            {'document.txt': b'original prefix\nreviewed\n'}, initial={'document.txt': b'original prefix\n'},
            after=['/expect inject: document.txt']),
        row('N08', 'generate related files from one prompt',
            {'01-first.ejs.t': template('generated/first.txt', b'First <%= message %>\n'),
             '02-second.ejs.t': template('generated/second.txt', b'Second <%= message %>\n')},
            {'generated/first.txt': b'First reviewed\n', 'generated/second.txt': b'Second reviewed\n'},
            after=['/expect added: generated/first.txt', '/expect added: generated/second.txt']),
        row('E01', 'accept the reviewed prompt default', {'output.ejs.t': simple},
            {'generated/result.txt': b'Hello, fallback!\n'}, question={**default_question, 'initial': 'fallback'},
            controls=['/key Enter']),
        row('E02', 'generate a spaced Unicode path and contents',
            {'output.ejs.t': template('generated/<%= message %>.txt', b'Name: <%= message %>\n')},
            {'generated/caf\u00e9 \u96ea.txt': 'Name: caf\u00e9 \u96ea\n'.encode()}, answer='caf\u00e9 \u96ea'),
        row('E03', 'retain existing CRLF when injecting',
            {'output.ejs.t': inject(b'<%= message %>\n', after='^# marker$')},
            {'document.txt': b'header\r\n# marker\r\nreviewed\r\nfooter\r\n'},
            initial={'document.txt': b'header\r\n# marker\r\nfooter\r\n'}, after=['/expect inject: document.txt']),
        row('E04', 'skip an existing destination with unless_exists',
            {'output.ejs.t': template('generated/result.txt', b'<%= message %>\n', unless_exists=True)}, {},
            initial=existing, after=['/expect skipped: generated/result.txt']),
        row('E05', 'force replacement of the selected existing destination',
            {'output.ejs.t': template('generated/result.txt', b'<%= message %>\n', force=True)},
            {'generated/result.txt': b'reviewed\n'}, initial=existing,
            after=['/expect FORCED: generated/result.txt']),
        row('E06', 'dry-run without creating a destination', {'output.ejs.t': simple}, {},
            args=['--dry'], missing=['generated', 'generated/result.txt'], after=['/expect added: generated/result.txt']),
        row('E07', 'skip a template using its rendered condition',
            {'output.ejs.t': template('generated/result.txt', b'<%= message %>\n', skip_if="<%= message === 'skip' %>")}, {},
            answer='skip', missing=['generated', 'generated/result.txt'], after=['/expect Loaded templates:']),
        row('E08', 'render a literal NUL without truncating generated bytes',
            {'output.ejs.t': template('generated/result.bin', b'prefix\x00<%= message %>\n')},
            {'generated/result.bin': b'prefix\x00reviewed\n'}),
        row('E09', 'copy a local from-file body without extra interpolation',
            {'output.ejs.t': template('generated/from.bin', b'ignored body\n', **{'from': 'shared/body.txt'})},
            {'generated/from.bin': b'literal <%= message %>\x00\r\n'},
            initial={'_templates/shared/body.txt': b'literal <%= message %>\x00\r\n'}),
        row('E10', 'prevent duplicate injection using skip_if',
            {'output.ejs.t': inject(b'new <%= message %>\n', after='^header$', skip_if='already-present')}, {},
            initial={'document.txt': b'header\nalready-present\nfooter\n'}, after=['/expect inject: document.txt']),
        row('E11', 'create an exactly empty file', {'output.ejs.t': template('generated/empty.txt', b'')},
            {'generated/empty.txt': b''}),
        row('E12', 'resize the active prompt with supported Unicode input', {'output.ejs.t': simple},
            {'generated/result.txt': 'Hello, caf\u00e9 \u96ea e\u0301AB!\n'.encode()},
            controls=[text('caf\u00e9 \u96ea e\u0301'), '/expect caf\u00e9 \u96ea e\u0301',
                      '/resize 70 20', text('A'), '/expect caf\u00e9 \u96ea e\u0301A', '/resize 100 28',
                      text('B'), '/expect caf\u00e9 \u96ea e\u0301AB', '/key Enter']),
    ]


def serialise(row):
    return {key: {n: value.hex() for n, value in data.items()} if key in {'files', 'expected'} else data
            for key, data in row.items()}


def plan_hash(row):
    return hashlib.sha256(json.dumps(serialise(row), sort_keys=True, ensure_ascii=True).encode()).hexdigest()


async def author(row):
    binary, frozen, cell = runner()
    root = RAW / 'hygen/authoring' / row['id'] / uuid.uuid4().hex
    fixture = root / 'fixture'
    fixture.mkdir(parents=True)
    for name, value in row['files'].items():
        path = fixture / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    immutable_json(root / 'declared-plan.json', serialise(row))
    controls = [*row['actions'], *['/file ' + name for name in sorted(row['expected'])],
                *['/missing ' + name for name in row['missing']],
                *['/entries ' + name for name in sorted(row['entry_sets'])], '/review', '/replay', '/save']
    spec = root / 'spec.json'
    captured = await execute([binary, 'record', '--output', spec.relative_to(ROOT), '--fixture', 'fixture',
        '--temporary-home', '--temporary-temp', '--width', '100', '--height', '28', '--timeout-ms', '10000',
        '--run-timeout-ms', '120000', '--env', 'TERM=xterm-256color', '--', 'hygen', 'work', 'new', *row['args']],
        'hygen', row['id'] + '-public-author-review-replay', input='\n'.join(controls) + '\n',
        env=environment(), timeout=180, campaign=Campaign())
    contract = load(spec)
    states = [s['state'] for s in contract['steps'] if 'state' in s]
    files = {s['path']: base64.b64decode(s['bytes_base64']) for s in states if s['kind'] == 'file'}
    require(files == row['expected'], row['id'] + ' independent generated/preserved byte oracle rejects export')
    require({s['path'] for s in states if s['kind'] == 'absent'} == set(row['missing']), 'absence oracle differs')
    entries = {s['path']: s['entries'] for s in states if s['kind'] == 'entries'}
    require({n: sorted(v) for n, v in entries.items()} == row['entry_sets']
            and all(len(v) == len(set(v)) for v in entries.values()), 'complete entry-set oracle differs')
    report = root / 'ordinary-result.json'
    ordinary = await execute([binary, 'test', '--report', report.relative_to(ROOT), '--artifacts-dir',
        (root / 'evidence').relative_to(ROOT), spec.relative_to(ROOT)], 'hygen', row['id'] + '-ordinary-authored-contract',
        env=environment(), timeout=130, campaign=Campaign())
    outcome = load(report)
    result = outcome['results'][0]
    require(outcome['runner_version'] == frozen['version'] and result['status'] == 'passed'
            and result['cleanup']['confirmed_exited'] and result['workspace']['cleaned'], 'ordinary result/cleanup differs')
    for step in result['steps']:
        if 'state' in step:
            require(step['state']['invocation_id'] == result['invocation_id']
                    and step['state']['workspace_id'] == result['workspace']['id'], 'cross-execution state')
    immutable_json(RAW / 'hygen/approved' / (row['id'] + '.json'), dict(case=row['id'], plan_sha256=plan_hash(row),
                   spec=spec.relative_to(ROOT).as_posix(), spec_sha256=sha256(spec), capture_attempt=captured['id'],
                   ordinary_attempt=ordinary['id'], report_sha256=sha256(report), runner_sha256=cell['binary_sha256'],
                   provisional_archive_sha256=cell['archive_sha256'], independently_checked=True))
    print(row['id'], 'authored, independently checked and ordinary replay passed', flush=True)


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', action='append')
    args = parser.parse_args()
    declared = rows()
    if len(declared) != 20 or sum(r['kind'] == 'normal' for r in declared) != 8:
        raise RuntimeError('twenty meaningful scenarios with eight normal required')
    selected = [r for r in declared if not args.case or r['id'] in args.case]
    if args.case and {r['id'] for r in selected} != set(args.case):
        raise RuntimeError('unknown scenario')
    batch = RAW / 'hygen/authoring-batches' / uuid.uuid4().hex
    immutable_json(batch / 'declared.json', dict(rows=[serialise(r) for r in selected], executed=False))
    failures = []
    for row in selected:
        approved = RAW / 'hygen/approved' / (row['id'] + '.json')
        if approved.exists():
            if load(approved)['plan_sha256'] != plan_hash(row):
                raise RuntimeError('approved case plan changed; explicit revision required')
            print(row['id'], 'already approved; not repeated', flush=True)
            continue
        try:
            await author(row)
        except Exception as error:
            failures.append(dict(case=row['id'], type=type(error).__name__, message=str(error)))
            print(row['id'], 'failed; first evidence retained:', error, flush=True)
    immutable_json(batch / 'outcomes.json', dict(selected=len(selected), failures=failures))
    if failures:
        raise RuntimeError('Some authored workflows failed; inspect original packets before revision')


if __name__ == '__main__':
    asyncio.run(main())
