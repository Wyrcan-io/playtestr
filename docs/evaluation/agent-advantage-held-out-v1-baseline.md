# Agent Advantage held-out V1 legacy baseline

Measured: 2026-08-19  
Agent implementation source commit: `1ff212e`  
Suite: `fixtures/held-out/agent-advantage.v1.json`  
Suite SHA-256: `fb5584d81f469462cb50eb4c1bf751adaf8cecf6470dc2618bac56b4fd93a85c`  
Command: `node dist/cli.js gauntlet --suite fixtures/held-out/agent-advantage.v1.json --artifacts artifacts/agent-advantage/legacy --trust-target`

This file freezes the pre-Agent-Advantage result. The suite and thresholds were written before changing the world model, planner, scheduler, agents, or benchmark evaluator.

| Scenario | Seeds | Intelligent | Coverage-guided | Result |
|---|---:|---:|---:|---|
| relay-vault | 11, 29 | 0.500, 0.500 | 0.500, 0.500 | competitive, below threshold |
| echo-ritual | 7, 31 | 0.250, 0.250 | 0.250, 0.250 | competitive, below threshold |
| branching-quest | 13, 37 | 0.667, 0.667 | 0.667, 0.667 | competitive, below threshold |
| fault-recovery | 17, 41 | 0.500, 0.500 | 0.500, 0.500 | competitive, below threshold |
| route-forge | 19, 43 | 0.334, 0.334 | 0.334, 0.334 | competitive, below threshold |

Aggregate observations:

- suite result: 0/5 scenarios passed;
- intelligent autonomy won 0/10 and tied coverage-guided 10/10;
- intelligent mean evidence: 0.4502;
- coverage-guided mean evidence: 0.4502;
- cleanup failures: 0 across all strategies;
- no advantage claim is supported by this baseline.

Raw local evidence is written to `artifacts/agent-advantage/legacy/gauntlet.json` and intentionally remains an ignored build artifact. This compact tracked record contains the promotion-relevant metrics.
