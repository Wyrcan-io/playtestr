# Runner readiness continuation checkpoint v181

## Campaign status

The campaign remains at **18/30 cumulative admissions**, with **2/20 new
packages** admitted (JOE and fzy). Percol remains in progress with zero admission
credit. The exact candidate is `v0.4.0-rc.8` (`native-exit-v3`).

## Percol development attempt v8

Run `43386753118` reached E07 on both Linux amd64 and macOS arm64 after N01–N08
and E01–E06 passed. The E07 screen filtered lowercase `blue` to one visible
result, and the target exited 0. Both exact output assertions rejected the bytes.
The harness-owned PTY dump shows `42 6c 75 65 0a` (`Blue\n`), the first source
candidate, despite the displayed 1/1 lowercase result. Provider artifact digests
match both downloaded ZIPs. Process cleanup, workspace cleanup, source/runtime
cleanup and storage checks passed on both hosts. No admission credit is earned.
See `percol/development-attempt-v8.json` and `percol/unsupported-controls-v3.json`.

## Next action

Preserve v8. V9 changes E07 into an explicit limitation characterization: require
the lowercase `1/1` screen but expect the exactly observed `Blue\n` output. This
prevents an unsupported selection claim while allowing the broader Percol
workflow suite to continue. Run the complete suite on both hosted native
platforms and preserve each result.
