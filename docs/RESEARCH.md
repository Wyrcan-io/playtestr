# Architecture research notes

These primary references inform the product gates. They are design inputs, not claims that Playtestr already implements every technique.

## Terminal execution

[`node-pty`](https://github.com/microsoft/node-pty) provides the Windows, macOS, and Linux PTY transport used by the local backend. Its security guidance states that spawned processes run with the parent process's permissions and recommends containerization for server scenarios. This is why Playtestr labels local targets as trusted and separates a future isolated backend.

## Coverage-guided search

[LLVM libFuzzer](https://llvm.org/docs/LibFuzzer.html) retains inputs that reach new coverage, emphasizes deterministic targets, supports explicit run/time budgets, and minimizes reproducing inputs. Playtestr applies those principles to observable terminal states and transitions while avoiding the stronger claim of internal code coverage.

## Environment lifecycle

[Gymnasium's environment API](https://gymnasium.farama.org/api/env/) separates `terminated` (the environment reached an end state) from `truncated` (an external limit ended the episode). Playtestr mirrors that distinction so a completed game is not confused with an action or time budget.

## Stateful action generation

[fast-check model-based testing](https://fast-check.dev/docs/advanced/model-based-testing/) represents actions as commands with preconditions, execution/assertion logic, serializable descriptions, replay metadata, and sequence shrinking. These ideas guide the future adapter action model and finding minimizer.

## Isolation and process control

[Microsoft Job Objects](https://learn.microsoft.com/en-us/windows/win32/procthread/job-objects) manage process groups as a unit, support resource limits and accounting, and can terminate associated process trees. They are a candidate primitive for a hardened Windows backend.

[Docker's security guidance](https://docs.docker.com/engine/security/) explains namespace/capability boundaries and daemon risk, while its [resource constraint documentation](https://docs.docker.com/engine/containers/resource_constraints/) notes that containers have no resource limits by default. Therefore "runs in a container" is not an isolation acceptance test by itself.
