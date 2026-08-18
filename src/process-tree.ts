import { execFile } from 'node:child_process';
import { join } from 'node:path';
import type { CleanupResult } from './types.js';

const sleep = (ms: number): Promise<void> => new Promise(resolve => setTimeout(resolve, ms));

export function probePid(pid: number): boolean {
  if (!Number.isSafeInteger(pid) || pid <= 0) return false;
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function waitForPidExit(pid: number, timeoutMs: number): Promise<boolean> {
  const deadline = Date.now() + timeoutMs;
  while (probePid(pid) && Date.now() < deadline) await sleep(20);
  return !probePid(pid);
}

function taskkill(pid: number): Promise<void> {
  const executable = process.env.SystemRoot
    ? join(process.env.SystemRoot, 'System32', 'taskkill.exe')
    : 'taskkill.exe';
  return new Promise((resolve, reject) => {
    execFile(executable, ['/PID', String(pid), '/T', '/F'], { windowsHide: true, timeout: 5000 }, error => {
      if (error && probePid(pid)) reject(error);
      else resolve();
    });
  });
}

export async function forceTerminateProcessTree(pid: number): Promise<Pick<CleanupResult, 'mechanism' | 'confirmedExited' | 'error'>> {
  if (!probePid(pid)) return { mechanism: 'none', confirmedExited: true };
  if (process.platform === 'win32') {
    try {
      await taskkill(pid);
      return {
        mechanism: 'windows-taskkill',
        confirmedExited: await waitForPidExit(pid, 1000),
      };
    } catch (error) {
      return {
        mechanism: 'windows-taskkill',
        confirmedExited: !probePid(pid),
        error: error instanceof Error ? error.message : String(error),
      };
    }
  }

  let mechanism: CleanupResult['mechanism'] = 'unix-process-group';
  let errorMessage: string | undefined;
  try {
    process.kill(-pid, 'SIGKILL');
  } catch (error) {
    mechanism = 'pty-kill';
    try { process.kill(pid, 'SIGKILL'); } catch (fallbackError) {
      errorMessage = fallbackError instanceof Error ? fallbackError.message : String(fallbackError);
      if (!probePid(pid)) errorMessage = undefined;
    }
    if (!errorMessage && probePid(pid) && error instanceof Error) errorMessage = error.message;
  }
  return {
    mechanism,
    confirmedExited: await waitForPidExit(pid, 1000),
    ...(errorMessage ? { error: errorMessage } : {}),
  };
}
