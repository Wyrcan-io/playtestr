"""Bounded source-build command and process-group cleanup tests for mg."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest

from next20_check import RAW, ROOT
from next20_mg_build import (MAX_OUTPUT, TOOLCHAIN_SOURCES, normalize_extracted_source_timestamps,
                             apply_reviewed_fault, process_group_members, run_bounded)
from readiness_acquire_plop import extract_source


class MgBuildCommandTests(unittest.TestCase):
    def test_reviewed_fault_mutations_are_exact_and_confined_to_one_source_file(self):
        cases = {
            "save-no-write": ("fileio.c", b"\treturn (FIOSUC);\n}\n\n/*\n * Read a line"),
            "delete-byte-corruption": ("line.c", b"\t\t\t*cp1++ = (char)(*cp2 ^ 1);"),
            "readonly-edit-accepted": ("line.c", b"int\nldelete(RSIZE n, int kflag)\n{"),
            "undo-delete-omitted": ("undo.c", b"case DELETE:\n"
                                    b"\t\t\t\t/* Fault calibration: omit restoration of deleted text. */\n"
                                    b"\t\t\t\tbreak;"),
        }
        originals = {
            "save-no-write": b"int\nffputbuf(FILE *ffp, struct buffer *bp, int eobnl)\n{\n"
                            b"\tstruct line\t*lp, *lpend;\n\n\tlpend = bp->b_headp;\n"
                            b"\treturn (FIOSUC);\n}\n\n/*\n * Read a line",
            "delete-byte-corruption": b"\t\t\t*cp1++ = *cp2;",
            "readonly-edit-accepted": (b"int\nldelete(RSIZE n, int kflag)\n{\n"
                                       b"\tif (curbp->b_flag & BFREADONLY) {\n"
                                       b"\t\tdobeep();\n"
                                       b"\t\tewprintf(\"Buffer is read only\");\n"
                                       b"\t\tgoto out;\n\t}\n"),
            "undo-delete-omitted": (b"\t\t\tcase DELETE:\n\t\t\t\tlp = curwp->w_dotp;\n"
                                    b"\t\t\t\toffset = curwp->w_doto;\n"
                                    b"\t\t\t\tregion_put_data(ptr->content,\n"
                                    b"\t\t\t\t    ptr->region.r_size);\n"
                                    b"\t\t\t\tcurwp->w_dotp = lp;\n"
                                    b"\t\t\t\tcurwp->w_doto = offset;\n"
                                    b"\t\t\t\tbreak;\n"),
        }
        for mutation, (filename, expected_fragment) in cases.items():
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                source = Path(directory)
                path = source / "src" / filename
                path.parent.mkdir()
                path.write_bytes(originals[mutation])
                receipt = apply_reviewed_fault(source, mutation)
                self.assertEqual(receipt["path"], f"src/{filename}")
                self.assertNotEqual(receipt["original_sha256"], receipt["mutated_sha256"])
                self.assertIn(expected_fragment, path.read_bytes())
                self.assertEqual(len(list(source.rglob("*"))), 2)

    def test_reviewed_fault_mutations_reject_changed_anchors_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            path = source / "src" / "line.c"
            path.parent.mkdir()
            original = b"changed upstream implementation\n"
            path.write_bytes(original)
            with self.assertRaisesRegex(ValueError, "anchor changed"):
                apply_reviewed_fault(source, "delete-byte-corruption")
            self.assertEqual(path.read_bytes(), original)

    def test_extracted_release_tree_uses_one_timestamp_for_shipped_generated_files(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            for name in ("configure", "Makefile.in", "aclocal.m4", "lib/config.hin"):
                path = source / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("generated", encoding="utf-8")
                os.utime(path, (1, 1))
            normalize_extracted_source_timestamps(source)
            mtimes = {(source / name).stat().st_mtime_ns
                      for name in ("configure", "Makefile.in", "aclocal.m4", "lib/config.hin")}
            self.assertEqual(len(mtimes), 1)
            self.assertGreater(next(iter(mtimes)), 1_000_000_000)

    def test_owned_autotools_inputs_have_fixed_official_archive_hashes(self):
        self.assertEqual([row["name"] for row in TOOLCHAIN_SOURCES],
                         ["m4", "autoconf", "automake"])
        self.assertEqual([row["sha256"] for row in TOOLCHAIN_SOURCES], [
            "f25c6ab51548a73a75558742fb031e0625d6485fe5f9155949d6486a2408ab66",
            "9fd672b1c8425fac2fa67fa0477b990987268b90ff36d5f016dae57be0d6b52e",
            "168aa363278351b89af56684448f525a5bce5079d0b6842bd910fdd3f1646887",
        ])
        for row in TOOLCHAIN_SOURCES:
            self.assertTrue(row["url"].startswith("https://ftp.gnu.org/gnu/"))
            self.assertEqual(len(row["sha256"]), 64)
            int(row["sha256"], 16)

    def test_safe_xz_source_extraction_and_traversal_rejection(self):
        RAW.joinpath("tmp").mkdir(exist_ok=True)
        for member_name, expected_error in (("tool-1/file.txt", None),
                                            ("tool-1/../escape.txt", RuntimeError)):
            buffer = io.BytesIO()
            with tarfile.open(fileobj=buffer, mode="w:xz") as archive:
                info = tarfile.TarInfo(member_name)
                payload = b"pinned tool source"
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
            with tempfile.TemporaryDirectory(dir=RAW / "tmp") as td:
                destination = Path(td) / "source"
                if expected_error:
                    with self.assertRaises(expected_error):
                        extract_source(buffer.getvalue(), destination, expanded_limit=1024,
                                       entry_limit=10, member_limit=1024, archive_mode="r:xz")
                    self.assertFalse(destination.exists())
                else:
                    count, expanded = extract_source(buffer.getvalue(), destination,
                                                     expanded_limit=1024, entry_limit=10,
                                                     member_limit=1024, archive_mode="r:xz")
                    self.assertEqual((count, expanded), (1, len(payload)))
                    self.assertEqual((destination / "file.txt").read_bytes(), payload)

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
