# Original Copier migration

The original MIT pin is `04a8619f3b083bc278b70e556bd085551a2b3f79`,
version 9.18.2. Twelve original scenarios are prepared for each previously
qualified native host, Windows and Linux. Preparation earns no migration credit.

Strict extraction initially rejected three documentation aliases and one
upstream test-only symlink (`00e63a45d1a04b98add26b75b73075e1`). Their exact
targets and the original archive are preserved in the acquisition review;
reviewed extraction omits those four entries without creating or following links.
All regular runtime source bytes remain original.

The reviewed packaging backend is pinned hatchling/hatch-vcs, without a custom
build hook. Runtime dependencies retain the original pinned constraints.
The initial owned editable install failed because the GitHub source archive
has no Git version metadata (`2a3bbcc8c36741a4aecc9598452b402a`). Inspection
of the installed hatch-vcs adapter showed it calls `setuptools_scm.get_version`
without a distribution name, so its package-specific version override does not
apply. The resumed build sets `SETUPTOOLS_SCM_PRETEND_VERSION=9.18.2` only in
the build subprocess environment. That version matches both the original
qualification and the pinned source's commitizen metadata. Original source
files remain unchanged; an actual module/CLI probe must still verify installation.

Only original local synthetic templates and Git fixtures are in scope. The one
reviewed trusted task writes `task-marker.txt` under its managed project.
No remote template, user configuration or arbitrary extension is tested.
Public same-execution migration, real writer corruption/recovery, independent
native audits and checked cleanup remain required before admission.

The first actual Windows suite passed ten of twelve cases; both Git update
cases exited before their first prompt because the preparation package lacked
the original synthetic Git repositories (`3810d94cc1dc4fefb72d223b7cb1f1f2`).
The original archive `synthetic-git-metadata.tar.gz` is hash-checked and its
130 regular members restored into each fresh execution copy. Four exact local
Git configurations and sample-only hooks are checked before writing anything.
Original working files, actions, snapshots and saved-state expectations remain
unchanged. Two restoration regressions pass, including refusing an existing
metadata destination before writing other files. The first failed suite stays
retained and counts in the observed execution denominator.
