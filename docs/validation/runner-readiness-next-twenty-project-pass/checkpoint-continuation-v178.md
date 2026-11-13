# Runner readiness continuation checkpoint v178

## Cumulative status

The ledger remains **18/30 admissions**, with **2/20 new project packages**
admitted (JOE and fzy). Percol is at zero. The exact runner candidate is
`v0.4.0-rc.8` (`native-exit-v3`).

## Percol development attempt v5

Run `43383160597` passed N01 through N08 and E01 through E04 on both Linux amd64
and macOS arm64. E05's dynamic unmatched-query cancellation failed on both:
the UI showed the unmatched query, the runner accepted Ctrl-C input, but the
target did not exit within 20 seconds. The target later exited with code 1 during
bounded runner cleanup. Scenario workspaces and process groups were confirmed
clean. Exact source/runtime removal and storage limits passed on both hosts.
Provider digests match both downloaded ZIPs. Details are preserved in
`percol/development-attempt-v5.json`; partial cases earn no final-series or
admission credit.

## Current v6 correction

V5 remains preserved. V6 keeps empty candidate input but supplies the unmatched
query with `--query=missing` at process start. It positively checks the rendered
query before sending Ctrl-C, avoiding the asynchronous query-edit debounce at
the cancellation boundary. V6 is materialized and verifies locally; it has not
launched. Focused tests must be rerun before committing v5 evidence and v6.

The previous development job is complete. No local target runtime, owned PID or
mounted volume remains; all downloaded failed-attempt ZIPs are local-only under
the ignored campaign `retained/` directory.
