# Sanitized R3c trial recipes

These recipes reproduce the shape of the September 2026 R3c campaign without publishing local paths or raw terminal captures. Pin the listed application release, verify its official package/archive checksum, install it in a trial-owned directory, and use the downloaded Playtestr binary. Commands are executed directly, not through a shell unless the target itself explicitly accepts a source command.

For every recipe:

1. Create separate `install`, `config`, `fixture`, and `attempt` directories under a disposable root.
2. Run the task manually in a real terminal and record the keys and clean-exit behavior.
3. Run a 5–20 step Playtestr spec with positive readiness after input, an exact exit assertion, and an independent oracle.
4. Copy/reset only the controlled fixture; run good three times, bad once, restored once, cancel/invalid once, and a fresh second session.
5. Start one more good run, wait for Playtestr to print the first passed readiness step, interrupt the runner, and require exit 130, `cancelled`, and `cleanup.confirmed_exited=true`.
6. Keep each attempt's report and oracle separate. Do not turn retries into the primary denominator.

| ID | Minimal setup and actions | Independent oracle | Controlled fault |
| --- | --- | --- | --- |
| PY-01 Posting 2.10.0 | Virtual environment; private config/collection; loopback HTTP server; open GET, submit fixture URL, inspect body, resize, Ctrl+C | Match exact request in the server access log and exact marker in the served file; [PowerShell oracle](../../scripts/trials/oracles/check-http-get.ps1) | Serve a marker-free JSON file |
| PY-02 litecli 1.17.1 | Virtual environment; baseline SQLite DB; insert/query Unicode row, ArrowUp, Ctrl+C, `\\q` | Query exact row and unchanged neighbor using Python's `sqlite3` | Start from a DB without the expected table |
| PY-03 mitmproxy 12.2.3 | Virtual environment; generate one mitmproxy flow; run `mitmproxy --no-server --rfile <flow>`; open request/response, resize, quit | Parse exact URL, header, and response body with `mitmproxy.io.FlowReader`; compare file hash | Load a flow containing a different marker |
| RS-01 bottom 0.14.9 | Pinned binary; start a uniquely named trial helper; search, accept, help/Escape, resize, quit | Verify helper PID resolves to the exact trial executable and remains alive; compare executable hash | Do not start the helper |
| RS-02 GitUI 0.28.1 | Pinned binary; disposable Git repo in a path with spaces; edit one Unicode file; stage it, quit | `git diff --cached --name-only` and `git show :path`; neighbor hash unchanged | Remove the selected edit from the reset fixture |
| RS-03 television 0.15.9 | Pinned binary; three-line candidates file; source-command reads only that file; filter Unicode marker, Enter | Capture exact selected stdout; candidates hash unchanged | Replace candidates with marker-free content |
| JS-01 npkill 0.12.2 | Inspect npm scripts, install locally with lifecycle scripts disabled; two tiny trees; run with update checks off and dry-run on; navigate/cancel | Marker and neighbor hashes remain exact | Rename selected `node_modules` |
| JS-02 create-vite 9.2.1 | Inspect/install local npm tarball; empty workspace; select Vanilla/JavaScript | Parse `package.json`, check exact expected manifest and absence of unrelated files | Rename the selected template directory |
| JS-03 ipm-cli 1.3.3 | Inspect/install local npm tarball; empty workspace; enter name, invalid `9`, theme, dark | Parse generated `package.json`; hash/list the three CSS files | Rename the theme template directory |

Full-screen specs use resize followed immediately by `wait_for_redraw`, then a fresh positive assertion. Prompt specs use an edit/history/validation action and Unicode when the target accepts it. `expect_not` is used only after the text was positively observed and input or resize could remove it.

Application cancellation and runner cancellation are different scenarios. Application cancellation must prove no unintended state change. Runner cancellation starts only after readiness and checks both the structured result and descendant cleanup. External fixtures such as HTTP servers or oracle helper processes are owned and stopped by the harness after evidence capture; Playtestr cleanup must not be credited for stopping them.
