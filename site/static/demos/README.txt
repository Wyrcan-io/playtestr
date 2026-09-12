Playtestr website demonstration provenance

The passing and intentional-failure states in terminal-demo.json correspond to
the repository's examples/menu.json, examples/snapshot-mismatch.json, demo
target, and reviewed diagnostics.txt baseline at source revision 26fbda8.

On Windows amd64, a local runner built from that source produced all six passing
menu steps. The intentional mismatch produced three passing steps, a
snapshot_mismatch at step 4, exit status 1, the actual screen stored in the JSON,
and the stored unified diff. Intermediate screens follow the deterministic demo
target's rendered output at each authored input. UI explanations and step
highlights are website annotations, not runner output.

The browser does not run a PTY or arbitrary commands. The data is a bounded,
sanitized demonstration of repository fixtures.
