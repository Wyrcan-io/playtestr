# Hygen first useful route

The starting point is an owned installation of pinned Hygen 6.2.11, a prepared trusted local Enquirer/EJS fixture, and the exact extracted provisional Playtestr archive. Prerequisite setup is measured separately. No global install or runtime template download is used.

The fixture has an explicit `.hygen.js` exporting an empty configuration, a prompt asking `Message for file?`, an EJS template writing `generated/hello.txt`, and a binary preservation sentinel. The prompt and template are reviewed executable inputs.

Check Playtestr's version. Start public `record` with the fixture, temporary home/temp and a 100 by 28 viewport, launching `hygen welcome new`. Observe the question, type `reviewed`, observe that input, and capture snapshot row one while the prompt is live. Submit Enter, observe `added: generated/hello.txt`, and require exact exit zero. Capture the five generated/preserved files and five complete directory entry sets; review, replay and save. Run the exported spec with ordinary `test`.

The revised route uses three shell invocations and twenty recorder controls. The generated file must be exactly `Hello, reviewed!\n`; all four original fixture files remain byte exact. The explicit snapshot row covers the interactive prompt and input; file assertions separately prove the generated output. This is not a claim that a live snapshot can be captured after this short CLI has exited.

Local Windows walkthrough b62a8a7ad7a841328c5abbe9633ca23d passes with the frozen Windows archive. Initial nineteen-control capture a052a726b2cf467c8be4b170b5b95c1b refuses its post-exit live snapshot and is preserved; it earns no completed first-use credit. Linux/macOS native execution remains open. The operator knows the source and uses warm prerequisites; human completion time and participant usability remain unmeasured.
