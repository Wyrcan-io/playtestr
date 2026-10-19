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

Native Linux execution, independent cell audits and checked retention/cleanup
remain required before project migration credit. These old-project checks add
no new-project, held-out-fault or final-archive credit.
