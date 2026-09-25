# Next Session

## Mandatory reading

1. `CONTEXT_INDEX.md`
2. `USER_REQUIREMENTS.md`
3. `VERIFIED_FACTS.md`
4. `DECISIONS.md`
5. `ARCHITECTURE.md`
6. `MASTER_STATUS.md`
7. `CURRENT_TASK.md`
8. `BLOCKERS.md`
9. `OPEN_QUESTIONS.md`

## Current scope

Continue the AI recognition algorithm audit and locally verifiable implementation in `workspace/ai-engine/`. The user limited this task to AI algorithms, their tests, algorithm documentation, and this project's `agent-state/`; do not expand into frontend visual work or long-form competition writing.

## Verified checkpoint

- `MedicationSequenceReasoner` and `WorkshopStateReasoner` are integrated with their plugins; source facts are retained in resulting events.
- Medication candidates require matching person/object/time evidence; workshop timeout requires `scene_observed`; zone returns require the same zone; `putdown_candidate` alone is not a return.
- `MotionDetector` resets state between sources/jobs and after malformed input; duplicate bbox observations keep distinct track IDs.
- Gray embedding input rejects ragged, non-finite, Boolean/string, and out-of-range samples; registry request schemas preserve strict numeric types and avoid coercion-based matches.
- AI source and curated submission suites now return 344 passed after keypoint-action timestamp and source provenance isolation; curated `VERIFY_OK`. Existing coverage includes strict frame sampling, temporal reasoning, recovered JSONL gaps, workshop continuity-segment matching, recursive frame-preview pixel redaction, and reference-document evidence boundaries.
- The pinned Makerverse and livestream-rs snapshots are media/control integration references. The current AI engine uses deterministic CPU/fixture paths; no real object detector, pose model, model weights, or real-video metrics are present.
- Boundary incident: `TEST_EVIDENCE.md` records pytest temp directories found outside the project from earlier default/relative-basetemp runs. Do not read-modify-clean those external directories; use only an absolute basetemp under the AIC root for future tests. The curated verifier now uses an absolute `.codex-pytest-temp-verify` child under its AI root and removes it after the run.
- User-provided AIC notice/rule PDFs are now inside the project root and mapped in `workspace/docs/AIC_ALGORITHM_COMPETITION_ALIGNMENT.md`. The current candidate is `AI+场景创新`; privacy source processing, real scene evidence, final track/team confirmation, and robot/hardware evidence remain open.
- `workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md` now schedules P0 privacy/schema, P1 model/pose/tracking, P2 temporal scenes, P3 multimodal quality gating, and P4 hardware validation. Do not import external DOCX metrics without reproducible data.
- Full details and evidence boundaries: `workspace/docs/TEMPORAL_EVENT_REASONING.md`, `workspace/docs/AI_PROVIDERS_PHASE3.md`, `agent-state/TEST_EVIDENCE.md`.

## Next actions

1. Check only for new authorized AI action/pose samples, model artifacts, or multimodal input contracts inside the AIC project tree.
2. Convert the rules-aligned privacy/skeletonization target into a separately testable input/output contract only when a real upstream AI source or authorized sample is available.
3. Use the AI analysis plan to choose the next concrete P0–P3 source-to-fact issue; keep explicit-keypoint fixtures separate from real pose model output.
4. After each AI change, run relevant regression tests with temp files inside this project root, synchronize the curated AI package, and confirm the verifier cleanup/contamination scan.

## Boundaries

- Create, modify, or clean files only under `C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料`; keep pytest basetemp there and remove only the verified temp directory.
- Do not modify the frontend, Makerverse, livestream-rs, or other workspaces.
- Do not claim real pose/action recognition, event accuracy, or robot operation from Mock/fixture/CPU tests.
- If external teacher/robot data is added, register it in project state first and stay within the active AI scope.


## Latest AI-only checkpoint (2026-09-24)

- Temporal reasoners enforce same explicit `source_id` for multi-fact medication and workshop evidence; malformed explicit provenance cannot pair, while missing provenance remains legacy unknown-source compatible.
- `KeypointActionExtractor` includes the observation source ID on emitted action facts.
- Source full suite and curated submission both return `363 passed`; curated verifier returns `VERIFY_OK`.
- The current user scope excludes hardware, robot control, camera calibration, field video and frontend work.

## Next AI-only action

- Continue with one concrete P0–P3 contract issue only when it is visible in current code or new authorized data. Do not add real-model adapters, sensor fusion, hardware integration or performance numbers without the corresponding source/model/data evidence.


## Latest P0–P3 software checkpoint (2026-09-24)

