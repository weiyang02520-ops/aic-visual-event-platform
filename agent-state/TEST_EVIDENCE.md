## 2026-09-23 — reject bool/string threshold configuration

- Added invalid-config cases across MotionDetector, CentroidTracker, RelationEngine, MedicationSequenceReasoner, and WorkshopStateReasoner. Before the fix, booleans passed as numeric 1 and numeric strings sometimes escaped as TypeError.
- Constructors now require non-boolean finite Real values for numeric thresholds and non-boolean integer values for count/area settings; invalid types raise ValueError consistently.
- Targeted provider/relation/reasoner tests returned 120 passed. Full source tests returned 173 passed with 386 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; project-local basetemp was cleaned.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 173 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 21 synchronized AI source/doc hashes matched.
- The config tests validate deterministic CPU/software contracts, not real deployment accuracy.

## 2026-09-23 — keep distinct same-time zone events

- Added a regression with one tracked object leaving two configured zones at the same timestamp, followed by a global scene observation. The old dedup key collapsed two object_removed and two object_missing candidates to one of each.
- Workshop event deduplication now includes zone ID or normalized location scope. Same-scope duplicates still collapse; distinct zone state changes retain their own evidence.
- Targeted reasoner/plugin tests returned 28 passed. The full source suite returned 155 passed with 386 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; source basetemp was cleaned.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 155 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 21 synchronized AI source/doc hashes matched.
- The regression uses synthetic zones and global observation facts; it does not establish real camera overlap behavior.

## 2026-09-23 — reject malformed explicit fixture object rows

- Added malformed-row cases for non-object entries, missing bbox, wrong bbox length, and a non-list objects field. Before the fix, FixtureDetector silently skipped them and the API job completed with no event.
- FixtureDetector now treats a missing objects key as a legitimate empty frame but raises an indexed ValueError when an explicit objects container or row is malformed.
- Targeted provider/fact-pipeline/API tests returned 39 passed. The full source suite returned 154 passed with 386 non-blocking Python 3.14 FastAPI/Starlette warnings; source basetemp was cleaned.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 154 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 21 synchronized AI source/doc hashes matched.
- This is input validation over synthetic fixtures; it does not claim real detector completeness.

## 2026-09-23 — fail closed on invalid fixture scores through API

- Added a frame-level threshold regression showing that a 50.8 px person/object gap was truncated to 50 px and incorrectly emitted near/pickup_candidate. FixtureDetector now preserves fractional coordinates through tracker and relation extraction.
- Invalid confidence values (NaN, infinity, outside [0,1], bool/string/null) are rejected by Detection; FixtureDetector adds the source object index and no longer clamps scores.
- API integration verifies an invalid fixture score marks the analysis job failed and leaves the event store empty. Targeted provider/fact-pipeline tests returned 26 passed; API regression returned 1 passed.
- Full source suite returned 149 passed with 330 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 149 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 21 synchronized AI source/doc hashes matched.
- Results verify fixture adaptation and fail-closed behavior; they do not establish real detector calibration or video accuracy.

## 2026-09-23 — tracker continuity across person-label variants

- Added regressions for Person -> person and Person -> 工作人员 while an object remains spatially close. The previous tracker used raw string equality, so both label changes allocated a new track ID despite the shared person classifier.
- CentroidTracker now treats supported person aliases as one tracking class and compares other category labels case-insensitively without merging person/object classes. A JSONL frame-to-fact test verifies the same person track ID survives the alias change.
- Targeted provider/fact-pipeline/core tests returned 36 passed. Full source suite returned 148 passed with 274 non-blocking Python 3.14 FastAPI/Starlette warnings; project-local basetemp was cleaned.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 148 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 21 synchronized source/doc hashes matched.
- These tests verify deterministic label-gated tracking on synthetic boxes; they do not measure identity tracking accuracy in real footage.

## 2026-09-23 — preserve fixture bbox precision and reject invalid scores

- Added an end-to-end JSONL frame regression: a 50.8 px person-to-medicine distance was truncated to 50 px and emitted near/pickup_candidate under the old FixtureDetector.
- FixtureDetector and Detection now preserve finite fractional bbox coordinates and reject bool/string/non-finite geometry, invalid confidence, blank labels, and malformed metadata; out-of-range/NaN scores are no longer clamped. Invalid fixture rows fail with their object index.
- Targeted provider/fact-pipeline tests returned 26 passed. Full source tests returned 145 passed with 274 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; source basetemp was cleaned.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 145 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 20 synchronized AI source/doc hashes matched.
- This validates numeric adaptation and rule thresholds over JSONL fixtures, not detector accuracy on real images.

## 2026-09-23 — direct Entity input and identity validation

- Added boundary tests for empty/non-string entity IDs and labels, bool/numeric-string bbox coordinates, invalid confidence types, normalization, and duplicate track IDs at the RelationEngine boundary.
- Entity now normalizes IDs, labels, bbox values, and confidence; it rejects invalid values before relation logic. RelationEngine rejects duplicate entity IDs before timestamp state changes, just as it rejects duplicate zone IDs.
- Targeted relation/fact-pipeline/reasoner/config tests returned 83 passed. Full source suite returned 136 passed with 274 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; source basetemp was cleaned.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 136 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 17 synchronized source/doc hashes matched.
- These checks verify input contracts and deterministic relation state only; they do not establish real detection, tracking or camera accuracy.

## 2026-09-23 — validate directly constructed scene zones

- Added regressions showing that direct Zone construction accepted blank/non-string IDs and labels, boolean/string coordinates, and whitespace IDs without normalization; duplicate zone IDs also collided in RelationEngine state. Blank zone IDs in facts were treated as equal across unrelated locations.
- Zone now validates and trims ID/label, accepts only finite non-boolean Real coordinates, and normalizes geometry to floats. RelationEngine rejects duplicate IDs before timestamp state mutation. WorkshopStateReasoner treats blank fact IDs as absent and falls back to normalized location labels.
- Targeted relations/fact-pipeline/zone-config/reasoner/API tests returned 70 passed. Full source suite returned 119 passed with 274 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; project-local basetemp was cleaned.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 119 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 17 synchronized AI source/doc hashes matched.
- Tests cover contracts and state isolation only; they do not establish real camera geometry calibration or physical scene accuracy.

## 2026-09-23 — scope explicit workshop missing facts

- Added a regression for two pending zone states on one object followed by object_missing scoped to shelf A. Before the fix, the newer bench B removal was attached as evidence and the missing event started at B's timestamp.
- A scoped explicit object_missing now consumes a pending removal only from the same zone. Unscoped explicit missing keeps the existing global behavior; explicit object_returned keeps its destination semantics, which can differ from the removal location.
- Targeted reasoner/plugin/fact-pipeline tests returned 29 passed. Full source tests returned 104 passed with 274 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; project-local basetemp was cleaned.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 104 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 15 synchronized AI source/doc hashes matched.
- This verifies scoped fact matching with synthetic region IDs and labels; no real zone calibration or scene-observation provider is present.

## 2026-09-23 — region-scoped workshop timeout evidence

- Added a regression for a tool removed from shelf A followed by an observation of bench B. Before the fix, the unrelated observation immediately produced object_missing and consumed the pending state.
- Timeout evidence now matches the removal scope when both facts provide zone/location information. If either is unscoped, existing explicit global-observation semantics are preserved.
- Targeted reasoner/plugin/fact-pipeline tests returned 28 passed. The source suite returned 103 passed with 274 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings; its project-local basetemp was removed.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 103 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 15 synchronized source/doc hashes matched.
- This verifies reasoner behavior over synthetic zone IDs and locations. No upstream scene_observed producer, physical zone calibration, or real-video absence metric exists; unscoped observations depend on an upstream global-coverage assertion.

## 2026-09-23 — independent workshop state across zones

- Added a regression for an object leaving shelf A, briefly entering and leaving bench B, then returning to both zones. Before the fix, the bench removal overwrote shelf A's pending state and the return event was missing; the new test reproduced this failure.
- WorkshopStateReasoner now keys pending removal state by tracked object and zone scope. Entering A resolves A's removal even when a later B removal exists; B remains independently resolvable.
- Targeted tests across test_algorithm_reasoner.py, test_plugins.py, and test_fact_pipeline.py returned 27 passed. The full AI source suite returned 102 passed with 274 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. The project-local basetemp was cleaned.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 102 passed. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 15 synchronized AI source/doc file hashes matched.
- This verifies deterministic facts with synthetic zone IDs and locations. It does not validate physical zone calibration, real-camera tracking, or real-video accuracy.

## 2026-09-23 — optional zone configuration and service integration

