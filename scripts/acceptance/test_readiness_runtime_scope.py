"""Real Unix process ownership checks; unrelated runtimes must not block removal."""
import asyncio
import os
from pathlib import Path
import signal
import tempfile
import unittest
import uuid

from readiness_cleanup_plop import runtime_inventory
from readiness_evidence import RAW


@unittest.skipIf(os.name == 'nt', 'Unix process command ownership uses native ps')
class NativeRuntimeScopeTests(unittest.TestCase):
    def test_owned_bash_is_reported_and_unrelated_bash_is_ignored(self):
        async def observe():
            RAW.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(dir=RAW) as directory:
                root = Path(directory)
                env = dict(PATH='/usr/bin:/bin', HOME=str(root), TMPDIR=str(root), LC_ALL='C')
                children = []
                private_marker='runtime-private-argument-'+uuid.uuid4().hex
                existing=set((RAW/'fff').rglob('*'))
                try:
                    for marker in ['simulated-unrelated-runtime', str(root/'owned-runtime')]:
                        child = await asyncio.create_subprocess_exec('/bin/bash', '--noprofile', '--norc',
                            '-c', 'printf ready; sleep 30; :', marker, private_marker, cwd=root, env=env,
                            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL,
                            start_new_session=True)
                        children.append(child)
                        self.assertEqual(await asyncio.wait_for(child.stdout.readexactly(5), 3), b'ready')
                    unrelated, owned = children
                    observed = await runtime_inventory('fff', 'real-runtime-scope-negative-control')
                    self.assertIn(str(owned.pid), observed, 'owned live Bash escaped the cleanup inventory')
                    self.assertNotIn(str(unrelated.pid), observed, 'unrelated live Bash blocked owned cleanup')
                    for path in set((RAW/'fff').rglob('*'))-existing:
                        if path.is_file() and path.suffix in {'.json','.log'}:
                            self.assertLessEqual(path.stat().st_size,4*1024**2,'unbounded ownership evidence')
                            self.assertNotIn(private_marker.encode(),path.read_bytes(),'private runtime arguments leaked into evidence')
                finally:
                    for child in children:
                        if child.returncode is None:
                            os.killpg(child.pid, signal.SIGKILL)
                        await asyncio.wait_for(child.wait(), 3)
                        transport = getattr(child, '_transport', None)
                        if transport is not None:
                            transport.close()
        asyncio.run(observe())
