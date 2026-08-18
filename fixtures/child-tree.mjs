import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const child = spawn(process.execPath, [fileURLToPath(new URL('./child-tree-child.mjs', import.meta.url))], {
  stdio: 'ignore',
});
process.on('SIGINT', () => {});
process.stdin.setRawMode?.(true);
process.stdin.resume();
console.log(`PARENT_PID ${process.pid} CHILD_PID ${child.pid}`);
setInterval(() => {}, 60_000);
