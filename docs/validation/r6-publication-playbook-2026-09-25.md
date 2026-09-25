# R6 publication and verification playbook

Status: commands reviewed but **not executed**. Run only after a new explicit
R6-P authorization and a final remote novelty check.

## Publication

From a clean checkout, verify `release/candidate-manifest.json`, download the
three artifacts from build run 36103641387, and compare all hashes. Then:

```powershell
git fetch origin --tags
git ls-remote --tags origin v0.4.0-rc.1
gh release view v0.4.0-rc.1
git tag -a v0.4.0-rc.1 f6ffeb76a7ec3b826052690ab53071dcdf0e565f -m "Playtestr v0.4.0-rc.1"
git push origin refs/tags/v0.4.0-rc.1
gh release create v0.4.0-rc.1 --prerelease --verify-tag --title "Playtestr v0.4.0-rc.1" --notes-file docs/releases/v0.4.0-rc.1.md playtestr_0.4.0-rc.1_darwin_arm64.tar.gz playtestr_0.4.0-rc.1_linux_amd64.tar.gz playtestr_0.4.0-rc.1_windows_amd64.zip release/checksums-v0.4.0-rc.1.txt
```

The immutable setup-action revision candidate is the final release-kit commit
recorded in the R6-K evidence. Consumers must pin that full commit separately
from `runner-version: v0.4.0-rc.1`. Do not create or move a marketplace tag as
part of runner publication unless separately authorized and verified.

## Post-publication verification

```powershell
gh release view v0.4.0-rc.1 --json tagName,isPrerelease,assets,url
gh release download v0.4.0-rc.1 --dir "public verification"
Get-FileHash "public verification\playtestr_0.4.0-rc.1_windows_amd64.zip" -Algorithm SHA256
```

On Linux/macOS use `sha256sum`; on macOS `shasum -a 256` is also acceptable.
For each native host, extract to a new path containing spaces, verify the
archive and executable hashes, run `playtestr version`, an unchanged pass,
intended failure (exit 1), recovery, cancellation/cleanup, and HTML report
export. Then run the immutable setup action with its exact action commit and
runner pin, confirm PATH/version changes, and repeat the v1 upgrade lane from
public `v0.3.0-rc.1`. Compare public bytes to the candidate; any mismatch stops
R6-V. Verify deployed nested routes, refresh, downloads, schemas, search, 404,
and report controls only after separately authorized deployment.
