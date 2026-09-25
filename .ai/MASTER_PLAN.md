# Master Plan

## M0 — Baseline + Automation Bootstrap
Status: COMPLETE after bootstrap merge. Preserve baseline, initialize .ai, freeze acceptance, issue TASK-0001.

## M1 — Real Vision Path
Status: COMPLETE. Optional pose adapter, model-ready OpenCV BGR path, actual Ultralytics CPU runtime, and real local-video-to-fact smoke are all recorded.

## M1F — AI Algorithm Finalization
Status: COMPLETE. TASK-0010 passed Master review; AI_ALGORITHM_FROZEN. Final AI evidence: 430 passed / VERIFY_OK.

## M2 — Frontend Quality + AI Integration
Status: READY / WAITING_FOR_USER. AI_ALGORITHM_FROZEN is complete, so frontend work may resume when the user explicitly chooses the next direction. No TASK-0011 is auto-dispatched.

## M3 — Existing Backend Integration
Add evidence/playback adapters against existing contracts; avoid intrusive backend changes.

## M4 — Competition Material + LaTeX
Prepare algorithm/architecture/plugin/event/experiment/frontend material and later teacher + robot fusion.

## M5 — Submission / Release
Clean package, verifier green, claim/evidence audit, final report and document.


## Task Packet Sizing Policy

Default for autonomous Codex work:
- target approximately 45–120 minutes of meaningful implementation/verification per Task Packet;
- bundle 2–4 tightly related subgoals when they share the same architecture and test boundary;
- prefer one larger coherent PR over several tiny PRs that cause worker idle time;
- keep one task/one PR/one Master review boundary;
- split only when there is a high-risk architecture boundary, external dependency, human decision, or a change that would make review too broad;
- Codex should continue through all subpackages in the packet before handoff unless a declared stop condition is met.


## User-led Control Mode

Current operating mode: **manual/user-led**.

- The roadmap may be maintained continuously in the repository.
- Master must not automatically start the next major phase after a PASS.
- The user explicitly chooses when to continue, review, change direction, or move phases.
- When the user asks to continue, prefer one large coherent Task Packet over several small packets.
- Default implementation packet: 60–180 minutes, 3–6 tightly related subgoals, one PR and one verification boundary.
- Keep suggested future work in `.ai/DEVELOPMENT_DIRECTION.md`.
