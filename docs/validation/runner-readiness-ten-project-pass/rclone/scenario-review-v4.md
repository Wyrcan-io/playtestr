# Rclone scenario review, revision 4

Run 39292483755 at 15c151e passed 19/20 authored cases on Linux and
18/20 on Windows. It is a failed workflow, with no full-suite freeze or
admission. First-use, actual native builds and checked source/runtime cleanup
passed on both hosts and were independently audited separately.

N08 reached the corrected alias-value prompt on both hosts, but its later
advanced and Keep captions were still visible from the first review. The
recorder rejected both stale captions and refused export. Revision 4 applies
the same public multiline editing and fresh-prefix reconstruction to those
two checkpoints, binding them to the newly entered and displayed alias path.
It retains the review-loop behavior and exact saved-byte oracle.

Windows E12 retained the correct saved name `café 雪AB`, but the expected
post-resize marker was absent at each checkpoint: the first screen still
showed the old name and the next showed only the preceding marker. The
original timeouts and refused export remain failures. Revision 4 uses the
documented public `/redraw` immediately after each Windows resize before
sending the next character. This requires observed output and a bounded
redraw window; the original positive character checks remain unchanged.
Linux retains its previously passing sequence. This is a synchronization
correction under investigation, not a demonstrated production runner fix.

All twenty risks, initial fixtures and expected saved bytes remain unchanged.
`scenario-declaration-v4.json` is recorded before the fresh native execution.
No production Go or frozen candidate bytes changed, and no source fault has
been selected. Revision 3 and its failures remain retained.