- Shared pixel metadata redaction now covers facts, vision preview, job metadata and SQLite payloads.
- Temporal reasoners enforce explicit source provenance; keypoint actions preserve source IDs.
- Optional `channel_quality` metadata now supports software-only usable/degraded/blocked decisions and fail-closed observation gaps.
- Source and curated suites return `363 passed`; curated verifier returns `VERIFY_OK`.
- Real models, sensor clocks, channel calibration, hardware and robot work remain outside the current user scope.

## Next AI-only action

- Resume only when a new concrete P0–P3 code issue or authorized AI sample appears. Preserve fixture/CPU versus real evidence labels and do not add hardware work.

## GitHub repository handoff (2026-09-24)

- Development repository: `https://github.com/weiyang02520-ops/aic-visual-event-platform`
- Visibility: Private; default branch: `main`.
- Initial checkpoint commit: `9481004b94e983faa2dd8780c021b6fa6c0806a8`.
- The repository keeps the existing `workspace/` layout plus root `agent-state/`; current AI source, tests, docs and submission package are available for Codex/ChatGPT/human review.
- Original competition attachments, third-party snapshots, rollback copies, runtime/cache/dependency/build output, model weights and secrets were not pushed.
- AI feature work is paused. On the next session, first read this file, `MASTER_STATUS.md`, the root `README.md`, and the GitHub remote status; wait for user direction before coding.


## Automation handoff update (2026-09-24)
Before coding, read `CODEX_BOOTSTRAP.md` and `.ai/CURRENT_STATE.json`. If state is READY_FOR_CODEX and next_actor is codex, execute only the named Task Packet. Adapter tests are not accuracy evidence.


## TASK-0001 handoff checkpoint (2026-09-24)

- Active branch: `codex/task-0001-real-vision-provider`.
- Optional `ultralytics` provider adapter is implemented and tested offline; source/curated suites are `368 passed` / `VERIFY_OK`.
- Real runtime smoke is unverified because `ultralytics` and model weights are absent.
- Read `.ai/CODEX_REPORT.md`, the Task-0001 run record and PR before Master review. Do not start TASK-0002 or merge on your own.

## TASK-0001 PR handoff (2026-09-24)

