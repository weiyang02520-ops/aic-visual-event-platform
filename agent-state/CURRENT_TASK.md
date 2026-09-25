# Current Task

## Current Focus (2026-09-23)

Continue the AI recognition algorithm audit and deliver locally verifiable improvements. This focus supersedes the older Phase 4 description below for the current task.

### Scope

- Keep every file change, test basetemp, and cleanup under C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料; within that root, modify only workspace/ai-engine, AI algorithm docs and their concise evidence summaries in workspace/docs and workspace/submission, and this project's agent-state.
- Keep frontend visual work and long-form competition writing out of this task.
- Distinguish Mock/fixture/CPU baseline results from real data, trained models, and robot evidence.

### Current acceptance

- [x] Read current task/state documents and inspect the AI source before editing.
- [x] Verify and integrate the temporal reasoners with the elderly-care and workshop plugins.
- [x] Require same-person/same-object/time-window evidence for complete medication cues.
- [x] Require explicit scene observation for timeout-missing events and same-zone evidence for zone returns.
- [x] Isolate frame-difference detector state across sources/jobs and reject malformed pixel matrices.
- [x] Prevent duplicate bounding boxes from collapsing to one normalized track ID.
- [x] Replace greedy centroid edges with distance-gated maximum-cardinality/minimum-total-distance assignment.
- [x] Normalize relation timestamps to UTC and fail closed on per-source timestamp regressions.
- [x] Reject non-finite/invalid entity geometry, zone dimensions, confidence, and relation thresholds.
- [x] Share person-label normalization between relation extraction and temporal reasoning, including the `家属` and case-insensitive English aliases.
- [x] Generate review-only `hand_to_face` facts from explicit, confident keypoints that satisfy the face/wrist/medication geometry rule.
- [x] Reject using a different person's proximity relation to associate a hand-to-face fact with a medication object.
- [x] Debounce keypoint action facts across one missing sample while rearming after a longer gap.
- [x] Reject malformed/non-finite embedding matrices.
- [x] Update AI algorithm documentation and full-suite test evidence.
- [x] Synchronize the relation-geometry validation into the curated AI submission and rerun its verifier/contamination scan.
- [x] Review the detector, tracker, embedding, relation and frame-to-fact paths; record verified behavior and semantic input gaps.
- [x] Clear motion, person-object proximity and zone continuity state across missing detections; verify at relation and JSONL frame-pipeline levels.
- [x] Reject bool/out-of-range grayscale samples and preserve fractional intensity in the motion CPU baseline; validate keypoint geometry/config so malformed Boolean values cannot create action evidence.
- [x] Reject Boolean/string registry features before API coercion, validate grayscale and match-threshold contracts, and map empty/zero registration vectors to client errors without saving records.
- [x] Preserve distinct medication candidates by falling back to normalized labels for deduplication only when entity IDs are absent; verify through the elderly-care plugin.
- [x] Reject explicit non-person subjects from complete and incomplete medication reasoning even when they carry IDs; retain the legacy ID-only subject format.
- [x] Reject Boolean/string/non-finite/out-of-range PrimitiveFact confidence before Pydantic coercion so malformed scores cannot cross reasoner thresholds.
- [x] Continue past low-confidence matching hand facts to find later qualified evidence; ignore low-confidence optional put-down support so it cannot suppress a complete sequence.
- [x] Exclude medication storage/location labels from drug-object reasoning unless an explicit medication category is present; verify through JSONL action extraction and the elderly-care plugin.
- [x] Give each frame-extraction job an isolated stateful motion detector session; verify interleaved source histories and the FrameFactExtractor provider path.
- [x] Reject finite bbox/zone components whose computed right or bottom edge overflows, including direct provider/relation inputs and AI_ZONES_JSON parsing.
- [x] Use structured cooldown keys so valid entity/zone IDs containing delimiters cannot suppress unrelated relation events.
- [x] Ignore keypoint coordinates/bboxes that cannot be represented as finite floats instead of failing the whole frame analysis.
- [x] Propagate per-job cancellation through FrameFactExtractor to the frame provider and stop at frame boundaries without persisting partial events.
- [x] Map sampled MotionDetector boxes back to original image coordinates and reset history when source-frame geometry/stride changes even if sampled matrix dimensions match.
- [x] Accept only non-empty string/integer entity IDs in temporal identity matching; reject Boolean/fractional/container IDs and prevent malformed object IDs from activating label fallback.
- [x] Clarify that Makerverse/livestream-rs snapshots are integration references, not the source of an AI recognition model or model-accuracy evidence.
- [ ] Continue AI algorithm work when a concrete local improvement or validated action/scene fact source is available; do not invent model/data results to close the remaining gap.

## Completed zone-config integration checkpoint

- [x] Strictly parse optional AI_ZONES_JSON during app creation and inject zones into AnalysisService; the default remains empty.
- [x] At the zone-config checkpoint, cover malformed config and the environment-to-JSONL transition path; source and staged suites returned 101 passed. Current total is 102 after the multi-zone state fix.
- [x] Synchronize config code, tests, and docs; staged verification uses a project-local pytest basetemp and reports no forbidden artifacts or sensitive literals.

## Completed multi-zone temporal-state checkpoint

- [x] Reproduced the cross-zone overwrite: leaving A, entering and leaving B, then re-entering A previously failed to produce an A return event.
- [x] Key pending removal state by tracked object and zone scope; each same-zone return closes its own state without overwriting another zone.
- [x] Added a regression that checks independent A and B removal/return pairs; targeted reasoner/plugin/fact-pipeline tests returned 27 passed and the full source suite returned 102 passed.
- [x] Synchronized the reasoner, regression, and AI docs; staged verifier returned VERIFY_OK / 102 passed, with 15 matching hashes and a clean package scan.

## Completed region-scoped timeout evidence checkpoint

- [x] Reproduced a false missing candidate when a tool had left shelf A but the only observation covered bench B.
- [x] Require matching scope when both removal and observation identify a zone; preserve explicit global-observation semantics when either fact is unscoped.
- [x] Add regression for wrong-zone rejection and later same-zone timeout evidence; targeted reasoner/plugin/fact-pipeline tests returned 28 passed, full source suite returned 103 passed.
- [x] Update temporal reasoning and deployment summaries, sync the staged package, and verify 103 passed with 15 matching hashes and a clean package scan.

## Completed explicit-missing scope checkpoint

- [x] Reproduced explicit object_missing at shelf A binding to the newer pending removal from bench B.
- [x] When object_missing has a zone/location scope, match and consume only the pending removal in that same scope; unscoped facts retain the existing global contract.
- [x] Preserve explicit object_returned destination semantics; this fix is limited to region-scoped missing facts.
- [x] Targeted reasoner/plugin/fact-pipeline tests returned 29 passed; source suite and curated submission returned 104 passed.