- Added strict AI_ZONES_JSON parsing and passed configured rectangles from create_app() through AnalysisService into FrameFactExtractor; unset or [] keeps the default zone list empty.
- Targeted parser/API command returned 8 passed, 3 deselected; the source full suite returned 101 passed, with 274 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Source pytest basetemp was workspace/ai-engine/.codex-pytest-temp-zones-final and was removed after the run.
- Curated submission VERIFY.ps1 -SkipFrontendBuild returned VERIFY_OK / 101 passed. The verifier now forces pytest basetemp to ai-engine/runtime/.pytest-temp, restores the prior environment setting, and cleans the runtime directory. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 109 package files, runtime absent; all 13 synchronized source/doc file hashes matched.
- The API regression uses synthetic JSONL boxes and configured pixel rectangles. It verifies object removal/return events with one object ID; it does not provide real-camera calibration, a pose model, scene_observed, or real-video accuracy evidence.

# Test Evidence

## 2026-09-22 — workspace initialization

- Check: `Test-Path` for the project root and required directories.
- Result: passed; directories exist.
- Scope: filesystem setup only.
- Limitation: no AI, frontend, repository, robot, or runtime behavior has been tested.

## 2026-09-22 — Phase 0 static audit

- Checks: tool discovery/version commands; `git rev-parse HEAD`; `git status --short --branch`; source tree and key README/proto/AppHost/controller/config inspection.
- Result: passed for static evidence; source snapshots are clean and baselines are recorded.
- Result: runtime build/test not executed because .NET SDK, Cargo and FFmpeg are unavailable.
- Evidence: `workspace/docs/PHASE0_AUDIT.md`, `ARCHITECTURE_BASELINE.md`, `INTEGRATION_NOTES.md`.

## 2026-09-22 — AI Phase 1

- Command: `PYTHONPATH=src python -m pytest -q` from `workspace/ai-engine`.
- Result: passed, 4 tests; warnings are Python 3.14 deprecations from FastAPI/Starlette.
- Covered: plugin discovery, parallel plugin evaluation, SQLite event review, health/plugins/jobs/events API, plugin enable/disable, object/person CRUD.
- HTTP smoke: launched Uvicorn on `127.0.0.1:8010`; `GET /health` = `ok`; 2 plugins loaded; `POST /api/v1/analysis/jobs` with `mock://elderly-medication` = completed; event type `suspected_medication`; review state initially `pending`.
- Limitation: Mock facts are deterministic fixtures, not model accuracy or real camera/robot evidence.

## 2026-09-22 — Source boundary and frontend

- AI command: `$env:PYTHONPATH='src'; python -m pytest -q` from `workspace/ai-engine`.
- Result: passed, 5 tests; FastAPI/Starlette Python 3.14 deprecation warnings remain non-blocking.
- Covered: `SourceResolver` for `mock://`, Windows local paths, RTMP/RTSP/HTTP stream configuration, and unsupported sources; HTTP `/api/v1/sources/inspect`.
- Frontend command: `npm run build` from `workspace/frontend`.
- Result: passed; TypeScript project build and Vite production bundle generated in `dist/` (ignored by Git).
- Frontend smoke: `npm run dev -- --host 127.0.0.1 --port 4173`; `GET /` returned HTTP 200, `text/html`, and contained the React root.
- Limitation: browser interaction, real AI API mode, real video frames, livestream-rs connectivity and robot hardware remain unverified.
- AI HTTP smoke: Uvicorn on `127.0.0.1:8010`; `/health` returned `ok`, `/api/v1/sources/inspect?source=rtmp://127.0.0.1/live/demo` returned provider `livestream-rs-adapter`, status `configured` and capabilities `stream-handoff,evidence-uri`.
- Frame pipeline extension: `PYTHONPATH=src python -m pytest -q` returned `8 passed`; coverage includes Mock timestamp spacing, JSONL malformed-line recovery, cancellation, unknown stream refusal, and `/api/v1/sources/frames`.
- Frame HTTP smoke: `/api/v1/sources/frames?source=mock://elderly-medication?frames=3&max_frames=3&interval_ms=250` returned 3 frames, indices 0–2, metadata provider `mock`.
- Detector/tracker/relations/plugins: `$env:PYTHONPATH='src'; python -m pytest -q` returned `15 passed`; coverage includes CPU frame difference connected components, centroid IDs, normalized observations, person-object relations, zone transitions, cooldown, incomplete medication, and workshop state events.

## 2026-09-22 — final regression in this turn

- AI: `$env:PYTHONPATH='src'; python -m pytest -q` returned `15 passed` (145 non-blocking Python 3.14/FastAPI deprecation warnings).
- Frontend: `npm run build` returned success; `tsc -b` and Vite production bundle both passed.
- Evidence resolver: `16 passed`; API checks fixture and conservative unavailable/provided-unverified semantics. Frontend build after evidence-status UI change passed.
- Evidence HTTP smoke: Uvicorn `127.0.0.1:8010` returned `status=fixture`, `resolver=fixture-resolver`, and a fixture URI for a Mock source/time window.
- Frontend Real API smoke: with Uvicorn on `127.0.0.1:8010`, `npm run smoke:real` returned health `ok`, 2 plugins, and successful events/objects/persons/evidence requests. This is an HTTP adapter smoke, not a browser visual acceptance.
- Local video provider: AI `python -m pytest -q` returned `18 passed`; an optional OpenCV test wrote a temporary 16x12 AVI with 2 frames and read both frames with source/timestamp/provider metadata.
- Local analysis chain: AI `python -m pytest -q` returned `20 passed`; a JSONL analysis job completed with `fact_count=1`, proving local frame → detector/tracker/relations → PrimitiveFact → job path.
- Latest regression: AI `22 passed`; frontend `npm run build` passed after model-provider changes.
- Model provider contract: AI `22 passed`; registry reports `motion_cpu` selected when ONNX is unavailable, JSONL selects fixture, and REST provider status is returned.
- Latest Real API smoke: `npm run smoke:real` returned health `ok`, 2 plugins, evidence `fixture`, and `selectedDetector=motion_cpu`.

## 2026-09-22 — media playback boundary

- Frontend: `npm run build` passed after adding `src/media.ts` DTO normalization and playback URL classification.
- Static contract: Makerverse `LivestreamEndpointDto` source snapshot was checked; adapter accepts PascalCase or lowerCamelCase and nested/flattened playback fields.
- Limitation: no running Makerverse/live session, HLS/HTTP-FLV player dependency, browser network trace, real media URL, or robot camera stream was available; this is a boundary/build result, not a real playback PASS.
- Real API HTTP smoke rerun: AI Uvicorn served `health=ok`; frontend `npm run smoke:real` returned `plugins=2`, `events=0`, `objects=0`, `persons=0`, `evidence=fixture`, `selectedDetector=motion_cpu`. The process was stopped after the check.
- Submission staging check: `workspace/submission/` contains only curated AI/frontend/docs sources and README; a recursive scan found no `__pycache__`, `.pyc`, `node_modules`, `.pytest_cache`, runtime DB, `dist`, or model files. This is a prototype staging package, not the final competition package.
- Submission AI package regression: from `workspace/submission/ai-engine`, `$env:PYTHONDONTWRITEBYTECODE='1'; python -B -m pytest -p no:cacheprovider -q` returned `27 passed`; generated runtime data was removed after verification.
- Registry embedding regression: AI `python -m pytest -q` returned `27 passed`; covers grayscale baseline vector, cosine similarity, threshold/ordering, invalid vectors, `/api/v1/registry/match`, and local fixture→analysis `PrimitiveFact.metadata.registry_matches`. This proves a deterministic CPU heuristic contract, not visual recognition accuracy.
- Real API HTTP smoke after registry addition: `npm run smoke:real` returned `health=ok`, `plugins=2`, `evidence=fixture`, `selectedDetector=motion_cpu`, and `registryMatches=0` against a clean empty registry; the new POST endpoint returned HTTP 200.
- Frontend regression after exposing optional registry embeddings in TypeScript types: `npm run build` passed (tsc + Vite production bundle).
- Frontend event filtering regression: `npm run build` passed after replacing the Events view placeholder controls with controlled query/status filters; browser interaction remains unverified without a browser session.
- Frontend Makerverse boundary regression: `npm run build` passed after wiring `MonitorLive` to the optional Makerverse adapter; no `VITE_MAKERVERSE_API_URL` was available, so real online-live/browser playback remains unverified.
- Latest HTTP smoke after registry-to-fact integration: Uvicorn + `npm run smoke:real` returned `health=ok`, `plugins=2`, `evidence=fixture`, `selectedDetector=motion_cpu`, `registryMatches=0`; all requested paths returned successful responses and the server was stopped afterward.
- Frontend event-detail regression: `npm run build` passed after adding the interactive event detail drawer and review actions; visual/browser click acceptance remains pending.
- Analysis cancellation regression: AI source and curated submission each returned `28 passed`; `test_stopped_job_does_not_run_plugins_or_save_events` verifies a stopped job remains stopped with no events. Submission runtime artifacts were removed after the check.
- Frontend async-job regression: `npm run build` passed after adding `Repository.getAnalysis` and Real-mode terminal-state polling; no browser click session was available to observe the UI toast.
- Submission provenance scan: recursive search of `workspace/submission` found no `agent-state`, actual `.env`, personal absolute Windows path, cache, runtime DB, dependency directory, build output or model artifact; placeholder token/config text is documentation only.
- Final current-version smoke: AI Uvicorn + frontend `npm run smoke:real` returned `health=ok`, `plugins=2`, `evidence=fixture`, `selectedDetector=motion_cpu`, `registryMatches=0`; server stopped after verification.
- ONNX safety regression: source and curated submission each passed `29` tests; a model file plus mocked runtime still reports unavailable when no verified input/output adapter exists.

