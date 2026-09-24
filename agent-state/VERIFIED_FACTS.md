# Verified Facts

## Workspace

### FACT-001
- Claim: 资料根目录已创建并可写入。
- Evidence: 目录存在，且包含 `workspace/` 与 `agent-state/`。
- File/URL: `C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料`
- Verified at: 2026-09-22
- Confidence: high

### FACT-002
- Claim: 交接计划书存在，当前文件长度为 12,514 行、364,993 字节。
- Evidence: PowerShell `Get-Item` 与 `Get-Content` 计数。
- File/URL: `..\Codex_Master_Execution_Plan_V5_FINAL.md`
- Verified at: 2026-09-22
- Confidence: high

### FACT-003
- Claim: 计划书正文标题写明版本 `V3.0 / Codex Execution Edition`，文件名为 `V5_FINAL`。
- Evidence: 文件首部标题与版本行。
- File/URL: `..\Codex_Master_Execution_Plan_V5_FINAL.md`
- Verified at: 2026-09-22
- Confidence: high
- Note: 版本号不一致，后续不以文件名单独推断内容版本。

### FACT-004
- Claim: 两个仓库的只读源快照已纳入本项目目录，工作树干净。
- Evidence: `git rev-parse HEAD`、`git status --short --branch`、remote inspection。
- File/URL: `workspace/source-snapshots/Makerverse/` and `workspace/source-snapshots/livestream-rs/`
- Commits: Makerverse `88423bc5e3b64dac1670180999b08e4cae36e5df`; livestream-rs `8b463533c5d218701482389dcdcf53eb18f5388f`
- Verified at: 2026-09-22
- Confidence: high

### FACT-005
- Claim: Current Windows environment has Git, Python 3.14.4, Node.js v24.15.0 and npm 11.12.1; .NET host exists without an installed SDK; Cargo and FFmpeg are absent from PATH.
- Evidence: `Get-Command` and version commands recorded in `workspace/docs/PHASE0_AUDIT.md`.
- Verified at: 2026-09-22
- Confidence: high

## Repository facts

Makerverse 与 livestream-rs 的静态仓库事实已在 Phase 0 以本目录内 checkout、commit 和文件内容核验；运行时事实仍受工具链和基础设施缺失限制。

### FACT-006
- Claim: 当前 Python 环境可导入 OpenCV、NumPy 和 Pillow；本项目新增 OpenCV 可选本地视频 provider。
- Evidence: `importlib.util.find_spec` 检查及 `test_opencv_provider_reads_real_local_video_when_available` 通过；测试生成 16x12 AVI 并读取 2 帧。
- File/URL: `workspace/ai-engine/src/visual_event_ai/frame_pipeline.py`, `tests/test_frame_pipeline.py`
- Verified at: 2026-09-22
- Confidence: high for this environment; clean installs should use the `media` optional extra.

### FACT-007
- Claim: No verified ONNX model contract is currently present in the project資料目录; the ONNX provider therefore reports unavailable/fallback rather than loading an invented model.
- Evidence: no model file has been added; registry tests assert ONNX unavailable and `motion_cpu` selected.
- File/URL: `workspace/ai-engine/src/visual_event_ai/model_providers.py`, `workspace/docs/MODEL_PROVIDER_CONTRACT.md`
- Verified at: 2026-09-22
- Confidence: high for the current workspace.

## AI algorithm verification — 2026-09-23

### FACT-008
- Claim: The elderly-care and workshop plugins now call deterministic temporal reasoners and retain their evidence facts in generated events.
- Evidence: `workspace/ai-engine/plugins/elderly_care/plugin.py`, `plugins/workshop/plugin.py`, and `tests/test_plugins.py`; same-person/object/window checks, same-zone return and explicit observed-timeout checks pass.
- File/URL: `workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py`
- Confidence: high for local fixture behavior; no real action-model accuracy is implied.

### FACT-009
- Claim: `FrameFactExtractor` accepts configured zones; a three-frame JSONL fixture generated `left_zone` then `entered_zone` for the same tracked object, and the workshop plugin emitted removed/returned events.
- Evidence: `tests/test_fact_pipeline.py::test_configured_zone_transitions_reach_workshop_state_reasoner`.
- Limitation: `AnalysisService` currently constructs `FrameFactExtractor` with its default empty zones, so its standard jobs do not emit zone transitions.
- Confidence: high for the configured JSONL fixture path.

### FACT-010
- Claim: The complete local AI test suite returned 66 passed on 2026-09-23.
- Evidence: `$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONPATH='src'; python -B -m pytest -p no:cacheprovider -q` from `workspace/ai-engine`; submission verifier also ran 66 tests.
- Limitation: 218 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; all AI algorithm evidence remains Mock/fixture/CPU baseline.
- Confidence: high for this checkout and test environment.

### FACT-011
- Claim: Current built-in providers do not generate `hand_to_face` or `scene_observed`; the motion detector returns frame-difference regions rather than semantic object classes.
- Evidence: `workspace/ai-engine/src/visual_event_ai/providers.py`, `fact_pipeline.py`, and `model_providers.py`.
- Consequence: Complete medication reasoning and observed-timeout missing events need upstream action/scene facts; no real detector metric is available.
- Confidence: high for current source.

### FACT-012
- Claim: `CentroidTracker` now maximizes valid one-to-one matches under class/max-distance gating, then minimizes total centroid distance.
- Evidence: two tests reproduce a greedy assignment with total distance 18 versus the global optimum 10, and a gated case where greedy retains one track despite a valid two-match assignment. A separate brute-force comparison checked 1,200 small rectangular matrices against the local Hungarian solver.
- File/URL: `workspace/ai-engine/src/visual_event_ai/providers.py`, `tests/test_providers.py`
- Confidence: high for the synthetic assignment objective; not evidence of real MOT accuracy or reduced IDF1/HOTA errors.

### FACT-013
- Claim: `RelationEngine` normalizes naive timestamps as UTC and rejects per-instance timestamp regressions before mutating relation state.
- Evidence: relation unit tests cover naive/aware ordering and recovery after a rejected timestamp; a JSONL extraction test confirms an out-of-order frame raises before it can produce relation events.
- File/URL: `workspace/ai-engine/src/visual_event_ai/relations.py`, `tests/test_relations.py`, `tests/test_fact_pipeline.py`
- Confidence: high for one source/engine instance; no cross-source clock synchronization is implemented.

### FACT-014
- Claim: The complete AI source test suite returned 71 passed on 2026-09-23 after tracker and timestamp changes.
- Evidence: `$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONPATH='src'; python -B -m pytest -p no:cacheprovider -q` from `workspace/ai-engine`.
- Limitation: 218 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; local rule/fixture/CPU evidence only.
- Confidence: high for this checkout and test environment.

### FACT-015
- Claim: The curated submission copy was synchronized with the tracker assignment and timestamp-order changes and passed its own verifier at 71 tests.
- Evidence: `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK`; pytest temp data used a basetemp under `workspace/submission/ai-engine/runtime/` and the verifier cleaned `runtime` afterward. Post-scan found 0 forbidden artifacts and 0 sensitive literals; SHA-256 matched all 12 synchronized files.
- Verified at: 2026-09-23
- Confidence: high for the current staged package; frontend build was skipped by the explicit flag.