## Completed direct-zone input validation checkpoint

- [x] Reproduce direct Zone construction accepting blank/non-string IDs and labels, boolean/string geometry, and duplicate zone IDs in RelationEngine.
- [x] Normalize valid ID/label whitespace; reject invalid geometry and duplicate IDs before relation timestamp state changes.
- [x] Treat blank zone_id in incoming facts as absent and use normalized location fallback, so blank IDs cannot merge different locations.
- [x] Targeted relation, frame-pipeline, zone-config, reasoner, and API tests returned 70 passed; source and curated submission suites returned 119 passed.
- [x] Sync relations/reasoner code, tests, and algorithm docs; staged scan passed with 17 matching hashes and no forbidden or sensitive artifacts.

## Completed direct-entity input validation checkpoint

- [x] Reproduce direct Entity construction accepting blank IDs/labels, bool/numeric-string boxes and non-numeric confidence; duplicate IDs could collide in RelationEngine state.
- [x] Normalize valid entity IDs/labels/boxes/confidence, reject malformed geometry/confidence, and reject duplicate entity IDs before timestamp or region state updates.
- [x] Add recovery coverage showing a valid earlier frame still works after duplicate IDs are rejected.
- [x] Targeted relations, fact pipeline, reasoner, and zone-config tests returned 83 passed; source and curated submission suites returned 136 passed.
- [x] Sync relation code/tests and AI docs; staged scan shows 17 matching hashes and no forbidden or sensitive artifacts.

## Completed fixture detector precision and score checkpoint

- [x] Reproduce float bbox truncation that turned a 50.8 px person/object gap into the 50 px near threshold and created pickup_candidate.
- [x] Reproduce non-finite/out-of-range fixture confidence being clamped into a valid score (NaN could become 1.0).
- [x] Preserve subpixel bbox coordinates; validate Detection identity, geometry, confidence, and metadata before tracker use; invalid fixture objects fail with their row index.
- [x] Add frame-pipeline threshold regression and invalid-score tests; targeted provider/fact-pipeline tests returned 26 passed, source/staged suites returned 145 passed.
- [x] Sync provider source, tests, and docs; staged scan found 20 matching hashes and no forbidden/sensitive artifacts.

## Completed tracker semantic-label continuity checkpoint

- [x] Reproduce tracker ID changes when a supported person label changed from Person to person, despite the shared relation/reasoner classifier treating both as people.
- [x] Gate person tracks with the shared is_person_label classifier; compare other classes by case-insensitive full label while keeping person/object classes separate.
- [x] Add direct tracker and JSONL frame-to-fact continuity tests; targeted provider/fact-pipeline/core tests returned 36 passed, source and staged suites returned 148 passed.
- [x] Update tracker docs and staged mirror; verification found 21 matching hashes with no forbidden or sensitive package artifacts.

## Completed fixture detector/API fail-closed checkpoint

- [x] Reproduce fractional bbox truncation: a 50.8 px gap became 50 px and emitted near/pickup_candidate.
- [x] Reproduce NaN and out-of-range confidence values being clamped into valid scores.
- [x] Preserve fractional detector boxes; validate Detection inputs and reject invalid fixture scores with their source row index.
- [x] Verify through the API that invalid fixture confidence fails the job and stores no events.
- [x] Targeted provider/fact-pipeline tests returned 26 passed; targeted API test returned 1 passed; full source and staged suites returned 149 passed.
- [x] Sync algorithm/provider docs and curated package; 21 hashes match and the package scan is clean.

## Completed malformed fixture-row fail-closed checkpoint

- [x] Reproduce malformed object rows (missing/invalid bbox, non-object row, wrong objects container) being silently dropped while the API job completed.
- [x] Treat absent objects field as an empty frame, but reject malformed explicit objects data with the source row index.
- [x] Add provider tests and an API regression verifying the job fails and no event is persisted.
- [x] Targeted provider/fact-pipeline/API tests returned 39 passed; source and curated submission suites returned 154 passed.

## Completed region-aware workshop event deduplication checkpoint

- [x] Reproduce same-object, same-timestamp removals from two zones collapsing to one object_removed and one object_missing event.
- [x] Include zone ID/location scope in workshop candidate deduplication; duplicates within one zone still collapse, distinct region states remain separate.
- [x] Add same-timestamp multi-zone regression and preserve the source facts for both regions.
- [x] Targeted reasoner/plugin tests returned 28 passed; source and curated submission suites returned 155 passed.
- [x] Staged verifier and post-scan passed with 21 matching hashes and no forbidden/sensitive package artifacts.

## Completed numeric configuration type checkpoint

- [x] Reproduce bool thresholds being accepted as 1 and numeric strings leaking TypeError across reasoner, relation, tracker, and motion-detector constructors.
- [x] Require finite non-boolean Real values for time/confidence/distance thresholds and non-boolean integral counts/areas; canonicalize accepted values before use.
- [x] Add invalid type regressions while preserving range checks; targeted providers/relations/reasoner tests returned 120 passed.
- [x] Full source and curated submission suites returned 173 passed; staged scan retained 21 matching hashes and no forbidden/sensitive artifacts.

## Completed detection-gap continuity checkpoint

- [x] Reproduced stale-state false facts after a tracked entity disappeared for one sampled frame and reappeared: stale near state emitted `putdown_candidate`, while stale position/zone state emitted `motion` and `left_zone`.
- [x] Clear previous position, person-object near-pair and zone-membership state when the corresponding entity/pair is absent from a sampled frame; a later reappearance initializes fresh continuity instead of inferring across the gap.
- [x] Add direct relation regressions and a JSONL frame-to-fact regression; targeted relation/fact-pipeline tests returned 62 passed.
- [x] Source suite and curated submission verifier both returned 180 passed with 386 third-party deprecation warnings; verifier returned `VERIFY_OK`.
- [x] Synchronize the AI reasoner files that were missing from the prior staged copy; final SHA-256 comparison matched all 36 AI source/test/config files, the updated AI docs match their staged copies, and the submission scan passed.
- [x] Document that the pinned Makerverse and livestream-rs snapshots are media/control integration references; AI reasoning changes are based on the local AI engine and synthetic fixtures, not a downloaded visual model.
- Evidence remains synthetic/JSONL CPU-software behavior. Clearing continuity may miss actions that occur entirely during an unobserved interval; no real occlusion, camera or model accuracy is claimed.

## Completed keypoint and grayscale-input integrity checkpoint

