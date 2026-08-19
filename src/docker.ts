import { execFile } from 'node:child_process';
import { createHash } from 'node:crypto';
import { promisify } from 'node:util';
import { PtyTerminalSession } from './terminal.js';
import type { CleanupReason, CleanupResult, ExecutionBackend, ExecutionBackendCapabilities, ExecutionBackendStartOptions, InputAction, ReplayBackendIdentity, TargetManifest, TerminalObservation, TerminalSession, TerminalSessionDiagnostics } from './types.js';

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
      'Environment values are redacted from this evidence plan and are injected only into the Docker client process environment.',
      'Replay V2 records backend and image identity; mutable image tags remain weaker evidence than digest-pinned references.',
    ],
  };
}

function seedLaunch(manifest: TargetManifest, seed?: number): { args: string[]; env: Record<string, string>; environmentNames: string[] } {
  const args = [...(manifest.args ?? [])];
  const env = { ...(manifest.env ?? {}) };
  if (seed !== undefined && manifest.seed?.mode === 'argv') args.push(manifest.seed.flag ?? '--seed', String(seed));
  if (seed !== undefined && manifest.seed?.mode === 'env') env[manifest.seed.envName ?? 'PLAYTESTR_SEED'] = String(seed);
  return { args, env, environmentNames: Object.keys(env).sort() };
}

class DockerTerminalSession implements TerminalSession {
  constructor(private readonly delegate: TerminalSession, private readonly dockerCommand: string, private readonly containerName: string) {}
  observe(): TerminalObservation { return this.delegate.observe(); }
  diagnostics(): TerminalSessionDiagnostics { return this.delegate.diagnostics(); }
  probeProcessAlive(): boolean { return this.delegate.probeProcessAlive(); }
  send(action: InputAction): Promise<void> { return this.delegate.send(action); }
  waitForExit(timeoutMs?: number): Promise<boolean> { return this.delegate.waitForExit(timeoutMs); }
  resize(cols: number, rows: number): Promise<void> { return this.delegate.resize(cols, rows); }

  async stop(reason: CleanupReason = 'completed'): Promise<CleanupResult> {
    const startedAt = Date.now();
    const local = await this.delegate.stop(reason);
    let dockerError: string | undefined;
    try {
      await execFileAsync(this.dockerCommand, ['rm', '--force', '--volumes', this.containerName], { timeout: 10_000, windowsHide: true, maxBuffer: 64 * 1024 });
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      if (!/No such container/iu.test(message)) dockerError = message.slice(0, 500);
    }
    let confirmedExited = false;
    try {
      await execFileAsync(this.dockerCommand, ['inspect', this.containerName], { timeout: 5_000, windowsHide: true, maxBuffer: 64 * 1024 });
    } catch { confirmedExited = true; }
    return {
      attempted: true,
      graceful: local.graceful && !dockerError,
      forced: local.forced || !local.confirmedExited,
      mechanism: 'docker-rm',
      elapsedMs: Date.now() - startedAt,
      confirmedExited,
      ...((dockerError || !confirmedExited) ? { error: dockerError ?? 'Docker container still exists after cleanup' } : {}),
    };
  }
}

export class DockerPtyBackend implements ExecutionBackend {
  readonly id = 'docker-pty';
  readonly capabilities: ExecutionBackendCapabilities = { isolation: 'container', processTreeCleanup: true, resize: true, signals: true, rawTerminalEvents: false };
  private imageDigest: string | undefined;
  private runtimeVersion: string | undefined;

  constructor(readonly profile: DockerProfileV1) {
    if (profile.version !== 1 || !imagePattern.test(profile.image)) throw new Error('Docker backend requires a valid V1 profile');
  }

  replayIdentity(): ReplayBackendIdentity {
    return {
      id: this.id, capabilities: { ...this.capabilities }, runtime: 'docker', ...(this.runtimeVersion ? { runtimeVersion: this.runtimeVersion } : {}), image: this.profile.image,
      ...(this.imageDigest ? { imageDigest: this.imageDigest } : {}),
    };
  }

  private async resolveImageDigest(command: string): Promise<void> {
    try {
      const { stdout } = await execFileAsync(command, ['version', '--format', '{{.Server.Version}}'], { timeout: 5_000, windowsHide: true, maxBuffer: 64 * 1024 });
      if (stdout.trim()) this.runtimeVersion = stdout.trim().slice(0, 100);
    } catch { /* docker run will provide the authoritative launch error */ }
    const pinned = /@((?:sha256:)?[a-f0-9]{32,})$/iu.exec(this.profile.image)?.[1];
    if (pinned) { this.imageDigest = pinned.startsWith('sha256:') ? pinned : `sha256:${pinned}`; return; }
    try {
      const { stdout } = await execFileAsync(command, ['image', 'inspect', '--format', '{{.Id}}', this.profile.image], { timeout: 5_000, windowsHide: true, maxBuffer: 64 * 1024 });
      const value = stdout.trim();
      if (/^sha256:[a-f0-9]{64}$/iu.test(value)) this.imageDigest = value;
    } catch { /* docker run will provide the authoritative launch error */ }
  }

  async start(options: ExecutionBackendStartOptions): Promise<TerminalSession> {
    const runId = `${process.pid}-${Date.now()}`;
    const plan = createDockerExecutionPlan(options.manifest, this.profile, runId);
    await this.resolveImageDigest(plan.command);
    const target = seedLaunch(options.manifest, options.seed);
    const imageIndex = plan.args.indexOf(this.profile.image);
    if (imageIndex < 0) throw new Error('Docker execution plan does not contain its image boundary');
    const withoutRedactedEnv: string[] = [];
    const plannedPrefix = plan.args.slice(0, imageIndex);
    for (let index = 0; index < plannedPrefix.length; index += 1) {
      if (plannedPrefix[index] === '--env') { index += 1; continue; }
      withoutRedactedEnv.push(plannedPrefix[index]!);
    }
    const args = [
      ...withoutRedactedEnv,
      ...target.environmentNames.flatMap(name => ['--env', name]),
      this.profile.image,
      options.manifest.command,
      ...target.args,
    ];
    const launcher: TargetManifest = {
      ...options.manifest,
      id: `${options.manifest.id}-docker-launch`,
      command: plan.command,
      args,
      cwd: process.cwd(),
      env: target.env,
      seed: undefined,
    };
    try {
      const session = await PtyTerminalSession.start({ manifest: launcher, viewport: options.viewport, signal: options.signal });
      return new DockerTerminalSession(session, plan.command, plan.containerName);
    } catch (error) {
      try { await execFileAsync(plan.command, ['rm', '--force', '--volumes', plan.containerName], { timeout: 10_000, windowsHide: true, maxBuffer: 64 * 1024 }); } catch { /* no container or already removed */ }
      throw error;
    }
  }
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
