#!/usr/bin/env python3
"""Validate captured evidence and publish the completed engineering ledger."""
import hashlib
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs/validation/ten-project-user-pass'
RAW = ROOT / 'artifacts/ten-project-user-pass'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

# Scope judgments are explicit operator decisions, never inferred coverage.
DETAILS = {
 'gum': ('Selector, confirmation, Unicode input, resize and length enforcement',
         'Shell pipelines, passwords, styling, every Gum subcommand and mouse input',
         'A real choose-output prefix mutation is rejected. A separate gamma selection demonstrates reviewed baseline maintenance. Exact decline exit 1 is declared.',
         'No generalized core defect discovered by these Gum scenarios.'),
 'fzf': ('Search across 1,004 synthetic entries, cancellation and resized Unicode selection',
         'External preview commands, personal shell integration, filesystem crawling and mouse interaction',
         'Synthetic alpha/beta/gamma/café entries plus 1,000 filler entries; exact cancellation exit 130. Actual emitted-result prefix regression fails unchanged tests.',
         'A mutation-build helper initially decoded UTF-8 through Windows legacy encoding; retained as operator error and corrected.'),
 'micro': ('Unicode save, discard without saving, regex search and resized cursor location',
           'Plugins, system clipboard, arbitrary languages, remote files and editor-wide compatibility',
           'Exact original and saved notes bytes are checked before workspace teardown. A source mutation suppresses the real Saved notification; another corrupts real saved bytes despite success UI.',
           'Recorder rerecord printed a stale working directory. Fixed generally in 06af0c0 with a failing-before/passing-after regression. Manual-edit encoding mistakes were also rejected.'),
 'lazygit': ('Stage a file, cancel discard, create and independently inspect a local commit',
             'Remotes, credentials, hooks, signing, conflicts and every Git operation',
             'A trusted synthetic launcher creates a local repository with fixed identity/date, no hooks/signing/remotes. Index blob, canceled file, commit subject, committed blob and clean status are independently checked. Real add-to-reset mutation fails.',
             'Portable explicit PATH setup replaces an operator-machine binary path; synthetic Git fixture modes and LF bytes are explicit. A real Git regression proved identical commits from 0644/LF and 0755/CRLF inputs after the fix. Only changed synthetic commit hashes were deliberately reviewed in selected baselines, then all scenarios were requalified. Intentional unstaging is reviewed separately from defect recovery.'),
 'gdu': ('Computed sizes, folder navigation, cancel deletion, help and resize',
         'Real disk/home scans, successful deletion, symlink traversal and every display mode',
         'Only 1/2/3 KiB synthetic files. Canceled deletion preserves exact child bytes. Actual size-formatting regression is rejected; explicit --si output provides intended expectation maintenance.',
         'Random fresh workspace name made full-viewport snapshots unstable. Implemented explicit reviewed physical-row snapshots in c8274d5; meaningful result rows stay asserted and full failure screens remain available.'),
 'visidata': ('Find noninitial row, cancel cell edit, save Unicode TSV and inspect exact exported bytes',
              'Network loaders, arbitrary formats, plugins, styles and spreadsheet-wide correctness',
              'Native isolated Python environment; --nothing plus explicit empty --motd-url avoids MOTD network access. Actual search regression and real saved-header corruption are rejected.',
              'Preserve empty argv values, and add general CtrlA/CtrlK keys (4a1f41d). Mounted Windows virtualenv startup took 11.85s; native /var/tmp runtime fixes setup. WSL erased a /tmp runtime; ownership-tracked /var/tmp replaces it.'),
 'litecli': ('Insert and select Unicode SQLite data, reject table deletion, invalid SQL and resized recovery',
             'Remote databases, completion compatibility, styles and every SQL construct',
             'Exact SQLite rows are independently queried. Actual result truncation and database corruption with normal-looking output are rejected. Public psql formatting is an intentional maintenance example.',
             'Upstream contains a Windows-invalid tracked filename: acquire actual unmodified source on Linux. Use explicit target-supported PROMPT_TOOLKIT_NO_CPR=1; terminal queries remain a documented product boundary. Exclude timing rows through reviewed row snapshots.'),
 'harlequin': ('Real SQLite result grid, cancel save, recover from actual SQL error, save Unicode SQL',
               'AI/agent features, non-SQLite adapters, remote files, clipboard and database-wide correctness',
               'Assert full SQL and actual result caption/grid. An early mechanically passing recovery test only showed typed SQL and an error modal; visually rejected, retained and excluded from acceptance. Corrected new-buffer/error-dismissal flow really executes 314. Saved SQL bytes are independently checked.',
               'General CtrlJ byte 0x0a differs from Enter 0x0d (53561e6). Cold startup needs an explicit bounded 15s application deadline. Timing toasts/completion are outside reviewed result rows; path prompts need unique Saving to evidence. Wrong save-path and UTF-8 edit attempts remain recorded.'),
 'npkill': ('Filter actual directories, cancel filter and inspect selection, delete only filtered beta',
            'User home scans, delete-all, explorer launch, age/update checks and real dependency trees',
            'Only synthetic node_modules directories and an outside sentinel. Independently verify all survivor bytes and deleted directory absence. Actual filtering regression and fake-success dry-run deletion are rejected.',
            'Recorder correctly rejects stale existing beta and trimmed trailing-space anchors. Require initial positive presence and actual disappearance; disable update/age through supported public flags.'),
 'create-vite': ('Full React TypeScript wizard, cancel nonempty destination, recover invalid Vue package name',
                 'Network/custom starters, immediate install/dev server, credentials and generated-app runtime correctness',
                 'Public --interactive --no-immediate --no-eslint, with no upstream test-only bypass. Independently compare full 18-file React and 15-file Vue manifests derived from pristine pinned templates. Exit-7 regression and corrupted package name despite success UI are rejected.',
                 'Retain @clack readiness checkpoints and package-name validation; snapshot final commands without random absolute destination. Native portable Node and task-local pinned pnpm build actual source; no global installs.'),
}