## 2026-09-22 — current-stage report and package audit

- AI source regression rerun with `python -B -m pytest -p no:cacheprovider -q`: `29 passed`, 218 non-blocking Python 3.14/FastAPI deprecation warnings.
- Frontend `npm run build`: TypeScript and Vite production build passed.
- Real API smoke rerun with a temporary local Uvicorn process: health `ok`, 2 plugins, evidence `fixture`, selected detector `motion_cpu`, registry matches `0`; server stopped after the check.
- Added `workspace/docs/当前实现与证据总览.md`, `workspace/submission/FINAL_REPORT.md`, and `workspace/submission/MANIFEST.md`.
- Submission package scan: `bad_count=0` for cache/runtime/dependency/build/model artifacts and `absolute_path_hits=0`; package remains `STAGED_PROTOTYPE` pending teacher/robot materials and real deployment evidence.
- Material-pack audit: required P12/P13 documents, `COMPETITION_MATERIAL_PACK.md`, `THIRD_PARTY_NOTES.md`, `LICENSES.md`, and LaTeX skeleton were created and copied into `workspace/submission/docs`; no official teacher template or unverified metric was invented.
- Submission structure audit: all 15 required material/skeleton paths exist, cache/runtime/dependency/build/model scan remains clean, and no sensitive literal or personal absolute path was found. LaTeX skeleton has 12 files with balanced braces; `xelatex`, `lualatex`, and `pdflatex` are not installed, so no PDF compile was claimed.
- Frontend routing regression: after adding hash-based view routing and browser hash listeners, `npm run build` passed; browser visual/back-forward acceptance remains pending without a browser session.
- Evidence replay boundary regression: Event Detail now exposes an external replay link only for `available` evidence with a URI, and otherwise shows an explicit unverified state; `npm run build` passed.
- Current source regression after frontend route/evidence changes: AI `29 passed`; frontend `npm run build` passed; submission cleanliness scan remains `bad_count=0`, `sensitive_literal_hits=0`.
- Logging regression: source and curated submission AI tests both returned `29 passed` after lifecycle logging changes; logs are documented as metadata-only and do not claim media/model evidence.
- Ready-probe regression: `GET /ready` returned `ready=true`, `database=ok`, `plugin_manager=ok`, `detector=ok`, `tracker=ok`, `plugins=2`; frontend Real smoke still passed against the same temporary local service.
- Final current submission scan after ready/logging/frontend changes: `bad_count=0`, `sensitive_literal_hits=0`, 98 curated files.
- Submission verifier execution: `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK`; required-file and contamination checks passed, AI tests `29 passed`, generated runtime was cleaned, and final scan returned `bad_count=0` (100 curated files including verifier/docs).

## 2026-09-23 — AI algorithm reasoning and source-to-fact regression

- Temporal reasoner/plugin command from `workspace/ai-engine`: `$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONPATH='src'; python -B -m pytest -p no:cacheprovider tests/test_algorithm_reasoner.py tests/test_plugins.py -q` returned `23 passed`.
- Detector/embedding command from `workspace/ai-engine`: the targeted `tests/test_providers.py` and `tests/test_embeddings.py` run returned `21 passed`; covers source/job frame-difference reset, invalid matrix rejection, duplicate bbox track mapping, and tiny grayscale feature matrices.
- End-to-end local frame command from `workspace/ai-engine`: `tests/test_fact_pipeline.py tests/test_algorithm_reasoner.py tests/test_plugins.py` returned `25 passed`; three JSONL frames crossing a configured zone produced `left_zone` and same-zone `entered_zone`, which the workshop reasoner converted into removal and return candidates.
- Full AI command from `workspace/ai-engine`: `$env:PYTHONDONTWRITEBYTECODE='1'; $env:PYTHONPATH='src'; python -B -m pytest -p no:cacheprovider -q` returned `66 passed` in 2.85 seconds.
- Warning note: 218 Python 3.14 FastAPI/Starlette `asyncio.iscoroutinefunction` deprecation warnings; no test failures.
- Curated submission: synchronized the changed AI sources, tests, and algorithm docs; `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` and AI tests `66 passed`. Frontend build was explicitly skipped by the verifier argument.
- Post-verifier submission scan: `forbidden_artifacts=0`, `sensitive_literal_hits=0`, `file_count=104`; test runtime was cleaned. SHA-256 comparison of all 22 changed AI source/test/algorithm-document files found `hash_mismatches=0` between the main workspace and curated submission copy.
- Limits: all added algorithm paths are deterministic rules, CPU baselines, or Mock/JSONL fixtures. No real pose/action model, authorized dataset metric, live stream, or robot hardware was tested.

## 2026-09-23 — tracker assignment and relation time-order regression

- `tests/test_providers.py -q` returned `14 passed`, including two reproductions where the prior greedy matcher either chose total distance 18 instead of the optimum 10, or dropped a track despite a two-match solution.
- `tests/test_relations.py tests/test_fact_pipeline.py -q` returned `7 passed`; relation timestamps normalize to UTC and a regressing JSONL frame fails before relation state is updated.
- Dependency-free assignment check compared the Hungarian solver with brute-force permutations for 1,200 rectangular cost matrices; all minimum costs matched.
- Current AI source suite: `71 passed`, 218 third-party FastAPI/Starlette deprecation warnings.
- Curated submission: synchronized 12 updated AI code/test/document files. `VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `71 passed`; `PYTEST_ADDOPTS=--basetemp=runtime/.pytest-temp` kept pytest temp output under `workspace/submission/ai-engine/runtime/`, and the verifier removed it after tests.
- Post-verifier scan: `forbidden_artifacts=0`, `sensitive_literal_hits=0`, `file_count=104`; SHA-256 comparison across all 12 synchronized files returned `hash_mismatches=0`.

## 2026-09-23 — shared person-label extraction

- Before the fix, `tests/test_relations.py -k recognizes_person_aliases_consistently` failed for both `家属` and uppercase `Person`; the relation layer emitted no proximity/pickup facts.
- Added one shared person-label classifier for relation extraction and temporal reasoning. The end-to-end JSONL job now uses `家属` as its person label and still produces only the pending incomplete cue when no action fact exists.
- Targeted relation/core/reasoner regression: `30 passed`; pytest basetemp was explicitly under `workspace/ai-engine/` and was cleaned after the run.
- Full source suite: `73 passed`, 218 non-blocking FastAPI/Starlette deprecation warnings.
- Curated submission: synchronized 10 source/test/algorithm-doc files; verifier returned `VERIFY_OK` / `73 passed`. Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 105 files; SHA-256 mismatches across the 10 synchronized files: 0.
- The label fix validates deterministic fixture behavior; it does not supply a real object/person detector or dataset accuracy metric.
- File-boundary incident: a read-only check found `%TEMP%\pytest-of-peng\pytest-812` through `pytest-814`, containing test names from this project. Those likely came from earlier runs that used pytest's default or relative basetemp. They are outside the user-authorized root; no action was taken on them. All later test commands used an absolute project-local basetemp and cleaned that path.

## 2026-09-23 — cross-person action association and review-state check

- Added a negative case proving `KeypointActionExtractor` cannot borrow another person's `near` relation to link a hand action to medicine.
- The `AnalysisService` keypoint fixture test now also asserts the result remains `pending`, `needs_review=true`, and `medical_diagnosis=false`.
- Keypoint action tests: `4 passed`; full source suite: `78 passed`, with 218 third-party FastAPI/Starlette deprecation warnings.
- Curated submission verifier: `VERIFY_OK` / `78 passed`, using basetemp under the project root; runtime cleaned afterward. Post-scan: 0 forbidden artifacts, 0 sensitive literals, 107 files; 15 unique AI source/test/doc file hashes matched.
- All keypoint inputs remain explicit JSONL fixture/provider metadata; no real pose model or real-video metric was evaluated.

## 2026-09-23 — keypoint dropout debounce

- A regression reproduced duplicate `hand_to_face` facts when one sampled frame lost keypoints and the same wrist/object pair was detected again immediately.
- Added a one-missing-sample grace interval per tracked person/medication pair; a longer gap rearms the extractor. `FrameFactExtractor` passes frame indices so the rule is deterministic across sampled frames.
- Full source suite: `79 passed`, 218 non-blocking FastAPI/Starlette deprecation warnings. Test basetemp was an absolute path under `workspace/ai-engine/` and cleaned afterward.
- Submission synchronization/verifier for the debounce change is pending; continue to use only project-local temp directories.

## 2026-09-23 — relation geometry configuration validation

- `Entity` now rejects non-finite/invalid bounding boxes and confidence; `Zone` rejects non-finite geometry and non-positive dimensions; `RelationEngine` rejects invalid near, motion, or cooldown thresholds.
- Targeted `tests/test_relations.py tests/test_fact_pipeline.py -q`: `23 passed`, including invalid geometry/configuration boundaries and timestamp regression.
- Full source suite: `93 passed`, 218 non-blocking FastAPI/Starlette deprecation warnings; pytest basetemp was an absolute directory inside the AIC root and cleaned afterward.
- Curated submission: synchronized the relation source/tests and matching algorithm docs; `VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `93 passed` with project-local basetemp. Post-scan found 0 forbidden artifacts / 0 sensitive literals; 7 synchronized files matched SHA-256.

