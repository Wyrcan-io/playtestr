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
Full admission remains pending independent native fault/maintenance verification,
retention and checked local removal. Human usability remains unmeasured.