frozen = read(DOC / 'final-runner.json')
source = frozen['source']
expected_runner = frozen['binaries']['playtestr-linux']
projects = []
rows = []
totals = dict(projects=0, scenarios=0, final_attempts=0, final_passed=0, final_failed=0,
              final_target_regressions_detected=0, final_recovery_passes=0, stateful_scenarios=0)
for candidate in read(DOC / 'candidates.json'):
    slug = 'create-vite' if candidate['repo']=='vitejs/vite' else candidate['repo'].split('/')[-1]
    directory = DOC / slug
    result = read(directory / 'result.json')
    config = read(directory / 'scenarios.json')
    final = result['final_qualification']
    assert result['status']=='qualified_on_final_source' and result['deleted'] is True, slug
    assert result['final_source']==source and final['runner_sha256']==expected_runner, slug
    assert result['final_negative_contracts_unchanged'] and result['final_oracles']['passed'], slug
    assert len(final['scenarios'])==len(config['cases'])>=3, slug
    for scenario in final['scenarios']:
        assert scenario['attempts']==scenario['passed']==10 and scenario['failed']==0 and scenario['cleanup_confirmed'], slug
        for name, recorded in scenario['contract_hashes'].items():
            assert digest(ROOT/name)==recorded, (slug,name)
    assert result['final_defect']['scenarios'][0]['contract_hashes']==result['final_recovery']['scenarios'][0]['contract_hashes'], slug
    license_file = directory / 'UPSTREAM-LICENSE.txt'
    assert license_file.is_file(), slug
    fixture_hashes = {str(p.relative_to(ROOT)).replace('\\','/'):digest(p) for p in (directory/'fixtures').rglob('*') if p.is_file()}
    result['fixture_hashes'] = fixture_hashes
    result['license_sha256'] = digest(license_file)
    result['retained_attempt_counts'] = read(directory/'reports/retained-attempt-counts.json')
    result['retained_failed_attempts'] = read(directory/'reports/retained-failures.json')
    scope, excluded, method, findings = DETAILS[slug]
    result['scope'] = dict(tested=scope,excluded=excluded,method=method,findings=findings)
    # Preserve historical root runner identity; final identity is explicitly separate.
    result['final_runner'] = frozen
    write(directory/'result.json',result)
    projects.append(result)
    count = len(final['scenarios'])
    totals['projects']+=1;totals['scenarios']+=count;totals['final_attempts']+=count*10;totals['final_passed']+=count*10
    totals['final_target_regressions_detected']+=1;totals['final_recovery_passes']+=len(result['final_recovery']['scenarios'])
    totals['stateful_scenarios']+=len(result['final_oracles']['checked'])
    rows.append(f"| [{slug}]({slug}/README.md) | [{candidate['sha']}]({candidate['url']}/tree/{candidate['sha']}) | {candidate['language']} / {candidate['terminal_stack']} | {candidate['license']} | {count} / {count*10} |")
    report = [f'# {slug}: completed real-project trial', '',
      f"Upstream [{candidate['repo']}]({candidate['url']}/tree/{candidate['sha']}), exact `{candidate['sha']}`, {candidate['license']}. [License](UPSTREAM-LICENSE.txt). Final Playtestr source `{source}`; actual execution on Ubuntu WSL2 Linux amd64. Native compatibility of this target on Windows/macOS is unclaimed.", '',
      f'Tested: {scope}.', '', f'Excluded: {excluded}.', '',
      '| Scenario / user risk | Positive terminal evidence | Fresh synthetic state / independent check | Final repetitions |',
      '| --- | --- | --- | --- |']
    for case in config['cases']:
        evidence = [str(step['expect']) for step in case['steps'] if 'expect' in step]
        positive = '; '.join(evidence).replace('|','\\|').replace('\n',' / ')
        fixture = 'Committed tiny fixtures; temporary copied workspace, HOME and temp'
        if case.get('oracle'): fixture += '; independent exact bytes/command state before teardown'
        report.append(f"| [{case['name']}]({case['name']}.json): {case['purpose']} | {positive}; reviewed `{case['snapshot']}` | {fixture} | 10/10 |")
    failure = result['final_defect'].get('failure',{})
    report += ['',method,'',findings,'',
      'The public recorder reviewed/replayed/exported the original journeys. Primary rerecord and manual JSON maintenance were exercised; intentional expectations were reviewed separately. Only specs that explicitly declare an exit assert natural exit; other bounded sessions are terminated and cleanup verified by the runner. No quiet-output or launch-only coverage is credited.', '',
      f"Final qualification: {count*10} fresh passes, including five normal and five bounded CPU-load repetitions per scenario. Real target mutation fails the unchanged contract, then restored source passes all {count} scenarios. [Negative screen/report](reports/defect.json), [exact patch](target-regression.patch), [final summary](reports/final-summary.json), [recovery](reports/recovery-summary.json), [state checks](reports/oracle-all-summary.json).", '',
      'Failures and retries are preserved: [retained attempt counts](reports/retained-attempt-counts.json), [failure identities/categories](reports/retained-failures.json), rejected recorder logs and recipe findings. These counts describe retained artifacts, not a fabricated total-ever denominator. Rejected or weak earlier tests receive no acceptance credit.', '',
      'Reproduce from the Playtestr repository using [recipe.json](recipe.json), [scenarios.json](scenarios.json), the exact dependency/build files here and [workflow.yml](workflow.yml). The workflow is a generated, reviewed Linux setup recipe; equivalent public test commands ran locally. No new hosted PR or all-target three-platform execution is claimed. Upstream source is fetched only into disposable owned directories.', '',
      'Evidence includes spec/baseline/fixture/license hashes, actual target identity, mutation and restored contract identities, elapsed operator setup measurements where captured, and cleanup/deletion in [result.json](result.json). The elapsed setup measurement uses warm shared caches and is not independent-user onboarding research. Temporary application/runtime directories were removed after process/evidence checks. Complete-product campaign credit: 0.']
    (directory/'README.md').write_text('\n'.join(report)+'\n',encoding='utf-8')

