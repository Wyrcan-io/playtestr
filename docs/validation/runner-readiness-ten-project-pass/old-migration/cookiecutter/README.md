# Original Cookiecutter migration

The original pin is `c88fbe921c97c58b65f1883ba90a0ab53cc91b34`, version 2.7.1.
Source, license, static setuptools packaging, original dependency constraints
and the one local synthetic Python hook were reviewed before installation.
The four documentation symlinks are explicitly omitted from extraction; the
original archive and exact link metadata remain preserved. No link is followed
or created, and runtime package bytes remain exact.

The owned Windows venv uses the original pinned runtime dependencies plus
explicit pinned packaging wheels. All ten original Windows cases passed on
the frozen private rc.4 runner with appended public saved-state assertions.
The original terminal-only contract also passed with a real corrupted writer;
the v3 contract rejected its wrong bytes after a passing snapshot and exit0,
then passed after exact source restoration. No contract or snapshot was
weakened to obtain those outcomes.

Execution copies add only `PYTHONDONTWRITEBYTECODE=1`, preventing target imports
from writing cache files into the installed base Python. Original commands,
input/screen/exit steps, fixtures and snapshots remain unchanged. Selection
names the ten declared specs explicitly: the initial directory listing also
selected six JSON template-data files and was stopped before target launch.
That preparation failure remains retained.

Native Linux run `39336792124` and local Windows both passed all ten migrated
cases, the terminal-only false-green calibration, saved corruption rejection
and exact restoration. Independent [Windows](verified-windows.json) and
[Linux](verified-linux.json) audits bind actual public commands, frozen runner
bytes, original contracts, same-execution state and checked cleanup.
The [migration admission](migration-admission.json) records one old project,
ten canonical scenarios and two native cells. Its 39 observed ordinary
executions include the first Linux run whose tests passed but cleanup failed
because the retention helper rejected the legacy v2 calibration report.
The corrected helper validates both report versions; the original failed run
remains archived. Both native packets are verified locally retained archives,
and the expanded packets and owned local source/runtime have been removed.
These old-project checks add no new-project, held-out-fault or final-archive credit.
