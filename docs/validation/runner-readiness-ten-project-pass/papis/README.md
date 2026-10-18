# Papis development qualification

The frozen Linux and Windows profiles retain exact native byte expectations.
Python text-mode writes produce their explicitly declared native line endings;
file copies preserve the original bytes.

E10 uses a synthetic library containing no document entries. Git cannot store its
empty directory. Before running a profile copied from this checkout, create
`fixtures/E10/library` inside that profile's `contracts` directory. For example,
PowerShell users can run `New-Item -ItemType Directory -Force fixtures/E10/library`
from the selected contracts directory. This is fixture setup, not an assertion or
an expected-output update. The native preparation helper performs exactly this
declared operation, including in the generated workflow's build step.

The first hosted transfer omitted that setup and failed E10 on both hosts. Its
reports remain retained. No frozen action, expected file or source fault changed.
Development admission is complete on Linux and Windows at source f46f240.
Run 39099744836 verifies twenty frozen scenarios, four actual source faults,
twelve-command maintenance and cleanup on both hosts. Only its initial Linux
F04 extra-file fault is current-source heldout; older local dev-binary results
are historical and excluded. Both native archive generations and local source
retention/removal are checked. Final candidate archives remain unqualified.
Human usability remains unmeasured.
