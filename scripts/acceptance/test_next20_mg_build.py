"""Bounded source-build command and process-group cleanup tests for mg."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

from next20_check import RAW, ROOT
from next20_mg_build import MAX_OUTPUT, process_group_members, run_bounded


class MgBuildCommandTests(unittest.TestCase):
    @unittest.skipIf(os.name == "nt", "the native build workflow runs on POSIX hosts")
    def test_successful_command_has_bounded_hashed_output(self):
        RAW.joinpath("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW / "tmp") as td:
            root = Path(td)
            log = root / "ok.log"
            commands = []
            row = run_bounded([sys.executable, "-c", "print('build probe')"],
                              root, dict(os.environ), log, time.monotonic() + 10, commands)
            self.assertEqual(row["exit_code"], 0)
            self.assertIn(log.read_bytes().replace(b"\r\n", b"\n"),
                          (b"build probe\n",))
            self.assertEqual(row["output_bytes"], log.stat().st_size)
            self.assertEqual(row["log"], log.relative_to(ROOT).as_posix())
            self.assertEqual(len(commands), 1)

    @unittest.skipIf(os.name == "nt", "the native build workflow runs on POSIX hosts")
    def test_timeout_terminates_owned_descendant_process_group(self):
        RAW.joinpath("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW / "tmp") as td:
            root = Path(td)
            log = root / "timeout.log"
            commands = []
            script = ("import os,subprocess,sys,time; "
                      "child=subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)']); "
                      "print(os.getpid(),child.pid,flush=True); time.sleep(60)")
            with self.assertRaises(TimeoutError):
                run_bounded([sys.executable, "-c", script], root, dict(os.environ), log,
                            time.monotonic() + 0.5, commands)
            pids = [int(value) for value in log.read_text().split()]
            self.assertEqual(len(pids), 2)
            members = process_group_members(pids[0])
            live = [member for member in members if not member["state"].startswith("Z")]
            self.assertEqual(live, [], "owned build process or descendant survived timeout")

    @unittest.skipIf(os.name == "nt", "the native build workflow runs on POSIX hosts")
    def test_output_limit_is_enforced(self):
        RAW.joinpath("tmp").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=RAW / "tmp") as td:
            root = Path(td)
            log = root / "output.log"
            commands = []
            with self.assertRaises(ValueError):
                run_bounded([sys.executable, "-c", f"import sys;sys.stdout.write('x'*{MAX_OUTPUT + 1})"],
                            root, dict(os.environ), log, time.monotonic() + 10, commands)
            self.assertGreater(log.stat().st_size, MAX_OUTPUT)


if __name__ == "__main__":
    unittest.main()
