"""Cancel an extracted Playtestr binary and verify its machine evidence."""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path


def fail(message, process=None):
    if process is not None and process.poll() is None:
        process.kill()
        process.wait(timeout=10)
    raise SystemExit(message)


if len(sys.argv) != 4:
    raise SystemExit("usage: release-cancel-smoke.py PLAYTESTR FIXTURE OUTPUT-DIR")

runner = Path(sys.argv[1]).resolve()
fixture = Path(sys.argv[2]).resolve()
output = Path(sys.argv[3]).resolve()
output.mkdir(parents=True, exist_ok=True)
spec_path = output / "cancellation.json"
report_path = output / "release-cancellation.json"
console_path = output / "release-cancellation-output.txt"
spec_path.write_text(
    json.dumps(
        {
            "version": 1,
            "name": "extracted binary cancellation",
            "command": [str(fixture), "hang"],
            "timeout_ms": 30000,
            "run_timeout_ms": 60000,
            "steps": [
                {"expect": "fixture ready; waiting forever"},
                {"expect": "this text never appears"},
            ],
        }
    ),
    encoding="utf-8",
)

creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0
with console_path.open("w+", encoding="utf-8") as console:
    process = subprocess.Popen(
        [str(runner), "test", "--report", str(report_path), str(spec_path)],
        stdout=console,
        stderr=subprocess.STDOUT,
        creationflags=creation_flags,
    )
    deadline = time.monotonic() + 30
    while time.monotonic() < deadline:
        console.flush()
        console.seek(0)
        if "PASS step 1" in console.read():
            break
        if process.poll() is not None:
            fail(f"runner exited before cancellation readiness: {process.returncode}")
        time.sleep(0.05)
    else:
        fail("cancellation readiness deadline exceeded", process)

    if os.name == "nt":
        process.send_signal(signal.CTRL_BREAK_EVENT)
    else:
        process.send_signal(signal.SIGINT)
    try:
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        fail("runner did not stop after cancellation", process)

if process.returncode != 130:
    fail(f"cancellation returned {process.returncode}, expected 130")
document = json.loads(report_path.read_text(encoding="utf-8-sig"))
result = document["results"][0]
if document["summary"]["cancelled"] != 1:
    fail("cancellation report summary is not cancelled=1")
if result["status"] != "cancelled":
    fail(f"cancellation status is {result['status']!r}")
if result["failure"]["category"] != "cancelled":
    fail(f"cancellation category is {result['failure']['category']!r}")
if result["cleanup"]["confirmed_exited"] is not True:
    fail("cancellation did not confirm target cleanup")

print("extracted binary cancellation passed: exit=130 cleanup=confirmed")
