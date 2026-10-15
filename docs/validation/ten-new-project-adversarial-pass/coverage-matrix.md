# Product control matrix — scoped evidence

Controls are mapped before qualification. Test names and configured hosts alone are not evidence. The JSON matrix preserves actual event hashes and source revisions, with a canonical test-file hash to distinguish historical definitions from the current control. Whole tests containing multiple cases count once. Final frozen-source qualification remains separate.

| ID | Family | Requirement | Go control |
| --- | --- | --- | --- |
| natural-zero | Lifecycle | Exact natural zero exit | `TestExpectedExitZero` |
| declared-nonzero | Lifecycle | Exact declared nonzero exit | `TestExpectedNonzeroExit` |
| wrong-exit | Lifecycle | Unexpected exit differs from declared code | `TestWrongExitCode` |
| early-exit | Lifecycle | Exit before readiness cannot pass | `TestExitWhileWaitingForText` |
| output-actual-crash | Lifecycle | Actual target panic after positive checkpoint cannot pass | `TestAdversarialOutputFollowedByActualCrash` |
| exit-final-output-race | Lifecycle | Twenty immediate exits retain final output after exit observation | `TestAdversarialImmediateExitPreservesFinalOutput` |
| native-terminal-eof | Lifecycle | Unix natural exit drains final output; platform-specific EOF contract | `TestNaturalExitReachesTerminalEOF` |
| exit-hang | Lifecycle | Expected exit that never arrives is bounded | `TestExitTimeout` |
| whole-run-budget | Lifecycle | Whole-run budget applies across steps | `TestRunTimeout` |
| cancel | Lifecycle | Cancellation returns accurate outcome | `TestCancellation` |
| direct-descendant | Process cleanup | Child survives parent until cleanup | `TestChildProcessCleanup` |
| grandchild-pty | Process cleanup | Two descendant generations inherit PTY handles | `TestAdversarialGrandchildAndRetainedPTYCleanup` |
| stubborn-live-generations | Process cleanup | Two executing descendant generations ignore actual SIGTERM, then are terminated after parent exit | `TestAdversarialStubbornUnixDescendantCleanup` |
| repeated-cleanup | Process cleanup | Repeated sessions leave no owned processes | `TestRepeatedSessionCleanup` |
| idempotent-stop | Process cleanup | Repeated stop preserves outcome | `TestSessionStopIsIdempotent` |
| recorder-tree | Process cleanup | Recorder owns descendants and nonzero observation | `TestRecordingTracksDescendantCleanupAndExpectedNonzero` |
| immediate-detached-startup | Process cleanup | Windows target cannot fork detached descendants before Job Object attachment | `TestAdversarialWindowsImmediateDescendantsCannotEscapeStartup` |
| flood | Output and input bounds | Real target output flood has bounded failure | `TestOutputLimit` |
| blocked-input | Output and input bounds | Input to nonreading target observes cancellation | `TestBlockedInputHonorsContext` |
| silent-input | Output and input bounds | Silent real target can receive initial input | `TestSilentTargetCanReceiveInputWithoutStartupTimeout` |
| startup-budget | Output and input bounds | Explicit startup readiness deadline | `TestStartupTimeout` |
| idle-recorder-flood | Output and input bounds | Idle recorder observes overflow or hang | `TestRecordingCancellationAndFloodStopIdleTargets` |
| input-sequence-readiness | Readiness | Filter-before-confirm input sequences use their first pre-input screen; unchanged/stale captions still reject, including reconstructed prefixes | `TestRecordingInputSequenceKeepsFirstTransitionScreen` |
| disappear-reappear | Readiness | Real target text disappears after input then reappears in a fresh third phase | `TestAdversarialDisappearanceAndReappearance` |
| stale-ambiguous | Readiness | Ambiguous capture and changing replay state do not qualify | `TestRecordingRejectsAmbiguousAndDynamicReadiness` |
| absence-transition | Readiness | Previously observed text must actually disappear | `TestExpectNotWaitsForObservedTextToDisappear` |
| absence-timeout | Readiness | Still-visible old text does not pass absence | `TestExpectNotTimesOutWhileObservedTextRemains` |
| unready-row | Readiness | No unready/empty/invalid row checkpoint | `TestRowSnapshotRejectsUnreadyEmptyInvalidAndResizedBounds` |
| rapid-key-order | Keys and terminal | 320 rapid control/text bytes retain exact independent ordering | `TestAdversarialRapidKeysPreserveEveryEvent` |
| all-letter-controls | Keys and terminal | All 26 named letter controls reach a real raw target with independently specified exact bytes | `TestAdversarialEveryLetterControlKeyThroughRealPTY` |
| standard-navigation-input | Keys and terminal | Home, End, PageUp and PageDown reach a real raw target and native operator decoder with positive receipts | `TestAdversarialStandardNavigationKeys` |
| native-navigation-modifiers | Keys and terminal | Unsupported native Alt/Ctrl/Shift navigation cannot silently become an unmodified key | `TestWindowsNativeNavigationModifiersRejected` |
| unicode-literal-paste | Keys and terminal | Bounded multi-line Unicode literal input retains exact UTF-8 bytes | `TestAdversarialBoundedUnicodeLiteralPaste` |
| repeated-resize-output | Keys and terminal | Twelve resizes during actual ongoing output expose correct target dimensions | `TestAdversarialRepeatedResizeDuringOutput` |
| output-cap-boundary | Keys and terminal | Real output below and above the cap has distinct accurate outcomes | `TestAdversarialOutputCapBoundary` |
| unsupported-query-bound | Keys and terminal | Unsupported cursor query produces bounded truthful failure, without claiming reply support | `TestAdversarialUnsupportedCursorQueryIsBounded` |
| windows-enter-lf | Keys and terminal | Real Windows target distinguishes CR, LF and CR after resize | `TestWindowsEnterAndCtrlJRemainDistinctThroughRealPTY` |
| windows-resize-fence | Keys and terminal | Protocol unit control rejects pre-return and superseded output read fences | `TestWindowsResizeOutputFenceRequiresReturnedCurrentRequest` |
| control-keys | Keys and terminal | Exact control bytes through real PTY | `TestEditingControlKeysThroughRealPTY` |
| empty-argv | Keys and terminal | Preserve empty arguments and quoted/spaced values | `TestEmptyArgumentPreservedThroughRealPTY` |
| resize-target | Keys and terminal | Actual target sees PTY dimensions | `TestTargetObservesResize` |
| resize-redraw | Keys and terminal | Resize/redraw synchronization before input | `TestWaitForRedrawSynchronizesAfterResize` |
| screen-redraw | Keys and terminal | Pure renderer erase/redraw state; real PTY complements are separately required | `TestScreenRedraw` |
| adversarial-real-vt | Keys and terminal | Real split UTF-8/VT, alternate screen, scroll, malformed controls, wrapping and bounded recovery from unsupported presentation modes | `TestAdversarialTerminalStreamsThroughRealPTY` |
| partial-real-input | Keys and terminal | A backend forwarding only part of real input cannot report success | `TestPartialBackendInputCannotPass` |
| windows-resize-reply | Keys and terminal | Current dimensions required; stale or payload-contained acknowledgments rejected | `TestWindowsResizeRepliesRequireCurrentDimensions` |
| windows-resize-bound | Keys and terminal | Absent Windows resize acknowledgment must time out accurately | `TestWindowsResizeWithoutAcknowledgmentIsBounded` |
| literal-recorder-control | Keys and terminal | Control-console escape can be transmitted literally | `TestRecordingLiteralControlKeyAndResolvedSetup` |
| recorder-redraw-readiness | Keys and terminal | Unique recorder readiness uses one real-PTY screen observation during repeated erase/redraw | `TestRecordingReadinessDuringRepeatedRedraw` |
| recorder-transient-ambiguity | Keys and terminal | Recorder waits within its deadline for a transient duplicate to become a unique rendered anchor | `TestRecordingWaitsForUniqueAnchorAfterRedraw` |
| final-drain-output-cap | Keys and terminal | Actual final PTY bytes exceeding the cap take precedence over a concurrently observed target exit | `TestAdversarialFinalDrainPreservesOutputLimit` |
| live-operator-restoration | Keys and terminal | Native operator terminal restored after live input | `TestNativeRecorderLiveInputAndOperatorRestoration` |
| strict-spec | Spec and paths | Malformed/version/field/action errors reject without launch | `TestAuthoringDiagnosticsRejectBeforeLaunchWithoutLeakingInput` |
| spec-size | Spec and paths | Spec version and size bounded | `TestSpecVersionAndSizeLimits` |
| workspace-path | Spec and paths | Workspace paths and environment conflicts rejected | `TestWorkspaceSpecValidation` |
| fixture-links-bounds | Spec and paths | Real fixture rejects links/specials/oversize | `TestWorkspaceFixtureCopyRejectsUnsafeAndBoundedInputs` |
| resolve-before-cwd | Spec and paths | Target executable resolved before changed cwd | `TestWorkspaceCommandResolutionPrecedesFixtureCWD` |
| missing-executable | Spec and paths | Missing executable produces an accurate launch failure | `TestLaunchFailure` |
| explicit-environment | Spec and paths | Actual target receives explicit cwd and environment | `TestWorkingDirectoryAndExplicitEnvironment` |
| selected-inheritance | Spec and paths | Actual target receives only the selected inherited environment value | `TestInheritedEnvironment` |
| terminal-profile-precedence | Spec and paths | Real v1/v2 PTY targets observe the stable TERM default, explicit inheritance and literal-over-inherited precedence without ambient opt-in | `TestAdversarialTerminalProfileEnvironmentThroughRealPTY` |
| report-traversal | Spec and paths | Evidence references cannot traverse admitted root | `TestRenderHTMLRejectsUnsafeEvidenceReferences` |
| windows-workspace-marker-visibility | Workspaces | Real Windows directory attributes hide only the internal ownership marker; fixture visibility, token integrity and owned cleanup remain correct | `TestWorkspaceOwnershipMarkerUsesNativeHiddenAttribute` |
| windows-workspace-long-path | Workspaces | Actual Windows target receives long workspace path when TEMP is an 8.3 alias; process and filesystem cleanup confirmed | `TestAdversarialWindowsWorkspaceExpandsShortTemporaryPath` |
| fresh-state | Workspaces | Every invocation has fresh owned fixture and cleanup | `TestWorkspaceRunsTwiceFromFreshFixtureAndCleans` |
| readonly-crlf-modes | Workspaces | Real read-only fixture preserves exact CRLF/UTF-8 bytes; copies are writable and Unix executable bits retained | `TestWorkspaceReadOnlyInputsPreserveBytesAndNormalizeModes` |
| failure-retention | Workspaces | Explicit failure retention has accurate evidence | `TestWorkspaceFailureCleanupAndExplicitRetention` |
| setup-no-launch | Workspaces | Invalid fixture never launches target | `TestWorkspaceSetupFailureDoesNotLaunchTarget` |
| cleanup-blocks-update | Workspaces | Cleanup failure prevents accepted baseline | `TestWorkspaceCleanupFailurePreventsSnapshotCommit` |
| fixture-dirty | Workspaces | Dirty fixture invalidates reviewed replay | `TestRecordingFixtureChangesAndCanceledExport` |
| genuine-mismatch | Snapshots and export | Actual screen mismatch is red with readable evidence | `TestSnapshotBaselineAndReadableMismatch` |
| missing-snapshot | Snapshots and export | Missing and oversized baselines produce distinct accurate failures | `TestSnapshotMissingAndSizeFailuresAreDistinct` |
| selected-update | Snapshots and export | Only named baseline changes | `TestTargetedSnapshotUpdate` |
| late-failure-rollback | Snapshots and export | Later failing step rolls back update | `TestSnapshotUpdatesAreNotCommittedAfterLaterFailure` |
| cancel-update | Snapshots and export | Cancellation prevents staged commit | `TestSnapshotUpdatesAreNotCommittedAfterCancellation` |
| multi-file-rollback | Snapshots and export | Real files and fault injection verify transactional rollback | `TestSnapshotRollbackRestoresEveryChangedFile` |
| interrupted-export | Snapshots and export | Observed interrupted multi-file export removes partial files | `TestRecordingInterruptedExportRollsBackWrittenFiles` |
| strict-row-format | Snapshots and export | Row metadata validates explicit version/range/text | `TestRowSnapshotMetadataIsStrict` |
| row-defect | Snapshots and export | Reviewed row checkpoint detects meaningful real change | `TestRowSnapshotFreshCaptureReplayAndRealDefect` |
| hostile-html | Reports and selection | Hostile synthetic text is escaped in offline HTML | `TestRenderHTMLMixedSuiteIsOfflineEscapedAndComplete` |
| corrupt-report | Reports and selection | Corrupt/oversized/inconsistent results cannot render green | `TestRenderHTMLRejectsMalformedVersionOversizeAndInconsistentInput` |
| artifact-association | Reports and selection | Wrong result/artifact association rejected | `TestRenderHTMLRejectsInconsistentAndSharedArtifactAssociation` |
| report-write-error | Reports and selection | Failed machine-report write preserves nonzero CLI status | `TestReportWriteFailureReturnsNonzero` |
| zero-selection | Reports and selection | Empty selection fails before launch with diagnosis | `TestAuthoringEmptySelectionExplainsNextActionWithoutLaunch` |
| output-alias | Reports and selection | Output cannot overwrite selected test input | `TestOutputAliasesAreRejectedBeforeLaunch` |
| prior-output-preserved | Reports and selection | Evidence/write failures preserve prior HTML | `TestRenderHTMLBoundsEvidenceAndPreservesOutputOnEveryFailure` |
| private-canaries | Confidentiality | Nonrendered fake environment/input absent from reports and logs; emitted evidence limitation explicit | `TestSecretCanaryPersistenceBoundary` |
| report-field-boundary | Confidentiality | Machine reports omit argument/input/environment values | `TestReportSummaryOrderAndSecretBoundary` |
