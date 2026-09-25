# Frozen-candidate evidence gallery

Status: recorded static evidence for `v0.4.0-rc.1`; publication pending. This
page remains useful without JavaScript, animation, network access, or video.

![Offline Playtestr report showing one failed wrong-selection story, its unexpected-exit category, viewport, and duration](/playtestr/images/release-stories/hero-defect-report.png)

The screenshot was captured without editing from the self-contained HTML
rendered by the frozen Windows candidate. PNG SHA-256:
`d43837b3a2bf1093d56cb8f6dd398391a892a6cf4f450003810a2fbccdc9e0db3`.
The text alternatives below carry the same essential outcome offline and when
images are unavailable.

## Wrong selection

```text
reviewed result: Beta
defective result: Alpha
runner outcome: failed / unexpected_exit / exit 1
cleanup: confirmed_exited
recovery result: Beta
```

## Wrong persisted state

```text
reviewed file: port=4242
defective file: port=8080
adapter exit: 90
runner outcome: failed / unexpected_exit / exit 1
recovery file: port=4242
```

## Stale viewport

```text
requested viewport: 80x20
defective redraw: Size: 60x12
runner outcome: failed / assertion_timeout / exit 1
cleanup: confirmed_exited; no postcondition file accepted
recovery file: size=80x20 modal=false
```

These are compact static excerpts, not invented screenshots. The complete
uncut logs, JSON reports, runner/target/spec hashes, and artifacts are retained
by [cross-host run 36108031093](https://github.com/Wyrcan-io/playtestr/actions/runs/36108031093)
for its configured retention period. Reproduce them from
[`release/stories/run.sh`](https://github.com/Wyrcan-io/playtestr/blob/main/release/stories/run.sh). Exported Playtestr HTML
reports are self-contained and make zero external requests.