- Branch: `codex/task-0001-real-vision-provider`
- Commit: `d819e5a44fd8854e58e8a26d25adb04632f3751a`
- PR: [#2](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/2)
- State: `WAITING_FOR_MASTER`; lock released; next actor is `chatgpt-master`.
- Do not start another task or merge this PR from Codex.

## TASK-0001 R1 PR handoff (2026-09-24)

- R1 fix commit: `e5f6180`; PR [#2](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/2) remains open against `main`.
- Master blocker fixed: registry-created Ultralytics provider reads `AI_ULTRALYTICS_MODEL_PATH` and exposes selection/status offline.
- Verification: source/curated `369 passed`, `VERIFY_OK`; real runtime remains unverified.
- State is `WAITING_FOR_MASTER`, lock is released, and Codex must not choose TASK-0002.


## TASK-0002 handoff checkpoint (2026-09-24)

- Active branch: `codex/task-0002-local-video-pixel-bridge`.
- OpenCV BGR+gray payload bridge and privacy/integration tests are implemented; source/curated suites are `371 passed` / `VERIFY_OK`.
- Real model runtime remains unverified; no weights or runtime dependency were added.
- Read `.ai/CODEX_REPORT.md`, the TASK-0002 run record and PR before Master review. Do not start TASK-0003 or merge on your own.


## TASK-0002 PR handoff (2026-09-24)

- Branch: `codex/task-0002-local-video-pixel-bridge`; commit `fe12552`.
- PR: [#3](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/3) targeting `main`.
- State: `WAITING_FOR_MASTER`; lock released; next actor `chatgpt-master`.
- Do not start TASK-0003 or merge from Codex.


## TASK-0003 handoff checkpoint (2026-09-24)

- Branch: `codex/task-0003-real-ultralytics-pose-runtime-smoke`; task hash verified; real runtime smoke evidence is in `workspace/docs/REAL_RUNTIME_SMOKE_TASK-0003.md`.
- Official `yolo11n-pose.pt` + `bus.jpg` ran through `UltralyticsProvider` on CPU: 4 person detections and nose/left_wrist/right_wrist keypoints.
- Source and curated suites: `371 passed`; curated `VERIFY_OK`.
- Weights, sample, venv and runtime caches are ignored and absent from the Git change.
- State returns to `WAITING_FOR_MASTER`, `next_actor=chatgpt`; Codex must not choose the next task.


## TASK-0003 PR handoff (2026-09-24)

- Commit: `23396f639322e1d37cd77ef822b42aa4a9356a52`; PR [#4](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/4) targets `main` and is `OPEN` / `CLEAN`.
- State: `WAITING_FOR_MASTER`; lock released; `next_actor=chatgpt`.
- Review the runtime evidence before any next task; Codex must not choose TASK-0004.


## TASK-0004 checkpoint (2026-09-24)

- Branch: `codex/task-0004-real-local-video-pose-smoke`; task hash verified; evidence is in `workspace/docs/REAL_LOCAL_VIDEO_SMOKE_TASK-0004.md`.
- Real two-frame local AVI → OpenCV BGR → real Ultralytics → tracker/normalization → `object_detected` facts succeeded: 2 decoded frames and 8 person facts.
- All person facts preserved provider keypoints, source ID and timezone-aware UTC timestamps; no raw pixel keys were present in fact metadata.
- Source and curated suites: `371 passed`; curated `VERIFY_OK`; project-local basetemp cleaned.
- State will return to `WAITING_FOR_MASTER`, `next_actor=chatgpt`; Codex must not choose TASK-0005.


## TASK-0004 PR handoff (2026-09-24)

- Commit: `f2b9e7505c16d6a979bfe25d8cefcfb9722f8a7e`; PR [#5](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/5) targets `main` and is `OPEN` / `CLEAN`.
- State: `WAITING_FOR_MASTER`; lock released; `next_actor=chatgpt`.
- Review the local-video source-to-fact evidence before any next task; Codex must not choose TASK-0005.


## TASK-0005 checkpoint (2026-09-24)

- Branch: `codex/task-0005-frontend-real-connection-state`; task hash verified; frontend connection evidence is recorded in the run/report files and frontend design docs.
- Real source loading requires `/health` plus initial resources; switching clears old data and stale responses; offline actions do not call Mock.
- `npm run build` passed; local AI service `npm run smoke:real` passed; source suite `371 passed`; curated `VERIFY_OK`.
- No browser executable was present for click-through validation; direct unreachable API probe returned `fetch failed`.
- State will return to `WAITING_FOR_MASTER`, `next_actor=chatgpt`; Codex must not choose TASK-0006.


## TASK-0005 PR handoff (2026-09-24)

- Commit: `08f0b7bf191d09ad8d22f51033e7d0e33a473363`; PR [#6](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/6) targets `main` and is `OPEN` / `CLEAN`.
- State: `WAITING_FOR_MASTER`; lock released; `next_actor=chatgpt`.
- Review Real connection/offline behavior and the browser-validation limitation before any next task; Codex must not choose TASK-0006.


## TASK-0006 checkpoint (2026-09-25)

- Branch: `codex/task-0006-skeleton-contract`; task hash verified; implementation and evidence are in `skeleton.py`, provider/action/fact paths and updated AI docs.
- Targeted tests: `61 passed`; source suite: `380 passed`; curated `VERIFY_OK`.
- Canonical skeleton metadata remains semantic and pixel-free; no frontend/hardware work was done.
- State will return to `WAITING_FOR_MASTER`, `next_actor=chatgpt`; Codex must not choose TASK-0007.


## TASK-0006 PR handoff (2026-09-25)

- Commit: `eadef5b97586ab0a82d4d93a6d6bd566b60ebbf9`; PR [#7](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/7) targets `main` and is `OPEN` / `CLEAN`.
- State: `WAITING_FOR_MASTER`; lock released; `next_actor=chatgpt`.
- Review canonical skeleton/full-pose evidence and privacy deployment modes before any next task; Codex must not choose TASK-0007.


## TASK-0007 checkpoint (2026-09-25)

- Branch: `codex/task-0007-visual-memory`; task hash verified; generic memory evidence is in `visual_memory.py`, relation/fact integration and tests.
- Targeted tests: `144 passed`; source suite: `389 passed`; curated `VERIFY_OK`.
- Identity remains source/continuity/track local; no ReID, gait, ByteTrack/Kalman or metrics claims.
- State will return to `WAITING_FOR_MASTER`, `next_actor=chatgpt`; Codex must not choose TASK-0008.


## TASK-0007 PR handoff (2026-09-25)

- Commit: `9e7021448869adf2fbc461b7a442342b030376f9`; PR [#8](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/8) targets `main` and is `OPEN` / `CLEAN`.
- State: `WAITING_FOR_MASTER`; lock released; `next_actor=chatgpt`.
- Review generic memory identity boundaries before any next task; Codex must not choose TASK-0008.


## TASK-0008 checkpoint (2026-09-25)

- Branch: `codex/task-0008-generic-action-primitives`; task hash verified; generic action evidence is in `action_primitives.py`, fact pipeline integration and tests.
- Targeted tests: `159 passed`; source suite: `396 passed`; curated `VERIFY_OK`.
- Medication behavior remains behind the compatibility adapter; no definitive grasp/carry or metrics claims.
- State will return to `WAITING_FOR_MASTER`, `next_actor=chatgpt`; Codex must not choose TASK-0009.
