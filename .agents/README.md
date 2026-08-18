# Playtestr agent workspace

The `.agents` directory contains repository-local guidance for autonomous development work. It is intentionally separate from runtime agents in `src/agents.ts`.

Runtime agents choose game actions. Repository agents maintain code quality, safety, reproducibility, and release evidence.

Before adding an agent:

1. State its objective and allowed tools.
2. Define its stop conditions and budgets.
3. Make its output replayable or reviewable.
4. Add a fixture or evaluation that can prove it helped.

See `skills/README.md` for the planned reusable workflows.