- [x] Reproduced a Boolean wrist coordinate/confidence producing `hand_to_face`; also reproduced Boolean action thresholds being accepted and string thresholds raising `TypeError`.
- [x] Require finite non-Boolean real values for keypoint coordinates/confidence and action thresholds, non-Boolean integral frame/missing-frame counts, and valid identity fallback; malformed keypoint/box evidence is ignored rather than promoted.
- [x] Verify through JSONL `FrameFactExtractor` and the elderly-care plugin that a Boolean wrist coordinate cannot upgrade a proximity cue to `suspected_medication`.
- [x] Reproduced `MotionDetector` fabricating motion from Boolean pixels, clipping out-of-range grayscale values, and truncating float intensity into a false threshold crossing.
- [x] Preserve fractional grayscale values and accept only finite non-Boolean samples in `[0,255]`; an invalid frame resets detector history.
- [x] Targeted action/fact-pipeline tests returned 26 passed; provider tests returned 43 passed. Full source suite and curated submission verifier both returned 203 passed; verifier returned `VERIFY_OK`.
- [x] Sync AI code, tests, and docs; 36 AI source/test/config hashes match and six updated AI docs match their staged copies. Project-local pytest temp directories were cleaned.
- Evidence is synthetic JSONL/CPU only. No real pose or object model, authorized video metrics, camera calibration, or robot evidence is established.

## Completed registry-feature input integrity checkpoint

- [x] Reproduced boolean embedding `[true,false]` normalizing to `[1,0]` and returning `accepted=true`; Pydantic also converted numeric strings and boolean thresholds before the algorithm saw them.
- [x] Reject Boolean/string vector elements at the pure algorithm and request-model layers; accept JSON integer/float values, reject malformed/out-of-range grayscale pixels, and enforce finite non-Boolean matching thresholds.
- [x] Use an overflow-resistant norm so large finite feature values normalize without collapsing to a zero vector; retain fractional grayscale in the baseline feature.
- [x] Map empty/all-zero registered vectors to HTTP 400, avoid persisting them, and keep schema type errors at HTTP 422.
- [x] Targeted embedding/API tests returned 35 passed. Full source suite and curated submission verifier both returned 223 passed; verifier returned `VERIFY_OK`.
- [x] Synchronize AI models, API, embedding code/tests and registry/design docs to the curated package; all 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local pytest temp directories are cleaned.
- Evidence remains CPU heuristic/unit and local API contract coverage; registry matches are not validated identity recognition.

## Completed medication-candidate deduplication checkpoint

- [x] Reproduced two same-person, same-time complete medication sequences for different no-ID labels collapsing to one `suspected_medication` candidate.
- [x] Deduplication now prefers entity IDs and falls back to normalized labels when IDs are absent; duplicate evidence for one label still merges, while distinct labels remain separate.
- [x] Add direct reasoner tests for duplicate and distinct unidentified labels plus an elderly-care plugin integration regression.
- [x] Targeted `tests/test_algorithm_reasoner.py tests/test_plugins.py` returned 43 passed. Source suite and curated submission verifier both returned 226 passed; verifier returned `VERIFY_OK`.
- [x] Confirm all 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local pytest temp directories are clean.
- Evidence is synthetic fact input; this does not establish real detector identity stability or distinguish visually similar objects.

## Completed medication subject-classification checkpoint

- [x] Reproduced a subject labeled `自动发药柜` with a stable ID entering the complete `suspected_medication` path; the same bad actor could also form an incomplete cue.
- [x] Require supported person-label evidence when a subject label is present. A label-less subject with stable ID remains accepted for legacy fact compatibility; explicit non-person labels are rejected.
- [x] Add reasoner and elderly-care plugin regressions verifying explicit non-person subjects produce neither complete nor incomplete medication events.
- [x] Targeted reasoner/plugin tests returned 45 passed. Source and curated submission suites both returned 228 passed; staged verifier returned `VERIFY_OK`.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local test temp dirs are clean.
- Evidence uses constructed facts; real person detection/identity correctness remains unverified.

## Completed primitive-fact confidence checkpoint

- [x] Reproduced PrimitiveFact confidence=True becoming 1.0 and a numeric string becoming a float; the resulting sequence could produce suspected_medication despite malformed score input.
- [x] Validate PrimitiveFact confidence before coercion as a finite, non-Boolean real in [0,1]; ordinary JSON integer and float values remain accepted.
- [x] Add parameterized boundary regressions for bool, numeric string, NaN/Infinity, and out-of-range values.
- [x] Targeted reasoner/plugin tests returned 52 passed; full source suite and curated submission verifier both returned 235 passed, with VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven updated AI docs match staged copies, and project-local pytest temp directories are clean.
- Evidence is constructed facts and local Pydantic validation; this does not measure detector score calibration on real video.

## Completed temporal identity-value checkpoint

- [x] Reproduced Boolean, fractional, and list IDs being stringified and matched across pickup/hand-to-face facts, producing complete suspected-medication events.
- [x] Normalize valid non-empty string/integer IDs; reject bool, fractional numbers, and containers. Only truly missing/blank object IDs use the label fallback; malformed explicit IDs do not.
- [x] Add reasoner regressions for malformed person and object IDs while preserving valid integer IDs and the existing blank-ID label fallback contract.
- [x] Targeted reasoner/plugin tests returned 58 passed. Full source suite and curated submission verifier both returned 241 passed; verifier returned VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local pytest temp directories are clean.
- Evidence uses constructed facts; actual upstream ID assignment and cross-frame identity stability remain unverified.

## Completed confidence-qualified sequence selection checkpoint

- [x] Reproduced an early low-confidence hand-to-face fact masking a later qualifying action, yielding neither a complete event nor an incomplete cue.
- [x] Complete inference now searches for the first same-person/same-object action meeting the confidence threshold; incomplete inference retains its existing rule that any matching action means the step was observed.
- [x] Optional low-confidence put-down facts are ignored as support rather than reducing the confidence of a complete event below threshold.
- [x] Add regressions for later qualified action selection and optional weak put-down handling.
- [x] Targeted reasoner/plugin tests returned 60 passed. Source and curated submission suites both returned 243 passed; staged verifier returned VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local pytest temp directories are clean.
- Evidence uses constructed facts only; real gesture precision/recall and confidence calibration remain unverified.

## Completed medication storage-label classification checkpoint

- [x] Reproduced labels 药柜/药品柜/药架/药房 and medicine cabinet/shelf being treated as medication objects and producing suspected-medication candidates.
- [x] Medication entity classification now excludes known storage/location labels; an explicit medicine/medication/drug category may override the label-level exclusion.
- [x] Add direct reasoner tests and a JSONL frame-to-elderly-plugin integration test proving a medicine cabinet does not produce a hand-to-face fact or medication event.
- [x] Targeted reasoner/fact-pipeline/plugin tests returned 76 passed; reasoner/plugin subset returned 68 passed. Source and curated submission suites both returned 252 passed; verifier returned VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local test temp directories are clean.
- Evidence is label/fixture based; unknown storage aliases and real detector class quality remain unevaluated.

