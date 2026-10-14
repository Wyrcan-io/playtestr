"""Predeclare distinct product controls; evidence is attached only after execution."""
import json
import hashlib
import subprocess
from adversarial_process import DOC,ROOT

def source_digest(data):
    return hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()

def recorded_source_digest(revision,path,cache):
    key=(revision,path)
    if key not in cache:
        if len(revision)!=40 or any(c not in '0123456789abcdef' for c in revision):
            raise RuntimeError('Invalid recorded source revision')
        data=subprocess.check_output(['git','show',revision+':'+path],cwd=ROOT,timeout=15)
        cache[key]=source_digest(data)
    return cache[key]

CONTROLS={
 'Lifecycle':[
 ('natural-zero','TestExpectedExitZero','Exact natural zero exit'),
 ('declared-nonzero','TestExpectedNonzeroExit','Exact declared nonzero exit'),
 ('wrong-exit','TestWrongExitCode','Unexpected exit differs from declared code'),
 ('early-exit','TestExitWhileWaitingForText','Exit before readiness cannot pass'),
 ('output-actual-crash','TestAdversarialOutputFollowedByActualCrash','Actual target panic after positive checkpoint cannot pass'),
 ('exit-final-output-race','TestAdversarialImmediateExitPreservesFinalOutput','Twenty immediate exits retain final output after exit observation'),
 ('native-terminal-eof','TestNaturalExitReachesTerminalEOF','Unix natural exit drains final output; platform-specific EOF contract'),
 ('exit-hang','TestExitTimeout','Expected exit that never arrives is bounded'),
 ('whole-run-budget','TestRunTimeout','Whole-run budget applies across steps'),
 ('cancel','TestCancellation','Cancellation returns accurate outcome'),
 ],
 'Process cleanup':[
 ('direct-descendant','TestChildProcessCleanup','Child survives parent until cleanup'),
 ('grandchild-pty','TestAdversarialGrandchildAndRetainedPTYCleanup','Two descendant generations inherit PTY handles'),
 ('stubborn-live-generations','TestAdversarialStubbornUnixDescendantCleanup','Two executing descendant generations ignore actual SIGTERM, then are terminated after parent exit'),
 ('repeated-cleanup','TestRepeatedSessionCleanup','Repeated sessions leave no owned processes'),
 ('idempotent-stop','TestSessionStopIsIdempotent','Repeated stop preserves outcome'),
 ('recorder-tree','TestRecordingTracksDescendantCleanupAndExpectedNonzero','Recorder owns descendants and nonzero observation'),
 ('immediate-detached-startup','TestAdversarialWindowsImmediateDescendantsCannotEscapeStartup','Windows target cannot fork detached descendants before Job Object attachment'),
 ],
 'Output and input bounds':[
 ('flood','TestOutputLimit','Real target output flood has bounded failure'),
 ('blocked-input','TestBlockedInputHonorsContext','Input to nonreading target observes cancellation'),
 ('silent-input','TestSilentTargetCanReceiveInputWithoutStartupTimeout','Silent real target can receive initial input'),
 ('startup-budget','TestStartupTimeout','Explicit startup readiness deadline'),
 ('idle-recorder-flood','TestRecordingCancellationAndFloodStopIdleTargets','Idle recorder observes overflow or hang'),
 ],
 'Readiness':[
 ('input-sequence-readiness','TestRecordingInputSequenceKeepsFirstTransitionScreen','Filter-before-confirm input sequences use their first pre-input screen; unchanged/stale captions still reject, including reconstructed prefixes'),
 ('disappear-reappear','TestAdversarialDisappearanceAndReappearance','Real target text disappears after input then reappears in a fresh third phase'),
 ('stale-ambiguous','TestRecordingRejectsAmbiguousAndDynamicReadiness','Ambiguous capture and changing replay state do not qualify'),
 ('absence-transition','TestExpectNotWaitsForObservedTextToDisappear','Previously observed text must actually disappear'),
 ('absence-timeout','TestExpectNotTimesOutWhileObservedTextRemains','Still-visible old text does not pass absence'),
 ('unready-row','TestRowSnapshotRejectsUnreadyEmptyInvalidAndResizedBounds','No unready/empty/invalid row checkpoint'),
 ],
 'Keys and terminal':[
 ('rapid-key-order','TestAdversarialRapidKeysPreserveEveryEvent','320 rapid control/text bytes retain exact independent ordering'),
 ('all-letter-controls','TestAdversarialEveryLetterControlKeyThroughRealPTY','All 26 named letter controls reach a real raw target with independently specified exact bytes'),
 ('unicode-literal-paste','TestAdversarialBoundedUnicodeLiteralPaste','Bounded multi-line Unicode literal input retains exact UTF-8 bytes'),
 ('repeated-resize-output','TestAdversarialRepeatedResizeDuringOutput','Twelve resizes during actual ongoing output expose correct target dimensions'),
 ('output-cap-boundary','TestAdversarialOutputCapBoundary','Real output below and above the cap has distinct accurate outcomes'),
 ('unsupported-query-bound','TestAdversarialUnsupportedCursorQueryIsBounded','Unsupported cursor query produces bounded truthful failure, without claiming reply support'),
 ('windows-enter-lf','TestWindowsEnterAndCtrlJRemainDistinctThroughRealPTY','Real Windows target distinguishes CR, LF and CR after resize'),
 ('windows-resize-fence','TestWindowsResizeOutputFenceRequiresReturnedCurrentRequest','Protocol unit control rejects pre-return and superseded output read fences'),
 ('control-keys','TestEditingControlKeysThroughRealPTY','Exact control bytes through real PTY'),
 ('empty-argv','TestEmptyArgumentPreservedThroughRealPTY','Preserve empty arguments and quoted/spaced values'),
 ('resize-target','TestTargetObservesResize','Actual target sees PTY dimensions'),
 ('resize-redraw','TestWaitForRedrawSynchronizesAfterResize','Resize/redraw synchronization before input'),
 ('screen-redraw','TestScreenRedraw','Pure renderer erase/redraw state; real PTY complements are separately required'),
 ('adversarial-real-vt','TestAdversarialTerminalStreamsThroughRealPTY','Real split UTF-8/VT, alternate screen, scroll, malformed controls, wrapping and bounded recovery from unsupported presentation modes'),
 ('partial-real-input','TestPartialBackendInputCannotPass','A backend forwarding only part of real input cannot report success'),
 ('windows-resize-reply','TestWindowsResizeRepliesRequireCurrentDimensions','Current dimensions required; stale or payload-contained acknowledgments rejected'),
 ('windows-resize-bound','TestWindowsResizeWithoutAcknowledgmentIsBounded','Absent Windows resize acknowledgment must time out accurately'),
 ('literal-recorder-control','TestRecordingLiteralControlKeyAndResolvedSetup','Control-console escape can be transmitted literally'),
 ('live-operator-restoration','TestNativeRecorderLiveInputAndOperatorRestoration','Native operator terminal restored after live input'),
 ],
 'Spec and paths':[
 ('strict-spec','TestAuthoringDiagnosticsRejectBeforeLaunchWithoutLeakingInput','Malformed/version/field/action errors reject without launch'),
 ('spec-size','TestSpecVersionAndSizeLimits','Spec version and size bounded'),
 ('workspace-path','TestWorkspaceSpecValidation','Workspace paths and environment conflicts rejected'),
 ('fixture-links-bounds','TestWorkspaceFixtureCopyRejectsUnsafeAndBoundedInputs','Real fixture rejects links/specials/oversize'),
 ('resolve-before-cwd','TestWorkspaceCommandResolutionPrecedesFixtureCWD','Target executable resolved before changed cwd'),
 ('missing-executable','TestLaunchFailure','Missing executable produces an accurate launch failure'),
 ('explicit-environment','TestWorkingDirectoryAndExplicitEnvironment','Actual target receives explicit cwd and environment'),
 ('selected-inheritance','TestInheritedEnvironment','Actual target receives only the selected inherited environment value'),
 ('terminal-profile-precedence','TestAdversarialTerminalProfileEnvironmentThroughRealPTY','Real v1/v2 PTY targets observe the stable TERM default, explicit inheritance and literal-over-inherited precedence without ambient opt-in'),
 ('report-traversal','TestRenderHTMLRejectsUnsafeEvidenceReferences','Evidence references cannot traverse admitted root'),
 ],
 'Workspaces':[
 ('windows-workspace-marker-visibility','TestWorkspaceOwnershipMarkerUsesNativeHiddenAttribute','Real Windows directory attributes hide only the internal ownership marker; fixture visibility, token integrity and owned cleanup remain correct'),
 ('windows-workspace-long-path','TestAdversarialWindowsWorkspaceExpandsShortTemporaryPath','Actual Windows target receives long workspace path when TEMP is an 8.3 alias; process and filesystem cleanup confirmed'),
 ('fresh-state','TestWorkspaceRunsTwiceFromFreshFixtureAndCleans','Every invocation has fresh owned fixture and cleanup'),
 ('readonly-crlf-modes','TestWorkspaceReadOnlyInputsPreserveBytesAndNormalizeModes','Real read-only fixture preserves exact CRLF/UTF-8 bytes; copies are writable and Unix executable bits retained'),
 ('failure-retention','TestWorkspaceFailureCleanupAndExplicitRetention','Explicit failure retention has accurate evidence'),
 ('setup-no-launch','TestWorkspaceSetupFailureDoesNotLaunchTarget','Invalid fixture never launches target'),
 ('cleanup-blocks-update','TestWorkspaceCleanupFailurePreventsSnapshotCommit','Cleanup failure prevents accepted baseline'),
 ('fixture-dirty','TestRecordingFixtureChangesAndCanceledExport','Dirty fixture invalidates reviewed replay'),
 ],
 'Snapshots and export':[
 ('genuine-mismatch','TestSnapshotBaselineAndReadableMismatch','Actual screen mismatch is red with readable evidence'),
 ('missing-snapshot','TestSnapshotMissingAndSizeFailuresAreDistinct','Missing and oversized baselines produce distinct accurate failures'),
 ('selected-update','TestTargetedSnapshotUpdate','Only named baseline changes'),
 ('late-failure-rollback','TestSnapshotUpdatesAreNotCommittedAfterLaterFailure','Later failing step rolls back update'),
 ('cancel-update','TestSnapshotUpdatesAreNotCommittedAfterCancellation','Cancellation prevents staged commit'),
 ('multi-file-rollback','TestSnapshotRollbackRestoresEveryChangedFile','Real files and fault injection verify transactional rollback'),
 ('interrupted-export','TestRecordingInterruptedExportRollsBackWrittenFiles','Observed interrupted multi-file export removes partial files'),
 ('strict-row-format','TestRowSnapshotMetadataIsStrict','Row metadata validates explicit version/range/text'),
 ('row-defect','TestRowSnapshotFreshCaptureReplayAndRealDefect','Reviewed row checkpoint detects meaningful real change'),
 ],
 'Reports and selection':[
 ('hostile-html','TestRenderHTMLMixedSuiteIsOfflineEscapedAndComplete','Hostile synthetic text is escaped in offline HTML'),
 ('corrupt-report','TestRenderHTMLRejectsMalformedVersionOversizeAndInconsistentInput','Corrupt/oversized/inconsistent results cannot render green'),
 ('artifact-association','TestRenderHTMLRejectsInconsistentAndSharedArtifactAssociation','Wrong result/artifact association rejected'),
 ('report-write-error','TestReportWriteFailureReturnsNonzero','Failed machine-report write preserves nonzero CLI status'),
 ('zero-selection','TestAuthoringEmptySelectionExplainsNextActionWithoutLaunch','Empty selection fails before launch with diagnosis'),
 ('output-alias','TestOutputAliasesAreRejectedBeforeLaunch','Output cannot overwrite selected test input'),
 ('prior-output-preserved','TestRenderHTMLBoundsEvidenceAndPreservesOutputOnEveryFailure','Evidence/write failures preserve prior HTML'),
 ],
 'Confidentiality':[
 ('private-canaries','TestSecretCanaryPersistenceBoundary','Nonrendered fake environment/input absent from reports and logs; emitted evidence limitation explicit'),
 ('report-field-boundary','TestReportSummaryOrderAndSecretBoundary','Machine reports omit argument/input/environment values'),
 ],
}