assert totals['projects']==10 and totals['scenarios']==33 and totals['final_passed']==330
ledger = read(DOC/'ledger.json')
ledger.update(status='completed_early_p5_reliability', completed_date='2026-10-10',projects=projects,
              final_runner=frozen,totals=totals,complete_product_campaign_credit=0,
              initial_accepted_fresh_repetitions=330,
              native_engine_validation=read(DOC/'native-final-source.json'),
              local_core_checks=read(DOC/'local-core-checks.json'),
              initial_count_scope='Ten accepted repetitions per final reviewed initial scenario; superseded weak Harlequin tests and failed/retry attempts excluded. Original source varied as fixes landed.',
              platform_scope='All ten actual applications on WSL2 Ubuntu Linux amd64. Go applications crosscompiled on Windows then executed on Linux. Engine actual native Linux/macOS/Windows CI separately verified.',
              remaining_gates=['P3 paid review integration','P4 commerce','remaining whole-product P5','100-project campaign','release/launch authorization'])
ledger['candidate_accounting']=dict(selected=10,completed_local_free_path=10,excluded_journeys=0,
                                    reserves_screened_at_closeout=3,examined_including_late_reserves=13,
                                    source='candidates.json and reserve-screening.json; reserves were screened at final review, not before initial selection')
ledger['retained_artifact_totals']={key:sum(p['retained_attempt_counts'][key] for p in projects)
    for key in ('machine_reports','observed_passed_results','observed_failed_results','expected_negative_failed_results','expected_intentional_change_failures','other_failed_results','capture_logs','rejected_captures')}