## 2026-09-23 — one-frame dropout end-to-end event deduplication

- Extended the two-frame keypoint AnalysisService fixture with a later keypoint dropout/reappearance; the stored `suspected_medication` event still contains exactly one `hand_to_face` fact.
- Targeted `tests/test_core.py -k local_keypoint_fixture`: `1 passed`; full AI source suite: `93 passed`.
- Curated submission test synchronized and reverified: `VERIFY_OK` / `93 passed`; post-scan 0 forbidden artifacts / 0 sensitive literals, 107 files, 1 changed test file hash matched.
- The continuity check uses explicit JSONL keypoints and remains a fixture-level debounce test, not evidence from real pose streams.

## 2026-09-23 — one-sample action-edge debounce

- Targeted `tests/test_keypoint_actions.py`: `5 passed`; a single missing keypoint sample does not re-emit the same `hand_to_face` edge, while a longer gap rearms it.
- Full source suite: `79 passed`, 218 third-party deprecation warnings.
- Curated submission: synced the keypoint extractor, frame-index forwarding, regression test, and updated AI docs; verifier returned `VERIFY_OK` / `79 passed` using project-local basetemp. Post-scan: 0 forbidden artifacts, 0 sensitive literals, 107 files; SHA-256 matched all 7 synced files.
- This is temporal debounce over explicit keypoints; it remains a CPU rule and is not calibrated on real video.

## 2026-09-23 — keypoint geometry to temporal event

- Added a keypoint-only action rule: a wrist must be near the nose, near the same medication-object box, and pass keypoint confidence thresholds; it emits one `hand_to_face` fact per continuous person/object episode.
- JSONL AnalysisService integration uses two frames: first records a person/medicine proximity cue, then explicit nose/wrist keypoints place the wrist near the face and medicine box; the resulting `suspected_medication` event retains the action fact and asserts `review_status=pending`, `needs_review=true`, and `medical_diagnosis=false`.
- Targeted command `tests/test_keypoint_actions.py tests/test_core.py tests/test_fact_pipeline.py -q`: `13 passed`.
- Full source suite: `77 passed`, 218 non-blocking FastAPI/Starlette deprecation warnings. The absolute pytest basetemp was inside `workspace/ai-engine/` and cleaned afterward.
- Curated submission: 15 changed AI source/test/algorithm-doc files synced; verifier returned `VERIFY_OK` / `77 passed` using `workspace/submission/ai-engine/runtime/.pytest-temp`. The verifier removed runtime afterward.
- The model-provider contract doc documents optional keypoint metadata; it is included in the synced set.
- Post-scan: 0 forbidden artifacts, 0 sensitive literal hits, 107 files; SHA-256 mismatches across the 15 unique synchronized files: 0.
- Limits: keypoints are explicit fixture/provider inputs. There is no real pose model or authorized video evaluation; this is a geometric CPU rule, not pose estimation from pixels.

## 2026-09-23 — reset relation continuity after detection gaps

- Reproduced three unsupported transitions after a tracked entity disappeared for one sampled frame: stale proximity emitted `putdown_candidate`, stale position emitted `motion`, and stale zone membership emitted `left_zone` when the entity reappeared elsewhere.
- `RelationEngine` now drops prior position, near-pair, and zone-membership state when an entity/pair is absent. Added two direct relation regressions and one JSONL frame-to-fact regression that retains the same tracker ID across a one-frame omission.
- Targeted `tests/test_relations.py tests/test_fact_pipeline.py -q`: `62 passed`. Full source suite: `180 passed`, with 386 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild`: `VERIFY_OK`, `180 passed`. An initial staged run was 175 because `algorithm_reasoner.py` and four tests for blank-ID normalization were stale; those AI files were synchronized and the final source/staged counts match.
- SHA-256 comparison: all 36 AI source/test/config files match; the six updated AI summary/design docs match their staged copies. The verifier's required-file and contamination scan passed. Project-local pytest temporary directories were removed after checking their exact paths.
- Evidence is synthetic JSONL/CPU behavior only. Clearing continuity may miss a transition that happens entirely while an entity is unobserved; no real occlusion, model accuracy, or robot performance is established.

## 2026-09-23 — fail closed on Boolean keypoints and preserve grayscale precision

- Reproduced Boolean wrist coordinates/confidence being treated as numeric and producing `hand_to_face`; Boolean geometry settings were accepted, and a string setting raised `TypeError` rather than the expected configuration error.
- Keypoint coordinates/confidence and action configuration now enforce finite non-Boolean numeric types; frame/missing-frame counts reject bools. Invalid keypoint/object-box geometry is ignored as missing action evidence. JSONL-to-elderly-care integration confirms a Boolean wrist cannot promote a proximity cue to `suspected_medication`.
- Reproduced MotionDetector generating motion from a Boolean pixel, truncating `100.9 → 100` and `120.0 → 120` into a false threshold crossing, and clipping `256` to `255`. It now preserves fractional grayscale and accepts only finite non-Boolean values in `[0,255]`; invalid frames clear history.
- Targeted `tests/test_keypoint_actions.py tests/test_fact_pipeline.py -q`: `26 passed`; targeted `tests/test_providers.py -q`: `43 passed`. Full source suite: `203 passed`, with 386 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild`: `VERIFY_OK`, `203 passed`. All 36 AI source/test/config hashes match; six updated AI docs match staged copies. Required-file and contamination checks passed, and project-local pytest temp directories were cleaned.
- Limits: keypoint/gray inputs are synthetic fixtures and CPU rules. No real pose model, camera noise/lighting evaluation, authorized video metrics, or hardware evidence is available.

## 2026-09-23 — reject coerced registry features

- Reproduced `[true,false]` normalizing to `[1,0]` and producing `accepted=true`; Pydantic converted numeric strings and Boolean thresholds before the match algorithm saw them. `gray_embedding` also clipped out-of-range pixels, and large finite vectors could overflow their norm into an unusable result.
- `normalize_vector`, `gray_embedding`, and `match_embeddings` now reject Boolean/string/non-finite/out-of-range inputs as appropriate, preserve fractional gray intensities, and use an overflow-resistant vector norm. API validators inspect raw values before float coercion; empty/all-zero registration vectors return HTTP 400 and are not stored, while schema type errors return 422.
- Targeted `tests/test_embeddings.py tests/test_api.py -q`: `35 passed`. Full source suite: `223 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild`: `VERIFY_OK`, `223 passed`. All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; required-file and contamination checks passed.
- Limits: all feature-matching checks use deterministic numeric fixtures and the CPU heuristic. They do not establish object/person identity accuracy.

## 2026-09-23 — preserve label-distinct medication candidates without IDs

- Reproduced two complete same-person medication sequences with missing object IDs and labels `药盒 A` / `药盒 B` collapsing to one candidate because deduplication keyed both objects as `None`.
- Candidate deduplication now keys by entity ID where available and falls back to the case-folded non-empty label. Duplicate same-label evidence still collapses; different no-ID labels remain separate.
- Added direct reasoner regressions for both sides of the rule and an elderly-care plugin test confirming two `suspected_medication` events survive into unified events. Targeted `tests/test_algorithm_reasoner.py tests/test_plugins.py -q`: `43 passed`.
- Full source suite: `226 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned `VERIFY_OK`, `226 passed`.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies. Project-local pytest temp directory was checked and removed.
- Evidence uses constructed facts. It does not establish detector identity continuity or real object similarity discrimination.

## 2026-09-23 — reject explicit non-person medication subjects

- Reproduced a subject labeled `自动发药柜` with a stable ID entering the complete medication reasoner path and producing `suspected_medication`.
- Medication anchors now require a supported person label whenever a label is present. Explicit non-person labels are rejected even with IDs; unlabeled ID-only facts retain the documented legacy compatibility path.
- Added direct tests proving both complete and incomplete inference reject the explicit non-person, plus an elderly-care plugin regression verifying it emits no event. Targeted reasoner/plugin tests returned `45 passed`.
- Full source suite: `228 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned `VERIFY_OK`, `228 passed`.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; the project-local pytest temp directory was removed.
- Evidence is constructed facts only; real person classification accuracy remains unverified.

