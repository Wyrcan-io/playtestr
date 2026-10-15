"""Bounded diagnostic of the actual Ranger first-key failure; no qualification credit."""
import hashlib
import json
import os
from pathlib import Path

from adversarial_process import DOC, RAW, ROOT, run
from adversarial_setup_python import source_identity


def startup_variants(steps):
    """Build explicit weak/strong controls from either reviewed recipe."""
    header = {'expect': '/fixture/file 000.txt'}
    readiness = [{'expect': 'RANGER BULK 000 TOKEN'}, {'expect': '1/200  Top'}]
    if not steps or steps[0] != header:
        raise RuntimeError('Diagnostic requires reviewed first navigation contract')
    suffix = steps[1:]
    if suffix[:2] == readiness:
        suffix = suffix[2:]
    if suffix[:3] != [{'text': 'G'}, {'expect': '/fixture/file 199.txt'},
                      {'expect': 'RANGER BULK 199 TOKEN'}]:
        raise RuntimeError('Diagnostic requires exact reviewed navigation suffix')
    weak = [header, *suffix]
    return {'header-only': weak, 'preview-and-status': [header, *readiness, *suffix]}


def main():
    import curses
    app = ROOT / '.cache/ten-new-project-apps/ranger'
    identity = json.loads((app / 'runtime.json').read_text(encoding='utf-8'))
    source = Path(identity['source_path'])
    source.resolve(strict=True).relative_to(app.resolve(strict=True))
    ui = source / 'ranger/gui/ui.py'
    original = ui.read_bytes()
    stat = ui.stat()
    pristine = source_identity(source)
    if pristine != identity['execution_identity']:
        raise RuntimeError('Diagnostic requires pristine owned Ranger source')
    evidence = RAW / 'ranger/startup-input-probe'
    evidence.mkdir(parents=True, exist_ok=False)
    log = app / 'tmp/startup-input-events.txt'
    log.parent.mkdir(exist_ok=True)
    anchor = '        key = self.win.getch()\n'
    value = original.decode('utf-8')
    if value.count(anchor) != 1:
        raise RuntimeError('Diagnostic getch anchor must be unique')
    # Only synthetic numeric key codes and public UI flags are captured. No
    # ambient environment, arbitrary screen bytes or user directories are read.
    probe = (anchor +
        '        if __import__("os").path.getsize(' + repr(str(log)) + ') < 8192:\n' +
        '            with open(' + repr(str(log)) + ', "a") as probe:\n' +
        '                probe.write("%s %s %s\\n" % (key, self.console.visible, self.fm.input_blocked))\n')
    binary = ROOT / 'bin/playtestr'
    env = dict(os.environ, PATH=identity['path'] + os.pathsep + os.environ['PATH'])
    public = DOC / 'ranger/edge-large-directory.json'
    contract = json.loads(public.read_text(encoding='utf-8'))
    # Store diagnostic specs beside the reviewed fixture/snapshots so path
    # semantics remain ordinary. They are not declared campaign scenarios.
    variants = startup_variants(contract['steps'])
    records = []
    try:
        ui.write_bytes(value.replace(anchor, probe).encode('utf-8'))
        os.utime(ui, ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000))
        instrumented = source_identity(source)
        for variant, steps in variants.items():
            spec = public.with_name('diagnostic-startup-' + variant + '.json')
            if spec.exists():
                raise RuntimeError('Refuse overwriting a diagnostic input')
            document = dict(contract, steps=steps)
            spec.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            for index in range(20):
                log.write_bytes(b'')
                report = evidence / (variant + '-' + str(index) + '.json')
                error = None
                try:
                    run([binary, 'test', '--report', report.relative_to(ROOT), '--artifacts-dir',
                                  report.with_suffix('').relative_to(ROOT), spec], 'ranger',
                                 'diagnostic-startup-' + variant + '-' + str(index), env=env, timeout=30)
                except RuntimeError as failure:
                    error = str(failure)
                if not report.is_file():
                    raise RuntimeError('Diagnostic lacks actual runner report')
                actual = json.loads(report.read_text(encoding='utf-8'))
                outcome = actual['results'][0]
                if not outcome['cleanup']['confirmed_exited']:
                    raise RuntimeError('Diagnostic did not confirm target termination')
                key_log = log.read_text(encoding='utf-8')
                if len(key_log.encode('utf-8')) > 9000:
                    raise RuntimeError('Diagnostic input-log bound exceeded')
                records.append(dict(variant=variant, index=index, report=report.relative_to(ROOT).as_posix(),
                    status=outcome['status'], failure=outcome.get('failure'), numeric_input_log=key_log,
                    harness_error=error, report_sha256=hashlib.sha256(report.read_bytes()).hexdigest()))
                print(variant, index, outcome['status'], flush=True)
        result = dict(records=records, pristine_source_sha256=pristine['digest'],
                      instrumented_source_sha256=instrumented['digest'],
                      diagnostic_steps=variants,
                      native_curses_codes={name: getattr(curses, name, None)
                                           for name in ['KEY_RESIZE', 'KEY_MOUSE', 'KEY_HOME']},
                      qualification_credit=0,
                      scope='Instrumented target diagnosis; file logging changes scheduling. No pristine application qualification.')
    finally:
        ui.write_bytes(original)
        os.utime(ui, ns=(stat.st_atime_ns, stat.st_mtime_ns))
        if source_identity(source) != pristine:
            raise RuntimeError('Diagnostic source restoration failed')
    result['exact_source_restored'] = True
    (evidence / 'summary.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
