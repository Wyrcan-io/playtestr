import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import { promisify } from 'node:util';
import type { ExecutionBackendCapabilities, TargetManifest } from './types.js';

const execFileAsync = promisify(execFile);

export interface DockerProfileV1 {
  version: 1;
  image: string;
  dockerCommand?: string;
  containerWorkdir?: string;
  user?: string;
  memory?: string;
  cpus?: number;
  pidsLimit?: number;
  tmpfsMb?: number;
  network?: 'none' | 'bridge';
  pull?: 'never' | 'missing';
  allowNetwork?: boolean;
  allowPull?: boolean;
}

export interface DockerExecutionPlan {
  version: 1;
  backendId: 'docker-pty-planned';
  capabilities: ExecutionBackendCapabilities;
  command: string;
  args: string[];
  containerName: string;
  environmentNames: string[];
  restrictions: string[];
  warnings: string[];
}

export interface DockerCapabilityReport {
  available: boolean;
  cli: string;
  daemonReachable: boolean;
  serverOs?: string;
  error?: string;
}

const imagePattern = /^[A-Za-z0-9][A-Za-z0-9._/:@-]{0,254}$/u;
const memoryPattern = /^[1-9][0-9]*(?:[bkmg])?$/iu;
const userPattern = /^[0-9]+(?::[0-9]+)?$/u;

function positive(value: number, label: string): number {
  if (!Number.isFinite(value) || value <= 0) throw new Error(`${label} must be positive`);
  return value;
}

export function createDockerExecutionPlan(manifest: TargetManifest, profile: DockerProfileV1, runId = 'run'): DockerExecutionPlan {
  if (profile.version !== 1 || !imagePattern.test(profile.image)) throw new Error('Docker profile requires a safe explicit image reference');
  const network = profile.network ?? 'none';
  const pull = profile.pull ?? 'never';
  if (network !== 'none' && !profile.allowNetwork) throw new Error('Docker network access requires explicit allowNetwork acknowledgement');
  if (pull !== 'never' && !profile.allowPull) throw new Error('Docker image pulling requires explicit allowPull acknowledgement');
  const memory = profile.memory ?? '512m';
  if (!memoryPattern.test(memory)) throw new Error('Docker memory must be a positive Docker byte value');
  const cpus = positive(profile.cpus ?? 1, 'Docker CPU limit');
  const pidsLimit = positive(profile.pidsLimit ?? 128, 'Docker PID limit');
  const tmpfsMb = positive(profile.tmpfsMb ?? 64, 'Docker tmpfs limit');
  if (!Number.isSafeInteger(pidsLimit) || !Number.isSafeInteger(tmpfsMb)) throw new Error('Docker PID and tmpfs limits must be safe integers');
  const user = profile.user ?? '65532:65532';
  if (!userPattern.test(user)) throw new Error('Docker user must be a numeric uid or uid:gid');
  const containerWorkdir = profile.containerWorkdir ?? '/work';
  if (!containerWorkdir.startsWith('/') || containerWorkdir.includes('\0')) throw new Error('Docker workdir must be an absolute container path');
  const digest = createHash('sha256').update(`${manifest.id}:${runId}`, 'utf8').digest('hex').slice(0, 12);
  const safeTarget = manifest.id.toLowerCase().replace(/[^a-z0-9_.-]+/gu, '-').replace(/^[^a-z0-9]+/u, '').slice(0, 30) || 'target';
  const containerName = `playtestr-${safeTarget}-${digest}`;
  const environmentNames = Object.keys(manifest.env ?? {}).sort();
  const args = [
    'run', '--rm', '--init', '--interactive', '--tty',
    '--pull', pull,
    '--network', network,
    '--read-only',
    '--cap-drop', 'ALL',
    '--security-opt', 'no-new-privileges',
    '--memory', memory,
    '--memory-swap', memory,
    '--cpus', String(cpus),
    '--pids-limit', String(pidsLimit),
    '--user', user,
    '--tmpfs', `/tmp:rw,noexec,nosuid,nodev,size=${tmpfsMb}m`,
    '--workdir', containerWorkdir,
    '--name', containerName,
    ...environmentNames.flatMap(name => ['--env', `${name}=<redacted>`]),
    profile.image,
    manifest.command,
    ...(manifest.args ?? []),
  ];
  const restrictions = ['no-host-mounts', 'read-only-root', 'all-capabilities-dropped', 'no-new-privileges', `network:${network}`, `pull:${pull}`, `memory:${memory}`, `cpus:${cpus}`, `pids:${pidsLimit}`, `user:${user}`, `tmpfs:${tmpfsMb}m`];
  return {
    version: 1,
    backendId: 'docker-pty-planned',
    capabilities: { isolation: 'container', processTreeCleanup: true, resize: true, signals: true, rawTerminalEvents: false },
    command: profile.dockerCommand ?? 'docker',
    args,
    containerName,
    environmentNames,
    restrictions,
    warnings: [
      'Container isolation is not VM-grade isolation and depends on the Docker daemon and host kernel.',
      'Environment values are redacted from this evidence plan and must be injected by a future backend without serialization.',
      'This plan is not executable through Replay V1 until backend identity is versioned in replay evidence.',
    ],
  };
}

export async function probeDocker(command = 'docker', timeoutMs = 5000): Promise<DockerCapabilityReport> {
  if (!Number.isSafeInteger(timeoutMs) || timeoutMs <= 0) throw new Error('Docker probe timeout must be a positive safe integer');
  try {
    const { stdout } = await execFileAsync(command, ['version', '--format', '{{json .Server}}'], { timeout: timeoutMs, windowsHide: true, maxBuffer: 64 * 1024 });
    const trimmed = stdout.trim();
    let serverOs: string | undefined;
    try {
      const server = JSON.parse(trimmed) as { Os?: string; Platform?: { Name?: string } };
      serverOs = server.Os ?? server.Platform?.Name;
    } catch {
      serverOs = trimmed || undefined;
    }
    return { available: true, cli: command, daemonReachable: true, ...(serverOs ? { serverOs } : {}) };
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    const missing = (error as NodeJS.ErrnoException).code === 'ENOENT';
    return { available: !missing, cli: command, daemonReachable: false, error: message.slice(0, 500) };
  }
}