### FACT-016
- Claim: Relation extraction and temporal reasoning now use the same person-label classifier; `家属` and uppercase `Person` produce proximity/pickup facts in the relation layer.
- Evidence: `tests/test_relations.py::test_relation_engine_recognizes_person_aliases_consistently` and the JSONL `AnalysisService` test using `家属` both pass.
- File/URL: `workspace/ai-engine/src/visual_event_ai/entity_labels.py`, `relations.py`, `algorithm_reasoner.py`
- Confidence: high for supported fixture labels; this does not prove an upstream real detector emits correct labels.

### FACT-017
- Claim: The current AI source test suite returned 73 passed on 2026-09-23 after shared label integration.
- Evidence: Full pytest run with a project-local basetemp; 218 Python 3.14 FastAPI/Starlette deprecation warnings and no test failures.
- Confidence: high for this checkout.

### FACT-018
- Claim: The curated submission suite also returned 73 passed after shared label synchronization.
- Evidence: `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK`; post-scan found 0 forbidden artifacts and 0 sensitive literal hits; SHA-256 matched all 10 synchronized files.
- Limitation: frontend build was skipped by request scope; semantic results remain fixture/CPU-only.
- Confidence: high for the current staged package.

### FACT-019
- Claim: A supplied-keypoint geometry rule can produce a `hand_to_face` fact only when a confident wrist is near the nose and the same medication-object bounding box.
- Evidence: `tests/test_keypoint_actions.py` covers contact, confidence, non-medication rejection, distance rejection, and per-episode emission; `tests/test_core.py::test_local_keypoint_fixture_runs_complete_medication_reasoning_path` validates JSONL to a `suspected_medication` event through `AnalysisService`, with pending review and no medical-diagnosis claim.
- File/URL: `workspace/ai-engine/src/visual_event_ai/keypoint_actions.py`, `fact_pipeline.py`
- Limitation: Fixture keypoints are explicit input; this is not a pose detector and has no real-video accuracy evidence.
- Confidence: high for the deterministic fixture path.

### FACT-020
- Claim: AI source and curated submission suites returned 77 passed after keypoint action integration.
- Evidence: source full pytest and `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` both returned `77 passed`; project-local pytest basetemp was cleaned afterward.
- Limitation: 218 Python 3.14 FastAPI/Starlette deprecation warnings; no real pose model or authorized data metrics.
- Confidence: high for this checkout.

### FACT-021
- Claim: The keypoint-based medication path cannot borrow another person's proximity relation and the resulting event remains review-only.
- Evidence: `tests/test_keypoint_actions.py::test_keypoint_action_does_not_borrow_another_persons_medication_relation` and `tests/test_core.py::test_local_keypoint_fixture_runs_complete_medication_reasoning_path` pass; the latter asserts `pending`, `needs_review=true`, and `medical_diagnosis=false`.
- Limitation: Keypoints and object boxes are explicit fixture inputs; no real pose model is included.
- Confidence: high for this fixture and plugin path.

### FACT-022
- Claim: The complete AI source and curated submission suites returned 78 passed after cross-person association coverage.
- Evidence: Full source pytest and `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` both returned `78 passed`; post-scan found 0 forbidden artifacts / 0 sensitive literals and 15 synchronized file hashes matched.
- Limitation: 218 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; frontend build skipped.
- Confidence: high for this checkout and staged package.

### FACT-023
- Claim: The keypoint action extractor tolerates one missing sampled frame without emitting a duplicate `hand_to_face` edge, and rearms after a longer gap.
- Evidence: `tests/test_keypoint_actions.py::test_keypoint_action_tolerates_one_frame_keypoint_dropout_but_rearms_after_longer_gap`; full source and staged verifier both returned 79 passed after sync.
- File/URL: `workspace/ai-engine/src/visual_event_ai/keypoint_actions.py`, `fact_pipeline.py`
- Limitation: The one-frame grace is a rule default and has not been calibrated against real pose streams.
- Confidence: high for the sampled fixture sequence.

### FACT-024
- Claim: Relation geometry/configuration rejects invalid entity boxes/confidence, invalid zone dimensions, and non-finite or out-of-range distance/cooldown thresholds.
- Evidence: parameterized tests in `tests/test_relations.py`; targeted relations/fact-pipeline suite returned 23 passed, and the curated submission verifier returned `VERIFY_OK` / `93 passed` after synchronization.
- File/URL: `workspace/ai-engine/src/visual_event_ai/relations.py`
- Confidence: high for the accepted input boundaries; not evidence of real-world zone calibration.

### FACT-025
- Claim: In the integrated JSONL AnalysisService path, one sampled-frame keypoint dropout and reappearance within the grace interval does not duplicate `hand_to_face` evidence in the stored event.
- Evidence: `tests/test_core.py::test_local_keypoint_fixture_runs_complete_medication_reasoning_path` provides four frames and asserts exactly one `hand_to_face` fact in the resulting event; source and submission suites both pass.
- Limitation: The keypoints are synthetic fixture inputs, not model output from camera frames.
- Confidence: high for the deterministic frame-to-event path.

### FACT-026
- Claim: The AI service strictly parses optional AI_ZONES_JSON and injects the resulting Zone tuple into AnalysisService; an unset or empty array leaves zones disabled.
- Evidence: tests/test_zone_config.py rejects malformed JSON, unknown/missing fields, non-finite coordinates, non-positive dimensions, and duplicate trimmed IDs. tests/test_api.py verifies a configured JSONL zone exit/return through the API. Source and curated submission suites both returned 101 passed; 13 synchronized files matched SHA-256.
- File/URL: workspace/ai-engine/src/visual_event_ai/zone_config.py, app.py, service.py
- Limitation: Geometry uses synthetic detector boxes and pixel rectangles; there are no real camera coordinates or zone calibration data.
- Confidence: high for configuration parsing and the fixture service path.

### FACT-027
- Claim: WorkshopStateReasoner keeps pending removal state independently for the same tracked object in multiple zones; a return to one zone does not get overwritten by removal from another.
- Evidence: tests/test_algorithm_reasoner.py::test_workshop_reasoner_preserves_pending_removal_for_each_zone covers shelf A exit, bench B entry/exit, then separate returns to A and B. The regression failed before the fix and passes afterward; targeted reasoner/plugin/fact-pipeline tests returned 27 passed, and source plus staged suites returned 102 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py, workspace/ai-engine/tests/test_algorithm_reasoner.py
- Limitation: The events use synthetic facts; no real camera zone calibration or continuous multi-camera state is verified.
- Confidence: high for the deterministic within-infer fixture path.

### FACT-028
- Claim: When both a removal and a timeout observation identify a zone, WorkshopStateReasoner does not let an observation from another zone prove the object missing; a later same-zone observation can close the timeout.
- Evidence: tests/test_algorithm_reasoner.py::test_workshop_reasoner_requires_timeout_observation_from_removed_zone fails before the fix on a bench observation for a shelf removal, then passes with a shelf observation at the next timestamp. Targeted reasoner/plugin/fact-pipeline tests returned 28 passed; source and staged suites returned 103 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py, workspace/ai-engine/tests/test_algorithm_reasoner.py
- Limitation: Both facts are synthetic. An unscoped scene_observed retains global-coverage semantics and has no real upstream producer in this project.
- Confidence: high for scoped fact matching in one infer call.