## 2026-09-23 — validate PrimitiveFact confidence before coercion

- Reproduced Pydantic converting PrimitiveFact confidence=True to 1.0 and "0.9" to a float; malformed confidence then passed the medication reasoner's minimum-score gate and produced a complete candidate.
- PrimitiveFact confidence now requires a finite, non-Boolean real in [0,1] before Pydantic coercion. JSON integer/float scores remain supported.
- Parameterized tests cover bools, numeric strings, NaN/Infinity, and out-of-range scores. Targeted tests/test_algorithm_reasoner.py tests/test_plugins.py: 52 passed.
- Full source suite: 235 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned VERIFY_OK, 235 passed.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; project-local pytest temp directories were cleaned.
- Evidence is constructed facts, not detector confidence calibration on real video.

## 2026-09-23 — reject malformed temporal identity values

- Reproduced Boolean, fractional, and list-valued person/object IDs being converted to strings and matched across pickup and hand-to-face facts, producing `suspected_medication`.
- Temporal identity parsing now accepts only non-empty strings or integers. Explicit malformed object IDs prevent label fallback; genuinely missing/blank IDs retain the documented normalized-label fallback.
- Targeted `tests/test_algorithm_reasoner.py tests/test_plugins.py -q`: `58 passed`, including malformed person/object IDs and preserved legacy fallback cases.
- Full source suite: `241 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned `VERIFY_OK`, `241 passed`.
- All 36 AI source/test/config hashes match, seven updated AI docs match staged copies, and project-local test temp directories were cleaned.
- Evidence is constructed facts only; no real cross-frame ID stability or detector performance is established.

## 2026-09-23 — select confidence-qualified action evidence

- Reproduced a weak early hand-to-face fact causing a later valid matching action to be ignored, and a weak optional put-down fact suppressing an otherwise complete sequence.
- Complete inference now searches for the first matching hand/action at or above the confidence threshold. Low-confidence optional put-down evidence is omitted rather than included in the confidence minimum. Incomplete inference preserves the existing contract that any matching hand fact means the step was observed, even if not strong enough for a complete event.
- Added regressions for the later qualified action and weak optional support. Targeted reasoner/plugin tests returned 60 passed.
- Full source suite: `243 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned `VERIFY_OK`, `243 passed`.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; project-local pytest temp directories were cleaned.
- Evidence is constructed facts; real action confidence calibration and event accuracy remain unmeasured.

## 2026-09-23 — distinguish medicine objects from storage locations

- Reproduced medication labels 药柜、药品柜、药架、药房、medicine cabinet/shelf and pharmacy being accepted as medicine objects and producing complete suspected-medication candidates.
- The shared medication-label classifier now excludes known storage/location labels, while an explicit medicine/medication/drug category remains authoritative.
- Added direct reasoner cases and a JSONL frame-to-elderly-plugin integration test. A nearby wrist and medicine-cabinet label no longer generate hand-to-face evidence or medication events. Targeted reasoner/fact-pipeline/plugin tests returned 76 passed; the reasoner/plugin subset returned 68 passed.
- Full source suite: 252 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned VERIFY_OK, 252 passed.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; project-local pytest temp directories were cleaned.
- Limits: synthetic labels and keypoints only. Storage alias coverage and actual detector classification remain unmeasured.

## 2026-09-23 — isolate stateful motion detector sessions per job

- Reproduced a shared MotionCPUProvider losing changed-region detections when two sources interleaved: each source switch reset the other job's previous-frame state.
- MotionCPUProvider now provides a fresh session per analysis extraction; FrameFactExtractor requests that session while stateless detector providers remain reusable.
- Targeted `tests/test_model_providers.py tests/test_fact_pipeline.py -q`: `13 passed`, covering interleaved source frames and fresh provider sessions through the frame-to-fact path.
- Full source suite: `254 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned `VERIFY_OK`, `254 passed`.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; project-local pytest temp directories were cleaned.
- Limits: deterministic synthetic grayscale frames only; no real multi-camera video or motion detection accuracy is established.

## 2026-09-23 — reject overflowing bbox and zone extents

- Reproduced individually finite x/width components whose sum overflowed to infinity; Zone.contains then treated an unbounded half-plane as the configured pixel region.
- Detection, Entity, Zone, JSON zone configuration, and keypoint action bbox parsing now require finite right/bottom extents in addition to finite components.
- Targeted provider/relation/zone-config/keypoint tests returned 130 passed. Full source suite: 259 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned VERIFY_OK, 259 passed.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; project-local pytest temp directories were cleaned.
- Evidence uses synthetic extreme coordinates only; deployment camera range and calibration remain unknown.

## 2026-09-23 — prevent relation cooldown-key collisions

- Reproduced distinct person/object pairs whose IDs contain colons flattening to the same near/pickup cooldown string; the second pair's events were suppressed. A parallel case made different entity/zone combinations share a zone-entry key.
- RelationEngine now keys cooldown state with structured tuples including event type, entity IDs, and zone-edge direction.
- Targeted `tests/test_relations.py -q`: `60 passed`, including both pair and zone collision regressions.
- Full source suite: `261 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned `VERIFY_OK`, `261 passed`.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; project-local pytest temp directories were cleaned.
- Evidence uses synthetic IDs; no external source ID allocation behavior is established.

## 2026-09-23 — ignore unrepresentable keypoint numbers safely

- Reproduced an extreme but valid JSON integer raising OverflowError while converting a keypoint or bbox coordinate to float, aborting FrameFactExtractor instead of treating the action geometry as missing.
- KeypointActionExtractor now catches unrepresentable/non-finite numeric values and ignores that point/box; unrepresentable configuration values fail with ValueError.
- Targeted `tests/test_keypoint_actions.py tests/test_fact_pipeline.py -q`: `33 passed`, including JSONL-to-elderly-plugin behavior with a preserved pickup cue but no action/completion event.
- Full source suite: `265 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned `VERIFY_OK`, `265 passed`.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; project-local pytest temp directories were cleaned.
- Synthetic extreme integer inputs only; no actual pose model or real video accuracy is established.

## 2026-09-23 — propagate stop requests into running frame extraction

- Reproduced that stop_job set a job event, but AnalysisService did not pass any token to FrameFactExtractor/FramePipeline; a long-running extraction could continue after stop was requested.
- Each job now owns a CancellationToken passed through FrameFactExtractor to the frame provider. The extractor checks it between frames, and a cancellation exception is recorded as stopped rather than failed; partially extracted facts never reach plugins or storage.
- Targeted `tests/test_core.py tests/test_fact_pipeline.py tests/test_frame_pipeline.py -q`: `23 passed`. The new running-job regression blocks after frame one, issues stop, and verifies prompt worker completion with stopped status and no stored events.
- Full source suite: `266 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned `VERIFY_OK`, `266 passed`.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; project-local pytest temp directories were cleaned.
- Limitation: synchronous decode/read already in progress cannot be forcibly interrupted; cancellation is observed at frame/provider boundaries.

## 2026-09-23 — map sampled motion regions back to source pixels

- Reproduced a 320x320 image downsampled by stride 2 yielding a motion bbox in sample coordinates (15,10,2,2) even though AI zones and downstream relations use source pixels.
- MotionDetector now maps component bounds back through per-axis sample strides and clips edge cells to original dimensions. It tracks source dimensions and stride in its history key, resetting on geometry changes even when sampled matrix shape remains equal.
- Targeted `tests/test_providers.py -q`: `46 passed`, including source-pixel bbox mapping and a 320-to-480 resolution change that retains the same 160x160 sample size but resets frame history.
- Full source suite: `268 passed`, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated verifier returned `VERIFY_OK`, `268 passed`.
- All 36 AI source/test/config hashes match; seven updated AI docs match staged copies; project-local pytest temp directories were cleaned.
- Evidence uses an array-like synthetic grayscale image; OpenCV and real camera coordinate calibration remain unverified.

## 2026-09-23 — make terminal job completion atomic and idempotent

- Reproduced duplicate event persistence when a completed analysis job was rerun, and a stop/completion race that could produce inconsistent terminal status or partial event writes.
- Added per-job terminal locking and SQLiteStore.complete_job: the event batch and completed job state commit in one transaction. A stop that wins prevents event persistence; a completion that wins is returned as completed to a later stop. Completed-job reruns return the existing result.
- Added test_completed_job_rerun_does_not_duplicate_events and test_stop_racing_with_atomic_completion_returns_completed in tests/test_core.py.
- Full source suite: 270 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned VERIFY_OK, 270 passed.
- All 36 AI source/test/config hashes match; seven AI docs match staged copies; project-local pytest temp directories are clean.
- Limitation: an in-progress synchronous media read cannot be forcibly interrupted. Tests use deterministic local providers and SQLite, not real video or hardware.

