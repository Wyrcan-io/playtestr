# Commitizen: source/dependency review

Canonical repository `commitizen-tools/commitizen`, MIT, pinned at
`b78d581f7e3089fa40bcd4794591fd56b43b671a`. Exact Git tree verification found
398 regular source blobs (439 archive entries including directories).

Useful first workflow: initialize a synthetic project configuration through the
real questionary prompts, accept reviewed defaults, assert the completion and
exact zero exit, then independently check the complete saved `.cz.toml` bytes.
The predeclared first window allows five invocations/twenty controls; planned
route is seven prompt/readiness + Enter pairs and six completion/approval controls.
No Playtestr JSON is supplied before public record/review/replay/export.

The fixture includes a deliberately minimal empty Git repository so read-only
version discovery cannot escape into Playtestr's ancestor repository. Its exact
HEAD/config bytes and empty refs/objects directories are reconstructed explicitly
before each fresh-host preparation and bound before target launch; Git never
commits, tags, installs hooks or contacts services. Global/system Git configuration
is disabled and PATH contains only the declared Git/system prerequisite locations.
No pre-commit/prek tool is installed. State oracles also preserve unrelated files.

The declared uv_build backend includes uv-build.exe in its wheel. The initial
wheel review stopped before installation; its Python shim and exact script hash
were reviewed, then existing downloaded wheels were reviewed without redownload.
Primary PyPI digest checks verify all sixteen wheels before any offline backend
execution. All target dependencies, source and venvs remain in owned campaign
paths. No project or native coverage credit exists yet.