### FACT-029
- Claim: A region-scoped explicit object_missing fact consumes pending removal evidence only from the same object and zone; a newer removal in another zone cannot replace the evidence.
- Evidence: tests/test_algorithm_reasoner.py::test_workshop_reasoner_scoped_explicit_missing_uses_same_zone_removal fails before the fix and verifies the shelf A removal timestamp/evidence after the fix. Targeted reasoner/plugin/fact-pipeline tests returned 29 passed; source and staged suites returned 104 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py, workspace/ai-engine/tests/test_algorithm_reasoner.py
- Limitation: The fact sequence is synthetic; unscoped object_missing retains global matching semantics and has no real upstream validation.
- Confidence: high for same-zone selection in one infer call.

### FACT-030
- Claim: Directly constructed zones receive the same core identity/geometry safeguards as environment-parsed zones; duplicate region IDs cannot collide in RelationEngine state, and blank metadata IDs do not equate different locations in the workshop reasoner.
- Evidence: tests/test_relations.py validates IDs, labels, numeric geometry normalization, duplicate rejection, and that rejected configuration does not advance relation time. tests/test_algorithm_reasoner.py rejects cross-location return matching for blank IDs. Targeted related tests returned 70 passed; source and staged suites returned 119 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/relations.py, algorithm_reasoner.py, tests/test_relations.py
- Limitation: All inputs are synthetic; this does not calibrate actual scene regions.
- Confidence: high for direct configuration validation and fixture relation-state isolation.

### FACT-031
- Claim: Entity inputs are normalized/validated at construction and RelationEngine rejects duplicate entity IDs before mutating temporal state.
- Evidence: tests/test_relations.py covers ID/label checks, numeric geometry/confidence boundaries, normalization, and duplicate-ID rejection followed by a valid earlier timestamp. Targeted relevant suite returned 83 passed; source and staged suites returned 136 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/relations.py, workspace/ai-engine/tests/test_relations.py
- Limitation: All entities are synthetic objects; no detector/tracker identity accuracy is implied.
- Confidence: high for direct object validation and duplicate-ID state safety.

### FACT-032
- Claim: FixtureDetector preserves fractional pixel boxes into relation extraction and rejects invalid confidence rather than clamping it.
- Evidence: tests/test_fact_pipeline.py::test_fractional_fixture_boxes_keep_relation_distance_and_threshold verifies a 50.8 px distance remains above the fixed 50 px near threshold, so neither near nor pickup_candidate is emitted. tests/test_providers.py rejects NaN, infinite, out-of-range, bool, string, and null confidence values. Targeted tests returned 26 passed; source and staged suites returned 145 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/providers.py, workspace/ai-engine/tests/test_providers.py, workspace/ai-engine/tests/test_fact_pipeline.py
- Limitation: The input is synthetic JSONL; no real detector score calibration or video accuracy is established.
- Confidence: high for fixture adapter precision and score validation.

### FACT-033
- Claim: CentroidTracker preserves identity when a supported person label varies in case or between the supported person aliases, while keeping person and object classes separate.
- Evidence: tests/test_providers.py covers Person -> person and Person -> 工作人员 track continuity; tests/test_fact_pipeline.py covers the same transition through JSONL detection/tracking/fact generation. Targeted tests returned 36 passed; source and staged suites returned 148 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/providers.py, workspace/ai-engine/tests/test_providers.py, workspace/ai-engine/tests/test_fact_pipeline.py
- Limitation: Synthetic centroids and labels only; no real-world IDF1/ID-switch evaluation.
- Confidence: high for the deterministic tested path.

### FACT-034
- Claim: JSONL fractional bbox coordinates reach relation-distance evaluation without truncation, and invalid fixture confidence cannot be clamped into a valid/high-confidence Detection or persisted event.
- Evidence: tests/test_fact_pipeline.py::test_fractional_fixture_boxes_keep_relation_distance_and_threshold verifies a 50.8 px distance remains above the 50 px threshold. tests/test_providers.py rejects invalid score variants. tests/test_api.py verifies the job fails and event storage remains empty. Full source/staged suites returned 149 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/providers.py, workspace/ai-engine/tests/test_providers.py, test_fact_pipeline.py, test_api.py
- Limitation: Inputs are synthetic JSONL fixtures; no real detector confidence calibration or scene accuracy is established.
- Confidence: high for the tested fixture/API path.

### FACT-035
- Claim: An absent objects key represents an empty fixture frame, but malformed explicit objects data is rejected rather than silently converted to no detections; the API job fails without persisting events.
- Evidence: tests/test_providers.py covers malformed rows/containers. tests/test_api.py::test_api_fails_malformed_fixture_detection_without_persisting_events verifies failed status, indexed error, and empty event storage. Source and staged suites returned 154 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/providers.py, workspace/ai-engine/tests/test_providers.py, workspace/ai-engine/tests/test_api.py
- Limitation: Tests use synthetic JSONL; no real detector completeness is established.
- Confidence: high for fixture parsing and API fail-closed behavior.

### FACT-036
- Claim: WorkshopStateReasoner deduplication preserves separate same-object/same-time event candidates when their zone ID or normalized location scopes differ, while still deduplicating same-scope candidates.
- Evidence: tests/test_algorithm_reasoner.py::test_workshop_reasoner_deduplicates_only_within_the_same_zone covers simultaneous A/B removals and timeouts under one global scene observation. Targeted reasoner/plugin tests returned 28 passed; full source and staged suites returned 155 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py, workspace/ai-engine/tests/test_algorithm_reasoner.py
- Limitation: The facts and zones are synthetic; event volume/calibration has not been evaluated on real footage.
- Confidence: high for deterministic candidate generation and scope-aware deduplication.

### FACT-037
- Claim: Numeric configuration constructors across reasoner, relation, motion-detection, and tracking components reject bool/string inputs and retain their range/finite checks.
- Evidence: parameterized tests in tests/test_algorithm_reasoner.py, tests/test_relations.py, and tests/test_providers.py cover bools, strings, NaN/Infinity, negative values, and out-of-range thresholds. The targeted group returned 120 passed; source and staged suites returned 173 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py, relations.py, providers.py
- Limitation: This validates local constructors only; deployment parameter sources are not calibrated from real data.
- Confidence: high for the listed test cases.

### FACT-038
- Claim: RelationEngine does not infer movement, person-object separation, or zone exit across an entity detection gap.
- Evidence: `tests/test_relations.py::test_relation_engine_does_not_infer_pair_transition_across_missing_detection` and `test_relation_engine_does_not_infer_zone_exit_or_motion_across_missing_detection` reproduce the behavior directly. `tests/test_fact_pipeline.py::test_frame_pipeline_does_not_infer_events_across_detection_gap` confirms it through tracked JSONL frames. Targeted relation/frame-pipeline tests returned 62 passed; source and curated submission suites both returned 180 passed, and submission verification returned `VERIFY_OK`.
- File/URL: workspace/ai-engine/src/visual_event_ai/relations.py, workspace/ai-engine/tests/test_relations.py, workspace/ai-engine/tests/test_fact_pipeline.py
- Limitation: Synthetic JSONL only. The conservative reset can miss real movement or zone transitions that occur entirely during an unobserved interval; no real occlusion or detector performance is established.
- Confidence: high for the deterministic tested behavior.

