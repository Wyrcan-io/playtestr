# Windows startup containment repair

The real detached-worker reproducer waits one second after ConPTY's actual
process creation before returning from `Start`. This exposes scheduling that
could otherwise be intermittent. The target immediately creates a child and
grandchild with `CREATE_NO_WINDOW`; neither inherits the terminal. Both PIDs
are independently observed through task-owned files, then process handles
are retained across cleanup to avoid PID reuse. With the startup barrier
removed, both workers survive while Playtestr reports confirmed Job Object
exit. The test independently terminates and waits those exact handles.

Create the target with `CREATE_SUSPENDED`, attach its Job Object, then resume
the initial thread. The pinned ConPTY dependency forwards creation flags but
closes the initial thread handle. Recover the single initial thread by its
exact owner PID using a Toolhelp thread snapshot. Reject missing or multiple
threads and unexpected suspend counts rather than guessing. Attachment or
activation failure terminates and reaps the target, retaining separate cleanup
errors. Unix session/process-group creation is unchanged.

Microsoft documents that [suspended creation delays thread execution](https://learn.microsoft.com/en-us/windows/win32/procthread/suspending-thread-execution),
that [children inherit Job Object membership](https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject),
and the [resume return value is the previous suspend count](https://learn.microsoft.com/en-us/windows/desktop/api/processthreadsapi/nf-processthreadsapi-resumethread).
This is lifecycle containment for trusted targets, not security isolation.
Microsoft also describes the runner-crash window between suspended creation
and attachment and an alternative [atomic Job List startup attribute](https://devblogs.microsoft.com/oldnewthing/20230209-00/?p=107812).
The current dependency does not expose that additional startup attribute.
An external crash in that small pre-attachment window remains outside the
confirmed normal runner cleanup contract; this repair makes no crash-proof
or security claim.

Local full Go tests, vet, race and ten repaired startup controls passed. Native
hosted qualification must be linked after actual execution. The earlier
post-attachment retained-PTY grandchild test remains a separate control.
