# .ai Automation Control Plane

Canonical automation state for ChatGPT Master ↔ GitHub ↔ Codex Worker.

- `.ai/`: current task, actor, lock, heartbeat, report/review handoff.
- `agent-state/`: deep historical facts, decisions and test evidence.
- code/tests: implementation truth.
- newest explicit user instruction overrides older project notes.

Codex reads bootstrap → current state → active task → only required context.
Master reads current state → task/report/PR/tests → acceptance.
