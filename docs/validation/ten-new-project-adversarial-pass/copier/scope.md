# Copier: declared scope before acquisition

Pinned repository: [copier-org/copier](https://github.com/copier-org/copier/tree/04a8619f3b083bc278b70e556bd085551a2b3f79),
revision `04a8619f3b083bc278b70e556bd085551a2b3f79`, MIT, Python/questionary.
Linux and Windows are provisional until native runs pass. Local trusted
synthetic templates only; no remote templates, extensions or arbitrary tasks.
One explicitly reviewed task writes a small synthetic marker.

Normal workflows:

1. Create a usable project with dependent slug and nondefault license selection;
   verify exact generated README and JSON configuration.
2. Include an optional component through a conditional question and file name;
   verify included bytes and absence of unselected files.
3. Choose multiple optional features with real checkbox navigation; verify the
   ordered saved selections and neighboring protected state.
4. Recopy an existing project from saved answers, changing one answer while
   declining overwrite of a protected local file; verify protection and newly
   generated missing files.
5. Execute a reviewed local task with explicit trust; verify independent marker
   and generated files. The task contains no network or external side effects.
6. Update a Git-tracked project from synthetic template v1 to v2, answer a new
   question and preserve an unrelated local edit; verify actual merged files.
   Git template/destination setup is upstream prerequisite work, separately
   measured from Playtestr authoring.

Distinct edge workflows:

1. Reject an invalid slug through the actual template validator, correct it,
   then verify saved corrected state.
2. Reject text where an integer is required, correct it and verify the exact
   numeric result.
3. Reject malformed JSON, clear/correct the input and verify structured output.
4. Cancel after editing a prompt; exact declared nonzero exit, no generated
   project, protected neighboring state unchanged.
5. Refuse task execution without the trust flag; exact nonzero exit, no task
   marker or generated project, protected state unchanged.
6. Refuse updating a dirty Git destination; exact exit 1, preserve the actual
   uncommitted edit and old generated README, and create no v2 file.

At least two real upstream code mutations must be detected by unchanged
contracts and restored. A separate source write corruption must preserve an
ordinary terminal green while the independent exact-file oracle turns red.
Mutation sites are selected after reading acquired pinned source; do not
invent an application fault or modify synthetic expectations to make it pass.

First use follows version, public recorder controls, review/replay/save and
ordinary test, with a measured bounded route. Maintenance includes meaningful
suffix rerecording, one manual spec edit, one reviewed named snapshot update,
relocation and a generated-workflow preview. Project-specific fixtures and
oracle expectations belong in this package; core Go code stays generic.

Admission is pending all of the above, native repetitions and actual owned
source/runtime deletion. No acceptance or coverage claim is made by this plan.
