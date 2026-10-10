"""Predeclare distinct product controls; evidence is attached only after execution."""
import json
from adversarial_process import DOC,ROOT

CONTROLS={
 'Lifecycle':[
 ('natural-zero','TestExpectedExitZero','Exact natural zero exit'),
 ('declared-nonzero','TestExpectedNonzeroExit','Exact declared nonzero exit'),
 ('wrong-exit','TestWrongExitCode','Unexpected exit differs from declared code'),
 ('early-exit','TestExitWhileWaitingForText','Exit before readiness cannot pass'),
 ('exit-hang','TestExitTimeout','Expected exit that never arrives is bounded'),
 ('whole-run-budget','TestRunTimeout','Whole-run budget applies across steps'),
 ('cancel','TestCancellation','Cancellation returns accurate outcome'),
 ],
 'Process cleanup':[
 ('direct-descendant','TestChildProcessCleanup','Child survives parent until cleanup'),
 ('grandchild-pty','TestAdversarialGrandchildAndRetainedPTYCleanup','Two descendant generations inherit PTY handles'),
 ('repeated-cleanup','TestRepeatedSessionCleanup','Repeated sessions leave no owned processes'),
 ('idempotent-stop','TestSessionStopIsIdempotent','Repeated stop preserves outcome'),
 ('recorder-tree','TestRecordingTracksDescendantCleanupAndExpectedNonzero','Recorder owns descendants and nonzero observation'),
 ],
 'Output and input bounds':[
 ('flood','TestOutputLimit','Real target output flood has bounded failure'),
 ('blocked-input','TestBlockedInputHonorsContext','Input to nonreading target observes cancellation'),
 ('silent-input','TestSilentTargetCanReceiveInputWithoutStartupTimeout','Silent real target can receive initial input'),
 ('startup-budget','TestStartupTimeout','Explicit startup readiness deadline'),
 ('idle-recorder-flood','TestRecordingCancellationAndFloodStopIdleTargets','Idle recorder observes overflow or hang'),
 ],
 'Readiness':[
 ('stale-ambiguous','TestRecordingRejectsAmbiguousAndDynamicReadiness','Ambiguous capture and changing replay state do not qualify'),
 ('absence-transition','TestExpectNotWaitsForObservedTextToDisappear','Previously observed text must actually disappear'),
 ('absence-timeout','TestExpectNotTimesOutWhileObservedTextRemains','Still-visible old text does not pass absence'),
 ('unready-row','TestRowSnapshotRejectsUnreadyEmptyInvalidAndResizedBounds','No unready/empty/invalid row checkpoint'),
 ],
 'Keys and terminal':[
 ('control-keys','TestEditingControlKeysThroughRealPTY','Exact control bytes through real PTY'),
 ('empty-argv','TestEmptyArgumentPreservedThroughRealPTY','Preserve empty arguments and quoted/spaced values'),
 ('resize-target','TestTargetObservesResize','Actual target sees PTY dimensions'),
 ('resize-redraw','TestWaitForRedrawSynchronizesAfterResize','Resize/redraw synchronization before input'),
 ('screen-redraw','TestScreenRedraw','Pure renderer erase/redraw state; real PTY complements are separately required'),
 ('literal-recorder-control','TestRecordingLiteralControlKeyAndResolvedSetup','Control-console escape can be transmitted literally'),
 ('live-operator-restoration','TestNativeRecorderLiveInputAndOperatorRestoration','Native operator terminal restored after live input'),
 ],
 'Spec and paths':[
 ('strict-spec','TestAuthoringDiagnosticsRejectBeforeLaunchWithoutLeakingInput','Malformed/version/field/action errors reject without launch'),
 ('spec-size','TestSpecVersionAndSizeLimits','Spec version and size bounded'),
 ('workspace-path','TestWorkspaceSpecValidation','Workspace paths and environment conflicts rejected'),
 ('fixture-links-bounds','TestWorkspaceFixtureCopyRejectsUnsafeAndBoundedInputs','Real fixture rejects links/specials/oversize'),
 ('resolve-before-cwd','TestWorkspaceCommandResolutionPrecedesFixtureCWD','Target executable resolved before changed cwd'),
 ('report-traversal','TestRenderHTMLRejectsUnsafeEvidenceReferences','Evidence references cannot traverse admitted root'),
 ],
 'Workspaces':[
 ('fresh-state','TestWorkspaceRunsTwiceFromFreshFixtureAndCleans','Every invocation has fresh owned fixture and cleanup'),
 ('failure-retention','TestWorkspaceFailureCleanupAndExplicitRetention','Explicit failure retention has accurate evidence'),
 ('setup-no-launch','TestWorkspaceSetupFailureDoesNotLaunchTarget','Invalid fixture never launches target'),
 ('cleanup-blocks-update','TestWorkspaceCleanupFailurePreventsSnapshotCommit','Cleanup failure prevents accepted baseline'),
 ('fixture-dirty','TestRecordingFixtureChangesAndCanceledExport','Dirty fixture invalidates reviewed replay'),
 ],
 'Snapshots and export':[
 ('genuine-mismatch','TestSnapshotBaselineAndReadableMismatch','Actual screen mismatch is red with readable evidence'),
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
                source=str(path.relative_to(ROOT)).replace('\\','/')))
    DOC.mkdir(parents=True,exist_ok=True)
    (DOC/'coverage-matrix.json').write_text(json.dumps(dict(controls=records,
        count=len(records),claim='Named distinct controls; actual events required; not a coverage percentage'),indent=2)+'\n')
    text='# Product control matrix — execution pending\n\nExisting controls were inspected and mapped before campaign control execution. Test names and configured hosts alone are not evidence. Native test events must be linked after actual execution. Whole tests containing multiple cases count once here.\n\n| ID | Family | Requirement | Go control |\n| --- | --- | --- | --- |\n'
    text+=''.join(f"| {r['id']} | {r['family']} | {r['requirement']} | `{r['test']}` |\n" for r in records)
    (DOC/'coverage-matrix.md').write_text(text,encoding='utf-8')
    print('Declared',len(records),'distinct controls across',len(CONTROLS),'families')

if __name__=='__main__': main()