### FACT-039
- Claim: Boolean or malformed keypoint/box geometry cannot produce a `hand_to_face` action fact, and Boolean or incorrectly typed action configuration is rejected.
- Evidence: `tests/test_keypoint_actions.py` covers Boolean nose/wrist coordinates, Boolean confidence, Boolean bbox geometry, Boolean/string/range-invalid action settings, Boolean frame indexes, and identity fallback. `tests/test_fact_pipeline.py::test_boolean_keypoint_fixture_cannot_create_a_suspected_medication_event` verifies the JSONL frame-to-fact-to-elderly-care path does not promote proximity to a complete suspected event. Targeted keypoint/fact-pipeline tests returned 26 passed; source and curated submission suites returned 203 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/keypoint_actions.py, workspace/ai-engine/tests/test_keypoint_actions.py, workspace/ai-engine/tests/test_fact_pipeline.py
- Limitation: Synthetic keypoints only; there is no built-in pose model and no real-video action accuracy evidence.
- Confidence: high for the deterministic tested input contract.

### FACT-040
- Claim: MotionDetector preserves fractional grayscale intensities and rejects Boolean, non-finite, out-of-range, and non-numeric pixels instead of quantizing or clipping them into motion evidence.
- Evidence: `tests/test_providers.py::test_motion_detector_rejects_invalid_pixel_values_and_resets_history` checks malformed values and recovery after reset; `test_motion_detector_preserves_fractional_grayscale_thresholds` distinguishes a 19.1 intensity difference from a 20.0 threshold. The provider tests returned 43 passed; source and curated submission suites returned 203 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/providers.py, workspace/ai-engine/tests/test_providers.py
- Limitation: Synthetic grayscale matrices only; this does not measure real image noise, lighting changes, motion recall, or video accuracy.
- Confidence: high for the deterministic tested pixel contract.

### FACT-041
- Claim: Registry features and API inputs reject Boolean/string coercions and invalid gray pixels; empty or all-zero registration vectors return a client error without being persisted.
- Evidence: `tests/test_embeddings.py` covers Boolean/numeric-string vectors, out-of-range and Boolean gray pixels, fractional-intensity preservation, large finite norms, and invalid thresholds. `tests/test_api.py::test_registry_api_rejects_boolean_and_string_feature_values` verifies 422 for malformed types, 400 for empty/zero vectors or out-of-range gray values, and no persisted invalid registrations. Targeted embedding/API tests returned 35 passed; source and curated submission suites returned 223 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/embeddings.py, models.py, app.py; workspace/ai-engine/tests/test_embeddings.py, test_api.py
- Limitation: Registry features remain a CPU heuristic; these checks do not validate object or person recognition accuracy.
- Confidence: high for the deterministic feature and API contracts.

### FACT-042
- Claim: MedicationSequenceReasoner preserves distinct complete candidates for different object labels when object IDs are absent, while deduplicating duplicate evidence for the same normalized label.
- Evidence: `tests/test_algorithm_reasoner.py::test_medication_reasoner_deduplicates_same_unidentified_object_by_label` and `test_medication_reasoner_preserves_distinct_unidentified_objects_in_deduplication` cover the direct reasoner behavior. `tests/test_plugins.py::test_elderly_plugin_preserves_distinct_label_only_medication_events` confirms both candidates reach the elderly-care event output. Targeted reasoner/plugin tests returned 43 passed; source and curated submission suites returned 226 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py, workspace/ai-engine/tests/test_algorithm_reasoner.py, workspace/ai-engine/tests/test_plugins.py
- Limitation: Constructed facts only; the upstream detector/tracker may still fail to assign or preserve IDs, and real lookalike separation is unmeasured.
- Confidence: high for label-based candidate retention in the tested path.

### FACT-043
- Claim: MedicationSequenceReasoner rejects an explicitly labeled non-person subject even when that subject has an ID; an unlabeled ID-only subject remains compatible with legacy facts.
- Evidence: `tests/test_algorithm_reasoner.py::test_medication_reasoner_rejects_explicit_non_person_subject_even_with_id` asserts both complete and incomplete inference reject the subject. `tests/test_plugins.py::test_elderly_plugin_rejects_explicit_non_person_subject_even_with_id` confirms no elderly-care event is emitted. Targeted reasoner/plugin tests returned 45 passed; source and curated submission suites returned 228 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py, workspace/ai-engine/tests/test_algorithm_reasoner.py, workspace/ai-engine/tests/test_plugins.py
- Limitation: Synthetic facts only; upstream person-label accuracy is not measured.
- Confidence: high for the tested subject-label gate.

### FACT-044
- Claim: PrimitiveFact rejects Boolean, numeric-string, non-finite, and out-of-range confidence values before Pydantic can coerce them into valid scores.
- Evidence: tests/test_algorithm_reasoner.py::test_primitive_fact_rejects_coerced_or_invalid_confidence covers bool, string, NaN, Infinity, and range violations. A pre-fix reproduction converted True to 1.0 and "0.9" to 0.9, allowing the medication reasoner to emit suspected_medication; post-fix targeted reasoner/plugin tests returned 52 passed and source/curated suites returned 235 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/models.py, workspace/ai-engine/tests/test_algorithm_reasoner.py
- Limitation: The values are constructed fact inputs; real detector confidence calibration and accuracy remain unverified.
- Confidence: high for Pydantic input rejection and tested reasoner safety.

### FACT-045
- Claim: Medication reasoning does not stringify Boolean, fractional, or container-valued entity IDs into identities; malformed explicit object IDs also cannot trigger the object-label fallback.
- Evidence: parameterized tests in `tests/test_algorithm_reasoner.py::test_medication_reasoner_rejects_malformed_person_identity_values` and `test_medication_reasoner_does_not_fallback_to_labels_for_malformed_object_ids` cover the malformed values. Existing tests continue to prove integer/string identity handling and fallback for blank IDs. Targeted reasoner/plugin tests returned 58 passed; source and curated submission suites returned 241 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py, workspace/ai-engine/tests/test_algorithm_reasoner.py
- Limitation: Constructed facts only; the upstream detector/tracker's real identity assignment and persistence are unmeasured.
- Confidence: high for the deterministic identity parsing and matching rules.

### FACT-046
- Claim: A low-confidence matching hand-to-face fact does not mask a later confidence-qualified action, and a low-confidence optional put-down fact does not suppress an otherwise complete medication candidate.
- Evidence: `tests/test_algorithm_reasoner.py::test_medication_reasoner_skips_weak_hand_for_later_qualified_action` and `test_medication_reasoner_ignores_low_confidence_optional_putdown` cover both cases. Targeted reasoner/plugin tests returned 60 passed; source and curated submission suites returned 243 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py, workspace/ai-engine/tests/test_algorithm_reasoner.py
- Limitation: Constructed facts only; real action-score calibration and event precision/recall are unmeasured.
- Confidence: high for the deterministic rule ordering and optional-evidence behavior.

### FACT-047
- Claim: Known medication storage/location labels are not treated as medicine objects unless an explicit medication category is supplied.
- Evidence: `tests/test_algorithm_reasoner.py::test_medication_reasoner_rejects_medication_storage_as_the_medicine_object` covers Chinese/English cabinet, shelf, pharmacy labels; `test_explicit_medication_category_overrides_storage_like_display_label` checks category precedence. `tests/test_fact_pipeline.py::test_storage_fixture_label_cannot_create_medication_action_or_event` confirms the JSONL frame-to-elderly-plugin path emits neither `hand_to_face` for the cabinet nor a medication event. Targeted reasoner/fact/plugin tests returned 76 passed; source and curated suites returned 252 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/entity_labels.py, workspace/ai-engine/tests/test_algorithm_reasoner.py, workspace/ai-engine/tests/test_fact_pipeline.py
- Limitation: Label heuristic and synthetic JSONL only; alias coverage and real detector classification quality are unmeasured.
- Confidence: high for the listed labels and tested pipeline.

