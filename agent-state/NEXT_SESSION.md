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
