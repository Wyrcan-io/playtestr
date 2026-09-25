# Qualified compatibility for v0.4.0-rc.1

Compatibility here means an exact pinned application/version/workflow/host
combination produced the expected terminal and independent state evidence. It
does not certify a language, TUI framework, project, or newer version as a
whole.

| Project | Pinned version | Windows matrix | Native Linux/macOS campaign |
| --- | --- | --- | --- |
| Charm Gum | v0.17.0 | GUM-01…08 | GUM-01, GUM-04, GUM-05 |
| Lazygit | v0.65.0 | LG-01…08 | LG-01, LG-04 |
| fzf | v0.74.4 | FZF-01…08 | Not run |
| Posting | 2.10.0 | POST-01…08 | Not run |
| litecli | 1.17.1 | LITE-01…08 | Not run |
| mitmproxy/mitmconsole | 12.2.3 | MITM-01…08 | Not run |
| bottom | 0.14.9 | BT-01…08 | BT-06 |
| GitUI | 0.28.1 | GUI-01…08 | Not run |
| television | 0.15.9 | TV-01…08 | Not run |
| npkill | 0.12.2 | NPK-01…08 | Not run |
| create-vite | 9.2.1 | CV-01…08 | CV-01, CV-06 |
| ipm-cli | 1.3.3 | IPM-01…08 | Not run |
| micro | v2.0.14 | MICRO-01…08 | MICRO-01, MICRO-05 |
| tig | tig-2.6.1 | TIG-01…08 via WSL target | Not native; WSL only |
| taskwarrior-tui | v0.27.0 | TASK-01…08 via WSL target | Not native; WSL only |

The 120-workflow pass used the native Windows candidate runner. The `tig` and
`taskwarrior-tui` target processes were intentionally WSL Linux programs, so
those rows are not native Windows application claims. The 3,000-execution
campaign used native candidate runners and native builds of the ten selected
workflows on Windows amd64, Linux amd64, and macOS arm64. All unlisted host/app
cells remain unavailable or unsupported, not inferred from portable tests.

Framework unit tests and Playtestr E2E tests answer different questions. A
framework test can cheaply validate widgets and application logic without a
real terminal. Playtestr launches the built program in a PTY and checks actual
keyboard input, redraws, exit behavior, cleanup, reports, and external state.
Use both: unit tests localize logic faults; a small E2E set catches integration
failures at the user-visible boundary.

See the [qualification record](validation/sprint-11-c-r6-q-2026-09-25.md) for
attempt counts, controls, transients, resource measurements, and exclusions.