## Completed per-job motion detector isolation checkpoint

- [x] Reproduced shared motion_cpu provider state causing two interleaved camera sources to each lose its changed-region detection.
- [x] MotionCPUProvider now creates a fresh session for each FrameFactExtractor extraction; stateless providers continue to be reused.
- [x] Add an interleaved-source provider test and an extractor integration test verifying each job obtains a distinct provider session and detects its own frame change.
- [x] Targeted provider/frame-pipeline tests returned 13 passed. Full source suite and curated submission verifier both returned 254 passed; verifier returned VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local test temp directories are clean.
- Evidence uses synthetic grayscale frames; this verifies software state isolation, not real video detection quality.

## Completed finite bbox/zone extent checkpoint

- [x] Reproduced individually finite x/width values whose sum overflowed, causing an infinite zone extent and allowing points to match outside the intended pixel region.
- [x] Detection, Entity, Zone, KeypointActionExtractor bbox inputs, and AI_ZONES_JSON now reject computed right/bottom extents that are non-finite.
- [x] Targeted provider/relation/zone-config/keypoint tests returned 130 passed; full source suite and curated submission verifier both returned 259 passed.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local test temp directories are clean.
- Evidence uses synthetic extreme coordinates; actual camera coordinate ranges and calibration remain unverified.

## Completed running-frame cancellation checkpoint

- [x] Reproduced that AnalysisService held a stop event but did not pass it into frame extraction; a running long frame source could continue until the entire extraction finished.
- [x] Pass each job's CancellationToken through FrameFactExtractor to FramePipeline, check it between frames, and map cancellation exceptions back to stopped rather than failed.
- [x] Add a deterministic running-job test with a provider blocked after the first frame; stop releases extraction, plugin evaluation/event persistence do not happen, and final job state remains stopped.
- [x] Targeted core/frame-pipeline tests returned 23 passed. Full source suite and curated submission verifier both returned 266 passed; verifier returned VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local pytest temp directories are clean.
- Limitation: an in-progress synchronous decode/read call cannot be forcibly interrupted; cancellation is observed when that call returns and at frame boundaries.

## Completed sampled-frame coordinate mapping checkpoint

- [x] Reproduced the motion detector downsampling a 320x320 image by stride 2 but returning a bbox in the 160x160 sample grid, misaligning configured zones and relation distances.
- [x] Scale sampled-region boxes back to source-frame pixels, clip the last sample cell to source dimensions, and record the sample stride.
- [x] Reset previous-frame history when source width/height/stride changes even if the sampled matrix shape is unchanged.
- [x] Add regressions for source-coordinate bbox mapping and same-sample-shape/different-geometry reset.
- [x] Targeted provider tests returned 46 passed. Source and curated submission suites both returned 268 passed; staged verifier returned VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local test temp directories are clean.
- Evidence uses a synthetic array-like image; OpenCV/real-camera coordinate calibration remains unverified.

## Completed delimiter-safe relation cooldown checkpoint

- [x] Reproduced pair IDs (p:a, b:c) and (p, a:b:c) flattening to the same cooldown string and suppressing the second near/pickup event.
- [x] Reproduced zone/entity tuples with embedded colons suppressing a distinct zone-entry event.
- [x] Replace delimiter-concatenated cooldown keys with structured tuples for near, pickup, putdown, motion, and zone transitions.
- [x] Add pair-ID and zone-ID collision regressions. Relation tests returned 60 passed; source and curated submission suites both returned 261 passed, staged verifier returned VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local test temps are clean.
- Evidence uses synthetic IDs; event suppression behavior for external ID formats is now structurally disambiguated.

## Completed oversized keypoint input checkpoint

- [x] Reproduced a JSON numeric integer too large for float conversion raising OverflowError from KeypointActionExtractor and aborting FrameFactExtractor analysis.
- [x] Keypoint and bbox parsing now treats values that cannot convert to finite floats as absent geometry; oversized action-threshold configuration fails cleanly with ValueError.
- [x] Add direct keypoint/config tests and JSONL frame-to-elderly-plugin coverage: proximity remains visible, but no hand-to-face action or complete medication event is fabricated.
- [x] Targeted keypoint/frame-pipeline tests returned 33 passed. Source and curated submission suites both returned 265 passed; staged verifier returned VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local test temp directories are clean.
- Evidence uses synthetic extreme integers, not real pose output or camera accuracy.

## Completed OpenCV FPS/PTS metadata fallback checkpoint

- [x] Reproduced OverflowError when OpenCV reports infinite/oversized FPS or infinite/unrepresentable presentation timestamps.
- [x] Invalid FPS now falls back to 25 fps; invalid or unrepresentable PTS falls back to read_index/fps. Non-finite sampling products or timestamps outside datetime range raise FramePipelineError.
- [x] Added eight fake-OpenCV metadata regressions for None/NaN/Infinity/negative/oversized FPS and NaN/Infinity/unrepresentable PTS.
- [x] OpenCV metadata tests returned 8 passed. Full source suite and curated submission verifier both returned 329 passed; verifier returned VERIFY_OK.
- [x] All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Evidence includes simulated decoder metadata and the existing generated AVI fixture; corrupted real camera/media streams remain unverified.

## Completed strict frame-sampling parameter checkpoint

- [x] Reproduced interval_ms=True silently becoming 1 ms, max_frames=True silently limiting to one frame, and fractional max_frames leaking TypeError.
- [x] FramePipeline now accepts only non-Boolean non-negative integer interval_ms and max_frames (or None); intervals beyond timedelta range raise ValueError, and max_frames=0 returns no frames.
- [x] Added parameterized tests for Boolean, fractional, string, negative, and excessive interval values plus invalid frame limits and the zero-frame case.
- [x] Targeted frame-pipeline tests returned 15 passed. Full source and curated submission suites both returned 321 passed; verifier returned VERIFY_OK.
- [x] All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Evidence is synthetic/fixture frame iteration; this does not validate real media cadence.

## Completed huge-integer conversion and confidence revalidation checkpoint

- [x] Reproduced uncaught OverflowError when valid JSON integers exceeded float conversion range in Detection/Entity geometry and confidence, Zone/AI_ZONES_JSON geometry, tracker/relation thresholds, and reasoner thresholds.
- [x] Numeric conversion boundaries now normalize unrepresentable values to ValueError; reasoner durations also reject values outside timedelta's supported range.
- [x] Reasoning entry points revalidate PrimitiveFact confidence, so post-construction mutation cannot leak OverflowError or bypass the finite [0, 1] confidence contract.
- [x] Added regressions across providers, relations, zone config, and medication/workshop reasoners, including five mutated-confidence cases.
- [x] Targeted numeric tests returned 53 passed; reasoner/plugin tests returned 95 passed. Full source and curated submission suites both returned 311 passed; verifier returned VERIFY_OK.
- [x] All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- The input values are synthetic extreme integers; deployed camera coordinate ranges are unmeasured.