## 2026-09-23 — reject input-order-dependent equal-time state transitions

- Reproduced that WorkshopStateReasoner emitted object_returned for same-timestamp left_zone and entered_zone facts when their input order was removal-first, but emitted no return when the facts were reversed.
- Pending removal evidence now binds to return or explicit missing facts only when removal time is strictly earlier. Equal-time entered_zone remains non-returning; explicit object_returned/object_missing facts remain independent candidates.
- Added four parameterized regressions across fact-order permutations. Targeted reasoner/plugin suite returned 72 passed.
- Full source suite: 274 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned VERIFY_OK, 274 passed.
- All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Limitation: constructed facts only; no real object-state/event accuracy evaluation.

## 2026-09-23 — exclude medication documents from medicine-object reasoning

- Reproduced a complete suspected_medication candidate from object_picked and hand_to_face facts whose shared object was labeled 药品说明书.
- Shared medication classification now rejects common medicine instructions, leaflets, lists, catalogs, medication records, prescription forms, and package inserts as medicine objects. An explicit upstream medicine/medication/drug category remains authoritative.
- Added 12 label cases, an explicit-category override regression, and a JSONL-to-elderly-plugin test showing that a medicine-instruction document produces neither hand_to_face nor suspected_medication.
- Targeted reasoner/plugin suite: 85 passed. Full source suite: 288 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated verifier returned VERIFY_OK, 288 passed.
- All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Limitation: synthetic labels/keypoints only; real detector semantics and event accuracy remain unmeasured.

## 2026-09-23 — reset relation cooldowns at evidence gaps and reject distance overflow

- Reproduced near/pickup, motion, and zone-entry facts being suppressed after a missing-entity gap because old cooldown keys survived after continuity state was cleared.
- RelationEngine now prunes cooldown keys for absent relation pairs/entities/zone keys. A reappearing pair or entity can begin a fresh evidence episode.
- Reproduced individually finite bbox coordinates producing infinite pair distance/displacement. Non-finite arithmetic now emits no person-object-distance, near/pickup, or motion fact.
- Added five regressions for pair, motion, and zone cooldown reset plus pair-distance and displacement overflow. Relation tests returned 65 passed.
- Full source suite: 293 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned VERIFY_OK, 293 passed.
- All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Limitation: cooldown timing and extreme coordinates use deterministic constructed inputs; deployed frame cadence and camera coordinate bounds remain unmeasured.

## 2026-09-23 — normalize numeric conversion overflow at AI boundaries

- Reproduced uncaught OverflowError from 10**1000 JSON-like values in Detection bbox/confidence, Entity bbox/confidence, Zone and AI_ZONES_JSON coordinates, CentroidTracker/RelationEngine thresholds, and reasoner thresholds. Finite but oversized durations also overflowed timedelta.
- Numeric constructors/config parsers now convert these failures to explicit ValueError. Reasoner durations are checked against timedelta range; reasoners revalidate PrimitiveFact confidence at inference to catch mutable post-construction changes.
- Added tests across providers, relations, zone config, and reasoners, including 5 post-construction confidence mutation values. Targeted numeric cases returned 53 passed; reasoner/plugin tests returned 95 passed.
- Full source suite: 311 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned VERIFY_OK, 311 passed.
- All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Limitation: synthetic extreme integers/config values only; actual camera coordinate bounds and deployment configurations remain unmeasured.

## 2026-09-23 — validate frame sampling parameters at the pipeline boundary

- Reproduced interval_ms=True being accepted as 1 ms, max_frames=True as one frame, and a fractional max_frames leaking TypeError from a provider.
- FramePipeline now rejects Boolean, fractional, string, and negative sampling values; interval_ms must fit timedelta, while max_frames=0 is a valid empty result.
- Added parameterized validation tests; tests/test_frame_pipeline.py returned 15 passed.
- Full source suite: 321 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned VERIFY_OK, 321 passed.
- All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Limitation: deterministic provider tests only; actual decoder cadence is not evaluated by these parameter-contract tests.

## 2026-09-23 — handle invalid OpenCV FPS and presentation timestamps

- Reproduced OverflowError when OpenCV reports infinite or unrepresentable FPS and when PTS is infinite or too large for timedelta.
- FPS values that are missing, non-finite, non-positive, or unrepresentable now fall back to 25 fps. Invalid/unrepresentable PTS falls back to read_index/fps. Non-finite sampling products or timestamps still outside datetime range raise FramePipelineError.
- Added eight fake-OpenCV metadata cases covering None/NaN/Infinity/negative/oversized FPS and NaN/Infinity/unrepresentable PTS. Targeted metadata tests returned 8 passed.
- Full source suite: 329 passed, with 454 non-blocking Python 3.14 FastAPI/Starlette deprecation warnings. Curated submission verifier returned VERIFY_OK, 329 passed.
- All 41 AI engine files match staged copies; six updated AI docs match staged copies; project-local pytest temp directories are clean.
- Evidence uses simulated OpenCV metadata and the local generated AVI fixture; corrupted real camera/media streams remain unverified.

## 2026-09-23 — isolate recovered JSONL observation gaps

- Reproduced a state-corruption path in `JsonlFrameProvider(recover=True)`: a malformed line was skipped, but the next valid frame could reuse pre-gap detector, tracker, relation, keypoint, and temporal-reasoner continuity.
- `JsonlFrameProvider` now marks the next valid frame with `discontinuity_before=true`, `discontinuity_reason=malformed_jsonl_record`, and the skipped line number. `FrameFactExtractor` emits `observation_gap`, starts a new `continuity_segment`, creates a fresh detector session, and resets tracker/relation/keypoint state. Medication and workshop reasoning rejects cross-segment evidence; workshop pending removals are cleared at the gap.
- Targeted recovered-gap tests (`test_frame_pipeline.py`, `test_fact_pipeline.py`, `test_relations.py`, `test_algorithm_reasoner.py`) returned `6 passed` using an absolute basetemp under `C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料\workspace\ai-engine`; the verified temp child was removed afterward.
- Targeted `tests/test_algorithm_reasoner.py tests/test_plugins.py` returned `97 passed` with absolute project-local basetemp. Full source suite returned `334 passed` with `454` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `334 passed`; its pytest basetemp was the absolute `workspace/submission/ai-engine/.codex-pytest-temp-verify` child and was removed by the script. Required-file and contamination checks passed.
- Post-verification SHA-256 comparison found `0` mismatches across all `41` non-runtime AI engine files. Eight updated AI algorithm documents match their staged copies; the only remaining source/staged docs mismatch is the known pre-existing `PHASE0_AUDIT.md` difference.
- Continuity auditor preflight could not resolve this explicit project root because the external `C:\Users\peng\Documents\工作区1\PROJECTS.json` does not register it; no external registry was modified. Evidence remains synthetic malformed-JSONL/fixture/CPU behavior and does not establish real stream recovery, model accuracy, or robot evidence.

## 2026-09-23 — AIC competition-rule and privacy-boundary review

