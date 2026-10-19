# Rclone scenario review, revision 5

Run 39325883832 at 030c2c6 completed successfully on Linux, including all
twenty authored cases and the full directory suite. Windows passed nineteen
cases; E12 alone failed. N08 now passes with the reviewed contextual prompts.
There is still no two-host freeze or Rclone admission.

Windows E12 again saved the correct full name but displayed the preceding
input at both immediate post-resize checkpoints, even with successful public
redraw waits. This disproves the proposed settling-only correction. The
precise target/backend cause remains unproven. This path remains a recorded
compatibility risk; no production fix is claimed.

Revision 5 declares one additional discriminating native variation: after
typing each post-resize marker, send the supported `ArrowRight` key at the end
of the line, then require the original complete Unicode marker. This tests
whether an explicit navigation event refreshes the line editor. It introduces
no sleeps, retries, deadline increases or weaker saved-byte checks. Linux
keeps its passing sequence. A passing variation would qualify only that
explicit sequence, not immediate character echo without navigation.

`scenario-declaration-v5.json` precedes execution. If this variation also fails,
stop repeating this immediate-echo hypothesis and retain an unresolved
disposition before choosing any different, explicitly scoped resize scenario.
Production Go and the frozen private candidate remain unchanged. Source
fault selection is still gated on the complete audited two-host freeze.
