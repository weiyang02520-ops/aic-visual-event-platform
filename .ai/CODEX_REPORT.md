# Codex Completion Report — TASK-0001

## Result

`PASS_OFFLINE_ADAPTER_UNVERIFIED_REAL_RUNTIME`

Implemented an optional Ultralytics-compatible person/pose provider adapter without changing downstream tracking, relation, keypoint-action, temporal-reasoner, plugin, event, storage or frontend semantics.

The environment has no `ultralytics` package and no `AI_ULTRALYTICS_MODEL_PATH`; no model was downloaded and no real-runtime smoke was claimed. Fake-result and local frame/fact integration tests pass.

## Task identity

- Task: `TASK-0001`
- Task version: `1`
- Task hash: `sha256:8521f4af6a1617f75ab85a0cd22dfe181775be6a6e6e1980152243a061273b40`
- Branch: `codex/task-0001-real-vision-provider`
- Base commit: `546f991` (`origin/main` at task claim)
- Run: `codex-task-0001-20260924T110609Z`

## Changed files

- `workspace/ai-engine/src/visual_event_ai/ultralytics_provider.py`
- `workspace/ai-engine/src/visual_event_ai/model_providers.py`
- `workspace/ai-engine/pyproject.toml` (`pose` optional extra)
- `workspace/ai-engine/tests/test_ultralytics_provider.py`
- `workspace/ai-engine/tests/test_model_providers.py`
- `workspace/ai-engine/tests/test_api.py`
- `workspace/ai-engine/README.md`
- `workspace/docs/MODEL_PROVIDER_CONTRACT.md`
- `workspace/docs/AI_ALGORITHM_DESIGN.md`
- Corresponding files synchronized under `workspace/submission/`

## Adapter behavior

- Provider ID: `ultralytics`.
- Configuration: `AI_DETECTOR_PROVIDER=ultralytics`, `AI_ULTRALYTICS_MODEL_PATH`.
- Optional dependency: `python -m pip install -e ".[pose]"`.
- Input: existing frame payload `image`, `frame`, `bgr` or `rgb`.
- Output: existing `Detection` contract with person bbox/confidence and optional COCO17 `nose`, `left_wrist`, `right_wrist` keypoints.
- Missing package/model, missing frame image, malformed tensors, invalid geometry and invalid confidence fail closed or report unavailable.
- Existing `motion_cpu`, `fixture` and `onnx` fallback behavior remains unchanged.

## Tests and evidence

- Targeted provider/API/fact tests: `35 passed`.
- Full source suite: `368 passed`, 616 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated verifier: `VERIFY_OK`, `368 passed`.
- Real runtime smoke: **not run**; package and model path are absent.
- Model weights: none added.
- Privacy/source/timestamp/continuity boundaries: existing tests remain green.

## Deviations and risks

- Ultralytics is optional and uninstalled in this environment, so provider availability is not runtime-verified.
- No official lightweight model was downloaded; accuracy, latency, CPU memory and keypoint quality are unmeasured.
- The adapter assumes the common Ultralytics result shape and COCO17 keypoint indices; model-specific output contracts still require a provider-specific test before production use.

## Master decision needed

Review the offline adapter contract and PR. If accepted, Master may merge and issue a follow-up task for an authorized model/runtime smoke test. Do not treat this PR as real-model accuracy evidence.

## Commit / PR

- Commit: `d819e5a44fd8854e58e8a26d25adb04632f3751a`
- PR: [#2](https://github.com/weiyang02520-ops/aic-visual-event-platform/pull/2) targeting `main`
- PR state at handoff: `OPEN`, merge state `CLEAN`