### FACT-048
- Claim: Stateful motion detection history is isolated per frame-extraction job, so interleaved sources do not reset or consume one another's previous frame.
- Evidence: `tests/test_model_providers.py::test_motion_cpu_sessions_keep_independent_history_when_sources_interleave` interleaves two camera frame sequences through separate sessions. `tests/test_fact_pipeline.py::test_frame_fact_extractor_requests_job_local_motion_provider_sessions` verifies each extraction requests a distinct session and emits its own motion-region detection. Targeted provider/frame-pipeline tests returned 13 passed; source and curated submission suites returned 254 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/model_providers.py, workspace/ai-engine/src/visual_event_ai/fact_pipeline.py, workspace/ai-engine/tests/test_model_providers.py, workspace/ai-engine/tests/test_fact_pipeline.py
- Limitation: Synthetic grayscale frame sequences only; this verifies provider-state isolation, not real video detection accuracy.
- Confidence: high for concurrent session separation and extraction wiring in the tested path.

### FACT-049
- Claim: Detection boxes, relation entities, configured zones, and keypoint action boxes reject individually finite coordinates whose computed right or bottom extent overflows to infinity.
- Evidence: `tests/test_providers.py::test_detection_rejects_finite_coordinates_with_overflowing_bbox_extent`, the finite-overflow case in `tests/test_relations.py::test_entity_rejects_invalid_geometry`, `test_zone_rejects_finite_values_with_overflowing_extent`, the malformed config case in `tests/test_zone_config.py`, and `tests/test_keypoint_actions.py::test_keypoint_action_rejects_bbox_with_overflowing_extent` cover the boundaries. Targeted provider/relation/zone/keypoint tests returned 130 passed; source and curated suites returned 259 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/providers.py, relations.py, keypoint_actions.py; tests/test_providers.py, test_relations.py, test_zone_config.py, test_keypoint_actions.py
- Limitation: Synthetic extreme coordinates only; deployed camera range/calibration is not measured.
- Confidence: high for computed-extent rejection in the covered constructors and action input path.

### FACT-050
- Claim: Relation cooldown state cannot collide merely because different valid entity/zone IDs contain the same delimiter characters.
- Evidence: `tests/test_relations.py::test_relation_cooldowns_do_not_collide_for_colon_delimited_entity_ids` verifies distinct person/object pairs each emit near and pickup facts; `test_zone_cooldowns_do_not_collide_for_colon_delimited_ids` verifies distinct zones each emit their own entry. Relation tests returned 60 passed; source and curated suites returned 261 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/relations.py, workspace/ai-engine/tests/test_relations.py
- Limitation: Tests use synthetic colon-containing IDs; they verify cooldown-key separation, not upstream ID allocation.
- Confidence: high for tuple-key isolation in the tested event types.

### FACT-051
- Claim: Oversized keypoint or bbox integers that cannot convert to finite floats are treated as absent action geometry rather than raising OverflowError and aborting frame extraction.
- Evidence: `tests/test_keypoint_actions.py::test_keypoint_action_ignores_unrepresentable_integer_geometry` covers direct action parsing; `tests/test_fact_pipeline.py::test_jsonl_unrepresentable_keypoint_is_treated_as_missing_action_evidence` verifies JSONL extraction completes, preserves the proximity fact, and emits no hand-to-face or suspected-medication event. Targeted keypoint/frame-pipeline tests returned 33 passed; source and curated submission suites returned 265 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/keypoint_actions.py, workspace/ai-engine/tests/test_keypoint_actions.py, workspace/ai-engine/tests/test_fact_pipeline.py
- Limitation: Synthetic oversized integers only; real detector coordinate ranges and action accuracy are unmeasured.
- Confidence: high for the tested fail-closed conversion path.

### FACT-052
- Claim: Stopping a running analysis job propagates cancellation through FrameFactExtractor into the frame provider, and cancellation at a frame boundary leaves the job stopped without plugin evaluation or event persistence.
- Evidence: `tests/test_core.py::test_stopping_running_frame_job_cancels_provider_and_finishes_as_stopped` uses a provider that yields one frame then waits on the job token; the stop request wakes it, the worker exits as stopped, and the event store remains empty. Targeted core/fact/frame-pipeline tests returned 23 passed; source and curated suites returned 266 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/service.py, fact_pipeline.py, workspace/ai-engine/tests/test_core.py
- Limitation: Synchronous media reads already in progress cannot be forcibly interrupted; the test uses a cancellation-aware synthetic provider and does not measure real decoder interruption latency.
- Confidence: high for token propagation and frame-boundary stop behavior.

### FACT-053
- Claim: MotionDetector maps sampled image-region boxes back to source-frame pixel coordinates and resets its previous-frame comparison when original geometry/stride changes, even if the sampled matrix dimensions stay the same.
- Evidence: `tests/test_providers.py::test_motion_detector_maps_sampled_image_boxes_back_to_source_pixels` verifies a stride-2 320x320 sample returns the original-pixel bbox; `test_motion_detector_resets_history_when_image_geometry_changes_but_sample_shape_does_not` checks resolution/stride reset. Provider tests returned 46 passed; source and curated submission suites returned 268 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/providers.py, workspace/ai-engine/tests/test_providers.py
- Limitation: Synthetic array-like image only; OpenCV throughput and real-camera geometric calibration remain unverified.
- Confidence: high for the tested sampling geometry and reset contract.

### FACT-054
- Claim: Analysis job completion is idempotent and event persistence is atomic with the completed status; stop and completion races have a single terminal outcome.
- Evidence: test_completed_job_rerun_does_not_duplicate_events verifies rerunning a completed job does not duplicate events. test_stop_racing_with_atomic_completion_returns_completed verifies that a completion transaction which wins the per-job terminal lock remains completed when a later stop arrives. SQLiteStore.complete_job writes the full event batch and terminal job status in one transaction. Source and curated submission suites returned 270 passed; verifier returned VERIFY_OK.
- File/URL: workspace/ai-engine/src/visual_event_ai/service.py, storage.py; workspace/ai-engine/tests/test_core.py
- Limitation: Deterministic local SQLite/provider tests only; no real media decoder or hardware evaluation.
- Confidence: high for atomic persistence and terminal race behavior in the tested paths.

### FACT-055
- Claim: WorkshopStateReasoner does not infer a temporal return from simultaneous left_zone and entered_zone facts, and its same-time behavior does not depend on input order.
- Evidence: test_workshop_reasoner_does_not_infer_return_from_equal_timestamp_zone_facts exercises both permutations and emits no object_returned candidate. test_workshop_reasoner_does_not_attach_equal_timestamp_removal_to_explicit_transitions verifies simultaneous explicit return/missing facts remain standalone in both orders. Targeted reasoner/plugin tests returned 72 passed; source and curated suites returned 274 passed, verifier returned VERIFY_OK.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py; workspace/ai-engine/tests/test_algorithm_reasoner.py
- Limitation: Deterministic constructed facts only; real timestamp precision and camera event accuracy remain unmeasured.
- Confidence: high for equal-timestamp handling and order independence in the tested transitions.