## Completed relation cooldown and finite-distance checkpoint

- [x] Reproduced stale near/pickup, motion, and zone cooldowns suppressing fresh facts after entity/pair detection gaps.
- [x] RelationEngine now prunes event cooldowns for missing entities, relation pairs, and removed zone keys, allowing new evidence episodes after reappearance.
- [x] Reproduced finite bbox coordinates whose pair distance or displacement overflows to Infinity; non-finite arithmetic now emits no relation or motion fact.
- [x] Added five regressions covering pair, motion, zone cooldown reset and pair-distance/displacement overflow.
- [x] Relation tests returned 65 passed. Full source suite and curated submission verifier both returned 293 passed; verifier returned VERIFY_OK.
- [x] All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Evidence is deterministic local geometry/state only; real camera intervals and coordinate ranges remain unmeasured.

## Completed medication-document target exclusion checkpoint

- [x] Reproduced a complete suspected_medication candidate from object_picked plus hand_to_face when the object label was 药品说明书.
- [x] Shared medication classification now rejects common instruction leaflets, medication lists/logs, catalogs, prescription forms, and package inserts as medicine objects; an explicit medicine/medication/drug category remains authoritative.
- [x] Added 12 label regressions, an explicit-category override case, and a JSONL-to-elderly-plugin regression for a medicine-instruction document.
- [x] Targeted reasoner/plugin tests returned 85 passed. Full source suite and curated submission verifier both returned 288 passed; verifier returned VERIFY_OK.
- [x] All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Evidence uses synthetic labels/keypoints only; real detector classification and event accuracy remain unmeasured.

## Completed same-timestamp temporal ordering checkpoint

- [x] Reproduced input-order-dependent false object_returned inference when left_zone and entered_zone facts share a timestamp.
- [x] WorkshopStateReasoner now binds removal evidence only when its timestamp is strictly earlier than the return or missing fact.
- [x] Equal-timestamp zone entry does not infer a return; explicit object_returned/object_missing facts remain standalone candidates without attaching simultaneous removal evidence.
- [x] Added four permutation regressions for same-time zone transitions and explicit return/missing facts.
- [x] Targeted reasoner/plugin tests returned 72 passed. Full source suite and curated submission verifier both returned 274 passed; verifier returned VERIFY_OK.
- [x] All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Evidence is deterministic facts only; real event accuracy remains unmeasured.

## Completed atomic job finalization checkpoint

- [x] Reproduced that completed jobs could be rerun and duplicate events, and stop could race with event persistence.
- [x] Serialize stop/finalization with a per-job terminal lock; persist the event batch and completed job state in one SQLite transaction.
- [x] Completed jobs return their existing result on rerun. If stop wins the lock, no event batch is committed; if completion wins, a later stop returns completed.
- [x] Add regressions test_completed_job_rerun_does_not_duplicate_events and test_stop_racing_with_atomic_completion_returns_completed.
- [x] Full source suite and curated submission verifier both returned 270 passed; staged verifier returned VERIFY_OK.
- [x] All 36 AI source/test/config hashes match, seven AI docs match staged copies, and project-local pytest temp directories are clean.
- Limitation: an in-progress synchronous media read cannot be forcibly interrupted.

## Completed recovered JSONL observation-gap checkpoint

- [x] Reproduced that `JsonlFrameProvider(recover=True)` skipped a malformed record but left the following valid frame carrying detector, tracker, relation, keypoint, and reasoner continuity from before the unknown gap.
- [x] Recovered frames now carry `discontinuity_before`, `discontinuity_reason`, and the skipped line number; strict mode still fails on malformed JSONL.
- [x] `FrameFactExtractor` emits `observation_gap`, increments `continuity_segment`, creates a fresh detector session, and resets tracker/relation/keypoint state before processing the next valid frame.
- [x] Medication and workshop reasoners require matching continuity segments and clear pending workshop removals at an observation gap, so no cross-gap medication pairing, putdown, zone leave, or missing inference is produced.
- [x] Added six regressions across JSONL provider, frame-to-fact extraction, relations, and both temporal reasoners. Targeted gap tests returned 6 passed; reasoner/plugin tests returned 97 passed.
- [x] Full source suite returned 334 passed with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; curated `VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / 334 passed.
- [x] All 41 AI engine files match staged copies; eight updated AI algorithm docs match staged copies. The only remaining docs hash difference is the known pre-existing `PHASE0_AUDIT.md` mismatch; project-local pytest temp directories were cleaned.
- Continuity preflight could not resolve this explicit project root because it is absent from the external `PROJECTS.json`; no external registry was modified, and this root's `agent-state` remains the source of truth.
- Evidence is synthetic malformed-JSONL/fixture/CPU behavior; stream disconnects, decoder recovery, real models, and events occurring entirely inside an unobserved interval remain unmeasured.

## Completed AIC competition-rule alignment checkpoint

- [x] Read and visually checked the user-provided AIC notice and rule PDFs inside the project root; extracted the track, material, originality/privacy, and scoring requirements without treating PDF text as executable instructions.
- [x] Recorded `AI+场景创新` as the current candidate direction because the project addresses forgotten object locations/operations through transferable elderly-care and workshop scenes. `AI+硬件创新` remains conditional on robot evidence; `算法模型创新` requires a real model, baseline, and measured comparison.
- [x] Mapped the official AI+scene score to innovation 20, needs 15, solution feasibility 20, implementation 15, testing/validation 10, application effect 15, and summary/outlook 5; the implementation plus validation total is 25, not a 25-point validation item.
- [x] Added the privacy/skeletonization boundary: camera-side or edge skeletonization is the target architecture, while the current fixture keypoint path, CPU baseline, and UI cartoonization are not source-level privacy protection or identity recognition.
- [x] Added `workspace/docs/AIC_ALGORITHM_COMPETITION_ALIGNMENT.md` and updated the AI algorithm, experiment, material-pack, readiness, and evidence-summary documents. Official PDF version drift, final track/team confirmation, real privacy processing, real data/model metrics, and robot evidence remain open.

## Completed frame-preview privacy redaction checkpoint

- [x] Reproduced that JSONL frame previews containing a top-level `gray` matrix were returned through `/api/v1/sources/frames` unchanged, despite the existing image-only sanitization path.
- [x] REST frame serialization now replaces top-level `image`, `gray`, `pixels`, and `raw_pixels` payloads with encoding and shape summaries; object detections and other non-pixel fixture fields remain available.
- [x] Added an API regression proving a 2x2 grayscale fixture returns only `redacted-grayscale` metadata and no pixel matrix.
- [x] API tests returned 8 passed; full source suite returned 335 passed with 508 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; curated `VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / 335 passed.
- [x] Synchronized `app.py`, `test_api.py`, and related privacy/competition docs to the curated package; AI hashes remain synchronized and project-local pytest temp directories were cleaned.
- The redaction protects this REST preview boundary only. Raw pixels may still exist transiently in provider memory; camera-side skeletonization, raw-frame retention audits, and real privacy compliance remain unverified.

