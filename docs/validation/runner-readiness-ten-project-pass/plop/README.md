# Plop development journey

Status: declared, not admitted. Canonical source [plopjs/plop at
0c90e7ef93ffa5f40b10fe8f53d3cc23adee5a8e](https://github.com/plopjs/plop/tree/0c90e7ef93ffa5f40b10fe8f53d3cc23adee5a8e).
MIT license text (copyright Andrew Worcester, 2014) and package declarations
reviewed before dependency installation. Node 24.7.0 is an installed prerequisite.

The CLI uses Inquirer and Handlebars. Synthetic generators are its documented
user configuration, not replacement applications. Intended outcomes include
single/multiple file generation, injection/modification, optional generation,
existing-file preservation and precise partial-failure state. No generator
executes shell actions or accesses a network service.

Owned active root: campaign `active/plop`. Before installation the active-target
forecast was revised from 512 MiB to 1.5 GiB to retain the upstream pinned Yarn
workspace lock (including development resolution) instead of resolving a new
npm lock. Acquisition
archive at most 8 MiB and extracted source at most 64 MiB/10,000 entries. Review
actual manifests before dependency installation. Root `prepare: husky` and
package publish/test hooks will not execute. The bundled Yarn 4.9.4 uses
`install --immutable --mode=skip-build` with `YARN_ENABLE_SCRIPTS=false`, owned
package cache/home/temp/config and no global installation. Periodic storage
observations stop growth at 3 GiB before the active 4 GiB cap. These observations
are not a quota or exact peak measurement. Standard Node launchers resolve their
script relative to the launcher; no target output is intercepted or synthesized.

First dependency attempt failed before resolution because the harness supplied
`skip-builds` instead of Yarn 4.9.4's `skip-build`. The original failed attempt
`c58a7c1fa52640b6859c8674f0fb472e` and its parent remain local evidence. The
[Yarn install contract](https://yarnpkg.com/cli/install) and bundled CLI diagnosed
the typo; this is a setup/harness correction, not a Playtestr repair.

Proposed native cells Linux amd64 and Windows amd64 remain unqualified. Twenty
meaningful scenarios and three source faults must be declared/reviewed before
authoring. No project count or timing claim follows from this declaration.