- Read the two user-provided PDF files inside the project root with the bundled `pdfplumber` runtime and visually rendered representative pages with Poppler. The notice has 6 pages; the detailed rule summary has 30 pages. Rendered pages 1–3 and 15–18 were legible and consistent with extracted text.
- Confirmed the candidate `AI+场景创新` score: innovation 20, needs analysis 15, solution feasibility 20, implementation 15, testing/validation 10, application effect 15, summary/outlook 5. Implementation plus testing/validation total 25; the official table does not assign 25 points to validation alone.
- Recorded official material constraints from the attached rules: title <=20 Chinese characters, summary <=300 characters, solution PDF <=10 MB, MP4 demo 3–5 minutes and <=300 MB, PPT/evidence as PDFs, source attribution, originality, and removal of school/logo/advisor identity information from submitted materials.
- Mapped the user-provided transcript as design input only: camera-side skeletonization is a target privacy architecture; current fixture keypoints, CPU baseline, and cartoonized UI are not evidence that source-level privacy processing or gait identity has been implemented.
- Added `workspace/docs/AIC_ALGORITHM_COMPETITION_ALIGNMENT.md` and updated the AI algorithm, experiment, material-pack, readiness, and evidence-summary documents; corresponding AI docs were synchronized to `workspace/submission/docs/`. No source code or test behavior was changed by this rules review.
- After synchronization, `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `334 passed` with the absolute project-local pytest temp child cleaned. AI hashes remain `0` mismatches across 41 files; docs have `0` mismatches except the known pre-existing `PHASE0_AUDIT.md` difference.
- The PDF files are treated as the user-provided rule version; the official website/registration system was not independently checked for later revisions. Real user needs, privacy processing, model metrics, application effects, and robot evidence remain open.

## 2026-09-23 — redact raw pixel matrices from frame preview API

- Reproduced a privacy-boundary leak: a JSONL frame whose payload contained a top-level `gray` matrix was returned by `/api/v1/sources/frames` with the raw pixel values, while the older sanitizer only handled OpenCV's `image` key.
- `_frame_payload_for_api` now replaces top-level `image`, `gray`, `pixels`, and `raw_pixels` values with an encoding and shape summary. Fixture object rows and other non-pixel metadata remain available for local preview/debugging.
- Added `test_api_frame_preview_redacts_fixture_pixel_matrices`; API tests returned `8 passed`. Full source suite returned `335 passed` with `508` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `335 passed`; the absolute project-local pytest temp child was removed. All `41` AI engine file hashes match; docs have no mismatches except the known pre-existing `PHASE0_AUDIT.md` difference.
- This only protects the REST preview serialization boundary. It does not prove camera-side skeletonization, absence of raw pixels in provider memory, or end-to-end privacy compliance.

## 2026-09-23 — require workshop continuity segments for state matching

- Reproduced a temporal state leak in `WorkshopStateReasoner`: a caller could omit `observation_gap`, and a later segment's return, explicit missing, or scene observation could still consume a pending removal from the earlier segment.
- `_latest_pending_key` now filters pending removals by the current fact's `continuity_segment`; timeout observation matching applies the same requirement. Explicit `object_returned` and `object_missing` remain standalone candidates when no same-segment removal exists.
- Added `test_workshop_reasoner_does_not_pair_explicit_transitions_across_segments` and `test_workshop_reasoner_does_not_use_scene_observation_from_another_segment`. Reasoner/plugin tests returned `99 passed`; full source suite returned `337 passed` with `508` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `337 passed`; all `41` AI engine hashes match and the project-local absolute pytest temp child was cleaned. The only docs hash difference remains the known pre-existing `PHASE0_AUDIT.md` mismatch.
- Facts without continuity metadata remain compatible with segment 0. This is synthetic fact/fixture evidence; real upstream segment propagation and camera event accuracy remain unmeasured.

## 2026-09-24 — recursively redact nested frame pixel fields and audit reference DOCX works

- Reproduced nested frame-preview leakage for `Image-Data`, camelCase `rawPixels`, `depth_map`, and other sensor arrays that bypassed the previous top-level sanitizer.
- Frame preview serialization now normalizes key names, recursively traverses dictionaries/lists, and redacts recognized image, RGB/BGR, grayscale, pixel, depth, thermal, infrared, and raw-frame fields to encoding/shape summaries. Pose keypoints, labels, objects, and other non-pixel metadata remain available.
- Added `test_api_frame_preview_redacts_nested_image_and_sensor_arrays`; targeted nested privacy tests returned 2 passed. Full source suite returned `338 passed` with `562` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `338 passed`; the absolute project-local pytest temp child was cleaned. AI hashes remain synchronized; docs differ only at known `PHASE0_AUDIT.md`.
- Read the four user-provided DOCX reference works under `算法精英/` with bundled `python-docx`: `智隐云眸最新V1`, `物联网应用类作品技术文档【终稿】002`, `面向复杂实验室环境的多模态感知 (1)`, and `MoMaGen`. Recorded reusable methods and source-specific claim boundaries in `workspace/docs/REFERENCE_ALGORITHM_AUDIT.md`; original DOCX files were not modified.
- DOCX PNG rendering was attempted through the packaged renderer but the environment has no LibreOffice `soffice.exe`; structural text/table/image inspection succeeded, while layout-level visual QA remains unavailable until a renderer is supplied. This does not upgrade any external metric or hardware claim.

## 2026-09-24 — schedule AI algorithm analysis work packages

- Added `workspace/docs/AI_ALGORITHM_ANALYSIS_PLAN.md` and synchronized it to `workspace/submission/docs/`. The plan schedules P0 privacy/schema, P1 detector/pose/tracking, P2 temporal scenes, P3 multimodal quality gating, and P4 real hardware validation.
- The plan explicitly treats the three supplied DOCX files as reference methods and source-specific claims. It does not import their model names, accuracy values, hardware parameters, or experiment results into the current evidence.
- No source behavior changed in this planning update. The curated package remains bounded to the AI scope and will be reverified after any subsequent code change.

## 2026-09-24 — isolate keypoint action state by source

- Reproduced a reusable `KeypointActionExtractor` carrying episode debounce state and frame-index monotonicity from one source into the next source. A valid first action in the new source could be suppressed, or a source-local frame index reset could raise an error.
- The extractor now resets episode/frame state when observation `source_id` changes and rejects a single call that mixes multiple sources. `FrameFactExtractor` already creates a fresh extractor per analysis job; this closes the reusable component boundary as well.
- Added `test_keypoint_action_resets_episode_state_when_source_changes` and `test_keypoint_action_rejects_mixed_sources_in_one_frame`. Full source suite returned `340 passed` with `562` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated synchronization is complete for the keypoint source, tests, and docs. Real pose-model identity stability is not established.

- Final curated verification for this checkpoint: `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `340 passed`; the absolute project-local pytest temp child was removed.

## 2026-09-24 — propagate and enforce source provenance for keypoint relations

- Reproduced a source-mixing path: observations from one camera/source and a `near`/`pickup_candidate` relation fact from another could share the same IDs and create `hand_to_face` evidence.
- `FrameFactExtractor` now propagates `source_id` into object, relation, action, and observation-gap fact metadata. `KeypointActionExtractor` rejects mixed-source observations and relation facts whose explicit source differs; legacy relation facts without source metadata remain compatible.
- Added `test_keypoint_action_rejects_relation_from_another_source` and source metadata coverage in `test_local_jsonl_frames_become_unified_facts`. Full source suite returned `341 passed` with `562` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `341 passed`; all `41` AI engine hashes remain matched and the absolute project-local pytest temp child was cleaned.
- This validates local provenance contracts only; it does not establish cross-camera identity or re-identification accuracy.

## 2026-09-24 — require same-frame relation evidence for keypoint actions

