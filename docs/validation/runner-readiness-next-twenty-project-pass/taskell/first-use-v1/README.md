# Taskell first-use attempt v1

This small synthetic board exercises the documented `taskell filename.md`
route and default Space completion key. The spec requires visible readiness,
then compares the same-run rendered task operation with exact Markdown bytes
before and after clean exit. Home and temp are managed by Playtestr; no network
import, credential, release helper, or existing user data is involved.

This is an initial reviewed candidate case, not a frozen campaign scenario or
passed result. Its assumptions still need to be checked on the actual built
native executable. Preserve any first mismatch or timeout before changing the
contract. Do not infer column placement from a screen that only contains the
task text; the exact saved bytes are the independent state oracle.
