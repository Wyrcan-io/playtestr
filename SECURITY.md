# Security policy

Please do not include secrets or private target code in public issues. For a suspected security issue involving command execution, sandbox escape, environment leakage, or artifact exposure, contact the maintainers privately through the repository’s configured security channel.

Playtestr is not yet a hosted sandbox. The local CLI runs targets with the invoking user’s permissions; do not run untrusted commands until the documented isolation controls are implemented.
