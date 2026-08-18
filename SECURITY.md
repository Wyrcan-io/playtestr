# Security policy

Report suspected command-execution, sandbox-escape, environment-leakage, dependency, or artifact-exposure vulnerabilities privately through GitHub's security advisory channel. Do not put secrets, private target code, or exploit details in a public issue.

## Current trust boundary

Playtestr is pre-alpha and has no sandbox backend. The local PTY runner executes a target with the invoking user's filesystem, process, and network permissions. Environment filtering prevents accidental inheritance of many credentials, but it does not make an untrusted program safe.

Only run targets you trust. The CLI requires explicit acknowledgement of this boundary. Do not expose the current runner as a public upload service.

See [docs/operations/security.md](docs/operations/security.md) for the controls required before untrusted or hosted execution.
