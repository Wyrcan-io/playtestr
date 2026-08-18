# Contributing to Playtestr

## Before opening a pull request

Run:

```sh
npm ci
npm run typecheck
npm test
npm run build
```

If the change affects PTY behavior, include a fixture or integration test and run `npm run soak` on the affected platform. If it affects reports or replays, update the schema version or document why compatibility is preserved.

## Pull requests

Explain the user-facing behavior, safety implications, and verification performed. Keep autonomous policies bounded and make new behavior observable through reports or artifacts.