- Reproduced a stale-evidence path: current-frame keypoints and object boxes could reuse an older `near`/`pickup_candidate` relation with the same IDs and emit `hand_to_face`.
- KeypointActionExtractor now requires one UTC frame timestamp for all observations in a call and ignores relation facts whose timestamp differs; timezone-equivalent timestamps are normalized before comparison.
- Added stale-relation, mixed-frame, and equivalent-timezone regressions. Full source suite returned `344 passed` with `562` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild` returned `VERIFY_OK` / `344 passed`; all `41` AI engine hashes remain matched and the absolute project-local pytest temp child was cleaned.
- This verifies local timestamp contracts only; real decoder clock precision and pose-model latency remain unmeasured.


## 2026-09-24 — explicit source provenance isolation in temporal reasoners

- Scope: AI code only. No hardware, robot, camera calibration, frontend, real model or field data was changed or used.
- Regression target: prevent a medication pickup/hand action, workshop removal/return, or workshop removal/observation timeout from combining facts whose explicit `metadata.source_id` values differ.
- Implementation: `algorithm_reasoner.py` now compares conservative source signatures at every multi-fact pairing point and keys pending workshop state by source; malformed explicit source values fail closed for pairing, while provenance-free legacy facts remain unknown-source compatible. `KeypointActionExtractor` records the observation source on emitted action facts.
- Targeted command: `python -m pytest tests/test_algorithm_reasoner.py tests/test_keypoint_actions.py -q --basetemp C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料\workspace\ai-engine\.codex-pytest-temp-source-isolation` → `125 passed`.
- Full source command: `python -m pytest -q --basetemp C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料\workspace\ai-engine\.codex-pytest-temp-full-source` → `348 passed`, `562` non-blocking Python 3.14 FastAPI/Starlette deprecation warnings.
- Curated command: `powershell -NoProfile -ExecutionPolicy Bypass -File .\workspace\submission\VERIFY.ps1 -SkipFrontendBuild` → `VERIFY_OK`, curated suite `348 passed`, same `562` warnings.
- Cleanup: both project-local pytest temp children were removed; no default/system TEMP basetemp was used for these runs.
- Evidence class: `LOCAL_ONLY` / `MOCK_OR_LOCAL`; source matching is verified, but real cross-camera re-identification and model quality remain unmeasured.


## 2026-09-24 — shared pixel-metadata privacy boundary (P0)

- Scope: AI code, tests, algorithm docs, curated AI submission and agent-state only. Hardware, robot control, camera calibration, frontend and real model/data work remain out of scope.
- Implementation: `visual_event_ai/privacy.py` recursively replaces recognized image/pixel/depth/thermal/infrared/raw-frame arrays with encoding/shape summaries. `FrameFactExtractor` sanitizes detector/relation metadata before facts; `/api/v1/vision/preview` sanitizes observation metadata; `AnalysisService.create_job` and SQLite job/event serialization sanitize metadata before returning or persisting it.
- Targeted commands: privacy/fact/core/api selection returned `35 passed`; API-only regression returned `10 passed`; every run used an absolute basetemp under `workspace\ai-engine` and the verified temp child was removed.
- Full source command: `python -m pytest -q --basetemp C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料\workspace\ai-engine\.codex-pytest-temp-full-privacy` → `352 passed`, `616` non-blocking deprecation warnings.
- Curated command: `powershell -NoProfile -ExecutionPolicy Bypass -File .\workspace\submission\VERIFY.ps1 -SkipFrontendBuild` → `VERIFY_OK`, curated suite `352 passed`, `616` warnings; verifier contamination scan passed.
- Evidence class: `LOCAL_ONLY` / `MOCK_OR_LOCAL`. The contract protects software API/storage boundaries; it does not prove camera-side skeletonization or raw-frame deletion at an external source.


## 2026-09-24 — software multimodal quality gate (P3)

- Scope: optional channel quality metadata only; no physical sensor, robot, camera calibration, frontend or real model/data work.
- Contract: `metadata.channel_quality` entries require non-empty channel names, boolean `available`, finite `[0,1]` `score`, optional string `reason`; `quality_required_channels` is an optional list.
- Behavior: absent metadata leaves the CPU/fixture path unchanged; one or more usable channels permits inference and marks facts with a safe `quality_gate.degraded` summary when needed; no usable or required channel failure emits `observation_gap`, increments continuity, resets detector/tracker/relation/keypoint state and skips the frame; malformed metadata raises `QualityContractError`.
- Targeted command: `python -m pytest tests/test_quality.py tests/test_fact_pipeline.py -q --basetemp C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料\workspace\ai-engine\.codex-pytest-temp-quality` → `25 passed`.
- Full source command: `python -m pytest -q --basetemp C:\Users\peng\Desktop\AIC算法大赛-机器人智能识别项目资料\workspace\ai-engine\.codex-pytest-temp-full-quality` → `363 passed`, `616` non-blocking deprecation warnings.
- Curated command: `powershell -NoProfile -ExecutionPolicy Bypass -File .\workspace\submission\VERIFY.ps1 -SkipFrontendBuild` → `VERIFY_OK`, curated suite `363 passed`, `616` warnings; contamination scan passed.
- Cleanup: all quality-test basetemp children were absolute paths under `workspace\ai-engine` and were removed after each run.
- Evidence class: `LOCAL_ONLY` / `MOCK_OR_LOCAL`; this is a software fallback contract, not real sensor quality or timestamp synchronization evidence.


## 2026-09-24 — TASK-0001 optional Ultralytics provider

- Branch: `codex/task-0001-real-vision-provider`; task hash verified against LF-normalized `.ai/tasks/TASK-0001.md`.
- Adapter: optional `UltralyticsProvider` registered as `ultralytics`; normalizes person boxes/confidence and COCO17 nose/wrist keypoints into the existing detection path.
- Targeted command: `python -B -m pytest -p no:cacheprovider tests/test_ultralytics_provider.py tests/test_model_providers.py tests/test_fact_pipeline.py tests/test_api.py -q --basetemp <project-root>\workspace\ai-engine\.codex-pytest-temp-task-0001` → `35 passed`.
- Full source command: `python -B -m pytest -p no:cacheprovider -q --basetemp <project-root>\workspace\ai-engine\.codex-pytest-temp-task-0001-full` → `368 passed`, 616 non-blocking deprecation warnings.
- Curated command: `powershell -NoProfile -ExecutionPolicy Bypass -File .\workspace\submission\VERIFY.ps1 -SkipFrontendBuild` → `VERIFY_OK`, `368 passed`, 616 warnings.
- Real smoke: `importlib.util.find_spec("ultralytics")` returned `None`; `AI_ULTRALYTICS_MODEL_PATH` was unset. No network download or model weight was used.
- Cleanup: project-local basetemp children were removed after verification.
- Evidence class: `LOCAL_ONLY` / offline fake-result contract; real model runtime remains `UNVERIFIED`.


## 2026-09-24 — TASK-0001 R1 environment-path fix

- Master R1 blocker: registry-created `UltralyticsProvider()` did not read documented `AI_ULTRALYTICS_MODEL_PATH`.
- Fix: provider constructor now reads the environment path when no explicit path is passed; registry selection and status are covered with an offline temporary placeholder and stubbed package discovery.
- Targeted command: `python -B -m pytest -p no:cacheprovider tests/test_model_providers.py tests/test_ultralytics_provider.py -q --basetemp <project-root>\workspace\ai-engine\.codex-pytest-temp-task-0001-r1` → `10 passed`.
- Full source command: `python -B -m pytest -p no:cacheprovider -q --basetemp <project-root>\workspace\ai-engine\.codex-pytest-temp-task-0001-r1-full` → `369 passed`, 616 non-blocking warnings.
- Curated command: `powershell -NoProfile -ExecutionPolicy Bypass -File .\workspace\submission\VERIFY.ps1 -SkipFrontendBuild` → `VERIFY_OK`, `369 passed`, 616 warnings.
- Real smoke: not run; optional package and model weights remain absent.
- Cleanup: all R1 basetemp children were absolute project-local paths and were removed.


## 2026-09-24 — TASK-0002 local video pixel bridge

- Branch: `codex/task-0002-local-video-pixel-bridge`; task hash verified against LF-normalized `.ai/tasks/TASK-0002.md`.
- OpenCV payload: decoded BGR `image`, list-based `gray`, shape and channels; MotionDetector reads `gray`.
- Targeted command: `python -B -m pytest -p no:cacheprovider tests/test_frame_pipeline.py tests/test_ultralytics_provider.py tests/test_fact_pipeline.py tests/test_api.py tests/test_privacy.py -q --basetemp <project-root>\workspace\ai-engine\.codex-pytest-temp-task-0002` → `57 passed`.
- Full source command: `python -B -m pytest -p no:cacheprovider -q --basetemp <project-root>\workspace\ai-engine\.codex-pytest-temp-task-0002-full` → `371 passed`, 616 non-blocking warnings.
- Curated command: `powershell -NoProfile -ExecutionPolicy Bypass -File .\workspace\submission\VERIFY.ps1 -SkipFrontendBuild` → `VERIFY_OK`, `371 passed`, 616 warnings.
- Privacy evidence: API frame preview regression confirms BGR and gray arrays are summarized; existing fact/job/event/SQLite redaction tests remain green.
- Real smoke: not run; model weights/runtime dependency absent by task design.
- Cleanup: project-local basetemp children were removed.


## 2026-09-24 — TASK-0003 real runtime smoke

- Runtime identity: Python 3.12.10, `ultralytics 8.4.161`, `torch 2.14.0+cpu`, OpenCV 5.0.0, CPU.
- Official `yolo11n-pose.pt` loaded from the ignored project runtime path and ran through `UltralyticsProvider` on official `bus.jpg`; 4 normalized `person` detections were returned, all with `nose`, `left_wrist` and `right_wrist`.
- Evidence class: `REAL_RUNTIME_SMOKE`; one-sample wall-clock time was about 1.438 seconds and is not a benchmark.
- Full source command used an absolute project-local basetemp under `workspace\ai-engine`: `371 passed`, 1 non-blocking warning.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild`: `VERIFY_OK`, `371 passed`, 616 non-blocking warnings; contamination scan passed.
- The project-local basetemp was removed after verification. Model weights/sample media/venv/runtime caches remain ignored and untracked.
- This does not establish accuracy, real-video metrics, privacy-source processing, production deployment or robot evidence.


## 2026-09-24 — TASK-0004 real local-video source-to-fact smoke

- Input: ignored project-local two-frame `runtime/samples/task-0004-bus.avi`, generated from official public `bus.jpg` solely to exercise OpenCV.
- `FramePipeline` decoded 2 frames through `OpenCVFrameProvider`, and BGR payloads reached the registry-selected real `UltralyticsProvider`.
- `FrameFactExtractor` produced 8 person `object_detected` facts with tracker IDs 1–4 on each frame; every fact retained nose, left_wrist and right_wrist keypoints.
- Source ID remained `runtime/samples/task-0004-bus.avi`; all timestamps were timezone-aware UTC; fact metadata had no raw pixel keys.
- Runtime identity: Python 3.12.10, `ultralytics 8.4.161`, `torch 2.14.0+cpu`, OpenCV 5.0.0, CPU. Decode and full-path timings were about 0.078 s and 3.074 s, explicitly non-benchmark.
- Full source command used an absolute project-local basetemp under `workspace\ai-engine`: `371 passed`, 1 non-blocking warning.
- Curated `workspace/submission/VERIFY.ps1 -SkipFrontendBuild`: `VERIFY_OK`, `371 passed`, 616 non-blocking warnings; contamination scan passed.
- The project-local basetemp was removed after verification; video/model/image/venv/runtime artifacts remain ignored and untracked.
- Evidence class: `REAL_RUNTIME_SMOKE`; no accuracy, scene-event, camera privacy or robot claim.
