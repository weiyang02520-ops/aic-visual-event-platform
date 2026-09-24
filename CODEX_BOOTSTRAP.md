# CODEX_BOOTSTRAP.md
## AIC Visual Event Platform — Codex Worker Bootstrap

Do not re-plan the whole project.

Repository: https://github.com/weiyang02520-ops/aic-visual-event-platform
Default branch: main
Current phase: M1 Real Vision Path
Active task: TASK-0001
AI: Python >=3.11, FastAPI/Pydantic, SQLite
Frontend: React + TypeScript + Vite

## Canonical State
Automation: `.ai/CURRENT_STATE.json`, task, lock, heartbeat, report.
Deep evidence/history: `agent-state/`.
Do not use chat memory as project truth.

## Startup
1. Fetch latest.
2. Stop if `.ai/EMERGENCY_STOP` or `.ai/PAUSE` exists.
3. Read CURRENT_STATE.
4. If next_actor != codex or status != READY_FOR_CODEX, exit with zero code changes.
5. Read exact active task; verify task_version and SHA-256 task_hash locally.
6. Check/claim lock; refetch/recheck.
7. Create task branch; never feature-edit main.
8. Execute only Task Packet.
9. Run required tests.
10. Update report/run/state.
11. Commit, push, open/update one PR.
12. Set WAITING_FOR_MASTER / next_actor=chatgpt and release lock.

## Rules
No force push, repo-setting changes, production deploy, secrets, model weights, unapproved irreversible changes, or broad Makerverse/livestream-rs rewrite. One active task/PR. Retry max 3.

Paths:
- AI: `workspace/ai-engine/src/`
- tests: `workspace/ai-engine/tests/`
- frontend: `workspace/frontend/`
- docs: `workspace/docs/`
- submission: `workspace/submission/`

AI tests:
```powershell
cd workspace/ai-engine
$env:PYTHONPATH = "src"
python -B -m pytest -p no:cacheprovider -q
```

Verifier:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\workspace\submission\VERIFY.ps1 -SkipFrontendBuild
```

Read `.ai/tasks/TASK-0001.md`. Do not choose TASK-0002 yourself.

At completion update `.ai/CODEX_REPORT.md`, a run record, relevant `agent-state/` evidence/status and `.ai/CURRENT_STATE.json`; then open one PR targeting main and hand control to Master.
