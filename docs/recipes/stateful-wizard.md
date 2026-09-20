# Stateful wizard: create-vite with a file oracle

Goal: create-vite 9.2.1 creates one Vanilla JavaScript project named
`playtestr-recipe`, while dependency installation and server startup remain
declined. The retained npm tarball SHA-256 is in the
[corpus manifest](https://github.com/Wyrcan-io/playtestr/blob/main/corpus/manifest.json).

## Setup and pass

Obtain and verify the exact tarball first. Install it without lifecycle scripts
into the ignored recipe root, then create an empty owned working directory:

```powershell
$root = '.trial-private\recipes\create-vite'
New-Item -ItemType Directory -Force "$root\runtime", "$root\work" | Out-Null
npm install --ignore-scripts --no-audit --no-fund --cache "$root\npm-cache" --prefix "$root\runtime" <verified-create-vite-9.2.1.tgz>
go run ./cmd/playtestr test examples/recipes/stateful-wizard.json
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/recipes/check-create-vite.ps1 -Root "$root\work\playtestr-recipe" -ExpectedName playtestr-recipe
```

The spec waits after each prompt-changing input. The independent oracle parses
the package, requires the selected template files, and rejects an unexpected
project `node_modules`; the final screen alone cannot prove the scaffold.

## Intentional failure and recovery

Run the same successful screen flow, then prove the harness rejects the wrong
state expectation before returning to the reviewed expectation:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/recipes/check-create-vite.ps1 -Root "$root\work\playtestr-recipe" -ExpectedName wrong-name
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts/recipes/check-create-vite.ps1 -Root "$root\work\playtestr-recipe" -ExpectedName playtestr-recipe
```

The first oracle must fail. Historical pilot evidence additionally removes the
selected template and observes the intended readiness failure before restoring
the pinned package.

Cleanup: resolve the exact `$root\work\playtestr-recipe` path, confirm it is
below the owned recipe root, then remove that project. Do not point this recipe
at an existing application directory.
