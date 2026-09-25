# .ai Automation Control Plane

Canonical automation state for ChatGPT Master ↔ GitHub ↔ Codex Worker.

- `.ai/`: current task, actor, lock, heartbeat, report/review handoff.
- `agent-state/`: deep historical facts, decisions and test evidence.
- code/tests: implementation truth.
- newest explicit user instruction overrides older project notes.

Codex reads bootstrap → current state → active task → only required context.
Master reads current state → task/report/PR/tests → acceptance.


## Worker freshness rule

Before any Codex worker decides whether to claim/exit:
1. fetch the latest `origin/main`;
2. read `.ai/CURRENT_STATE.json`, `.ai/LOCK.json`, `.ai/HEARTBEAT.json` and the active Task Packet from the fetched `origin/main`, not from a stale local task branch;
3. if local state disagrees with `origin/main`, `origin/main` wins unless a live non-expired lock proves an in-progress task;
4. only exit for `next_actor != codex` after this freshness check.

This prevents an old task branch from repeatedly reporting a superseded WAITING_FOR_MASTER state after Master has already dispatched the next task.
