# User discovery and product direction

Status: discovery proposal, 17 November 2026. No outreach has been sent and no
participant evidence is claimed.

## Decision

Pause the next-project qualification campaign at **18 cumulative admissions**.
Two of the next twenty packages are admitted; Percol was explored but did not
complete admission and receives no credit. Preserve its failures and evidence,
but do not spend more engineering time on that target until user research shows
that broader project qualification is the highest-value next step.

The next product decision should come from observed author behavior. Do not start
a hosted dashboard, paid GitHub App, or large new compatibility campaign yet.
First find out whether the current local runner, recorder, report, and CI path
solve a real repeated problem for maintainers.

## Product hypothesis to test

For maintainers of interactive command-line applications, Playtestr lets them
record one important keyboard workflow, review the generated test, and catch a
visible or saved-state regression on a pull request. The maintainer decides what
behavior is correct. Playtestr runs the reviewed contract and reports the
captured screen, state, exit, and cleanup evidence.

The early product should remain a local Go runner plus ordinary customer-owned
CI. Existing terminal tools already automate or record terminal sessions;
Playtestr must earn its place through repeatable regression assertions,
reviewable state oracles, bounded failure evidence, and a low-friction authoring
path. Charmbracelet VHS presents itself as a terminal-session recorder for
shareable output and CI recording, while Playwright's documentation illustrates
the more mature pattern of guided assertions, fixtures, and useful diagnostics.
These are references for adjacent workflows, not claims that they are direct
competitors or that users want Playtestr's proposed paid features.

## Who to learn from first

Start with people who own a CLI/TUI and are responsible for keeping its behavior
stable:

1. Maintainers of actively developed Go, Rust, Python, and Node command-line or
   terminal applications.
2. Engineers on developer-tools or infrastructure teams whose internal tools
   prompt, redraw, update files, or run in CI.
3. Contributors who currently use shell scripts, snapshots, PTY libraries, VHS,
   Expect, or hand-written fixtures to test an interactive flow.

Prefer a mix of solo maintainers and small teams. Screen for an actual recurring
workflow and recent change pressure, not repository popularity alone. Do not
assume every CLI is interactive or needs a PTY regression tool.

## Two-week discovery loop

Recruit a small first cohort of 8–12 people through channels the founder is
permitted to use. Ask for a short research conversation, not a purchase or an
endorsement. Use the same neutral questions with each person:

- Show me the last time a CLI/TUI change broke behavior or surprised a user.
- How did you find it, and what did the existing test miss?
- Show me how you currently test that workflow, including the slow or awkward
  parts.
- What does a useful failure report need to contain for you to fix it?
- Which state changes matter beyond text on screen: files, exit codes, data,
  environment, or process cleanup?
- How often does this workflow change, who reviews expected behavior, and what
  would make the test too brittle to keep?
- If we set up one test together, what would you expect to do next week without
  help?

Do not lead with the product pitch. Ask permission before recording a call or
retaining a repository, transcript, screen capture, or other personal data. Use
synthetic fixtures unless the participant explicitly supplies a safe target.
Never run a target the participant has not approved; Playtestr is not a sandbox.

After the interview, offer an optional 20–30 minute task using the participant's
own approved CLI or a small synthetic example. Observe silently while they
install the binary, author or record one workflow, decide whether assertions are
correct, run it, diagnose one deliberate failure, and update a reviewed
expectation. Do not coach unless asked. Record task completion, time, wrong
turns, help requests, and the participant's own explanation of the failure.
Separate observed behavior from opinions and inferred needs.

For every session, capture only consented, de-identified notes: role/context,
current workaround, frequency/severity, exact friction, completion outcome,
quotes only if separately approved, and a confidence label. Do not publish
names, repositories, recordings, or quotes without separate permission.

## Decisions after discovery

Review evidence after the first five sessions and again at twelve. Stop or change
direction if the problem is rare, current alternatives are good enough, or
participants will not maintain reviewed tests. Continue only if several people
independently describe a recurring failure cost and can complete the setup task.

Use these decision gates:

- **Authoring:** Can a first-time user get a meaningful test without learning
  the whole spec? If not, improve the recorder, starter template, or a small
  local guided setup before building a web interface.
- **Trust:** Do users understand what target commands execute, what evidence is
  saved, and why a run passed or failed? Confusion here blocks expansion.
- **Retention:** Do participants rerun and maintain the test after the session?
  A one-time demo does not establish ongoing value.
- **Distribution:** Do users naturally want a GitHub check, downloadable report,
  or team review policy? Build only the integration supported by observed use.
- **Payment:** Ask about budget and current spending only after the workflow is
  understood. Do not infer willingness to pay from compliments or hypothetical
  price questions.

## Product surface recommendation

Treat the first user interface as the **authoring and failure-recovery path**,
not a web dashboard. The current command-line product should make the first
success and the first useful failure obvious. Test this with real users before
choosing between improved CLI guidance, a local terminal wizard, or a separate
visual editor. Keep authored tests as ordinary reviewable files and keep local
execution useful without a service account.

Only consider a hosted review surface after users repeatedly ask for shared
baseline approval, policy, or history that ordinary CI artifacts do not solve.
The existing roadmap's paid App remains a separate later hypothesis, not the
default next milestone.

## Outreach boundary

This document is private preparation. It does not authorize contacting named
maintainers, posting in communities, opening issues, sending invitations, or
recruiting participants. Before any specific outreach, choose the exact people
or channel, message, purpose, and data requested, then get authorization for
that action. Respect community rules and do not turn bug reports or support
requests into unsolicited sales pitches.

## Measures and evidence

Keep discovery counts separate from the 18 project admissions. Report invitations
sent, replies, sessions completed, consented tasks, task completion, time to first
passing test, independent reruns, recurring pain patterns, contrary evidence,
and participant requests. A session or repository used for research is not a
runner-readiness admission. Do not publish compatibility, usability, demand, or
revenue claims from this small qualitative sample.

## References

- [Charmbracelet VHS](https://github.com/charmbracelet/vhs): terminal recording
  and shareable/CI output workflow.
- [Playwright test fixtures](https://playwright.dev/docs/test-fixtures):
  examples of composable test setup and teardown.
- [Playwright test assertions](https://playwright.dev/docs/writing-tests):
  examples of readable assertions and diagnostics.
- [Playtestr validation evidence policy](../validation/README.md): local-only
  raw evidence, retained failure identities, and limits on public claims.