### FACT-056
- Claim: MedicationSequenceReasoner and KeypointActionExtractor do not treat common medication instruction/list/prescription document labels as medicine objects; explicit medicine/medication/drug category remains authoritative.
- Evidence: test_medication_reasoner_rejects_medication_documents_as_the_medicine_object covers 12 Chinese and English labels; test_explicit_medication_category_overrides_document_like_display_label checks precedence. The JSONL frame-to-elderly-plugin test verifies 药品说明书 yields no hand_to_face or suspected_medication. Targeted reasoner/plugin tests returned 85 passed; source and curated suites returned 288 passed, verifier returned VERIFY_OK.
- File/URL: workspace/ai-engine/src/visual_event_ai/entity_labels.py; workspace/ai-engine/src/visual_event_ai/keypoint_actions.py; workspace/ai-engine/tests/test_algorithm_reasoner.py; workspace/ai-engine/tests/test_fact_pipeline.py
- Limitation: Synthetic labels/keypoints only; real detector classification and accuracy are unmeasured.
- Confidence: high for the enumerated lexical exclusions and explicit-category override.

### FACT-057
- Claim: RelationEngine clears cooldown state when the associated entity, person-object pair, or zone key is absent, and does not emit relation/motion facts when finite-coordinate arithmetic produces a non-finite distance.
- Evidence: test_relation_engine_resets_pair_cooldown_after_detection_gap, test_relation_engine_resets_motion_cooldown_after_entity_gap, and test_relation_engine_resets_zone_cooldown_after_entity_gap verify fresh events after gaps despite long cooldowns. test_relation_engine_omits_pair_facts_when_finite_coordinates_overflow_distance and test_relation_engine_omits_motion_when_finite_coordinates_overflow_displacement verify fail-closed numerical behavior. Relation tests returned 65 passed; source and curated suites returned 293 passed, verifier returned VERIFY_OK.
- File/URL: workspace/ai-engine/src/visual_event_ai/relations.py; workspace/ai-engine/tests/test_relations.py
- Limitation: Synthetic state transitions and extreme finite coordinates only; real camera cadence and coordinate ranges are unmeasured.
- Confidence: high for cooldown pruning and non-finite-distance handling in the tested paths.

### FACT-058
- Claim: AI geometry, threshold, zone, and duration conversion boundaries reject unrepresentable large numeric inputs with ValueError instead of leaking OverflowError; temporal reasoners reject durations outside timedelta's supported range and revalidate fact confidence before reasoning.
- Evidence: new tests cover Detection bbox/confidence, Entity bbox/confidence, Zone coordinates, AI_ZONES_JSON coordinates, tracker/relation thresholds, reasoner float/timedelta thresholds, and post-construction PrimitiveFact confidence mutation. Targeted numeric cases returned 53 passed; reasoner/plugin tests returned 95 passed; source and curated suites returned 311 passed, verifier returned VERIFY_OK.
- File/URL: workspace/ai-engine/src/visual_event_ai/providers.py, relations.py, zone_config.py, algorithm_reasoner.py; corresponding tests/test_providers.py, test_relations.py, test_zone_config.py, test_algorithm_reasoner.py
- Limitation: Synthetic extreme numbers only; deployed image coordinate ranges and runtime configuration distributions are not measured.
- Confidence: high for the tested numeric conversion boundaries and reasoner confidence revalidation.

### FACT-059
- Claim: FramePipeline rejects Boolean, fractional, string, and negative interval/max-frame arguments, rejects intervals outside timedelta range, and preserves max_frames=0 as an empty result.
- Evidence: test_frame_pipeline_rejects_invalid_interval_types_and_ranges covers Boolean, fractional, string, negative, and oversized interval values; test_frame_pipeline_rejects_invalid_frame_limits covers invalid frame caps; test_frame_pipeline_allows_zero_frame_limit checks the empty-result contract. Frame-pipeline tests returned 15 passed; source and curated suites returned 321 passed, verifier returned VERIFY_OK.
- File/URL: workspace/ai-engine/src/visual_event_ai/frame_pipeline.py; workspace/ai-engine/tests/test_frame_pipeline.py
- Limitation: Mock/fixture iteration only; no real decoder cadence or hardware is measured.
- Confidence: high for the public FramePipeline argument contract exercised by the tests.

### FACT-060
- Claim: OpenCVFrameProvider normalizes missing, non-finite, non-positive, or unrepresentable FPS metadata to a 25 fps fallback; invalid/unrepresentable PTS falls back to read_index/fps, and impossible timestamps fail as FramePipelineError rather than leaking OverflowError.
- Evidence: test_opencv_provider_falls_back_when_fps_metadata_is_invalid covers None, NaN, Infinity, negative, and oversized integer FPS. test_opencv_provider_falls_back_when_position_metadata_is_invalid covers NaN, Infinity, and oversized finite PTS. Targeted metadata tests returned 8 passed; source and curated suites returned 329 passed, verifier returned VERIFY_OK.
- File/URL: workspace/ai-engine/src/visual_event_ai/frame_pipeline.py; workspace/ai-engine/tests/test_frame_pipeline.py
- Limitation: Simulated metadata and generated local AVI only; real corrupted codecs/cameras are not tested.
- Confidence: high for the enumerated metadata fallback and range-error paths.

### FACT-061
- Claim: A recovered malformed JSONL record creates an explicit observation boundary, and frame-to-fact plus temporal reasoning cannot reuse state or pair evidence across that unknown interval.
- Evidence: `test_jsonl_fixture_skips_bad_lines_and_supports_cancel` verifies the next valid frame carries `discontinuity_before`, reason, and skipped line metadata. `test_frame_fact_extractor_resets_temporal_state_after_recovered_jsonl_gap` verifies a fresh segment emits pickup evidence but no cross-gap motion, putdown, or zone-leave fact. `test_frame_fact_extractor_starts_new_detector_session_after_discontinuity` verifies session isolation. `test_relation_engine_discontinuity_reset_preserves_timestamp_regression_guard`, `test_medication_reasoner_does_not_pair_actions_across_observation_gap`, and `test_workshop_reasoner_does_not_infer_missing_across_observation_gap` cover relation timestamp safety and cross-segment temporal rejection. Targeted gap tests returned 6 passed; reasoner/plugin tests returned 97 passed; source and curated suites returned 334 passed with `VERIFY_OK`.
- File/URL: workspace/ai-engine/src/visual_event_ai/frame_pipeline.py, fact_pipeline.py, relations.py, algorithm_reasoner.py; corresponding tests/test_frame_pipeline.py, test_fact_pipeline.py, test_relations.py, test_algorithm_reasoner.py
- Limitation: Synthetic malformed JSONL and constructed facts only. Real decoder reconnects, network gaps, model outputs, and actions that occur entirely inside an unobserved interval remain unmeasured; the conservative reset can miss such actions.
- Confidence: high for the tested discontinuity marker, state reset, timestamp guard, and same-segment matching paths.