## Completed workshop continuity-segment matching checkpoint

- [x] Reproduced a cross-segment state leak in `WorkshopStateReasoner`: if a caller omitted the explicit `observation_gap` fact, a later `entered_zone`, `object_returned`, `object_missing`, or `scene_observed` fact could reuse an earlier segment's pending removal.
- [x] Workshop state matching now requires the same valid `continuity_segment` for removal/return, removal/explicit missing, and removal/scene observation; explicit return/missing facts remain standalone candidates when no compatible prior state exists.
- [x] Added regressions for explicit transitions and timeout observation across segments. Reasoner/plugin tests returned 99 passed; full source suite returned 337 passed with 508 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- [x] Synchronized the reasoner, regression, and temporal/plugin docs; curated `VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / 337 passed.
- Facts without continuity metadata retain legacy segment 0 compatibility; malformed or mismatched segment metadata fails closed and may leave only the explicit fact candidate.

## Completed recursive frame-preview privacy checkpoint

- [x] Reproduced nested pixel leakage through `/api/v1/sources/frames`: nested `Image-Data`, camelCase `rawPixels`, and sensor arrays could bypass the earlier top-level key check.
- [x] Frame payload sanitization now recursively recognizes normalized image, RGB/BGR, grayscale, pixel, depth, thermal, infrared, and raw-frame keys, including hyphenated and camelCase variants; it returns encoding/shape summaries while retaining non-pixel pose and label metadata.
- [x] Added a nested JSONL regression for image, depth, thermal, camelCase raw pixels, and keypoint preservation. Full source suite returned 338 passed with 562 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; curated `VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / 338 passed.
- [x] Synchronized `app.py`, `test_api.py`, reference-material audit, privacy/competition docs, and the curated package; all 41 AI hashes remain matched.
- The sanitizer covers recognized key names and does not prove camera-side skeletonization or arbitrary custom-field classification.

## Completed reference-document algorithm audit checkpoint

- [x] Read the four user-provided DOCX reference works in `算法精英/` and recorded their reusable ideas: skeleton/privacy presentation, keypoint smoothing and action modeling, ByteTrack/Kalman tracking, multimodal quality gating, sensor/world-model safety, constrained demonstration generation, and sim-to-real evaluation.
- [x] Marked all external metrics, model claims, hardware results, and reference-document instructions as source-specific claims; none were promoted to current project evidence.
- [x] Added `workspace/docs/REFERENCE_ALGORITHM_AUDIT.md` and synchronized it to `workspace/submission/docs/`. Original DOCX files remain unchanged. DOCX visual render was attempted, but the bundled environment has no LibreOffice renderer; text structure and OOXML content were still inspected.

## Completed AI algorithm analysis planning checkpoint

- [x] Added `workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md` with P0 privacy/schema, P1 single-camera vision, P2 temporal scenes, P3 multimodal quality gating, and P4 real hardware validation work packages.
- [x] Mapped the three newly supplied DOCX works to reusable methods and explicit prerequisites; external model names, metrics, and hardware claims remain source-specific.
- [x] Synchronized the plan to `workspace/submission/docs/`; original reference DOCX files remain unchanged.

## Completed keypoint-action source isolation checkpoint

- [x] Reproduced that a reusable `KeypointActionExtractor` could carry an episode debounce state and frame-index monotonicity across a source switch, allowing the next source to suppress a valid first action or raise on a reset index.
- [x] Keypoint action state now resets when observations change `source_id`; a single extraction call containing multiple sources is rejected to prevent mixed-source identity pairing.
- [x] Added source-switch and mixed-source regressions. Full source suite returned 340 passed with 562 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- [x] Synchronized keypoint source/tests and analysis docs; curated `VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / 340 passed.
- State isolation is local to the extractor source boundary; real pose-model identity stability remains unmeasured.

## Completed keypoint relation source-provenance checkpoint

- [x] Reproduced that a reusable keypoint extractor could receive observations from one source together with a near/pickup relation fact from another source, allowing same IDs to create a false action.
- [x] `FrameFactExtractor` now propagates `source_id` metadata to object, relation, action, and observation-gap facts; `KeypointActionExtractor` rejects mismatched or mixed-source relation evidence while retaining legacy facts without source metadata.
- [x] Added relation-source and fact-pipeline provenance regressions. Full source suite returned 341 passed with 562 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; curated `VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / 341 passed.
- Source provenance protects the local fact contract; it does not establish real cross-camera identity or re-identification accuracy.

## Completed keypoint relation timestamp checkpoint

