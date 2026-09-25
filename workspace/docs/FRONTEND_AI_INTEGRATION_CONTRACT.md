# Frontend ↔ AI Integration Contract

Status: `READY_FOR_MASTER_FREEZE` (TASK-0010; Master must approve the freeze)
Last updated: 2026-09-25

This document freezes the fields and meanings that frontend work may consume. It does not add a REST endpoint or promise that every optional field is present in every source.

## 1. Event object and review state

The existing event API returns a `UnifiedEvent` with:

```json
{
  "event_id": "uuid",
  "schema_version": "1.0",
  "plugin_id": "elderly_care",
  "plugin_version": "0.1.0",
  "event_type": "suspected_medication",
  "title": "reviewable title",
  "description": "explainable description",
  "source_id": "camera://one",
  "started_at": "2026-01-01T08:00:00Z",
  "ended_at": "2026-01-01T08:00:02Z",
  "confidence": 0.74,
  "severity": "low|medium|high|info",
  "review_status": "pending|confirmed|rejected",
  "subject": {"id": "track-1", "label": "老人"},
  "object": {"id": "track-2", "label": "药盒"},
  "location": "药品架",
  "facts": [],
  "evidence": [],
  "metadata": {}
}
```

`review_status` is a human review state. `pending` and a high confidence do not mean medical or physical certainty. Frontend labels must preserve `suspected`, `candidate`, `incomplete`, `missing`, and `needs review` semantics.

## 2. Primitive facts and provenance

Every fact may carry:

- `fact_type`;
- timezone-aware `timestamp`;
- `[0,1]` `confidence`;
- optional `subject`, `object`, `location`;
- `metadata.source_id`;
- `metadata.continuity_segment`;
- track/entity IDs and safe geometry/provenance.

`source_id` identifies an input source, not a person identity. `continuity_segment` increments after an observation gap or quality boundary. Frontend must not join facts across source or continuity values merely because numeric IDs match.

## 3. Skeleton/keypoint input

The canonical skeleton payload is metadata-only:

```json
{
  "schema": "coco17",
  "version": "1.0",
  "source_id": "camera://one",
  "timestamp": "2026-01-01T08:00:00Z",
  "track_id": "track-1",
  "continuity_segment": 0,
  "keypoints": {
    "nose": [20.0, 20.0, 0.90],
    "left_wrist": [24.0, 25.0, 0.88]
  }
}
```

Keypoints are `[x_px, y_px, confidence]`. Missing joints are allowed; malformed values fail closed. Raw RGB/BGR/gray/image arrays are not part of the frontend AI evidence contract. A cartoon/avatar view may render these points, but it must not imply source-camera deletion or identity recognition.

## 4. Object and last-known location

Object observations use `subject` for the tracked entity:

```json
{
  "fact_type": "object_detected|object_in_zone|entered_zone|left_zone",
  "subject": {"track_id": 2, "label": "tool box"},
  "object": {"bbox": [x, y, width, height], "zone_id": "shelf-a"},
  "location": "工具架 A",
  "metadata": {"source_id": "camera://one", "continuity_segment": 0}
}
```

`VisualMemory` returns last-known records with source, continuity, track identity, `last_seen_at`, last bbox, current/last zone and provenance. A last-known location is historical evidence, not proof that the object is currently present. Same-label candidates remain a list.

## 5. Temporal history

`TemporalVisualMemory` records use:

- `fact_type`;
- UTC `timestamp`;
- `source_id` and `continuity_segment`;
- `confidence`;
- `subject_id`/`subject_label`;
- `object_id`/`object_label`;
- `location`/`zone_id`;
- sanitized subject/object and metadata.

`recent_actions()` is newest-first; `timeline()` is chronological. The memory is bounded and may evict old records. `object_detected` updates location memory but is not an action-history item.

## 6. Medication-plan review cues

`MedicationPlanEvaluator` may emit only:

- `plan_match_candidate`;
- `early_candidate`;
- `late_candidate`;
- `wrong_item_candidate`;
- `unresolved_candidate`.

Each cue carries entry ID when resolved, observed time, source/continuity, confidence, evidence facts and `review_required=true`, `medical_diagnosis=false`. Optional configured `plan_note`/`plan_dose` are configuration echoes. Frontend must never display these cues as proof of swallowing, treatment correctness, dosage correctness or diagnosis.

## 7. Provider and readiness status

`GET /api/v1/providers/detectors` returns provider rows with:

- `provider_id`, `version`, `available`, `selected`, `reason`, `model_path`;
- for composed Ultralytics: `component`, `pose_available`, `object_available`, `object_model_path`, `object_reason`.

`available=true` for the composition means the pose primary path is available; it does not guarantee semantic object availability. `/ready` reports service/database/plugin/detector state and may be `degraded` when the optional provider is unavailable.

## 8. Evidence resolver states

Evidence is explicit and conservative:

- `available`: a verified replay URI exists;
- `fixture`: deterministic local evidence;
- `provided_unverified`: a URI was provided but retention/time alignment is not verified;
- `unavailable`/`unsupported`: no safe resolver is available;
- `designed`: event evidence window is recorded but not externally resolved.

Frontend may show a replay action only for `available` evidence with a URI. It must not synthesize HLS/RTSP/MinIO links.

## 9. Privacy and optional fields

The frontend must tolerate missing `subject`, `object`, `location`, `zone_id`, `track_id`, `keypoints`, `evidence.uri`, `model_path` and optional provider components. It must not expect raw images in facts, events, memory records or logs. Shapes/encodings may be shown as diagnostics, not pixel values.

## 10. Stable contract checklist for the next frontend phase

- [ ] Dashboard renders event title, severity, confidence and review state without upgrading candidate semantics.
- [ ] Skeleton/cartoon view consumes only canonical schema/keypoints and handles missing joints.
- [ ] Object-location UI shows `last_seen_at`, current/last zone and “last known” wording.
- [ ] Recent-action timeline uses newest-first `recent_actions` and chronological `timeline` correctly.
- [ ] Medication UI renders the five review cue values and keeps medical disclaimers/人工复核 state.
- [ ] Provider panel distinguishes pose availability from optional semantic-object availability.
- [ ] Empty/loading/offline/degraded states remain explicit; no fallback silently changes source truth.
- [ ] Privacy labels explain software boundary redaction versus unverified camera-edge deletion.
- [ ] Evidence replay is enabled only for `available` + URI and otherwise shows the resolver state.
- [ ] Frontend does not infer cross-camera identity, model accuracy, robot action, medical certainty or hardware validation.