### FACT-062
- Claim: The user-provided AIC rule PDFs support treating `AI+场景创新` as the current candidate direction, while privacy/skeletonization, real application evidence, and robot/hardware evidence remain unverified requirements rather than implemented features.
- Evidence: The notice PDF defines seven open tracks and separates AI+scene from AI+hardware. The detailed rule PDF pages 2–3 require originality, truthful evidence, privacy/compliance, and material completeness; page 3 sets title/summary/video/PDF submission limits; page 16 scores AI+scene as 20/15/20/15/10/15/5; pages 17–18 require needs analysis, implementation, testing/validation, application effects, and reproducible code/model references. Pages were text-extracted and representative pages were rendered for visual review. `AIC_ALGORITHM_COMPETITION_ALIGNMENT.md` records the source boundary and evidence matrix.
- File/URL: 关于举办第八届AIC算法创新赛道竞赛的通知2604291.pdf; 2026AIC算法创新赛赛题规则汇总260506-1.pdf; workspace/docs/AIC_ALGORITHM_COMPETITION_ALIGNMENT.md; workspace/docs/EXPERIMENT_PLAN.md
- Limitation: These are user-provided local PDFs and were not independently checked against a later official website revision. They establish submission requirements, not project performance, user demand, privacy compliance, or competition results.
- Confidence: high for the extracted page-level requirements in these files; medium for final track selection until the team confirms the submission direction.

### FACT-063
- Claim: The frame preview REST boundary does not return top-level raw pixel matrices for the supported image/gray/pixel payload keys.
- Evidence: Before the fix, a JSONL payload with `gray: [[1,2],[3,4]]` passed through `/api/v1/sources/frames` unchanged because `_frame_payload_for_api` only sanitized `image`. It now replaces `image`, `gray`, `pixels`, and `raw_pixels` with encoding/shape summaries. `test_api_frame_preview_redacts_fixture_pixel_matrices` verifies the 2x2 grayscale case; API tests returned 8 passed, source and curated suites returned 335 passed with `VERIFY_OK`.
- File/URL: workspace/ai-engine/src/visual_event_ai/app.py; workspace/ai-engine/tests/test_api.py; workspace/docs/AI_ALGORITHM_DESIGN.md; workspace/docs/EXPERIMENT_PLAN.md
- Limitation: The guard covers top-level REST payload keys only. Provider memory can still hold raw frames, nested or future pixel fields require explicit review, and camera-side skeletonization/raw-frame retention are not established.
- Confidence: high for the tested REST serialization path and supported provider payload shapes.

### FACT-064
- Claim: Workshop temporal state cannot be paired across mismatched continuity segments, even when the caller omits an explicit `observation_gap` fact.
- Evidence: `test_workshop_reasoner_does_not_pair_explicit_transitions_across_segments` verifies that a later-segment return and explicit missing remain standalone instead of consuming an earlier removal. `test_workshop_reasoner_does_not_use_scene_observation_from_another_segment` verifies that a later-segment `scene_observed` cannot create timeout missing evidence. Reasoner/plugin tests returned 99 passed; source and curated suites returned 337 passed with `VERIFY_OK`.
- File/URL: workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py; workspace/ai-engine/tests/test_algorithm_reasoner.py; workspace/docs/TEMPORAL_EVENT_REASONING.md; workspace/docs/SCENE_PLUGINS_PHASE6_7.md
- Limitation: Synthetic facts only. Upstream continuity metadata propagation outside `FrameFactExtractor`, real stream reconnect behavior, and real event accuracy remain unverified.
- Confidence: high for the tested pending-removal matching and timeout-observation paths; legacy facts without metadata intentionally map to segment 0.

### FACT-065
- Claim: Frame preview REST serialization recursively redacts recognized nested image and sensor pixel fields while preserving non-pixel pose metadata.
- Evidence: `test_api_frame_preview_redacts_nested_image_and_sensor_arrays` covers nested hyphenated `Image-Data`, camelCase `rawPixels`, `depth_map`, `Thermal-Map`, and keypoint metadata. The sanitizer normalizes key names and returns encoding/shape summaries for recognized image/RGB/BGR/grayscale/pixel/depth/thermal/infrared/raw-frame fields. Targeted privacy tests returned 2 passed; source and curated suites returned 338 passed with `VERIFY_OK`.
- File/URL: workspace/ai-engine/src/visual_event_ai/app.py; workspace/ai-engine/tests/test_api.py; workspace/docs/REFERENCE_ALGORITHM_AUDIT.md
- Limitation: Name-based recognition cannot classify every future custom field, and camera-side raw-frame retention/skeletonization are not proven.
- Confidence: high for the normalized names and nested shapes exercised by the regression.

### FACT-066
- Claim: Four user-provided DOCX reference works were reviewed as method and evidence references without promoting their external metrics or hardware claims to this project's evidence.
- Evidence: Structural extraction covered `智隐云眸最新V1.docx` (privacy skeletonization, keypoints, multimodal action, tracking), `物联网应用类作品技术文档【终稿】002.docx` (AlphaPose/YOLO/bone replay/testing claims), `面向复杂实验室环境的多模态感知 (1).docx` (multimodal quality gating/world model/safety ideas), and `MoMaGen.docx` (constrained demo generation and sim-to-real limits). `REFERENCE_ALGORITHM_AUDIT.md` records reusable methods and source-specific boundaries. Original DOCX files were not modified.
- File/URL: workspace/算法精英/智隐云眸最新V1.docx; workspace/算法精英/物联网应用类作品技术文档【终稿】002.docx; workspace/算法精英/面向复杂实验室环境的多模态感知 (1).docx; workspace/算法精英/MoMaGen.docx; workspace/docs/REFERENCE_ALGORITHM_AUDIT.md
- Limitation: LibreOffice was unavailable for page-image rendering, so layout-level visual QA could not be completed; text, tables, styles, and embedded-image counts were inspected with bundled `python-docx`. External claims remain unverified.
- Confidence: high for document content extraction and source boundary; low for any external performance claim until independently reproduced.

### FACT-067
- Claim: The current project has an explicit staged AI algorithm analysis plan derived from the three supplied reference DOCX works and the existing source/fixture baseline.
- Evidence: `workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md` defines P0 privacy/schema, P1 single-camera detector/pose/tracking, P2 temporal scene reasoning, P3 multimodal quality gating, and P4 real hardware validation. It names the reusable ideas from the reference documents and states the prerequisite evidence for each stage. The plan is synchronized to `workspace/submission/docs/`.
- File/URL: workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md; workspace/算法精英/物联网应用类作品技术文档【终稿】002.docx; workspace/算法精英/智隐云眸最新V1.docx; workspace/算法精英/面向复杂实验室环境的多模态感知 (1).docx
- Limitation: This is a planning artifact. It does not establish real models, datasets, metrics, privacy compliance, or robot performance.
- Confidence: high for the plan's scope and evidence gates; external DOCX claims remain unverified.

### FACT-068
- Claim: Reusable keypoint action extraction isolates its debounce and frame-index state by source and rejects mixed-source observations in one call.
- Evidence: `test_keypoint_action_resets_episode_state_when_source_changes` emits an action for source 1 and a fresh action after switching to source 2 with frame index reset. `test_keypoint_action_rejects_mixed_sources_in_one_frame` verifies mixed source observations fail closed. Full source suite returned 340 passed.
- File/URL: workspace/ai-engine/src/visual_event_ai/keypoint_actions.py; workspace/ai-engine/tests/test_keypoint_actions.py; workspace/docs/AI_ALGORITHM_DESIGN.md; workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md
- Limitation: This validates component state isolation with synthetic observations; it does not validate real pose-model identity continuity, camera handoff, or cross-camera re-identification.
- Confidence: high for the source boundary and mixed-input contract exercised by the tests.