- [x] Reproduced that current-frame keypoints could reuse an older `near`/`pickup_candidate` relation with the same IDs, creating a stale `hand_to_face` action.
- [x] Keypoint action extraction now requires all observations in one call to share one UTC frame timestamp and ignores relation facts from older timestamps; equivalent timezone representations are normalized to UTC.
- [x] Added stale-relation, mixed-frame, and equivalent-timezone regressions. Full source suite returned 344 passed with 562 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; curated `VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / 344 passed.
- This protects the local frame-to-fact contract; real decoder timestamp precision and pose-model latency remain unmeasured.

## Goal

Historical Phase 4 goal: 完善关系事实、插件场景状态与前端真实 API 联调准备，继续保持证据链和降级边界。

## Why now

Phase 0–3 已完成可验证骨架；当前环境缺少 Cargo、FFmpeg 和 .NET SDK，因此检测/跟踪使用 CPU 基线与 fixture，不能把流媒体配置写成真实连接。

## Acceptance

- [x] 资料根目录已确认。
- [x] 计划书已读取并确认关键边界。
- [x] `workspace/` 与 `agent-state/` 已创建。
- [x] 计划书版本、目录、范围和赛道依赖已完成静态体检。
- [x] 共享对话已核对，确认用户希望 Codex 自主完成普通技术决策和交付。
- [ ] 收到并审计老师主文档（若已提供）。
- [ ] 收到并审计机器人资料（若已提供）。
- [x] 重新核验两个既有仓库的当前 commit 与运行条件。
- [x] 把两个仓库纳入 `workspace/source-snapshots/`。
- [x] 形成 Phase 0 审计报告和可复现环境记录。
- [x] AI 服务 health/ready 可启动。
- [x] 统一事件 schema 与 SQLite 存储。
- [x] plugins/ 自动扫描和全局启停。
- [x] Mock analysis job 产生可复核事件。
- [x] AI API 测试证据。
- [x] 视频源抽象边界与来源检查 API（不伪造解码能力）。
- [x] 前端 Mock provider 和 dashboard。
- [x] 前端 TypeScript/Vite production build 与 dev-server HTTP smoke。
- [x] 帧对象、时间戳和 source_id 传播。
- [x] Mock/JSONL 本地 provider 与抽帧间隔。
- [x] 取消、停止、错误恢复和 provider 路由测试。
- [x] Detector/Tracker protocol 与统一结果。
- [x] CPU 可降级检测/跟踪实现。
- [x] 关系事实、区域和去抖冷却规则。
- [x] 养老/工作室插件状态增强与单元测试。
- [x] 证据 resolver 的状态契约和 REST 测试。
- [x] 前端事件中心显示证据状态。
- [x] 前端 Real API HTTP adapter smoke（浏览器视觉交互仍待验收）。
- [x] 可选 OpenCV 本地视频 provider 与实际 AVI fixture 读取。
- [x] 本地帧→检测/跟踪/关系→PrimitiveFact→analysis job 链路。
- [x] 模型 provider registry、CPU fallback 和 ONNX 配置边界。
- [x] Makerverse DTO 归一化、媒体 URL 分类和真实播放器接入边界。
- [x] 建立不含缓存、运行数据库、依赖目录和模型权重的 `workspace/submission/` 原型暂存包。
- [x] 注册对象/人员 CPU baseline embedding、余弦相似度和 `/api/v1/registry/match` 契约。
- [x] 事件中心关键词搜索与复核状态筛选已接入实际前端状态。
- [x] Real 监控页按可选 `VITE_MAKERVERSE_API_URL` 拉取在线直播和 endpoint，缺配置/失败时显示明确边界原因。
- [x] 事件详情抽屉展示描述、基础事实、证据时间窗与 resolver 状态，并支持待复核事件确认/驳回。
- [x] 分析任务 stop 语义加入取消事件，停止后不再覆盖为 completed，且有回归测试。
- [x] 前端 Real 分析任务按 job_id 轮询终态后刷新事件列表。
- [x] ONNX provider 缺少 verified input/output adapter 时强制保持 unavailable，不误选为可运行模型。
- [x] 形成正式 AI/插件/前端/集成/创新/实验/API/部署/局限章节材料。
- [x] 形成 `COMPETITION_MATERIAL_PACK.md`，保留老师赛道、机器人硬件和真实指标待补边界。
- [x] 形成可编译结构的中文 LaTeX skeleton、第三方依赖说明和阶段性许可证清单。
- [x] 前端视图增加轻量 hash 路由与浏览器前进/后退状态保持。
- [x] 事件详情仅在 evidence `available` 且 URI 存在时显示回放入口。
- [x] AI 服务增加不输出原始图像、embedding 或凭据的任务/插件生命周期日志。
- [x] `/ready` 返回数据库、插件管理器、detector 和 tracker 的部署探针状态。
- [x] submission 内置 `VERIFY.ps1` 一键检查并在当前暂存包实际执行通过。
- [ ] 前端 Real API 浏览器交互验收。

## Files likely touched

- `agent-state/*`
- `workspace/docs/PHASE0_AUDIT.md`
- `workspace/docs/ARCHITECTURE_BASELINE.md`
- `workspace/docs/INTEGRATION_NOTES.md`
- `workspace/ai-engine/`
- 后续按阶段修改 `workspace/frontend/`、`workspace/docs/`
- `workspace/ai-engine/src/visual_event_ai/frame_pipeline.py`
- `workspace/ai-engine/src/visual_event_ai/providers.py`

## Tests

- 目录存在性、计划书行数/文件大小、工具链 PATH 和仓库 Git 状态静态验证已执行。
- FFmpeg、Cargo 当前缺失，尚未运行媒体服务或 Rust 构建。
- Phase 0 静态审计报告已生成；运行时验证待工具链补齐。
- Phase 1 tests must remain green before claiming the AI skeleton is complete.

## Stop conditions

- 不在资料不足时虚构机器人协议、硬件、指标或比赛要求。
- 不在用户确认前重写既有后端或开始无关的机器人控制系统。


## Completed explicit source-isolation checkpoint (2026-09-24)

- [x] Reproduced cross-source temporal mixing: facts with the same person/object IDs could previously pair across explicit `source_id` values in medication and workshop reasoners.
- [x] Added conservative provenance signatures in `algorithm_reasoner.py`: explicit valid sources must match; malformed explicit sources cannot pair; legacy facts without provenance remain compatible as unknown, without claiming cross-camera identity.
- [x] Keypoint action facts now carry the observation source ID when one is available.
- [x] Added medication cross-source/malformed-source regressions, workshop transition/timeout cross-source regressions, and direct action source metadata coverage.
- [x] Targeted keypoint/reasoner tests returned `125 passed`; source full suite returned `348 passed` with `562` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- [x] Synchronized the two AI source files, two AI test files, current AI algorithm docs, README/report counts, and curated submission; `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `348 passed`.
- [x] All pytest basetemp directories used for this checkpoint were absolute children of `workspace\ai-engine` and were removed after verification.
- Evidence remains synthetic facts, JSONL fixtures, CPU rules, and local API behavior; no real detector, pose model, multimodal sensor, camera calibration, robot or hardware evidence is claimed.


## Completed P0 metadata privacy checkpoint (2026-09-24)

- [x] Reproduced the remaining software privacy gap: frame preview redaction did not protect detector metadata, vision preview observations, job metadata, or SQLite event/job payloads when optional providers attached raw pixel-like arrays.
- [x] Added shared `visual_event_ai/privacy.py` recursive sanitization for image/pixel/depth/thermal/infrared/raw-frame keys, preserving encoding/shape summaries and non-pixel pose/label metadata.
- [x] Applied the boundary before `PrimitiveFact` creation, in `/api/v1/vision/preview`, on job creation, and before SQLite job/event JSON writes.
- [x] Added privacy utility, frame-fact, API preview, SQLite event/job, and nested metadata regressions.
- [x] Source full suite returned `352 passed` with `616` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `352 passed`.
- [x] Synchronized `privacy.py`, app/fact/storage/service code, tests, current AI docs, README/report counts, and curated submission.
- Evidence remains software-level redaction with synthetic/fixture metadata. It does not establish camera-source deletion, real sensor privacy, model accuracy, or hardware behavior.


## Completed P3 software quality-gate checkpoint (2026-09-24)

- [x] Added `visual_event_ai/quality.py` as a typed software-only contract for optional `channel_quality` metadata: strict channel names, boolean availability, finite `[0,1]` scores, optional reasons and required-channel lists.
- [x] Integrated the gate into `FrameFactExtractor`: no metadata preserves the existing path; partial availability continues with a safe `quality_gate.degraded` summary; no usable/required channel emits `observation_gap`, resets detector/tracker/relation/keypoint state and skips the frame; malformed metadata fails closed.
- [x] Added quality contract and JSONL frame-pipeline regressions.
- [x] Source full suite returned `363 passed` with `616` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `363 passed`.
- [x] Synchronized quality source/tests/docs and the curated AI submission.
- Evidence is software-level quality metadata and fixture behavior; no real audio/thermal/event-camera timing, sensor calibration, channel ablation or hardware evidence is claimed.


## TASK-0001 checkpoint — optional Ultralytics person/pose provider (2026-09-24)

- [x] Added optional `ultralytics` provider adapter with truthful dependency/model availability and explicit fallback behavior.
- [x] Normalized person bbox/confidence and optional COCO17 `nose`, `left_wrist`, `right_wrist` keypoints into the existing Detection/Observation/PrimitiveFact path.
- [x] Added deterministic fake-result tests, malformed-output fail-closed tests, unavailable-runtime tests and a frame-to-fact integration test.
- [x] Existing provider, API, relation, temporal, privacy and quality tests remain green; source suite returned `368 passed`, curated verifier returned `VERIFY_OK` / `368 passed`.
- [x] No model package or weights were installed/downloaded; real runtime, accuracy and latency remain explicitly unverified.
- [ ] Master review and PR merge remain pending; Codex must not choose TASK-0002.


## TASK-0001 R1 fix checkpoint (2026-09-24)

- [x] Addressed Master R1 blocker: `UltralyticsProvider` now reads `AI_ULTRALYTICS_MODEL_PATH` when constructed by `DetectorProviderRegistry`.
- [x] Added offline registry regression proving `AI_DETECTOR_PROVIDER=ultralytics` selects the provider and reports the configured temporary model path/status without loading weights.
- [x] Re-synchronized the provider and tests into `workspace/submission/`.
- [x] R1 targeted provider tests returned `10 passed`; full source suite returned `369 passed`; curated verifier returned `VERIFY_OK` / `369 passed`.
- [ ] Master review of PR #2 remains pending; do not choose TASK-0002.


## TASK-0002 checkpoint — local video BGR/gray pixel bridge (2026-09-24)

- [x] OpenCV local-video frames now expose BGR `payload["image"]`, list-based grayscale `payload["gray"]`, `shape` and `channels`.
- [x] MotionDetector continues using the grayscale helper; timestamp/FPS/PTS behavior is unchanged.
- [x] Added deterministic OpenCV payload contract and OpenCV-style frame → fake Ultralytics provider → normalized fact integration coverage.
- [x] Added BGR/gray public preview privacy regression and preserved existing metadata/storage redaction behavior.
- [x] Source full suite returned `371 passed`; curated verifier returned `VERIFY_OK` / `371 passed`.
- [x] Real model runtime remains unverified by design; no weights or runtime dependency were added.
- [ ] Master review and PR handoff remain pending; do not choose TASK-0003.


## TASK-0003 checkpoint — real Ultralytics pose runtime smoke (2026-09-24)

- [x] Verified the Task Packet hash and claimed the task on `codex/task-0003-real-ultralytics-pose-runtime-smoke`.
- [x] Installed the existing optional `pose` and `media` extras into the project virtual environment.
- [x] Downloaded official `yolo11n-pose.pt` and `bus.jpg` only to ignored project runtime paths.
- [x] Ran the actual model through `UltralyticsProvider` with OpenCV BGR input: 4 person detections, each with nose and both wrist keypoints.
- [x] Recorded sanitized `REAL_RUNTIME_SMOKE` evidence without raw pixels or weights.
- [x] Full source suite returned `371 passed`; curated verifier returned `VERIFY_OK` / `371 passed`; project-local basetemp cleanup passed.
- [x] No adapter bug was exposed; no source/test changes were necessary.
- [ ] Master review and PR merge remain pending; Codex must not choose TASK-0004.


## TASK-0004 checkpoint — real local-video pose-to-fact smoke (2026-09-24)

- [x] Verified the Task Packet hash and claimed the task on `codex/task-0004-real-local-video-pose-smoke`.
- [x] Reused the authorized official model/runtime and generated only an ignored two-frame AVI from `bus.jpg` for decoder coverage.
- [x] Fed the video through `FramePipeline`/`OpenCVFrameProvider`, real `UltralyticsProvider`, tracker, observation normalization and `FrameFactExtractor`.
- [x] Observed 2 decoded BGR frames and 8 person `object_detected` facts with tracker IDs, keypoints, source ID and timezone-aware timestamps.
- [x] Confirmed fact metadata had no raw pixel keys; recorded sanitized `REAL_RUNTIME_SMOKE` evidence.
- [x] Full source suite returned `371 passed`; curated verifier returned `VERIFY_OK` / `371 passed`; project-local basetemp cleanup passed.
- [x] No adapter/pipeline bug was exposed; no source/test changes were necessary.
- [ ] Master review and PR handoff remain pending; Codex must not choose TASK-0005.


## TASK-0005 checkpoint — truthful frontend Real connection state (2026-09-24)

- [x] Verified the Task Packet hash and claimed the task on `codex/task-0005-frontend-real-connection-state`.
- [x] Added Repository health checks and explicit loading/online/offline/Mock state.
- [x] Cleared stale source data on every mode switch and ignored late responses from prior sources.
- [x] Guarded review, plugin, analysis and registry actions so Real failures never fall back to Mock.
- [x] Made sidebar, dashboard, monitor, settings and media labels derive from connection/media state.
- [x] Synchronized frontend source, README/design docs and curated submission copies.
- [x] Frontend build passed; local AI service `npm run smoke:real` passed; AI suite and curated verifier passed.
- [ ] Browser click-through remains pending because the worker environment has no browser executable.
- [ ] Master review and PR handoff remain pending; Codex must not choose TASK-0006.


## TASK-0006 checkpoint — canonical skeleton contract (2026-09-25)

- [x] Verified the Task Packet hash and resumed the claimed branch `codex/task-0006-skeleton-contract` with a refreshed lock.
- [x] Added canonical COCO17 names/index/schema and validated partial named skeleton observations.
- [x] Expanded default Ultralytics normalization to all available COCO17 joints with fail-closed malformed values and custom-map compatibility.
- [x] Refactored action/fact normalization to preserve pixel-free skeleton/source/timestamp/track/continuity metadata.
- [x] Added skeleton-only upper-pipeline/privacy/action regressions; targeted 61 passed.
- [x] Full source suite returned `380 passed`; curated verifier returned `VERIFY_OK` / `380 passed`; project-local temp cleanup passed.
- [ ] Master review and PR handoff remain pending; Codex must not choose TASK-0007.
