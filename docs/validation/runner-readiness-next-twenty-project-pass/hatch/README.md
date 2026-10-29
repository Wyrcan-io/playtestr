# Hatch source review

Status: source only; no dependency installation, build or target execution yet.
The originally screened metadata-only reserve replaces PDM under the
[explicit substitution](../substitution-pdm-hatch-v1.json); PDM's complete
engineering observations and historical loss remain separately retained.

Pinned `pypa/hatch` source `ad6d66e7c5dba7deea7601e50072676defae8b3e`, MIT.
Acquisition retained721 archive entries/8,239,971 expanded bytes. All546 primary
Git file blobs and modes were verified. These are source-provenance observations,
not execution approval or native compatibility credit.

Proposed scope: built-in interactive project creation and existing-project
metadata updates, with exact generated/preserved file state on Windows and Linux.
Review actual source/backend/dependency hooks before any execution. The ordinary
backend is hatchling plus hatch-vcs; its generated `src/hatch/_version.py` needs
an explicit pin-derived archive-source build version and separate generated-file
provenance rather than a fabricated primary Git blob.

The default template downloads SPDX license text on cache misses and inserts the
current UTC year into some license text/headers. Select an explicit documented
owned configuration that disables generated licenses for the first deterministic
no-network workflow. Any later license-specific case needs a separately reviewed
owned cache and explicit date scope. Existing setuptools migration creates a
temporary venv and installs setuptools; exclude that route from this synthetic
project-generation scope. External templates/plugins, publishing, environment
creation, Python downloads and external services require separate source review
and are not approved by acquiring this source.

Local-only owned source: `artifacts/runner-readiness-next-twenty-project-pass/active/hatch/`.
No project admission or target execution credit is claimed.