### FACT-069
- Claim: Keypoint action inference rejects relation evidence from a different explicit source and receives source provenance on facts generated by `FrameFactExtractor`.
- Evidence: `test_keypoint_action_rejects_relation_from_another_source` passes observations from `fixture://cam-01` with a relation marked `fixture://cam-02` and expects a source error. `test_local_jsonl_frames_become_unified_facts` verifies `source_id` is propagated into generated fact metadata. Full source and curated suites returned 341 passed with `VERIFY_OK`.
- File/URL: workspace/ai-engine/src/visual_event_ai/keypoint_actions.py, fact_pipeline.py; workspace/ai-engine/tests/test_keypoint_actions.py, test_fact_pipeline.py; workspace/docs/AI_ALGORITHM_DESIGN.md
- Limitation: Synthetic source IDs only. This prevents explicit fact mixing but does not solve real cross-camera re-identification or identity stability.
- Confidence: high for the explicit source-provenance contract and tested mismatch rejection.

### FACT-070
- Claim: Keypoint action inference cannot borrow a relation fact from an older frame; observations in one extraction call must share a UTC timestamp, while equivalent timezone representations match.
- Evidence: `test_keypoint_action_ignores_relation_from_an_older_frame` produces no action for a stale relation. `test_keypoint_action_rejects_observations_from_different_frame_timestamps` rejects mixed-frame observations. `test_keypoint_action_matches_equivalent_timezone_timestamps` confirms UTC normalization. Full source and curated suites returned 344 passed with `VERIFY_OK`.
- File/URL: workspace/ai-engine/src/visual_event_ai/keypoint_actions.py; workspace/ai-engine/tests/test_keypoint_actions.py; workspace/docs/AI_ALGORITHM_DESIGN.md; workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md
- Limitation: Synthetic timestamps only. Real decoder precision, asynchronous pose/relationship delivery, and model latency are not measured.
- Confidence: high for the tested same-frame and UTC-normalized matching contract.


### FACT-071
- Claim: Temporal reasoners no longer combine explicit evidence from different sources, and emitted keypoint action facts preserve their source when observations provide one.
- Evidence: `test_medication_reasoner_does_not_pair_explicit_facts_across_sources`, `test_medication_reasoner_rejects_malformed_source_provenance_for_pairing`, `test_workshop_reasoner_does_not_pair_explicit_transitions_across_sources`, and `test_workshop_reasoner_does_not_use_observation_from_another_source_for_missing` all pass. `test_keypoint_action_emits_once_for_wrist_near_face_and_same_medication_object` verifies `metadata.source_id`. Source and curated suites both returned `348 passed` with `VERIFY_OK`.
- File/URL: `workspace/ai-engine/src/visual_event_ai/algorithm_reasoner.py`, `workspace/ai-engine/src/visual_event_ai/keypoint_actions.py`, corresponding test files, `workspace/docs/AI_ALGORITHM_DESIGN.md`, `workspace/docs/TEMPORAL_EVENT_REASONING.md`, `workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md`.
- Limitation: Missing provenance on legacy facts is intentionally treated as unknown for compatibility; this does not establish camera handoff, re-identification, real pose quality, or any hardware behavior.
- Confidence: high for the explicit source-pairing contract and local regressions; low for external identity continuity until authorized data exists.


### FACT-072
- Claim: Pixel-bearing detector metadata is redacted before it can enter facts, vision-preview responses, job metadata, or SQLite event/job payloads.
- Evidence: `test_privacy_sanitizer_redacts_nested_pixel_channels_but_keeps_algorithm_metadata` verifies recursive key normalization and shape summaries; `test_frame_fact_pipeline_redacts_pixel_metadata_before_fact_storage` verifies detector metadata is sanitized before `PrimitiveFact`; `test_api_vision_preview_redacts_detector_metadata` verifies REST observation metadata; `test_sqlite_event_and_job_metadata_redact_pixel_arrays` verifies event/job persistence and retrieval. Full source and curated suites returned `352 passed` with `VERIFY_OK`.
- File/URL: `workspace/ai-engine/src/visual_event_ai/privacy.py`, `app.py`, `fact_pipeline.py`, `service.py`, `storage.py`, corresponding tests, `workspace/docs/AI_ALGORITHM_DESIGN.md`.
- Limitation: The sanitizer recognizes documented image-like key names and keeps summaries; it does not prove camera-source deletion, detect arbitrary provider-specific aliases, or replace a real privacy-preserving camera pipeline.
- Confidence: high for the tested software metadata/API/SQLite boundary; external sensor privacy remains unverified.


### FACT-073
- Claim: The AI frame pipeline has a fail-closed software quality gate for optional multimodal channels.
- Evidence: `test_quality_gate_is_ungated_when_metadata_is_absent` confirms backward compatibility; `test_quality_gate_allows_with_one_usable_channel_but_marks_degraded` confirms partial-channel continuation; `test_quality_gate_blocks_when_required_channel_is_unusable` and `test_frame_fact_pipeline_blocks_inference_when_required_channel_is_unusable` confirm observation-gap/reset behavior; malformed contract parametrization rejects bad values. Source and curated suites returned `363 passed` with `VERIFY_OK`.
- File/URL: `workspace/ai-engine/src/visual_event_ai/quality.py`, `workspace/ai-engine/src/visual_event_ai/fact_pipeline.py`, `workspace/ai-engine/tests/test_quality.py`, `workspace/ai-engine/tests/test_fact_pipeline.py`, `workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md`, `workspace/docs/AI_ALGORITHM_DESIGN.md`.
- Limitation: No physical audio/thermal/event-camera stream, clock synchronization, channel calibration or ablation is present; scores are provider-supplied metadata and are not sensor measurements.
- Confidence: high for the software contract and fixture fail-closed behavior; external multimodal performance remains unverified.

### FACT-074
- Claim: The existing AIC project was initialized and pushed as a private GitHub development repository without replacing the existing project contents.
- Evidence: `gh repo view` reports `weiyang02520-ops/aic-visual-event-platform`, `PRIVATE`, default branch `main`; `git ls-remote --heads origin main` reports `9481004b94e983faa2dd8780c021b6fa6c0806a8`, matching local `main`. The initial commit message is `chore: initialize AIC visual event AI development repository`.
- Included paths: root `README.md`, `workspace/ai-engine`, `workspace/frontend` source, `workspace/docs`, `workspace/submission` and current `agent-state` Markdown.
- Excluded paths: unpublished root PDF/DOCX material, `workspace/source-snapshots`, `agent-state/rollback`, runtime/cache/build/dependency directories, model weights and secret-bearing files according to the root `.gitignore` and staged-file audit.
- Verification: staged content scan found no tracked non-example `.env`, credential pattern, private key, model weight or >10 MB tracked file; the AI verifier returned `VERIFY_OK` / `363 passed`.
- Limitation: GitHub access is private to the authenticated account/team; repository contents do not prove real model, camera, sensor or robot performance.
- Confidence: high for repository initialization, staged-file exclusions and remote branch identity.