def main():
    records=[]
    previous={}
    matrix=DOC/'coverage-matrix.json'
    if matrix.exists():
        previous={row['test']:row for row in json.loads(matrix.read_text(encoding='utf-8'))['controls']}
    files=list((ROOT/'internal').rglob('*_test.go'))+list((ROOT/'cmd/playtestr').glob('*_test.go'))
    for family,controls in CONTROLS.items():
        for name,test,requirement in controls:
            locations=[p for p in files if 'func '+test+'(' in p.read_text(encoding='utf-8')]
            if len(locations)!=1:
                raise RuntimeError('Ambiguous or missing control '+test)
            path=locations[0]
            package='./'+str(path.parent.relative_to(ROOT)).replace('\\','/')
            records.append(dict(id=name,family=family,test=test,package=package,
                requirement=requirement,severity='high',hosts=['linux','macos','windows'],
                evidence=[],status='declared_not_qualified',
                layer='real PTY where terminal/process behavior; pure logic/real temporary files for parsing or serialization',
                source=str(path.relative_to(ROOT)).replace('\\','/'),
                test_source_sha256=source_digest(path.read_bytes())))
    DOC.mkdir(parents=True,exist_ok=True)
    source_cache={}
    for row in records:
        row['evidence']=previous.get(row['test'],{}).get('evidence',[])
        for evidence in row['evidence']:
            actual=recorded_source_digest(evidence['source'],row['source'],source_cache)
            evidence.update(test_source_sha256=actual,
                matches_current_test_source=actual==row['test_source_sha256'])
        if row['test'] in {'TestNaturalExitReachesTerminalEOF','TestAdversarialStubbornUnixDescendantCleanup'}:
            row['hosts']=['linux','macos']
        if row['test'] in {'TestAdversarialWindowsImmediateDescendantsCannotEscapeStartup',
                           'TestWindowsResizeRepliesRequireCurrentDimensions',
                           'TestWindowsEnterAndCtrlJRemainDistinctThroughRealPTY',
                           'TestWindowsResizeOutputFenceRequiresReturnedCurrentRequest',
                           'TestAdversarialWindowsWorkspaceExpandsShortTemporaryPath',
                           'TestWorkspaceOwnershipMarkerUsesNativeHiddenAttribute',
                           'TestWindowsResizeWithoutAcknowledgmentIsBounded'}:
            row['hosts']=['windows']
    (DOC/'coverage-matrix.json').write_text(json.dumps(dict(controls=records,
        count=len(records),claim='Named distinct controls; actual events required; not a coverage percentage'),indent=2)+'\n')
    text='# Product control matrix — scoped evidence\n\nControls are mapped before qualification. Test names and configured hosts alone are not evidence. The JSON matrix preserves actual event hashes and source revisions, with a canonical test-file hash to distinguish historical definitions from the current control. Whole tests containing multiple cases count once. Final frozen-source qualification remains separate.\n\n| ID | Family | Requirement | Go control |\n| --- | --- | --- | --- |\n'
    text+=''.join(f"| {r['id']} | {r['family']} | {r['requirement']} | `{r['test']}` |\n" for r in records)
    (DOC/'coverage-matrix.md').write_text(text,encoding='utf-8')
    print('Declared',len(records),'distinct controls across',len(CONTROLS),'families')

if __name__=='__main__': main()