ledger['retained_artifact_count_scope']='Observed retained report/capture artifacts, including repeated qualification and rejected weak tests; not total-ever attempts, product-bug counts, or accepted scenario counts. Build/setup errors are documented separately in recipes/findings.'
write(DOC/'ledger.json',ledger)
shutil.copyfile(RAW/'state-probe-controls.json',DOC/'state-probe-controls.json')
wizard = []
for p in sorted(RAW.glob('windows-wizard-*.json')):
    d=read(p)
    assert d['summary']['failed']==0
    wizard.append(dict(path=str(p.relative_to(ROOT)).replace('\\','/'),sha256=digest(p),summary=d['summary'],runner_version=d.get('runner_version')))
assert len(wizard)==40
write(DOC/'windows-wizard-reproduction.json',dict(attempts=40,passed=40,failed=0,reports=wizard,
      original_failed_run='https://github.com/Wyrcan-io/playtestr/actions/runs/37538837223',
      result='Original retained input/resize timeout not reproduced; cause unestablished, later success is not a causal fix.'))
overview = f'''# Ten-project reliability pass — completed 10 October 2026

All ten distinct real applications completed reviewed public-recorder user journeys, meaningful target-regression detection and unchanged-contract restoration. Final qualification on Playtestr **`{source}`**: **33 scenarios, 330 fresh passing repetitions, 10 detected target regressions, {totals['final_recovery_passes']} restored scenario passes, {totals['stateful_scenarios']} independently checked stateful scenarios**. Initial accepted journeys also supplied 330 fresh repetitions on the then-current source; superseded tests and rejected attempts are excluded.

| Project | Exact upstream revision | Language / terminal stack | License | Scenarios / final passes |
| --- | --- | --- | --- | --- |
'''+'\n'.join(rows)+f'''

## General fixes delivered

- `06af0c0`: recorder rerecord reports the actual newly created working directory, allowing inspection of the correct saved state.
- `c8274d5`: explicit versioned physical-row snapshots, strict validation, recorder support and transactional selected updates. Reviewers choose meaningful rows; failure evidence preserves the full viewport.
- `4a1f41d`: preserve legitimate empty argv values; add CtrlA/CtrlK and reconcile named-key schema validation. Empty executable/NUL remain rejected.
- `53561e6`: CtrlJ emits LF independently of Enter's CR, enabling documented terminal shortcuts with actual PTY coverage.

Reduced regressions exercised failing behavior before fixes. No application-name branches, framework dependencies, AI inference or automatic baseline acceptance were added.

## What actually ran

All ten applications ran in real Linux PTYs on Ubuntu WSL2 amd64, using exact upstream source and synthetic state. Five Go targets were built on Windows for Linux and executed on Linux; cross-compilation itself supplies no native-host compatibility claim. Python applications used isolated native Python 3.12 environments; Node applications used verified portable Node 24.7.0 and explicit pinned build prerequisites. Actual target/binary/module/tree hashes live in each result. Source/dependency pins and [toolchain integrity](toolchains.json) are retained.

Each final scenario ran ten times from freshly copied fixture/HOME/temp/process state: five normal and five with a bounded external CPU worker. This supplies load variation, not an invented application startup-delay mechanism. An additional real target mutation per project produced a red result; restored original bytes passed the same contracts. Independent bounded file/Git/SQLite/manifest checks inspect persisted state before teardown. Six additional saved-state negative controls rejected real corruption despite success-looking UI. The public runner does not yet provide these independent file/database assertions; they are explicit campaign-harness checks, bounded to 10 seconds and 4 MiB. [Real-process harness controls](state-probe-controls.json) cover success, nonzero exit, flood, timeout and reaping.

The runner's **actual native Linux, macOS and Windows** full tests/vet/race/public recorder acceptance passed on exact final source: [run 37654006327](https://github.com/Wyrcan-io/playtestr/actions/runs/37654006327). [Successful job identities](native-final-source.json), [prior fix runs](native-validation.json), and [local final tests/vet/race/examples](local-core-checks.json) are separate evidence. This does not imply all ten upstream applications ran on all three hosts.

Generated per-project workflows were inspected and their equivalent public commands executed locally. They target Linux and explicitly acquire/build prerequisites; they are reproducible setup recipes, **not ten executed hosted PR journeys**. No new PRs, issues, releases, deployments or outreach were performed for this pass.

## Failed attempts and limitations

Per-project reports retain failure categories/steps/cleanup, hashes, rejected recorder captures, actual regression patches, state-corruption evidence and scope exclusions. Retained-artifact counts include retries and intentional negatives; they are not independent adoption, total-ever execution counts or a zero-flakiness claim. Early passing retries overwritten before history preservation cannot be recovered. Original runner identities remain historical; final source/hash associations are explicitly separate.

Notable findings include random-workspace and timing-row snapshot instability; stale/ambiguous readiness; mounted Python startup cost; an upstream Windows-invalid path; WSL `/tmp` removal; explicit prompt-toolkit CPR opt-out; save-path/UTF-8 operator mistakes; synthetic Git fixture mode/line-ending portability; and a Harlequin recovery test that mechanically passed without actual query results. That weak test was rejected and replaced with positive result-grid proof. App-supported configuration, meaningful anchors and reviewed physical rows resolve setup/authoring issues without silent normalization.

Candidate accounting: ten selected/executed/completed, zero substituted or excluded journeys. Three additional [reserves](reserve-screening.json) were screened from primary GitHub metadata at final review, not before the original selection; they receive no execution credit. This sequencing deviation is explicit. Rejected recorder attempts and blocked build/setup attempts belong to the selected journeys and do not create additional projects.

The historical Windows wizard timeout in [run 37538837223](https://github.com/Wyrcan-io/playtestr/actions/runs/37538837223) remains unexplained. Forty bounded local repetitions of its retained sequence passed; [report hashes and denominator](windows-wizard-reproduction.json). Original failed evidence is preserved. Later green runs do not establish a causal fix; broadened Windows reliability remains a measured risk.

Only trusted synthetic targets were executed. PTYs and subprocesses are not isolation. Mouse/style/grapheme completeness, terminal-query replies, secret handling for arbitrary apps, network/credential integrations and whole-application coverage are outside these scenario claims. See each scope table. New source features are not a claim about older published archives; no release was made.

## Reproduction, retention and next gate

[Machine ledger](ledger.json), [frozen source/binary hashes](final-runner.json), [findings and dispositions](findings.md), per-project specs/baselines/fixtures, exact licensed patches, locks, recipes, workflow templates and compact reports remain. Raw bounded evidence is ignored under `artifacts/ten-project-user-pass`; hosted artifacts have their original retention and are not promised after expiry. Patch/license attribution identifies every pinned upstream; fixture data is synthetic. Operator elapsed measurements use warm caches, not independent-user research; interrupted historical repeats are not assigned invented elapsed figures.

Every temporary application checkout, binary, native environment and task-specific dependency cache was removed after evidence/process checks. [Final cleanup verification](cleanup.json) and [package checks](package-checks.json) are recorded separately; shared pre-existing Go caches/compiler and Playtestr itself are preserved.

This completes the **early reliability portion of P5**. P3 paid review, P4 commerce, remaining whole-product P5 and the full campaign remain unqualified. **Complete-product credit: 0/100.** It is evidence for tested terminal workflows, not readiness for commercial launch or proof of demand.
'''
(DOC/'README.md').write_text(overview,encoding='utf-8')
print(json.dumps(totals))
